"""
Lawn-mower grid generator + TSP оптимизация + деление на миссии.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List

from shapely.affinity import rotate
from shapely.geometry import (
    LineString, MultiLineString, GeometryCollection,
    Point, Polygon
)

from fire_uav.utils.settings_loader import load_settings
from fire_uav.flight.no_fly import load_no_fly
from ..core.geometry import haversine_m
from .energy import EnergyModel

settings = load_settings()        # ← читаем единожды

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
except ImportError as e:
    raise RuntimeError("Install `ortools` to use FlightPlanner") from e


# ───────────────── dataclasses ───────────────── #

@dataclass(slots=True)
class CameraSpec:
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
    lat: float; lon: float; alt: float; yaw_deg: float = 0.0


# ───────────────── FlightPlanner ──────────────── #

class FlightPlanner:
    def __init__(self,
                 aoi: Polygon,
                 cam: CameraSpec | None = None,
                 grid: GridParams | None = None,
                 energy: EnergyModel | None = None):
        # вычитаем запретные зоны
        nfz = load_no_fly(settings.get("no_fly_geojson", ""))
        if nfz:
            aoi = aoi.difference(nfz)

        self.aoi = aoi
        self.cam = cam or CameraSpec()
        self.grid = grid or GridParams()
        self.energy = energy or EnergyModel()

        self.altitude_m = self._altitude_for_gsd(self.grid.gsd_target_cm)
        self.line_spacing_m = self._line_spacing()
        self.forward_spacing_m = self._forward_spacing()

    # ───── helpers ───── #
    def _altitude_for_gsd(self, gsd_cm):          # м над землёй
        return (gsd_cm * self.cam.focal_length_mm *
                self.cam.resolution_px / (100 * self.cam.sensor_width_mm))

    def _line_spacing(self):
        return self.cam.swath_m(self.altitude_m) * (1 - self.grid.side_overlap)

    def _forward_spacing(self):
        return self.cam.swath_m(self.altitude_m) * (1 - self.grid.front_overlap)

    # ───── grid ───── #
    def build_grid(self) -> List[LineString]:
        """Сетка «гребёнки» — шаг в метрах ⇒ пересчитываем в градусы."""
        rot = rotate(self.aoi, -self.grid.orientation_deg,
                     origin="centroid", use_radians=False)
        minx, miny, maxx, maxy = rot.bounds

        step_deg = self.line_spacing_m / 111_000          # метр → градус
        lines: list[LineString] = []
        y = miny
        while y <= maxy:
            seg = LineString([(minx, y), (maxx, y)])
            inter = seg.intersection(rot)
            if not inter.is_empty:
                if isinstance(inter, LineString):
                    lines.append(inter)
                elif isinstance(inter, MultiLineString):
                    lines.extend(inter.geoms)
                elif isinstance(inter, GeometryCollection):
                    lines.extend(g for g in inter.geoms if isinstance(g, LineString))
            y += step_deg

        # возвращаем исходный угол
        lines = [rotate(l, self.grid.orientation_deg,
                        origin="centroid", use_radians=False) for l in lines]
        # зиг-заг
        for i in range(1, len(lines), 2):
            lines[i] = LineString(list(lines[i].coords)[::-1])
        return lines

    # ───── lines → waypoints ───── #
    def lines_to_waypoints(self, lines):
        """Превращаем линии в точки съёмки.
           Шаг пересчитываем в градусы, чтобы точек было адекватно."""
        step_deg = self.forward_spacing_m / 111_000  # ≈ град/шаг
        wps: list[Waypoint] = []
        for ln in lines:
            length_deg = ln.length  # длина в °
            n = max(2, math.ceil(length_deg / step_deg))
            for i in range(n):
                pt: Point = ln.interpolate(i / (n - 1), normalized=True)
                wps.append(Waypoint(lat=pt.y, lon=pt.x, alt=self.altitude_m))
        return wps

    # ───── TSP ───── #
    def optimise(self, wps: List[Waypoint]) -> List[Waypoint]:
        n = len(wps)
        if n <= 3:
            return wps
        dist = [[0]*n for _ in range(n)]
        for i in range(n):
            for j in range(i+1, n):
                d = int(haversine_m((wps[i].lat, wps[i].lon),
                                    (wps[j].lat, wps[j].lon)))
                dist[i][j] = dist[j][i] = d
        mgr = pywrapcp.RoutingIndexManager(n, 1, 0)
        rt = pywrapcp.RoutingModel(mgr)
        cb = rt.RegisterTransitCallback(
            lambda a, b: dist[mgr.IndexToNode(a)][mgr.IndexToNode(b)])
        rt.SetArcCostEvaluatorOfAllVehicles(cb)
        p = pywrapcp.DefaultRoutingSearchParameters()
        p.time_limit.seconds = 5
        p.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        sol = rt.SolveWithParameters(p)
        if not sol:
            return wps
        route = []
        idx = rt.Start(0)
        while not rt.IsEnd(idx):
            route.append(wps[mgr.IndexToNode(idx)])
            idx = sol.Value(rt.NextVar(idx))
        return route

    # ───── разделение по батареям ───── #
    def split_missions(self, ordered):
        missions, cur, dist, prev = [], [], 0.0, None
        for wp in ordered:
            if prev:
                dist += haversine_m((prev.lat, prev.lon), (wp.lat, wp.lon))
            cur.append(wp); prev = wp
            if self.energy.energy_used_wh(dist) >= self.energy.battery_wh*0.9:
                missions.append(cur); cur, dist, prev = [], 0.0, None
        if cur:
            missions.append(cur)
        return missions

    # ───── pipeline ───── #
    def generate(self):
        grid = self.build_grid()
        wps = self.lines_to_waypoints(grid)
        ordered = self.optimise(wps)
        return self.split_missions(ordered)
