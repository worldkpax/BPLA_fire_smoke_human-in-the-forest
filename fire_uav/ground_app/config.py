from __future__ import annotations

from fire_uav.config.settings import settings


def load_ground_settings():
    """Return ground-station settings (shared with module for now)."""
    return settings


__all__ = ["load_ground_settings", "settings"]

