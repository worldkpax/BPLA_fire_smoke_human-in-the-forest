"""
Run-time configuration, читаемая из `.env` или перем. окружения FIRE_*.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FIRE_", extra="ignore")

    # YOLO
    yolo_model: str = "best_yolo11.pt"
    yolo_conf: float = 0.40
    yolo_iou: float = 0.50
    yolo_classes: list[int] = []  # пусто → все классы

    # Recorder
    output_root: str = "./artifacts"

    # Flight
    gsd_target_cm: float = 2.5
    side_overlap: float = 0.7
    front_overlap: float = 0.8
    battery_wh: float = 27.0


settings = Settings()  # импортируйте и используйте
