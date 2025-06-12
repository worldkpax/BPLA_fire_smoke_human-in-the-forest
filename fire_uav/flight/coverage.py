from shapely.geometry import box, Polygon
from shapely.ops import unary_union       # ← вместо .union(*cells)

def coverage_percent(aoi: Polygon, waypoints, swath_m: float) -> float:
    half = swath_m / 3
    cells = [box(wp.lon - half, wp.lat - half,
                 wp.lon + half, wp.lat + half) for wp in waypoints]

    # Shapely >=1.8: правильно использовать unary_union
    covered = unary_union(cells).intersection(aoi)
    return 100 * covered.area / aoi.area if aoi.area else 0.0
