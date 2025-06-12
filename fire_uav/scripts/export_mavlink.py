#!/usr/bin/env python3
"""
mission.plan  ➜  простой текстовый MAVLink-waypoint файл (QGC WPL 120).
Использование:
    python scripts/export_mavlink.py artifacts/mission.plan artifacts/mission.txt
"""
import json, sys, pathlib

def main(src: str, dst: str):
    items = json.load(open(src, encoding="utf-8"))["mission"]["items"]
    with open(dst, "w", encoding="utf-8") as f:
        f.write("QGC WPL 120\n")
        for idx, it in enumerate(items):
            lat = it["params"][4]
            lon = it["params"][5]
            alt = it["params"][6]
            #               idx  cur  frame cmd  param1-4  lat   lon   alt autocontinue
            f.write(f"{idx}\t0\t3\t16\t0\t0\t0\t0\t{lat}\t{lon}\t{alt}\t1\n")
    print(f"✓ wrote {len(items)} waypoints ➜ {dst}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: export_mavlink.py <mission.plan> <mission.txt>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
