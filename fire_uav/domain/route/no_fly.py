"""
Читает GeoJSON с запретными зонами и вычитает их из AOI.
"""

import json
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, shape


def load_no_fly(path: str | Path) -> Polygon | MultiPolygon | None:
    p = Path(path)
    if not p.exists():
        return None
    gjs = json.load(p.open())
    if gjs["type"] == "FeatureCollection":
        geoms = [shape(f["geometry"]) for f in gjs["features"]]
        return geoms[0].union(*geoms[1:]) if geoms else None
    return shape(gjs)  # допустим «голый» Polygon
