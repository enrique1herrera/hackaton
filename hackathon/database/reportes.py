from __future__ import annotations

from typing import Any, Dict, List

from .inventario import obtener_inventario_centro, obtener_stock
from .movimientos_db import obtener_movimientos


def total_articulos_recibidos_por_campana(campana_id: str) -> float:
    total = 0.0
    for movimiento in obtener_movimientos():
        if movimiento.get("campana_id") == campana_id and movimiento.get("tipo") == "recepcion":
            total += float(movimiento.get("cantidad", 0) or 0)
    return total


def total_articulos_entregados_por_campana(campana_id: str) -> float:
    total = 0.0
    for movimiento in obtener_movimientos():
        if movimiento.get("campana_id") == campana_id and movimiento.get("tipo") == "entrega":
            total += float(movimiento.get("cantidad", 0) or 0)
    return total


def total_merma_por_campana(campana_id: str) -> float:
    total = 0.0
    for movimiento in obtener_movimientos():
        if movimiento.get("campana_id") == campana_id and movimiento.get("tipo") == "merma":
            total += float(movimiento.get("cantidad", 0) or 0)
    return total


def stock_por_centro_y_articulo(centro_id: str, campana_id: str) -> Dict[str, float]:
    return obtener_inventario_centro(centro_id, campana_id)


def movimientos_por_centro(centro_id: str) -> List[Dict[str, Any]]:
    return [m for m in obtener_movimientos() if m.get("centro_id") == centro_id]


def articulos_mas_recibidos() -> List[Dict[str, Any]]:
    agregados: Dict[str, float] = {}
    for movimiento in obtener_movimientos():
        if movimiento.get("tipo") == "recepcion":
            articulo_id = movimiento.get("articulo_id")
            agregados[articulo_id] = agregados.get(articulo_id, 0.0) + float(movimiento.get("cantidad", 0) or 0)
    return [{"articulo_id": k, "cantidad": v} for k, v in sorted(agregados.items(), key=lambda x: x[1], reverse=True)]


def articulos_mas_entregados() -> List[Dict[str, Any]]:
    agregados: Dict[str, float] = {}
    for movimiento in obtener_movimientos():
        if movimiento.get("tipo") == "entrega":
            articulo_id = movimiento.get("articulo_id")
            agregados[articulo_id] = agregados.get(articulo_id, 0.0) + float(movimiento.get("cantidad", 0) or 0)
    return [{"articulo_id": k, "cantidad": v} for k, v in sorted(agregados.items(), key=lambda x: x[1], reverse=True)]
