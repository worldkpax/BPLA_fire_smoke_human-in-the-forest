"""
Pydantic-модели (DTO) — единый формат данных между модулями.
"""
from __future__ import annotations
from datetime import datetime
from typing import Tuple, List

from pydantic import BaseModel, Field


class WorldCoord(BaseModel):
    lat: float
    lon: float


class Detection(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    camera_id: str
    class_id: int
    confidence: float
    bbox: Tuple[int, int, int, int]          # x1, y1, x2, y2
    world_coord: WorldCoord | None = None
    relative_angles: Tuple[float, float] | None = None  # az, el


class FrameMeta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    camera_id: str
    width: int
    height: int


class DetectionsBatch(BaseModel):
    frame: FrameMeta
    detections: List[Detection]
