"""
Чистые геометрические функции без внешних зависимостей —
можно переиспользовать из flight-планировщика и из детектора.
"""
from __future__ import annotations
import math
from typing import Tuple

EARTH_RADIUS_M: float = 6_378_137.0  # WGS-84 semi-major ось, метры


def haversine_m(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Great-circle distance **в метрах** между двумя (lat, lon) точками."""
    lat1, lon1 = p1
    lat2, lon2 = p2
    phi1, phi2 = map(math.radians, (lat1, lat2))
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def offset_latlon(lat: float, lon: float, dx_m: float, dy_m: float) -> Tuple[float, float]:
    """Сместить точку на dx (восток), dy (север) в метрах — вернуть новую (lat, lon)."""
    d_lat = dy_m / EARTH_RADIUS_M
    d_lon = dx_m / (EARTH_RADIUS_M * math.cos(math.radians(lat)))
    return lat + math.degrees(d_lat), lon + math.degrees(d_lon)
