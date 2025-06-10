"""
fire_uav – UAV toolkit for forest-fire detection & autonomous survey.

"""
from .core.geometry import haversine_m, offset_latlon
from .core.camera import CameraParams
from .core.detection import DetectionEngine
from .core.schema import Detection, WorldCoord, DetectionsBatch
from .flight.planner import FlightPlanner
from .flight.energy import EnergyModel

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
