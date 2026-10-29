from fastapi import APIRouter, HTTPException
from pymysql.err import IntegrityError

from app.database import conectar
from app.schemas import ClienteCrear, ClienteRespuesta

router = APIRouter(prefix="/clientes", tags=["Clientes"])

MYSQL_ERROR_DUPLICADO = 1062


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