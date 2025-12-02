"""
Настройки проекта: единый объект `settings`, который подхватывает значения из JSON
и предоставляет их всем слоям приложения.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from fire_uav.core.settings_loader import Settings as _SettingsDict, load_settings


@dataclass
class Settings:
    # Параметры YOLO
    yolo_model: str = "yolov11n.pt"
    yolo_conf: float = 0.25
    yolo_iou: float = 0.45
    yolo_classes: List[int] = field(default_factory=lambda: [0, 1, 2])

    # Общие пути
    output_root: Path = Path("data/outputs")

    # Отправка на наземную станцию
    ground_station_host: str = "127.0.0.1"
    ground_station_port: int = 9000
    ground_station_udp: bool = False
    ground_station_enabled: bool = False

    # Агрегация по кадрам / телеметрия
    agg_window: int = 5
    agg_votes_required: int = 3
    agg_min_confidence: float = 0.6
    agg_max_distance_m: float = 35.0
    agg_ttl_seconds: float = 8.0

    # ------------------------ #

    @classmethod
    def from_dict(cls, data: _SettingsDict) -> "Settings":
        """Собрать объект настроек из dict (например, из JSON-файла)."""
        defaults = cls()
        return cls(
            yolo_model=data.get("yolo_model", defaults.yolo_model),
            yolo_conf=float(data.get("yolo_conf", defaults.yolo_conf)),
            yolo_iou=float(data.get("yolo_iou", defaults.yolo_iou)),
            yolo_classes=list(data.get("yolo_classes", defaults.yolo_classes)),
            output_root=Path(data.get("output_root", defaults.output_root)),
            ground_station_host=data.get("ground_station_host", defaults.ground_station_host),
            ground_station_port=int(data.get("ground_station_port", defaults.ground_station_port)),
            ground_station_udp=bool(data.get("ground_station_udp", defaults.ground_station_udp)),
            ground_station_enabled=bool(
                data.get("ground_station_enabled", defaults.ground_station_enabled)
            ),
            agg_window=int(data.get("agg_window", defaults.agg_window)),
            agg_votes_required=int(data.get("agg_votes_required", defaults.agg_votes_required)),
            agg_min_confidence=float(data.get("agg_min_confidence", defaults.agg_min_confidence)),
            agg_max_distance_m=float(data.get("agg_max_distance_m", defaults.agg_max_distance_m)),
            agg_ttl_seconds=float(data.get("agg_ttl_seconds", defaults.agg_ttl_seconds)),
        )


settings = Settings.from_dict(load_settings())

__all__ = ["Settings", "settings"]
