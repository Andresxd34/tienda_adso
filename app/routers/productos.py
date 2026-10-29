from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.database import conectar
from app.schemas import ProductoCrear, ProductoRespuesta

router = APIRouter(prefix="/productos", tags=["Productos"])


def _escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=list[ProductoRespuesta])
def listar_productos(
    buscar: Annotated[str | None, Query(max_length=100)] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
):
    sql = "SELECT id, nombre, precio, stock FROM productos"
    params: list = []
    if buscar:
        sql += " WHERE nombre LIKE %s"
        params.append(f"%{_escapar_like(buscar)}%")
    sql += " ORDER BY id LIMIT %s OFFSET %s"
    params.extend([limite, (pagina - 1) * limite])

    with conectar() as db, db.cursor() as cur:
        cur.execute(sql, tuple(params))
        return cur.fetchall()


@router.get("/{producto_id}", response_model=ProductoRespuesta)
def obtener_producto(producto_id: int):
    with conectar() as db, db.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, precio, stock FROM productos WHERE id = %s",
            (producto_id,),
        )
        producto = cur.fetchone()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.post("", response_model=ProductoRespuesta, status_code=201)
def crear_producto(datos: ProductoCrear):
    with conectar() as db, db.cursor() as cur:
        cur.execute(
            "INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)",
            (datos.nombre, datos.precio, datos.stock),
        )
        nuevo_id = cur.lastrowid
        cur.execute(
            "SELECT id, nombre, precio, stock FROM productos WHERE id = %s",
            (nuevo_id,),
        )
        return cur.fetchone()


@router.patch("/{producto_id}/stock", response_model=ProductoRespuesta)
def actualizar_stock(producto_id: int, stock: Annotated[int, Query(ge=0)]):
    with conectar() as db, db.cursor() as cur:
        cur.execute(
            "SELECT id FROM productos WHERE id = %s FOR UPDATE", (producto_id,)
        )
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        cur.execute(
            "UPDATE productos SET stock = %s WHERE id = %s", (stock, producto_id)
        )
        cur.execute(
            "SELECT id, nombre, precio, stock FROM productos WHERE id = %s",
            (producto_id,),
        )
        return cur.fetchone()