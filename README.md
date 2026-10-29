index.html# Tienda ADSO — Taller práctico 03

API REST para gestionar clientes, productos y pedidos con FastAPI, MySQL/MariaDB y transacciones InnoDB.

## Requisitos

- Python 3.10 o superior.
- MySQL Server o MariaDB iniciado.
- Una cuenta de aplicación con permisos `SELECT`, `INSERT`, `UPDATE` y `DELETE` sobre `tienda_adso.*`. No usar `root` en el archivo `.env`.

## Preparar la base de datos

Ejecuta una vez, en Workbench o phpMyAdmin, los archivos en este orden:

1. `sql/01_esquema.sql`
2. `sql/02_datos_prueba.sql`

El segundo archivo agrega dos clientes y tres productos de ejemplo. Si ya existen esos datos, no lo vuelvas a ejecutar porque se duplicarán.

## Configurar y arrancar

Desde la raíz del proyecto, crea y activa un entorno virtual e instala dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Completa `.env` con el host, puerto, usuario y contraseña de tu cuenta local. El nombre de la base es `tienda_adso`. El `.env` real contiene credenciales y no se debe compartir ni incluir en una entrega.

Inicia la API desde la raíz:

```powershell
fastapi dev app/main.py
```

Abre `http://127.0.0.1:8000/docs` para usar Swagger y `index.html` para ver el panel visual del proyecto.

## Estructura

```text
tienda_adso/
├── app/
│   ├── main.py                 # Aplicación FastAPI y registro de routers
│   ├── database.py             # Conexión y control COMMIT/ROLLBACK
│   ├── schemas.py              # Validación de entradas y respuestas
│   └── routers/
│       ├── clientes.py         # Endpoints de clientes
│       ├── productos.py        # Catálogo y ajuste de stock
│       └── pedidos.py          # Pedidos, JOIN y transacción de venta
├── sql/
│   ├── 01_esquema.sql
│   └── 02_datos_prueba.sql
├── Evidencias/                 # Capturas de la ejecución del taller
├── index.html                  # Panel visual local
├── requirements.txt
├── .env.example
└── README.md
```

## Probar escenarios principales

- `GET /clientes` y `GET /productos` listan los datos existentes.
- `POST /clientes` registra un cliente; un correo duplicado responde `409`.
- `POST /productos` valida precio y stock; un precio no positivo responde `422`.
- `POST /pedidos` recibe `cliente_id` y una lista `items`. Al confirmar, guarda el encabezado y sus detalles, conserva el precio unitario y descuenta stock dentro de una transacción.
- Un cliente inexistente devuelve `404`; un producto sin existencias suficientes devuelve `409` y la transacción revierte toda la operación.
- `GET /pedidos/{id}` muestra el encabezado y sus líneas. Verifica el inventario con `GET /productos`.
- `PATCH /productos/{id}/stock?stock=10` actualiza existencias.

Ejemplo de pedido: cliente `1`, Mouse (`producto_id: 1`, cantidad `2`) y Teclado (`producto_id: 2`, cantidad `1`). Con los datos iniciales, total esperado: `150000.00`.

## Respuestas para la sustentación

- **¿Para qué sirve `detalle_pedidos`?** Resuelve la relación muchos-a-muchos entre pedidos y productos. Cada fila conserva producto, cantidad, precio unitario y subtotal.
- **¿Por qué se usan claves foráneas?** Aseguran que los pedidos apunten a clientes existentes y los detalles a pedidos y productos válidos.
- **¿Qué protege una transacción?** La atomicidad: encabezado, detalles y descuento de stock se confirman juntos o se revierten juntos ante un error.
- **¿En qué archivos se separa la lógica?** `main.py` configura la app; `database.py` gestiona conexiones y transacciones; `schemas.py` valida datos; cada archivo dentro de `routers/` implementa un recurso; `sql/` define y carga la base de datos.

## Evidencias sugeridas

En `Evidencias/` se guardan capturas reales de: estructura del proyecto, documentación Swagger, pedido exitoso, detalle del pedido, consulta SQL JOIN, stock antes y después, rollback por cantidad excesiva y persistencia tras reiniciar FastAPI.
