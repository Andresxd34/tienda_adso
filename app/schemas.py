from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ClienteCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=2, max_length=100)
    correo: EmailStr = Field(max_length=120)


class ClienteRespuesta(ClienteCrear):
    id: int


class ProductoCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=2, max_length=100)
    precio: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock: int = Field(ge=0)


class ProductoRespuesta(ProductoCrear):
    id: int


class ItemPedido(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0)


class PedidoCrear(BaseModel):
    cliente_id: int = Field(gt=0)
    items: list[ItemPedido] = Field(min_length=1)

    @field_validator("items")
    @classmethod
    def sin_productos_repetidos(cls, items: list[ItemPedido]) -> list[ItemPedido]:
        ids = [item.producto_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("No repita el mismo producto en la lista de items")
        return items


class ItemPedidoRespuesta(BaseModel):
    producto_id: int
    producto: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class PedidoResumen(BaseModel):
    id: int
    cliente_id: int
    cliente: str
    fecha: datetime
    estado: str
    total: Decimal


class PedidoDetalle(PedidoResumen):
    items: list[ItemPedidoRespuesta]