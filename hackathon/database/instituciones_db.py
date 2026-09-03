from __future__ import annotations

from typing import Any, Dict, List, Optional

from .exceptions import DuplicateRecordError, NotFoundError, ValidationError
from .json_manager import load_json, save_json

FILE_NAME = "instituciones.json"


def _load_instituciones() -> List[Dict[str, Any]]:
    data = load_json(FILE_NAME)
    return data if isinstance(data, list) else []


def _save_instituciones(instituciones: List[Dict[str, Any]]) -> None:
    save_json(FILE_NAME, instituciones)


def _next_id() -> str:
    instituciones = _load_instituciones()
    numbers = []
    for institucion in instituciones:
        inst_id = str(institucion.get("id", ""))
        if inst_id.startswith("I"):
            suffix = inst_id[1:]
            if suffix.isdigit():
                numbers.append(int(suffix))
    next_num = max(numbers, default=0) + 1
    return f"I{next_num:03d}"


def crear_institucion(
    nombre: str,
    tipo: str,
    contacto: str = "",
    telefono: str = "",
    email: str = "",
    activa: bool = True,
    institucion_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea una institución receptora."""
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre de la institución es obligatorio.")
    if not tipo or not tipo.strip():
        raise ValidationError("El tipo de la institución es obligatorio.")

    instituciones = _load_instituciones()
    if institucion_id and any(i.get("id") == institucion_id for i in instituciones):
        raise DuplicateRecordError(f"La institución '{institucion_id}' ya existe.")

    nueva = {
        "id": institucion_id or _next_id(),
        "nombre": nombre.strip(),
        "tipo": tipo.strip(),
        "contacto": contacto.strip(),
        "telefono": telefono.strip(),
        "email": email.strip(),
        "activa": bool(activa),
    }
    instituciones.append(nueva)
    _save_instituciones(instituciones)
    return nueva


def obtener_institucion(institucion_id: str) -> Dict[str, Any]:
    instituciones = _load_instituciones()
    for institucion in instituciones:
        if institucion.get("id") == institucion_id:
            return institucion
    raise NotFoundError(f"No existe la institución {institucion_id}.")


def obtener_instituciones() -> List[Dict[str, Any]]:
    return _load_instituciones()


def actualizar_institucion(institucion_id: str, cambios: Dict[str, Any]) -> Dict[str, Any]:
    instituciones = _load_instituciones()
    for indice, institucion in enumerate(instituciones):
        if institucion.get("id") == institucion_id:
            actual = dict(institucion)
            for key, value in cambios.items():
                if key in {"nombre", "tipo", "contacto", "telefono", "email", "activa"}:
                    actual[key] = value
            if not actual.get("nombre", "").strip():
                raise ValidationError("El nombre de la institución es obligatorio.")
            if not actual.get("tipo", "").strip():
                raise ValidationError("El tipo de la institución es obligatorio.")
            instituciones[indice] = actual
            _save_instituciones(instituciones)
            return actual
    raise NotFoundError(f"No existe la institución {institucion_id}.")


def desactivar_institucion(institucion_id: str) -> Dict[str, Any]:
    institucion = obtener_institucion(institucion_id)
    institucion["activa"] = False
    instituciones = _load_instituciones()
    for i, item in enumerate(instituciones):
        if item.get("id") == institucion_id:
            instituciones[i] = institucion
            _save_instituciones(instituciones)
            return institucion
    raise NotFoundError(f"No existe la institución {institucion_id}.")
