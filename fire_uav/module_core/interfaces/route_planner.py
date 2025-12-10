from __future__ import annotations

from abc import ABC, abstractmethod

from fire_uav.module_core.schema import Route, TelemetrySample, Waypoint


class IRoutePlanner(ABC):
    """Abstract interface for UAV route planning and maneuvers."""

    @abstractmethod
    def plan_route(self, geom_wkt: str, gsd_cm: int | float = 0) -> Route:
        """Plan a base route (signature mirrors existing planner)."""

    @abstractmethod
    def plan_maneuver(
        self,
        current_state: TelemetrySample,
        target_lat: float,
        target_lon: float,
        base_route: Route,
    ) -> Route | None:
        """Build a maneuver route (approach + orbit + rejoin) or return None if not feasible."""

    @abstractmethod
    def plan_rejoin(self, exit_wp: Waypoint, base_route: Route) -> list[Waypoint]:
        """Plan a path from maneuver exit waypoint back to the base route."""

