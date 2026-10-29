import os
from contextlib import contextmanager
from typing import Iterator

import pymysql
from dotenv import load_dotenv
from pymysql.connections import Connection

load_dotenv()


def _variable_requerida(nombre: str) -> str:
    valor = os.getenv(nombre)
    if not valor:
        raise RuntimeError(f"Falta la variable de entorno {nombre} en el archivo .env")
    return valor


@contextmanager
def conectar() -> Iterator[Connection]:
    conexion = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=_variable_requerida("DB_USER"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "tienda_adso"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
    )
    try:
        yield conexion
        conexion.commit()
    except BaseException:
        try:
            conexion.rollback()
        except pymysql.MySQLError:
            pass
        raise
    finally:
        conexion.close()