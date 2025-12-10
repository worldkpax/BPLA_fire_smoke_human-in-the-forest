from __future__ import annotations

from fire_uav.config.settings import settings


def load_module_settings():
    """Return module-side settings (reuse shared config for now)."""
    return settings


__all__ = ["load_module_settings", "settings"]

