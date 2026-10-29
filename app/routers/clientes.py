from fastapi import APIRouter, HTTPException
from pymysql.err import IntegrityError

from app.database import conectar
from app.schemas import ClienteCrear, ClienteRespuesta, PedidoResumen

router = APIRouter(prefix="/clientes", tags=["Clientes"])

MYSQL_ERROR_DUPLICADO = 1062
MYSQL_ERROR_LLAVE_FORANEA = 1451


@router.get("", response_model=list[ClienteRespuesta])
def listar_clientes():
    with conectar() as db, db.cursor() as cur:
        cur.execute("SELECT id, nombre, correo FROM clientes ORDER BY id")
        return cur.fetchall()


@router.get("/{cliente_id}", response_model=ClienteRespuesta)
def obtener_cliente(cliente_id: int):
    with conectar() as db, db.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, correo FROM clientes WHERE id = %s", (cliente_id,)
        )
        cliente = cur.fetchone()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/{cliente_id}/pedidos", response_model=list[PedidoResumen])
def listar_pedidos_de_cliente(cliente_id: int):
    with conectar() as db, db.cursor() as cur:
        cur.execute("SELECT id FROM clientes WHERE id = %s", (cliente_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        cur.execute(
            """
            SELECT p.id, p.cliente_id, c.nombre AS cliente,
                   p.fecha, p.estado, p.total
            FROM pedidos p
            JOIN clientes c ON c.id = p.cliente_id
            WHERE p.cliente_id = %s
            ORDER BY p.fecha DESC, p.id DESC
            """,
            (cliente_id,),
        )
        return cur.fetchall()


@router.post("", response_model=ClienteRespuesta, status_code=201)
def crear_cliente(datos: ClienteCrear):
    try:
        with conectar() as db, db.cursor() as cur:
            cur.execute(
                "INSERT INTO clientes (nombre, correo) VALUES (%s, %s)",
                (datos.nombre, str(datos.correo)),
            )
            nuevo_id = cur.lastrowid
            cur.execute(
                "SELECT id, nombre, correo FROM clientes WHERE id = %s", (nuevo_id,)
            )
            return cur.fetchone()
    except IntegrityError as exc:
        if exc.args and exc.args[0] == MYSQL_ERROR_DUPLICADO:
            raise HTTPException(
                status_code=409, detail="El correo electrónico ya está registrado"
            ) from exc
        raise


@router.put("/{cliente_id}", response_model=ClienteRespuesta)
def actualizar_cliente(cliente_id: int, datos: ClienteCrear):
    try:
        with conectar() as db, db.cursor() as cur:
            cur.execute(
                "SELECT id FROM clientes WHERE id = %s FOR UPDATE", (cliente_id,)
            )
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            cur.execute(
                "UPDATE clientes SET nombre = %s, correo = %s WHERE id = %s",
                (datos.nombre, str(datos.correo), cliente_id),
            )
            cur.execute(
                "SELECT id, nombre, correo FROM clientes WHERE id = %s", (cliente_id,)
            )
            return cur.fetchone()
    except IntegrityError as exc:
        if exc.args and exc.args[0] == MYSQL_ERROR_DUPLICADO:
            raise HTTPException(
                status_code=409, detail="El correo electrónico ya está registrado"
            ) from exc
        raise


@router.delete("/{cliente_id}", status_code=204)
def eliminar_cliente(cliente_id: int):
    try:
        with conectar() as db, db.cursor() as cur:
            cur.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
    except IntegrityError as exc:
        if exc.args and exc.args[0] == MYSQL_ERROR_LLAVE_FORANEA:
            raise HTTPException(
                status_code=409, detail="El cliente tiene pedidos asociados"
            ) from exc
        raise