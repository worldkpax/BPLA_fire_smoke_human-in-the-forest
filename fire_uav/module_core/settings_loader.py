# Shared settings loader (imported by both module and ground runtimes).
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, TypeAlias

# --------------------------------------------------------------------------- #
#  Публичный тип: «сырые» настройки как словарь
#  (его используют другие модули и mypy)
# --------------------------------------------------------------------------- #
Settings: TypeAlias = Dict[str, Any]


# --------------------------------------------------------------------------- #
#  Поиск JSON-файла с настройками
# --------------------------------------------------------------------------- #
def _find_settings_file() -> Path:
    """
    Определяет, откуда брать конфигурацию:

    1. Если задана переменная окружения ``$FIRE_UAV_SETTINGS`` —
       используем её.
    2. Иначе — встроенный ``fire_uav/config/settings_default.json``.
    """
    env_path = os.environ.get("FIRE_UAV_SETTINGS")
    if env_path:
        return Path(env_path).expanduser()

    # fallback → встроенный settings_default.json
    import fire_uav  # локальный импорт, чтобы избежать циклов

    pkg_root = Path(fire_uav.__file__).resolve().parent
    return pkg_root / "config" / "settings_default.json"


# --------------------------------------------------------------------------- #
#  Загрузка настроек
# --------------------------------------------------------------------------- #
def load_settings() -> Settings:
    """Читает JSON и возвращает его содержимое как ``dict[str, Any]``."""
    cfg_path = _find_settings_file()
    with cfg_path.open(encoding="utf-8") as fh:
        data: Settings = json.load(fh)
    return data


# --------------------------------------------------------------------------- #
#  Экспортируем символы, чтобы IDE / mypy «видели» их из-вне модуля
# --------------------------------------------------------------------------- #
__all__: list[str] = ["Settings", "load_settings"]
