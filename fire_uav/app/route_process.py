"""
Генерирует маршрут ТОЧНО по нарисованной линии (Polyline).
Polygon и другие геометрии больше не поддерживаются.
Возвращает list[list[(lat, lon, alt)]] — сериализуемо.
"""
from __future__ import annotations
from typing import List, Tuple
from shapely import wkt
import fire_uav.route_planner_cpp as rpcp   # C++ модуль

WaypointT = Tuple[float, float, float]      # lat, lon, alt


def build_route(line_wkt: str, _: int) -> List[List[WaypointT]]:
    geom = wkt.loads(line_wkt)
    if geom.geom_type != "LineString":
        raise ValueError("Only Polyline supported")

    altitude = 120.0
    path_latlon = [(lat, lon) for lon, lat in geom.coords]   # lon,lat → lat,lon
    wps = rpcp.follow_path(path_latlon, altitude)

    return [[(wp.lat, wp.lon, wp.alt) for wp in wps]]
