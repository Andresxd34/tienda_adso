from fastapi import APIRouter

from app.database import conectar
from app.schemas import VentaPorCliente

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/ventas-por-cliente", response_model=list[VentaPorCliente])
def ventas_por_cliente():
    with conectar() as db, db.cursor() as cur:
        cur.execute(
            """
            SELECT c.id AS cliente_id,
                   c.nombre AS cliente,
                   COUNT(p.id) AS total_pedidos,
                   COALESCE(SUM(p.total), 0) AS total_vendido
            FROM clientes c
            LEFT JOIN pedidos p
                   ON p.cliente_id = c.id AND p.estado <> 'cancelado'
            GROUP BY c.id, c.nombre
            ORDER BY total_vendido DESC, c.id
            """
        )
        return cur.fetchall()