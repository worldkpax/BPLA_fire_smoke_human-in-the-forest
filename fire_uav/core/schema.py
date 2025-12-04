"""
Pydantic-модели (DTO) — единый формат данных между модулями.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from pydantic import BaseModel, Field


class WorldCoord(BaseModel):
    lat: float
    lon: float


class Detection(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    camera_id: str
    class_id: int
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
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


class TelemetrySample(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    alt_m: float = Field(..., ge=0)
    yaw_deg: float = Field(0.0, description="Heading/yaw angle in degrees")
    pitch_deg: float = Field(0.0)
    roll_deg: float = Field(0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str | None = Field(
        default=None,
        description="Optional identifier of the telemetry source (autopilot channel, etc.)",
    )


class GeoDetection(BaseModel):
    class_id: int
    confidence: float
    location: WorldCoord
    captured_at: datetime
    source_frame: str
