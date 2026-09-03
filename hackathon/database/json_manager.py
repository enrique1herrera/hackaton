from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def get_data_dir() -> Path:
    return DATA_DIR


def set_data_dir(path: str | Path) -> Path:
    global DATA_DIR
    DATA_DIR = Path(path).resolve()
    ensure_data_dir()
    return DATA_DIR


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _resolve_file_path(filename: str) -> Path:
    ensure_data_dir()
    if filename.startswith("/"):
        return Path(filename)
    return DATA_DIR / filename


def load_json(filename: str) -> Any:
    """Lee un archivo JSON y devuelve su contenido."""
    file_path = _resolve_file_path(filename)
    if not file_path.exists():
        save_json(filename, [])
        return []

    try:
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            return data if data is not None else []
    except (json.JSONDecodeError, OSError):
        save_json(filename, [])
        return []


def save_json(filename: str, data: Any) -> None:
    """Guarda un JSON con formato legible y UTF-8."""
    file_path = _resolve_file_path(filename)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
