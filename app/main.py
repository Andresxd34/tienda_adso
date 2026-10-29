from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from pymysql.err import OperationalError

from app.routers import clientes, pedidos, productos, reportes

RUTA_INDEX = Path(__file__).parent / "static" / "index.html"

app = FastAPI(
    title="Taller 3 ADSO - Tienda",
    version="3.0",
    description="API relacional: clientes, productos, pedidos y detalles",
)

app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(pedidos.router)
app.include_router(reportes.router)


@app.exception_handler(OperationalError)
async def error_base_de_datos(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Base de datos no disponible o con conflicto temporal. Intente de nuevo."},
    )


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(RUTA_INDEX)