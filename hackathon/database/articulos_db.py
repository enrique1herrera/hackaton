from __future__ import annotations

from typing import Any, Dict, List, Optional

from .exceptions import DuplicateRecordError, NotFoundError, ValidationError
from .json_manager import load_json, save_json

FILE_NAME = "articulos.json"
VALID_CATEGORIAS = {"no_perecedero", "perecedero", "ropa", "limpieza", "medicamento", "otro"}
VALID_UNIDADES = {"pieza", "kg", "bolsa", "caja"}


def _load_articulos() -> List[Dict[str, Any]]:
    data = load_json(FILE_NAME)
    return data if isinstance(data, list) else []


def _save_articulos(articulos: List[Dict[str, Any]]) -> None:
    save_json(FILE_NAME, articulos)


def _next_id() -> str:
    articulos = _load_articulos()
    numbers = []
    for articulo in articulos:
        articulo_id = str(articulo.get("id", ""))
        if articulo_id.startswith("A"):
            suffix = articulo_id[1:]
            if suffix.isdigit():
                numbers.append(int(suffix))
    next_num = max(numbers, default=0) + 1
    return f"A{next_num:03d}"


def crear_articulo(
    nombre: str,
    categoria: str,
    unidad: str,
    activo: bool = True,
    articulo_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea un artículo con validaciones."""
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre del artículo es obligatorio.")
    if categoria not in VALID_CATEGORIAS:
        raise ValidationError(f"Categoría inválida: {categoria}")
    if unidad not in VALID_UNIDADES:
        raise ValidationError(f"Unidad inválida: {unidad}")

    articulos = _load_articulos()
    if articulo_id and any(a.get("id") == articulo_id for a in articulos):
        raise DuplicateRecordError(f"El artículo '{articulo_id}' ya existe.")

    nuevo = {
        "id": articulo_id or _next_id(),
        "nombre": nombre.strip(),
        "categoria": categoria,
        "unidad": unidad,
        "activo": bool(activo),
    }
    articulos.append(nuevo)
    _save_articulos(articulos)
    return nuevo


def obtener_articulo(articulo_id: str) -> Dict[str, Any]:
    articulos = _load_articulos()
    for articulo in articulos:
        if articulo.get("id") == articulo_id:
            return articulo
    raise NotFoundError(f"No existe el artículo {articulo_id}.")


def obtener_articulos() -> List[Dict[str, Any]]:
    return _load_articulos()


def actualizar_articulo(articulo_id: str, cambios: Dict[str, Any]) -> Dict[str, Any]:
    articulos = _load_articulos()
    for indice, articulo in enumerate(articulos):
        if articulo.get("id") == articulo_id:
            actual = dict(articulo)
            for key, value in cambios.items():
                if key in {"nombre", "categoria", "unidad", "activo"}:
                    actual[key] = value
            if not actual.get("nombre", "").strip():
                raise ValidationError("El nombre del artículo es obligatorio.")
            if actual.get("categoria") not in VALID_CATEGORIAS:
                raise ValidationError(f"Categoría inválida: {actual.get('categoria')}")
            if actual.get("unidad") not in VALID_UNIDADES:
                raise ValidationError(f"Unidad inválida: {actual.get('unidad')}")
            articulos[indice] = actual
            _save_articulos(articulos)
            return actual
    raise NotFoundError(f"No existe el artículo {articulo_id}.")


def desactivar_articulo(articulo_id: str) -> Dict[str, Any]:
    articulo = obtener_articulo(articulo_id)
    articulo["activo"] = False
    articulos = _load_articulos()
    for i, item in enumerate(articulos):
        if item.get("id") == articulo_id:
            articulos[i] = articulo
            _save_articulos(articulos)
            return articulo
    raise NotFoundError(f"No existe el artículo {articulo_id}.")
