import json
import sys
from pathlib import Path
from typing import Any


def main(src: str | Path, dst: str | Path) -> None:
    items: list[dict[str, Any]] = json.load(open(src, encoding="utf-8"))["mission"]["items"]
    with open(dst, "w", encoding="utf-8") as f:
        f.write("QGC WPL 120\n")
        for idx, it in enumerate(items):
            lat = it["params"][4]
            lon = it["params"][5]
            alt = it["params"][6]
            # idx  cur  frame cmd  param1-4  lat   lon   alt autocontinue
            f.write(f"{idx}\t0\t3\t16\t0\t0\t0\t0\t{lat}\t{lon}\t{alt}\t1\n")
    print(f"✓ wrote {len(items)} waypoints ➜ {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: export_mavlink.py <mission.plan> <mission.txt>")
        sys.exit(1)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
