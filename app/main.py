from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pymysql.err import OperationalError

from app.routers import clientes, pedidos, productos

app = FastAPI(
    title="Taller 3 ADSO - Tienda",
    version="3.0",
    description="API relacional: clientes, productos, pedidos y detalles",
)

app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(pedidos.router)


@app.exception_handler(OperationalError)
async def error_base_de_datos(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Base de datos no disponible o con conflicto temporal. Intente de nuevo."},
    )


@app.get("/", tags=["Inicio"])
def inicio():
    return {"mensaje": "API tienda ADSO", "documentacion": "/docs"}