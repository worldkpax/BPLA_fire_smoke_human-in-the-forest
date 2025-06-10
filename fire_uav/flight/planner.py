"""
Lawn-mower grid generator + TSP оптимизация и разделение на миссии.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon

from ..core.geometry import haversine_m
from .energy import EnergyModel

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
except ImportError as e:
    raise RuntimeError("Install `ortools` to use FlightPlanner") from e


@dataclass(slots=True)
class CameraSpec:  # повторяю, чтобы не тянуть зависимость
    sensor_width_mm: float = 6.3
    resolution_px: int = 8064
    focal_length_mm: float = 5.7
    fov_deg: float = 82.1

    def swath_m(self, alt_m: float) -> float:
        return 2 * alt_m * math.tan(math.radians(self.fov_deg / 2))


@dataclass(slots=True)
class GridParams:
    side_overlap: float = 0.7
    front_overlap: float = 0.8
    gsd_target_cm: float = 2.5
    orientation_deg: float = 0


@dataclass(slots=True)
class Waypoint:
    lat: float
    lon: float
    alt: float
    yaw_deg: float = 0.0


class FlightPlanner:
    def __init__(
        self,
        aoi: Polygon,
        cam: CameraSpec | None = None,
        grid: GridParams | None = None,
        energy: EnergyModel | None = None,
    ):
        self.aoi = aoi
        self.cam = cam or CameraSpec()
        self.grid = grid or GridParams()
        self.energy = energy or EnergyModel()

        self.altitude_m = self._altitude_for_gsd(self.grid.gsd_target_cm)
        self.line_spacing_m = self._line_spacing()
        self.forward_spacing_m = self._forward_spacing()

    # ------------------------------------------------------------------ #
    # Geometry helpers
    # ------------------------------------------------------------------ #
    def _altitude_for_gsd(self, gsd_cm: float) -> float:
        return (
            gsd_cm
            * self.cam.focal_length_mm
            * self.cam.resolution_px
            / (100 * self.cam.sensor_width_mm)
        )

    def _line_spacing(self) -> float:
        return self.cam.swath_m(self.altitude_m) * (1 - self.grid.side_overlap)

    def _forward_spacing(self) -> float:
        return self.cam.swath_m(self.altitude_m) * (1 - self.grid.front_overlap)

    # ------------------------------------------------------------------ #
    # Grid generation
    # ------------------------------------------------------------------ #
    def build_grid(self) -> List[LineString]:
        rotated = rotate(self.aoi, -self.grid.orientation_deg, origin="centroid", use_radians=False)
        minx, miny, maxx, maxy = rotated.bounds

        lines: list[LineString] = []
        y = miny
        while y <= maxy:
            segment = LineString([(minx, y), (maxx, y)])
            inter = segment.intersection(rotated)
            if not inter.is_empty:
                if isinstance(inter, LineString):
                    lines.append(inter)
                else:  # MultiLineString
                    lines.extend(inter)
            y += self.line_spacing_m

        # rotate обратно
        lines = [rotate(l, self.grid.orientation_deg, origin="centroid", use_radians=False) for l in lines]

        # чередуем направление
        for i in range(1, len(lines), 2):
            lines[i] = LineString(list(lines[i].coords)[::-1])

        return lines

    # ------------------------------------------------------------------ #
    # Lines -> waypoints
    # ------------------------------------------------------------------ #
    def lines_to_waypoints(self, lines: List[LineString]) -> List[Waypoint]:
        wps: list[Waypoint] = []
        for line in lines:
            length = line.length
            samples = max(2, int(math.ceil(length / self.forward_spacing_m)))
            for i in range(samples):
                pt: Point = line.interpolate(i / (samples - 1), normalized=True)
                wps.append(Waypoint(lat=pt.y, lon=pt.x, alt=self.altitude_m))
        return wps

    # ------------------------------------------------------------------ #
    # TSP optimisation
    # ------------------------------------------------------------------ #
    def optimise(self, waypoints: List[Waypoint]) -> List[Waypoint]:
        n = len(waypoints)
        if n <= 3:  # микроскопический набор — смысла оптимизировать нет
            return waypoints

        dist = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                dij = int(haversine_m((waypoints[i].lat, waypoints[i].lon), (waypoints[j].lat, waypoints[j].lon)))
                dist[i][j] = dist[j][i] = dij

        manager = pywrapcp.RoutingIndexManager(n, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def cb(from_idx, to_idx):
            return dist[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]

        transit_cb = routing.RegisterTransitCallback(cb)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

        params = pywrapcp.DefaultRoutingSearchParameters()
        params.time_limit.seconds = 5
        params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

        sol = routing.SolveWithParameters(params)
        if not sol:
            return waypoints  # вернём без оптимизации

        route: list[Waypoint] = []
        idx = routing.Start(0)
        while not routing.IsEnd(idx):
            route.append(waypoints[manager.IndexToNode(idx)])
            idx = sol.Value(routing.NextVar(idx))
        return route

    # ------------------------------------------------------------------ #
    # Energy split
    # ------------------------------------------------------------------ #
    def split_missions(self, ordered: List[Waypoint]) -> List[List[Waypoint]]:
        missions: list[list[Waypoint]] = []
        current: list[Waypoint] = []
        distance_accum = 0.0
        prev: Waypoint | None = None

        for wp in ordered:
            if prev:
                distance_accum += haversine_m((prev.lat, prev.lon), (wp.lat, wp.lon))
            current.append(wp)
            prev = wp
            if self.energy.energy_used_wh(distance_accum) >= self.energy.battery_wh * 0.9:
                missions.append(current)
                current = []
                distance_accum = 0.0
                prev = None
        if current:
            missions.append(current)
        return missions

    # ------------------------------------------------------------------ #
    # Public pipeline
    # ------------------------------------------------------------------ #
    def generate(self) -> List[List[Waypoint]]:
        grid = self.build_grid()
        wps = self.lines_to_waypoints(grid)
        ordered = self.optimise(wps)
        return self.split_missions(ordered)
