from __future__ import annotations

from typing import Any, Dict, List

from .movimientos_db import obtener_movimientos


def _clasificar_movimiento(movimiento: Dict[str, Any]) -> float:
    tipo = movimiento.get("tipo")
    cantidad = float(movimiento.get("cantidad", 0) or 0)

    if tipo == "recepcion":
        return cantidad
    if tipo == "transferencia_entrada":
        return cantidad
    if tipo == "ajuste":
        ajuste_tipo = str(movimiento.get("ajuste_tipo") or "").strip().lower()
        if ajuste_tipo == "positivo":
            return cantidad
        if ajuste_tipo == "negativo":
            return -cantidad
        return cantidad if str(movimiento.get("motivo") or "").lower() not in {"negativo", "disminucion"} else -cantidad
    if tipo == "entrega":
        return -cantidad
    if tipo == "merma":
        return -cantidad
    if tipo == "transferencia_salida":
        return -cantidad
    return 0.0


def obtener_stock(centro_id: str, campana_id: str, articulo_id: str) -> float:
    """Calcula el stock real a partir de los movimientos."""
    total = 0.0
    for movimiento in obtener_movimientos():
        if movimiento.get("centro_id") == centro_id and movimiento.get("campana_id") == campana_id and movimiento.get("articulo_id") == articulo_id:
            total += _clasificar_movimiento(movimiento)
    return total


def obtener_inventario_centro(centro_id: str, campana_id: str) -> Dict[str, float]:
    inventario: Dict[str, float] = {}
    for movimiento in obtener_movimientos():
        if movimiento.get("centro_id") == centro_id and movimiento.get("campana_id") == campana_id:
            articulo_id = movimiento.get("articulo_id")
            if articulo_id is None:
                continue
            inventario.setdefault(articulo_id, 0.0)
            inventario[articulo_id] += _clasificar_movimiento(movimiento)
    return inventario


def obtener_inventario_general() -> Dict[str, Dict[str, float]]:
    """Calcula el stock consolidado por campaña y artículo."""
    inventario: Dict[str, Dict[str, float]] = {}
    for movimiento in obtener_movimientos():
        campana_id = movimiento.get("campana_id")
        articulo_id = movimiento.get("articulo_id")
        if campana_id is None or articulo_id is None:
            continue

        inventario.setdefault(campana_id, {})
        inventario[campana_id].setdefault(articulo_id, 0.0)
        inventario[campana_id][articulo_id] += _clasificar_movimiento(movimiento)
    return inventario


def obtener_historial_articulo(centro_id: str, campana_id: str, articulo_id: str) -> List[Dict[str, Any]]:
    historial = []
    for movimiento in obtener_movimientos():
        if (
            movimiento.get("centro_id") == centro_id
            and movimiento.get("campana_id") == campana_id
            and movimiento.get("articulo_id") == articulo_id
        ):
            historial.append(movimiento)
    return historial


def obtener_movimientos_centro(centro_id: str) -> List[Dict[str, Any]]:
    return [m for m in obtener_movimientos() if m.get("centro_id") == centro_id]
