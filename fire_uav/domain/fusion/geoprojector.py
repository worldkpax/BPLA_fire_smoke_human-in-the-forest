from __future__ import annotations

from typing import Tuple

from fire_uav.core.geometry import offset_latlon
from fire_uav.core.schema import TelemetrySample, WorldCoord
from fire_uav.domain.video.camera import CameraParams

BBox = Tuple[int, int, int, int]


class GeoProjector:
    """
    Простейшая геопривязка детекций: считаем, что камера смотрит вниз и
    переводим смещение центра bbox в метры с помощью GSD, затем в lat/lon.
    """

    def __init__(self, camera: CameraParams | None = None) -> None:
        self._camera = camera or CameraParams()

    def project(
        self, bbox: BBox, frame_size: Tuple[int, int], telemetry: TelemetrySample
    ) -> WorldCoord:
        width, height = frame_size
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        center_x = width / 2.0
        center_y = height / 2.0
        dx_px = cx - center_x
        dy_px = center_y - cy  # экранная ось Y направлена вниз

        gsd_cm = self._camera.gsd_cm_per_px(max(telemetry.alt_m, 1.0))
        gsd_m = gsd_cm / 100.0

        offset_x_m = dx_px * gsd_m
        offset_y_m = dy_px * gsd_m

        lat, lon = offset_latlon(telemetry.lat, telemetry.lon, offset_x_m, offset_y_m)
        return WorldCoord(lat=lat, lon=lon)
