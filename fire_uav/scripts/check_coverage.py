#!/usr/bin/env python3
"""
Посчитать процент покрытия AOI кадрами по сохранённому mission.plan
"""
import json, sys
from shapely.geometry import shape, Polygon
from fire_uav.flight.coverage import coverage_percent

def waypoints_from_plan(path):
    items = json.load(open(path))["mission"]["items"]
    from fire_uav.flight.planner import Waypoint
    return [Waypoint(lat=i["params"][4],
                     lon=i["params"][5],
                     alt=i["params"][6]) for i in items]

def main(plan, aoi_geojson):
    aoi = shape(json.load(open(aoi_geojson)))
    wp = waypoints_from_plan(plan)
    from fire_uav.flight.planner import CameraSpec
    swath = CameraSpec().swath_m(wp[0].alt)
    print(f"Coverage ≈ {coverage_percent(aoi, wp, swath):.1f} %")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: check_coverage.py mission.plan aoi.geojson")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
