# mypy: ignore-errors
#!/usr/bin/env python3
"""Печатает профиль высот маршрута из `mission.plan`."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from fire_uav.domain.route.converter import waypoints_from_plan
from fire_uav.domain.route.elevation import profile
from fire_uav.domain.route.planner import Waypoint


def _load(plan: Path) -> List[Waypoint]:
    return waypoints_from_plan(plan)  # type: ignore[no-any-return]


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: profile_elevation.py <mission.plan>")
        sys.exit(1)

    elev = profile(_load(Path(argv[0])))
    for idx, h in enumerate(elev, 1):
        print(f"{idx:03d}: {h:.1f} m")  # noqa: T201


if __name__ == "__main__":
    main()
