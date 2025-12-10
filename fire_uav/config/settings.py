"""
Настройки проекта: единый объект `settings`, который подхватывает значения из JSON
и предоставляет их всем слоям приложения.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from fire_uav.module_core.settings_loader import Settings as _SettingsDict, load_settings


@dataclass
class Settings:
    # Runtime role/adapter
    role: str = "module"
    uav_backend: str = "mavlink"
    mavlink_connection_string: str = "udp:127.0.0.1:14550"
    unreal_base_url: str = "http://127.0.0.1:9000"
    custom_sdk_config: dict = field(default_factory=dict)
    use_native_core: bool = False
    uav_id: str | None = None
    notifications_dir: Path = Path("data/notifications")
    bbox_smooth_alpha: float = 0.5
    bbox_smooth_max_dist_px: float = 80.0
    track_iou_threshold: float = 0.25
    track_max_age_seconds: float = 2.0
    track_min_hits: int = 2
    track_max_missed: int = 10
    track_max_center_distance_px: float = 80.0
    visualizer_enabled: bool = False
    visualizer_url: str = "http://127.0.0.1:8000"

    # Параметры YOLO
    yolo_model: str = "yolov11n.pt"
    yolo_conf: float = 0.4
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
            role=data.get("role", defaults.role),
            uav_backend=data.get("uav_backend", defaults.uav_backend),
            mavlink_connection_string=data.get(
                "mavlink_connection_string", defaults.mavlink_connection_string
            ),
            unreal_base_url=data.get("unreal_base_url", defaults.unreal_base_url),
            custom_sdk_config=data.get("custom_sdk_config", defaults.custom_sdk_config),
            use_native_core=bool(data.get("use_native_core", defaults.use_native_core)),
            uav_id=data.get("uav_id", defaults.uav_id),
            notifications_dir=Path(data.get("notifications_dir", defaults.notifications_dir)),
            bbox_smooth_alpha=float(data.get("bbox_smooth_alpha", defaults.bbox_smooth_alpha)),
            bbox_smooth_max_dist_px=float(
                data.get("bbox_smooth_max_dist_px", defaults.bbox_smooth_max_dist_px)
            ),
            track_iou_threshold=float(data.get("track_iou_threshold", defaults.track_iou_threshold)),
            track_max_age_seconds=float(
                data.get("track_max_age_seconds", defaults.track_max_age_seconds)
            ),
            track_min_hits=int(data.get("track_min_hits", defaults.track_min_hits)),
            track_max_missed=int(data.get("track_max_missed", defaults.track_max_missed)),
            track_max_center_distance_px=float(
                data.get("track_max_center_distance_px", defaults.track_max_center_distance_px)
            ),
            visualizer_enabled=bool(data.get("visualizer_enabled", defaults.visualizer_enabled)),
            visualizer_url=data.get("visualizer_url", defaults.visualizer_url),
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
