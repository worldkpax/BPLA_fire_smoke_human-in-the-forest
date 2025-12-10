from __future__ import annotations

from fire_uav.module_core.geometry import haversine_m
from fire_uav.module_core.interfaces.energy import IEnergyModel
from fire_uav.module_core.schema import Route, TelemetrySample


class PythonEnergyModel(IEnergyModel):
    """Simple cruise-based energy estimator."""

    def __init__(
        self,
        cruise_speed_mps: float = 12.0,
        power_cruise_w: float = 45.0,
        battery_wh: float = 27.0,
    ) -> None:
        self.cruise_speed_mps = cruise_speed_mps
        self.power_cruise_w = power_cruise_w
        self.battery_wh = battery_wh

    def _route_distance_m(self, route: Route) -> float:
        distance = 0.0
        for prev, cur in zip(route.waypoints, route.waypoints[1:]):
            distance += haversine_m((prev.lat, prev.lon), (cur.lat, cur.lon))
        return distance

    def energy_cost(self, route: Route) -> float:
        distance = self._route_distance_m(route)
        if self.cruise_speed_mps <= 0:
            return float("inf")
        cruise_time_s = distance / self.cruise_speed_mps
        return cruise_time_s / 3600.0 * self.power_cruise_w

    def remaining_energy(self, telemetry: TelemetrySample) -> float:
        battery_fraction = max(0.0, min(1.0, telemetry.battery))
        return battery_fraction * self.battery_wh


__all__ = ["PythonEnergyModel"]
