from __future__ import annotations

from typing import Any, Dict, List, Optional

from .exceptions import DuplicateRecordError, NotFoundError, ValidationError
from .json_manager import load_json, save_json

FILE_NAME = "usuarios.json"
VALID_ROLES = {
    "coordinador_general",
    "encargado_centro",
    "voluntario",
    "institucion_receptora",
    "lider_campana",
}


def _load_usuarios() -> List[Dict[str, Any]]:
    data = load_json(FILE_NAME)
    return data if isinstance(data, list) else []


def _save_usuarios(usuarios: List[Dict[str, Any]]) -> None:
    save_json(FILE_NAME, usuarios)


def _next_id() -> str:
    usuarios = _load_usuarios()
    numbers = []
    for usuario in usuarios:
        user_id = str(usuario.get("id", ""))
        if user_id.startswith("U"):
            suffix = user_id[1:]
            if suffix.isdigit():
                numbers.append(int(suffix))
    next_num = max(numbers, default=0) + 1
    return f"U{next_num:03d}"


def crear_usuario(
    nombre: str,
    username: str,
    password: str,
    rol: str,
    centro_id: Optional[str] = None,
    activo: bool = True,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea un usuario y lo guarda en usuarios.json."""
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre es obligatorio.")
    if not username or not username.strip():
        raise ValidationError("El username es obligatorio.")
    if not password:
        raise ValidationError("La contraseña es obligatoria.")
    if rol not in VALID_ROLES:
        raise ValidationError(f"Rol inválido: {rol}")

    usuarios = _load_usuarios()
    if any(u.get("username", "").strip().lower() == username.strip().lower() for u in usuarios):
        raise DuplicateRecordError(f"El username '{username}' ya existe.")

    if user_id is not None and any(u.get("id") == user_id for u in usuarios):
        raise DuplicateRecordError(f"El id '{user_id}' ya existe.")

    nuevo = {
        "id": user_id or _next_id(),
        "nombre": nombre.strip(),
        "username": username.strip(),
        "password": password,
        "rol": rol,
        "centro_id": centro_id,
        "activo": bool(activo),
    }
    usuarios.append(nuevo)
    _save_usuarios(usuarios)
    return nuevo


def obtener_usuarios() -> List[Dict[str, Any]]:
    return _load_usuarios()


def obtener_usuario_por_id(usuario_id: str) -> Dict[str, Any]:
    usuarios = _load_usuarios()
    for usuario in usuarios:
        if usuario.get("id") == usuario_id:
            return usuario
    raise NotFoundError(f"No existe un usuario con id {usuario_id}.")


def obtener_usuario_por_username(username: str) -> Dict[str, Any]:
    usuarios = _load_usuarios()
    for usuario in usuarios:
        if usuario.get("username", "").strip().lower() == username.strip().lower():
            return usuario
    raise NotFoundError(f"No existe un usuario con username {username}.")


def actualizar_usuario(usuario_id: str, cambios: Dict[str, Any]) -> Dict[str, Any]:
    usuarios = _load_usuarios()
    for indice, usuario in enumerate(usuarios):
        if usuario.get("id") == usuario_id:
            datos = dict(usuario)
            for key, value in cambios.items():
                if key in {"id", "username", "password", "rol", "nombre", "centro_id", "activo"}:
                    datos[key] = value
            if not datos.get("nombre", "").strip():
                raise ValidationError("El nombre es obligatorio.")
            if not datos.get("username", "").strip():
                raise ValidationError("El username es obligatorio.")
            if datos.get("rol") not in VALID_ROLES:
                raise ValidationError(f"Rol inválido: {datos.get('rol')}")
            if datos.get("username", "").strip().lower() != usuario["username"].strip().lower():
                if any(
                    u.get("username", "").strip().lower() == datos["username"].strip().lower() and u.get("id") != usuario_id
                    for u in usuarios
                ):
                    raise DuplicateRecordError("El username ya existe.")
            usuarios[indice] = datos
            _save_usuarios(usuarios)
            return datos
    raise NotFoundError(f"No existe un usuario con id {usuario_id}.")


def desactivar_usuario(usuario_id: str) -> Dict[str, Any]:
    usuario = obtener_usuario_por_id(usuario_id)
    usuario["activo"] = False
    usuarios = _load_usuarios()
    for i, item in enumerate(usuarios):
        if item.get("id") == usuario_id:
            usuarios[i] = usuario
            _save_usuarios(usuarios)
            return usuario
    raise NotFoundError(f"No existe un usuario con id {usuario_id}.")


def validar_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    try:
        usuario = obtener_usuario_por_username(username)
    except NotFoundError:
        return None

    if usuario.get("password") == password and usuario.get("activo") is True:
        return usuario
    return None
