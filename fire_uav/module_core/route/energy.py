"""Energy & battery helper."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EnergyModel:
    cruise_speed_mps: float = 12.0
    power_cruise_w: float = 45.0
    battery_wh: float = 27.0

    def cruise_time_s(self, distance_m: float) -> float:
        return distance_m / self.cruise_speed_mps

    def energy_used_wh(self, distance_m: float) -> float:
        return self.cruise_time_s(distance_m) / 3600 * self.power_cruise_w


__all__ = ["EnergyModel"]
