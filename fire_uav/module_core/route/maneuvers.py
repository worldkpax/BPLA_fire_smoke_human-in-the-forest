from __future__ import annotations

import math
from typing import List

from fire_uav.module_core.geometry import haversine_m, offset_latlon
from fire_uav.module_core.interfaces.energy import IEnergyModel
from fire_uav.module_core.schema import Route, TelemetrySample, Waypoint


def _as_waypoint(current: TelemetrySample | Waypoint, *, alt: float | None = None) -> Waypoint:
    if isinstance(current, Waypoint):
        return current
    return Waypoint(lat=current.lat, lon=current.lon, alt=alt if alt is not None else current.alt)


def build_orbit(
    target_lat: float,
    target_lon: float,
    radius_m: float,
    altitude_m: float,
    points_per_circle: int,
    loops: int,
) -> List[Waypoint]:
    steps = max(3, points_per_circle)
    result: List[Waypoint] = []
    total = loops * steps
    for i in range(total):
        angle = 2 * math.pi * (i / steps)
        dx = radius_m * math.cos(angle)
        dy = radius_m * math.sin(angle)
        lat, lon = offset_latlon(target_lat, target_lon, dx, dy)
        result.append(Waypoint(lat=lat, lon=lon, alt=altitude_m))
    # ensure we end near entry point
    result.append(Waypoint(lat=target_lat, lon=target_lon, alt=altitude_m))
    return result


def build_approach(current_pos: TelemetrySample | Waypoint, entry_wp: Waypoint) -> List[Waypoint]:
    start = _as_waypoint(current_pos, alt=entry_wp.alt)
    if haversine_m((start.lat, start.lon), (entry_wp.lat, entry_wp.lon)) < 0.5:
        return [entry_wp]
    return [start, entry_wp]


def build_rejoin(exit_wp: Waypoint, base_route: Route) -> List[Waypoint]:
    if not base_route.waypoints:
        return []

    closest_idx = 0
    closest_dist = float("inf")
    for idx, wp in enumerate(base_route.waypoints):
        dist = haversine_m((exit_wp.lat, exit_wp.lon), (wp.lat, wp.lon))
        if dist < closest_dist:
            closest_dist = dist
            closest_idx = idx

    path = [exit_wp]
    path.extend(base_route.waypoints[closest_idx:])
    return path


def build_maneuver(
    current_state: TelemetrySample,
    target_lat: float,
    target_lon: float,
    base_route: Route,
    energy_model: IEnergyModel,
    settings,
) -> Route | None:
    altitude = getattr(settings, "maneuver_alt_m", current_state.alt)
    radius = getattr(settings, "orbit_radius_m", 50.0)
    points_per_circle = getattr(settings, "orbit_points_per_circle", 12)
    loops = getattr(settings, "orbit_loops", 1)

    entry_wp = Waypoint(lat=target_lat, lon=target_lon, alt=altitude)
    orbit = build_orbit(target_lat, target_lon, radius, altitude, points_per_circle, loops)
    approach = build_approach(current_state, entry_wp)
    exit_wp = orbit[-1] if orbit else entry_wp
    rejoin_path = build_rejoin(exit_wp, base_route)

    waypoints = approach + orbit + rejoin_path
    route = Route(
        version=base_route.version if base_route.version is not None else 1,
        waypoints=waypoints,
        active_index=0 if waypoints else None,
    )

    required = energy_model.energy_cost(route)
    available = energy_model.remaining_energy(current_state)
    if required > available:
        return None
    return route


__all__ = [
    "build_orbit",
    "build_approach",
    "build_rejoin",
    "build_maneuver",
]

