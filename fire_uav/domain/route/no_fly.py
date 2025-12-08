"""
Читает GeoJSON с запретными зонами и вычитает их из AOI.
"""

import json
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, shape


def load_no_fly(path: str | Path) -> Polygon | MultiPolygon | None:
    p = Path(path)
    candidates = [p]
    if not p.is_absolute():
        try:
            import fire_uav

            pkg_root = Path(fire_uav.__file__).resolve().parent
            candidates.append(pkg_root.parent / p)
        except Exception:
            candidates.append(Path(__file__).resolve().parents[3] / p)

    target = next((c for c in candidates if c.exists()), None)
    if target is None:
        return None

    gjs = json.load(target.open())
    if gjs["type"] == "FeatureCollection":
        geoms = [shape(f["geometry"]) for f in gjs["features"]]
        return geoms[0].union(*geoms[1:]) if geoms else None
    return shape(gjs)  # допустим «голый» Polygon
