class ValidationError(ValueError):
    """Se lanza cuando un valor o una estructura de datos es inválida."""


class NotFoundError(FileNotFoundError):
    """Se lanza cuando un registro no existe."""


class InsufficientStockError(ValidationError):
    """Se lanza cuando la cantidad solicitada supera el stock disponible."""


class PermissionDeniedError(Exception):
    """Se lanza cuando un usuario no tiene permisos para una acción."""


class DuplicateRecordError(ValidationError):
    """Se lanza cuando se intenta crear un registro duplicado."""
