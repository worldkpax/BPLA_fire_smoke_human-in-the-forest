"""Convert missions → QGroundControl JSON & KML."""
import json
from typing import List
from .planner import Waypoint


def to_qgc(missions: List[List[Waypoint]]) -> dict:
    seq = 0
    items = []
    for mission in missions:
        for wp in mission:
            items.append(
                {
                    "AMSLAltAboveTerrain": None,
                    "Altitude": wp.alt,
                    "AltitudeMode": 1,
                    "Command": 16,
                    "DoJumpId": seq,
                    "Frame": 3,
                    "Params": [0, 0, 0, 0, wp.lat, wp.lon, wp.alt],
                    "Type": "SimpleItem",
                }
            )
            seq += 1
    return {
        "fileType": "Plan",
        "geoFence": {},
        "mission": {"items": items},
        "rallyPoints": {},
        "version": 2,
    }


def dump_qgc(missions, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_qgc(missions), f, indent=2)
