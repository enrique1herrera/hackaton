from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .articulos_db import obtener_articulo
from .campanas_db import obtener_campana
from .centros_db import obtener_centro
from .exceptions import InsufficientStockError, NotFoundError, ValidationError
from .json_manager import load_json, save_json
from .usuarios_db import obtener_usuario_por_id

FILE_NAME = "movimientos.json"
VALID_MOVIMIENTOS = {
    "recepcion",
    "entrega",
    "merma",
    "transferencia_entrada",
    "transferencia_salida",
    "ajuste",
}
MOTIVOS_MERMA = {"caducidad", "daño", "pérdida", "perdida"}


def _load_movimientos() -> List[Dict[str, Any]]:
    data = load_json(FILE_NAME)
    return data if isinstance(data, list) else []


def _save_movimientos(movimientos: List[Dict[str, Any]]) -> None:
    save_json(FILE_NAME, movimientos)


def _next_id() -> str:
    movimientos = _load_movimientos()
    numbers = []
    for movimiento in movimientos:
        movimiento_id = str(movimiento.get("id", ""))
        if movimiento_id.startswith("M"):
            suffix = movimiento_id[1:]
            if suffix.isdigit():
                numbers.append(int(suffix))
    next_num = max(numbers, default=0) + 1
    return f"M{next_num:03d}"


def _generar_fecha_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _validar_actor(actor_id: str) -> None:
    try:
        obtener_usuario_por_id(actor_id)
    except NotFoundError as exc:
        raise ValidationError("El actor indicado no existe.") from exc


def _validar_movimiento_basico(
    tipo: str,
    centro_id: str,
    campana_id: str,
    articulo_id: str,
    cantidad: float,
    actor_id: str,
    destino_id: Optional[str] = None,
    motivo: Optional[str] = None,
) -> None:
    if tipo not in VALID_MOVIMIENTOS:
        raise ValidationError(f"Tipo de movimiento inválido: {tipo}")
    if not centro_id:
        raise ValidationError("El centro es obligatorio.")
    if not campana_id:
        raise ValidationError("La campaña es obligatoria.")
    if not articulo_id:
        raise ValidationError("El artículo es obligatorio.")
    if cantidad <= 0:
        raise ValidationError("La cantidad debe ser mayor que cero.")
    if not actor_id:
        raise ValidationError("El actor es obligatorio.")

    try:
        centro = obtener_centro(centro_id)
    except NotFoundError as exc:
        raise ValidationError(f"El centro {centro_id} no existe.") from exc
    if not centro.get("activo", False):
        raise ValidationError(f"El centro {centro_id} está inactivo.")

    try:
        campana = obtener_campana(campana_id)
    except NotFoundError as exc:
        raise ValidationError(f"La campaña {campana_id} no existe.") from exc
    if not campana.get("activa", False):
        raise ValidationError(f"La campaña {campana_id} está inactiva.")

    try:
        obtener_articulo(articulo_id)
    except NotFoundError as exc:
        raise ValidationError(f"El artículo {articulo_id} no existe.") from exc

    _validar_actor(actor_id)

    if tipo in {"merma"} and not motivo:
        raise ValidationError("El motivo de la merma es obligatorio.")
    if tipo in {"merma"} and motivo not in MOTIVOS_MERMA:
        raise ValidationError("El motivo de la merma debe ser caducidad, daño o pérdida.")
    if tipo in {"transferencia_salida", "transferencia_entrada"} and destino_id is None:
        raise ValidationError("La transferencia requiere destino_id.")


