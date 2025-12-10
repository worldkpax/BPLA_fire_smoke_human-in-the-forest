from __future__ import annotations

from typing import Tuple

from fire_uav.domain.video.camera import CameraParams
from fire_uav.module_core.geometry import haversine_m, offset_latlon
from fire_uav.module_core.interfaces.geo import IGeoProjector
from fire_uav.module_core.schema import TelemetrySample, WorldCoord


class PythonGeoProjector(IGeoProjector):
    """Pure-Python geo projector based on simple nadir camera assumptions."""

    def __init__(self, camera: CameraParams | None = None) -> None:
        self._camera = camera or CameraParams()

    def compute_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return haversine_m((lat1, lon1), (lat2, lon2))

    def project_bbox_to_ground(
        self,
        telemetry: TelemetrySample,
        bbox: tuple[float, float, float, float],
        image_width: int,
        image_height: int,
    ) -> tuple[float, float]:
        width, height = image_width, image_height
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        center_x = width / 2.0
        center_y = height / 2.0
        dx_px = cx - center_x
        dy_px = center_y - cy  # экранная ось Y направлена вниз

        gsd_cm = self._camera.gsd_cm_per_px(max(telemetry.alt, 1.0))
        gsd_m = gsd_cm / 100.0

        offset_x_m = dx_px * gsd_m
        offset_y_m = dy_px * gsd_m

        lat, lon = offset_latlon(telemetry.lat, telemetry.lon, offset_x_m, offset_y_m)
        return lat, lon

    # Legacy helper used by existing call sites
    def project(
        self, bbox: Tuple[int, int, int, int], frame_size: Tuple[int, int], telemetry: TelemetrySample
    ) -> WorldCoord:
        lat, lon = self.project_bbox_to_ground(telemetry, bbox, frame_size[0], frame_size[1])
        return WorldCoord(lat=lat, lon=lon)


# Backwards-compatible alias
GeoProjector = PythonGeoProjector

__all__ = ["PythonGeoProjector", "GeoProjector"]

