from __future__ import annotations

from typing import Any, List

from fire_uav.config import settings as app_settings
from fire_uav.module_core.factories import get_energy_model
from fire_uav.module_core.interfaces.energy import IEnergyModel
from fire_uav.module_core.interfaces.route_planner import IRoutePlanner
from fire_uav.module_core.route.maneuvers import build_maneuver, build_rejoin
from fire_uav.module_core.schema import Route, TelemetrySample, Waypoint
from fire_uav.module_core.route.planner import build_route


class PythonRoutePlanner(IRoutePlanner):
    """Route planner backed by the existing grid/coverage generator."""

    def __init__(self, *, energy_model: IEnergyModel | None = None, settings: Any | None = None) -> None:
        self.energy_model = energy_model or get_energy_model(app_settings)
        self.settings = settings or app_settings

    def plan_route(self, geom_wkt: str, gsd_cm: int | float = 0) -> Route:
        missions = build_route(geom_wkt, int(gsd_cm) if gsd_cm else 0)
        wps: List[Waypoint] = [
            Waypoint(lat=lat, lon=lon, alt=alt) for mission in missions for (lat, lon, alt) in mission
        ]
        return Route(version=1, waypoints=wps, active_index=0 if wps else None)

    def plan_maneuver(
        self,
        current_state: TelemetrySample,
        target_lat: float,
        target_lon: float,
        base_route: Route,
    ) -> Route | None:
        return build_maneuver(
            current_state=current_state,
            target_lat=target_lat,
            target_lon=target_lon,
            base_route=base_route,
            energy_model=self.energy_model,
            settings=self.settings,
        )

    def plan_rejoin(self, exit_wp: Waypoint, base_route: Route) -> list[Waypoint]:
        return build_rejoin(exit_wp, base_route)


__all__ = ["PythonRoutePlanner"]
