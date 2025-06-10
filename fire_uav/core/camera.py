"""
Оптические параметры камеры + пара утилит для пересчёта в GSD и охват.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(slots=True)
class CameraParams:
    # Defaults for DJI Mini 4 Pro
    sensor_width_mm: float = 6.3
    resolution_px: int = 8_064           # long side
    focal_length_mm: float = 5.7
    fov_deg: float = 82.1                # diagonal FOV

    # --------------------------------------------------------------------- #
    # Derived values
    # --------------------------------------------------------------------- #
    def gsd_cm_per_px(self, altitude_m: float) -> float:
        """Ground-sampling distance в cm/px на высоте altitude_m."""
        return (
            100
            * altitude_m
            * self.sensor_width_mm
            / (self.focal_length_mm * self.resolution_px)
        )

    def swath_m(self, altitude_m: float) -> float:
        """Ширина охвата (по диагонали) при заданной высоте."""
        return 2 * altitude_m * math.tan(math.radians(self.fov_deg / 2))
