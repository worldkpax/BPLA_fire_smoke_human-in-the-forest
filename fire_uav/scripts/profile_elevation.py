#!/usr/bin/env python3
"""
Скачивает профиль высот для маршрута и печатает min / max / Δ  (метры)
"""
import sys, json
from fire_uav.flight.elevation import sampled_profile
from fire_uav.flight.planner import Waypoint

def waypoints_from_plan(path):
    items = json.load(open(path))["mission"]["items"]
    return [Waypoint(lat=i["params"][4],
                     lon=i["params"][5],
                     alt=i["params"][6]) for i in items]

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: profile_elevation.py mission.plan")
        sys.exit(1)
    wp = waypoints_from_plan(sys.argv[1])
    h = sampled_profile(wp)
    print(f"min {min(h):.0f} m  max {max(h):.0f} m  Δ {max(h)-min(h):.0f} m")
