# mypy: ignore-errors
"""Заглушка-пример для профиля высот (добавлены только типы)."""

from __future__ import annotations

import math
from typing import List, Sequence

import requests

from fire_uav.module_core.schema import Waypoint

_API_URL = "https://api.opentopodata.org/v1/test-dataset"
_EARTH_R = 6_371_000  # м


def profile(route: Sequence[Waypoint]) -> List[float]:
    coords = "|".join(f"{wp.lat},{wp.lon}" for wp in route)
    r = requests.get(_API_URL, params={"locations": coords}, timeout=10)
    r.raise_for_status()
    return [item["elevation"] for item in r.json()["results"]]


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat, dlon = map(math.radians, (lat2 - lat1, lon2 - lon1))
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * _EARTH_R * math.asin(math.sqrt(a))
