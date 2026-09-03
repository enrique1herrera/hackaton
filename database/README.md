# Capa de persistencia en JSON

Esta capa permite almacenar la información del sistema de centros de acopio usando archivos JSON en la carpeta `data`. No se usa ninguna base de datos relacional ni NoSQL. Toda la persistencia se hace con la librería estándar de Python.

## Estructura

- `data/usuarios.json`
- `data/campanas.json`
- `data/centros.json`
- `data/articulos.json`
- `data/movimientos.json`
- `data/instituciones.json`

## Módulos principales

- `database/json_manager.py`: manejo centralizado de lectura y escritura JSON.
- `database/usuarios_db.py`: gestión de usuarios y login.
- `database/campanas_db.py`: gestión de campañas.
- `database/centros_db.py`: gestión de centros.
- `database/articulos_db.py`: gestión de artículos.
- `database/instituciones_db.py`: gestión de instituciones receptoras.
- `database/movimientos_db.py`: registro de recepciones, entregas, mermas, transferencias y ajustes.
- `database/inventario.py`: cálculo de stock y trazabilidad por centro/campaña/artículo.
- `database/reportes.py`: funciones para consultar dashboard y reportes.

## Importaciones típicas

```python
from database.usuarios_db import crear_usuario, validar_login
from database.campanas_db import crear_campana
from database.centros_db import crear_centro, agregar_campana_a_centro
from database.articulos_db import crear_articulo
from database.movimientos_db import registrar_recepcion, registrar_entrega, registrar_merma, registrar_transferencia, registrar_ajuste
from database.inventario import obtener_stock
```

## Cálculo del stock

El stock no se guarda como un valor aislado. Se calcula desde los movimientos:

- recepción: +cantidad
- transferencia_entrada: +cantidad
- ajuste positivo: +cantidad
- entrega: -cantidad
- merma: -cantidad
- transferencia_salida: -cantidad
- ajuste negativo: -cantidad

Esta regla asegura que el inventario sea consistente.

## Transferencias

Las transferencias se registran con dos movimientos relacionados:

- `transferencia_salida` en el centro origen
- `transferencia_entrada` en el centro destino

Ambos comparten el mismo `transferencia_id`.

## Trazabilidad

Todo movimiento guarda:

- id
- tipo
- centro_id
- campana_id
- articulo_id
- cantidad
- fecha
- actor_id
- motivo
- destino_id
- observaciones

## Cómo ejecutar los tests

```bash
python -m pytest tests/test_database.py
```

## Ejemplo de uso

```python
from database.usuarios_db import crear_usuario
from database.campanas_db import crear_campana
from database.centros_db import crear_centro, agregar_campana_a_centro
from database.articulos_db import crear_articulo
from database.movimientos_db import registrar_recepcion, registrar_entrega

usuario = crear_usuario(
    nombre="Ana",
    username="ana",
    password="1234",
    rol="encargado_centro",
)

campana = crear_campana(
    nombre="Ayuda inmediata",
    fecha_inicio="2026-09-01",
    fecha_fin="2026-09-30",
)

centro = crear_centro(
    nombre="Centro Norte",
    institucion="Municipio",
    ubicacion="Ciudad",
    encargado_id=usuario["id"],
)

agregar_campana_a_centro(centro["id"], campana["id"])
articulo = crear_articulo(nombre="Arroz", categoria="no_perecedero", unidad="bolsa")
registrar_recepcion(centro["id"], campana["id"], articulo["id"], 50, usuario["id"])
```
