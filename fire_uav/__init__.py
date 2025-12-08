"""
fire_uav – UAV toolkit: fire/smoke detection + flight-planner.
"""

from __future__ import annotations

# ── public API -------------------------------------------------------------
from fire_uav.domain.detect.detection import DetectionEngine
from fire_uav.domain.route.energy import EnergyModel
from fire_uav.domain.route.planner import FlightPlanner
from fire_uav.domain.video.camera import CameraParams

from .core.geometry import haversine_m, offset_latlon
from .core.schema import Detection, DetectionsBatch, WorldCoord

__all__ = (
    "haversine_m",
    "offset_latlon",
    "CameraParams",
    "DetectionEngine",
    "Detection",
    "WorldCoord",
    "DetectionsBatch",
    "FlightPlanner",
    "EnergyModel",
)

# ── logging: сразу на старте отправляем всё в artifacts/logs/ -------------
from fire_uav.logging_setup import setup_logging

setup_logging()  # создаёт каталоги и вешает FileHandler
