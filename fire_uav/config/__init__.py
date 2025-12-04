"""
fire_uav.config  ― пакет конфигурации.

Позволяет импортировать:
    • settings
    • load_settings
    • Settings
из корня пакета, без .settings
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

_settings_mod: ModuleType = import_module(".settings", package=__name__)

Settings = _settings_mod.Settings  # noqa: F401
settings = _settings_mod.settings  # noqa: F401
load_settings = _settings_mod.load_settings  # noqa: F401

__all__ = ["Settings", "settings", "load_settings"]
