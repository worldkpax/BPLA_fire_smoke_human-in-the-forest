"""
Единый объект `settings`, пригодный и для рантайма, и для статического анализа.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from fire_uav.core.settings_loader import Settings as _SettingsDict, load_settings


@dataclass
class Settings:
    # ───────── YOLO ─────────
    yolo_model: str = "yolov11n.pt"
    yolo_conf: float = 0.25
    yolo_iou: float = 0.45
    yolo_classes: List[int] = field(default_factory=lambda: [0, 1, 2])

    # ───────── I/O ──────────
    output_root: Path = Path("data/outputs")

    # ------------------------ #

    @classmethod
    def from_dict(cls, data: _SettingsDict) -> "Settings":
        """Строим экземпляр из dict (например, из JSON-конфига)."""
        defaults = cls()
        return cls(
            yolo_model=data.get("yolo_model", defaults.yolo_model),
            yolo_conf=float(data.get("yolo_conf", defaults.yolo_conf)),
            yolo_iou=float(data.get("yolo_iou", defaults.yolo_iou)),
            yolo_classes=list(data.get("yolo_classes", defaults.yolo_classes)),
            output_root=Path(data.get("output_root", defaults.output_root)),
        )


settings = Settings.from_dict(load_settings())

__all__ = ["Settings", "settings"]
