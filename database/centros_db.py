from __future__ import annotations

from typing import Any, Dict, List, Optional

from .campanas_db import obtener_campana
from .exceptions import DuplicateRecordError, NotFoundError, ValidationError
from .json_manager import load_json, save_json
from .usuarios_db import obtener_usuario_por_id

FILE_NAME = "centros.json"


def _load_centros() -> List[Dict[str, Any]]:
    data = load_json(FILE_NAME)
    return data if isinstance(data, list) else []


def _save_centros(centros: List[Dict[str, Any]]) -> None:
    save_json(FILE_NAME, centros)


def _next_id() -> str:
    centros = _load_centros()
    numbers = []
    for centro in centros:
        centro_id = str(centro.get("id", ""))
        if centro_id.startswith("C"):
            suffix = centro_id[1:]
            if suffix.isdigit():
                numbers.append(int(suffix))
    next_num = max(numbers, default=0) + 1
    return f"C{next_num:03d}"


def crear_centro(
    nombre: str,
    institucion: str,
    ubicacion: str,
    encargado_id: Optional[str] = None,
    campanas: Optional[List[str]] = None,
    activo: bool = True,
    centro_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea un centro de acopio."""
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre del centro es obligatorio.")
    if not institucion or not institucion.strip():
        raise ValidationError("La institución es obligatoria.")
    if not ubicacion or not ubicacion.strip():
        raise ValidationError("La ubicación es obligatoria.")

    centros = _load_centros()
    if centro_id and any(c.get("id") == centro_id for c in centros):
        raise DuplicateRecordError(f"El centro '{centro_id}' ya existe.")

    if encargado_id is not None:
        try:
            obtener_usuario_por_id(encargado_id)
        except NotFoundError as exc:
            raise ValidationError("El encargado indicado no existe.") from exc

    nuevo = {
        "id": centro_id or _next_id(),
        "nombre": nombre.strip(),
        "institucion": institucion.strip(),
        "ubicacion": ubicacion.strip(),
        "encargado_id": encargado_id,
        "campanas": campanas or [],
        "activo": bool(activo),
    }
    centros.append(nuevo)
    _save_centros(centros)
    return nuevo


def obtener_centro(centro_id: str) -> Dict[str, Any]:
    centros = _load_centros()
    for centro in centros:
        if centro.get("id") == centro_id:
            return centro
    raise NotFoundError(f"No existe el centro {centro_id}.")


def obtener_centros() -> List[Dict[str, Any]]:
    return _load_centros()


def actualizar_centro(centro_id: str, cambios: Dict[str, Any]) -> Dict[str, Any]:
    centros = _load_centros()
    for indice, centro in enumerate(centros):
        if centro.get("id") == centro_id:
            actual = dict(centro)
            for key, value in cambios.items():
                if key in {"nombre", "institucion", "ubicacion", "encargado_id", "campanas", "activo"}:
                    actual[key] = value
            if not actual.get("nombre", "").strip():
                raise ValidationError("El nombre del centro es obligatorio.")
            if actual.get("encargado_id") is not None:
                try:
                    obtener_usuario_por_id(actual["encargado_id"])
                except NotFoundError as exc:
                    raise ValidationError("El encargado indicado no existe.") from exc
            centros[indice] = actual
            _save_centros(centros)
            return actual
    raise NotFoundError(f"No existe el centro {centro_id}.")


def activar_centro(centro_id: str) -> Dict[str, Any]:
    centro = obtener_centro(centro_id)
    centro["activo"] = True
    centros = _load_centros()
    for i, item in enumerate(centros):
        if item.get("id") == centro_id:
            centros[i] = centro
            _save_centros(centros)
            return centro
    raise NotFoundError(f"No existe el centro {centro_id}.")


def desactivar_centro(centro_id: str) -> Dict[str, Any]:
    centro = obtener_centro(centro_id)
    centro["activo"] = False
    centros = _load_centros()
    for i, item in enumerate(centros):
        if item.get("id") == centro_id:
            centros[i] = centro
            _save_centros(centros)
            return centro
    raise NotFoundError(f"No existe el centro {centro_id}.")


def agregar_campana_a_centro(centro_id: str, campana_id: str) -> Dict[str, Any]:
    centro = obtener_centro(centro_id)
    if not centro.get("activo", False):
        raise ValidationError("No se puede operar con un centro inactivo.")

    try:
        obtener_campana(campana_id)
    except NotFoundError as exc:
        raise ValidationError("La campaña indicada no existe.") from exc

    campanas = centro.setdefault("campanas", [])
    if campana_id not in campanas:
        campanas.append(campana_id)

    centros = _load_centros()
    for i, item in enumerate(centros):
        if item.get("id") == centro_id:
            centros[i] = centro
            _save_centros(centros)
            return centro
    raise NotFoundError(f"No existe el centro {centro_id}.")


def quitar_campana_de_centro(centro_id: str, campana_id: str) -> Dict[str, Any]:
    centro = obtener_centro(centro_id)
    campanas = centro.get("campanas", [])
    if campana_id in campanas:
        campanas.remove(campana_id)
    centro["campanas"] = campanas
    centros = _load_centros()
    for i, item in enumerate(centros):
        if item.get("id") == centro_id:
            centros[i] = centro
            _save_centros(centros)
            return centro
    raise NotFoundError(f"No existe el centro {centro_id}.")
