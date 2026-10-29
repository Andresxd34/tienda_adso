from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.database import conectar
from app.schemas import PedidoCrear, PedidoDetalle, PedidoResumen

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

CENTAVOS = Decimal("0.01")


def _consultar_pedido(cur, pedido_id: int) -> dict | None:
    cur.execute(
        """
        SELECT p.id, p.cliente_id, c.nombre AS cliente,
               p.fecha, p.estado, p.total
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        WHERE p.id = %s
        """,
        (pedido_id,),
    )
    pedido = cur.fetchone()
    if pedido is None:
        return None

    cur.execute(
        """
        SELECT d.producto_id, pr.nombre AS producto, d.cantidad,
               d.precio_unitario, d.subtotal
        FROM detalle_pedidos d
        JOIN productos pr ON pr.id = d.producto_id
        WHERE d.pedido_id = %s
        ORDER BY d.id
        """,
        (pedido_id,),
    )
    pedido["items"] = cur.fetchall()
    return pedido


@router.post("", response_model=PedidoDetalle, status_code=201)
def crear_pedido(datos: PedidoCrear):
    cantidades = {item.producto_id: item.cantidad for item in datos.items}
    ids_ordenados = sorted(cantidades)

    with conectar() as db, db.cursor() as cur:
        cur.execute("SELECT id FROM clientes WHERE id = %s", (datos.cliente_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        marcadores = ", ".join(["%s"] * len(ids_ordenados))
        cur.execute(
            f"""
            SELECT id, precio, stock
            FROM productos
            WHERE id IN ({marcadores})
            ORDER BY id
            FOR UPDATE
            """,
            tuple(ids_ordenados),
        )
        productos = {fila["id"]: fila for fila in cur.fetchall()}

        faltantes = [pid for pid in ids_ordenados if pid not in productos]
        if faltantes:
            lista = ", ".join(str(pid) for pid in faltantes)
            raise HTTPException(
                status_code=404, detail=f"Producto(s) no encontrado(s): {lista}"
            )

        sin_stock = [
            pid for pid in ids_ordenados if productos[pid]["stock"] < cantidades[pid]
        ]
        if sin_stock:
            lista = ", ".join(str(pid) for pid in sin_stock)
            raise HTTPException(
                status_code=409,
                detail=f"Stock insuficiente para el/los producto(s): {lista}",
            )

        detalles = []
        total = Decimal("0.00")
        for pid in ids_ordenados:
            precio = productos[pid]["precio"]
            cantidad = cantidades[pid]
            subtotal = (precio * cantidad).quantize(CENTAVOS)
            total += subtotal
            detalles.append((pid, cantidad, precio, subtotal))

        cur.execute(
            "INSERT INTO pedidos (cliente_id, estado, total) VALUES (%s, 'confirmado', %s)",
            (datos.cliente_id, total),
        )
        pedido_id = cur.lastrowid

        for pid, cantidad, precio, subtotal in detalles:
            cur.execute(
                """
                INSERT INTO detalle_pedidos
                    (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (pedido_id, pid, cantidad, precio, subtotal),
            )
            cur.execute(
                "UPDATE productos SET stock = stock - %s WHERE id = %s",
                (cantidad, pid),
            )

        return _consultar_pedido(cur, pedido_id)


@router.get("", response_model=list[PedidoResumen])
def listar_pedidos(
    pagina: Annotated[int, Query(ge=1)] = 1,
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
):
    with conectar() as db, db.cursor() as cur:
        cur.execute(
            """
            SELECT p.id, p.cliente_id, c.nombre AS cliente,
                   p.fecha, p.estado, p.total
            FROM pedidos p
            JOIN clientes c ON c.id = p.cliente_id
            ORDER BY p.id DESC
            LIMIT %s OFFSET %s
            """,
            (limite, (pagina - 1) * limite),
        )
        return cur.fetchall()


@router.get("/{pedido_id}", response_model=PedidoDetalle)
def obtener_pedido(pedido_id: int):
    with conectar() as db, db.cursor() as cur:
        pedido = _consultar_pedido(cur, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido