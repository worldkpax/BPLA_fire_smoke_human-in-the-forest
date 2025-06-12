"""
Запрашиваем высоту SRTM1 (≈30 м) через open-elevation.com
или любую совместимую точку доступа.
"""
from typing import List
import requests, math

def sampled_profile(waypoints, step_m: float = 50) -> List[float]:
    # дискретизируем путь по step_m
    lats, lons = [], []
    for a, b in zip(waypoints[:-1], waypoints[1:]):
        dist = _haversine(a.lat, a.lon, b.lat, b.lon)
        n = max(1, int(math.ceil(dist / step_m)))
        for i in range(n):
            t = i / n
            lats.append(a.lat + (b.lat - a.lat) * t)
            lons.append(a.lon + (b.lon - a.lon) * t)

    q = "|".join(f"{la},{lo}" for la, lo in zip(lats, lons))
    rsp = requests.get("https://api.open-elevation.com/api/v1/lookup",
                       params={"locations": q}, timeout=10)
    data = rsp.json()["results"]
    return [d["elevation"] for d in data]

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ, dλ = map(math.radians, (lat2-lat1, lon2-lon1))
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return 2*R*math.asin(math.sqrt(a))
