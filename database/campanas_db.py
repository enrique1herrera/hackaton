from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .exceptions import DuplicateRecordError, NotFoundError, ValidationError
from .json_manager import load_json, save_json

FILE_NAME = "campanas.json"


def _load_campanas() -> List[Dict[str, Any]]:
    data = load_json(FILE_NAME)
    return data if isinstance(data, list) else []


def _save_campanas(campanas: List[Dict[str, Any]]) -> None:
    save_json(FILE_NAME, campanas)


def _next_id() -> str:
    campanas = _load_campanas()
    numbers = []
    for campana in campanas:
        campana_id = str(campana.get("id", ""))
        if campana_id.startswith("CAM"):
            suffix = campana_id[3:]
            if suffix.isdigit():
                numbers.append(int(suffix))
    next_num = max(numbers, default=0) + 1
    return f"CAM{next_num:03d}"


def _validar_fecha(fecha: str) -> str:
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return fecha
    except ValueError as exc:  # pragma: no cover
        raise ValidationError("La fecha no tiene un formato válido (YYYY-MM-DD).") from exc


def crear_campana(
    nombre: str,
    fecha_inicio: str,
    fecha_fin: str,
    descripcion: str = "",
    activa: bool = True,
    campana_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea una campaña con validaciones básicas."""
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre de la campaña es obligatorio.")

    fecha_inicio = _validar_fecha(fecha_inicio)
    fecha_fin = _validar_fecha(fecha_fin)
    if datetime.strptime(fecha_fin, "%Y-%m-%d") < datetime.strptime(fecha_inicio, "%Y-%m-%d"):
        raise ValidationError("La fecha de fin no puede ser anterior a la de inicio.")

    campanas = _load_campanas()
    if campana_id and any(c.get("id") == campana_id for c in campanas):
        raise DuplicateRecordError(f"La campaña '{campana_id}' ya existe.")

    nueva = {
        "id": campana_id or _next_id(),
        "nombre": nombre.strip(),
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "descripcion": descripcion,
        "activa": bool(activa),
    }
    campanas.append(nueva)
    _save_campanas(campanas)
    return nueva


def obtener_campana(campana_id: str) -> Dict[str, Any]:
    campanas = _load_campanas()
    for campana in campanas:
        if campana.get("id") == campana_id:
            return campana
    raise NotFoundError(f"No existe la campaña {campana_id}.")


def obtener_campanas() -> List[Dict[str, Any]]:
    return _load_campanas()


def actualizar_campana(campana_id: str, cambios: Dict[str, Any]) -> Dict[str, Any]:
    campanas = _load_campanas()
    for indice, campana in enumerate(campanas):
        if campana.get("id") == campana_id:
            actual = dict(campana)
            for key, value in cambios.items():
                if key in {"nombre", "fecha_inicio", "fecha_fin", "descripcion", "activa"}:
                    actual[key] = value
            if not actual.get("nombre", "").strip():
                raise ValidationError("El nombre de la campaña es obligatorio.")
            actual["fecha_inicio"] = _validar_fecha(str(actual["fecha_inicio"]))
            actual["fecha_fin"] = _validar_fecha(str(actual["fecha_fin"]))
            if datetime.strptime(actual["fecha_fin"], "%Y-%m-%d") < datetime.strptime(actual["fecha_inicio"], "%Y-%m-%d"):
                raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")
            campanas[indice] = actual
            _save_campanas(campanas)
            return actual
    raise NotFoundError(f"No existe la campaña {campana_id}.")


def activar_campana(campana_id: str) -> Dict[str, Any]:
    campana = obtener_campana(campana_id)
    campana["activa"] = True
    campanas = _load_campanas()
    for indice, item in enumerate(campanas):
        if item.get("id") == campana_id:
            campanas[indice] = campana
            _save_campanas(campanas)
            return campana
    raise NotFoundError(f"No existe la campaña {campana_id}.")


def desactivar_campana(campana_id: str) -> Dict[str, Any]:
    campana = obtener_campana(campana_id)
    campana["activa"] = False
    campanas = _load_campanas()
    for indice, item in enumerate(campanas):
        if item.get("id") == campana_id:
            campanas[indice] = campana
            _save_campanas(campanas)
            return campana
    raise NotFoundError(f"No existe la campaña {campana_id}.")
