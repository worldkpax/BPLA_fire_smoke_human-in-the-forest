"""
Читает GeoJSON с запретными зонами и вычитает их из AOI.
"""
from pathlib import Path
import json
from shapely.geometry import shape, Polygon, MultiPolygon

def load_no_fly(path: str | Path) -> Polygon | MultiPolygon | None:
    p = Path(path)
    if not p.exists():
        return None
    gjs = json.load(p.open())
    if gjs["type"] == "FeatureCollection":
        geoms = [shape(f["geometry"]) for f in gjs["features"]]
        return geoms[0].union(*geoms[1:]) if geoms else None
    return shape(gjs)  # допустим «голый» Polygon