def _registrar_movimiento(
    tipo: str,
    centro_id: str,
    campana_id: str,
    articulo_id: str,
    cantidad: float,
    actor_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    _validar_movimiento_basico(tipo, centro_id, campana_id, articulo_id, cantidad, actor_id, kwargs.get("destino_id"), kwargs.get("motivo"))

    movimiento = {
        "id": _next_id(),
        "tipo": tipo,
        "centro_id": centro_id,
        "campana_id": campana_id,
        "articulo_id": articulo_id,
        "cantidad": float(cantidad),
        "fecha": _generar_fecha_iso(),
        "actor_id": actor_id,
        "destino_id": kwargs.get("destino_id"),
        "motivo": kwargs.get("motivo"),
        "observaciones": kwargs.get("observaciones", ""),
        "donante": kwargs.get("donante"),
        "institucion_receptora_id": kwargs.get("institucion_receptora_id"),
        "transferencia_id": kwargs.get("transferencia_id"),
        "ajuste_tipo": kwargs.get("ajuste_tipo"),
    }

    movimientos = _load_movimientos()
    movimientos.append(movimiento)
    _save_movimientos(movimientos)
    return movimiento


def registrar_recepcion(
    centro_id: str,
    campana_id: str,
    articulo_id: str,
    cantidad: float,
    actor_id: str,
    donante: Optional[Dict[str, Any]] = None,
    observaciones: str = "",
) -> Dict[str, Any]:
    """Registra una recepción y la retorna."""
    return _registrar_movimiento(
        "recepcion",
        centro_id,
        campana_id,
        articulo_id,
        cantidad,
        actor_id,
        observaciones=observaciones,
        donante=donante,
    )


def registrar_entrega(
    centro_id: str,
    campana_id: str,
    articulo_id: str,
    cantidad: float,
    actor_id: str,
    destino_id: Optional[str] = None,
    institucion_receptora_id: Optional[str] = None,
    observaciones: str = "",
) -> Dict[str, Any]:
    """Registra una entrega si hay stock suficiente."""
    from .inventario import obtener_stock

    if obtener_stock(centro_id, campana_id, articulo_id) < cantidad:
        raise InsufficientStockError("No hay suficiente stock disponible.")
    return _registrar_movimiento(
        "entrega",
        centro_id,
        campana_id,
        articulo_id,
        cantidad,
        actor_id,
        destino_id=destino_id,
        institucion_receptora_id=institucion_receptora_id,
        observaciones=observaciones,
    )


def registrar_merma(
    centro_id: str,
    campana_id: str,
    articulo_id: str,
    cantidad: float,
    actor_id: str,
    motivo: str,
    observaciones: str = "",
) -> Dict[str, Any]:
    """Registra una merma con motivo obligatorio."""
    from .inventario import obtener_stock

    if obtener_stock(centro_id, campana_id, articulo_id) < cantidad:
        raise InsufficientStockError("No hay suficiente stock disponible.")
    return _registrar_movimiento(
        "merma",
        centro_id,
        campana_id,
        articulo_id,
        cantidad,
        actor_id,
        motivo=motivo,
        observaciones=observaciones,
    )


def registrar_transferencia(
    origen_id: str,
    destino_id: str,
    campana_id: str,
    articulo_id: str,
    cantidad: float,
    actor_id: str,
    observaciones: str = "",
) -> Dict[str, Any]:
    """Registra transferencia entre dos centros bajo la misma campaña."""
    from .inventario import obtener_stock

    if origen_id == destino_id:
        raise ValidationError("El centro origen y destino no pueden ser el mismo.")

    origen = obtener_centro(origen_id)
    destino = obtener_centro(destino_id)
    if not origen.get("activo") or not destino.get("activo"):
        raise ValidationError("Ambos centros deben estar activos.")

    if campana_id not in origen.get("campanas", []) or campana_id not in destino.get("campanas", []):
        raise ValidationError("Ambos centros deben participar en la campaña indicada.")

    if obtener_stock(origen_id, campana_id, articulo_id) < cantidad:
        raise InsufficientStockError("No hay suficiente stock disponible para transferir.")

    transferencia_id = f"TR{datetime.now().strftime('%Y%m%d%H%M%S')}"
    salida = _registrar_movimiento(
        "transferencia_salida",
        origen_id,
        campana_id,
        articulo_id,
        cantidad,
        actor_id,
        destino_id=destino_id,
        observaciones=observaciones,
        transferencia_id=transferencia_id,
    )
    entrada = _registrar_movimiento(
        "transferencia_entrada",
        destino_id,
        campana_id,
        articulo_id,
        cantidad,
        actor_id,
        destino_id=origen_id,
        observaciones=observaciones,
        transferencia_id=transferencia_id,
    )
    return {"transferencia_id": transferencia_id, "salida": salida, "entrada": entrada}


def registrar_ajuste(
    centro_id: str,
    campana_id: str,
    articulo_id: str,
    cantidad: float,
    actor_id: str,
    tipo: str,
    motivo: str,
    observaciones: str = "",
) -> Dict[str, Any]:
    """Registra un ajuste positivo o negativo."""
    if tipo not in {"positivo", "negativo"}:
        raise ValidationError("El tipo de ajuste debe ser 'positivo' o 'negativo'.")
    if not motivo or not motivo.strip():
        raise ValidationError("El motivo del ajuste es obligatorio.")

    if tipo == "negativo":
        from .inventario import obtener_stock

        if obtener_stock(centro_id, campana_id, articulo_id) < cantidad:
            raise InsufficientStockError("No hay suficiente stock disponible.")

    return _registrar_movimiento(
        "ajuste",
        centro_id,
        campana_id,
        articulo_id,
        cantidad,
        actor_id,
        motivo=motivo,
        observaciones=observaciones,
        ajuste_tipo=tipo,
    )


def obtener_movimientos() -> List[Dict[str, Any]]:
    return _load_movimientos()


def obtener_movimientos_centro(centro_id: str) -> List[Dict[str, Any]]:
    return [m for m in _load_movimientos() if m.get("centro_id") == centro_id]
