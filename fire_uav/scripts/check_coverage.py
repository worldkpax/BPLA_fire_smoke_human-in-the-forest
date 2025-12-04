# mypy: ignore-errors
#!/usr/bin/env python3
"""CLI-утилита: печатает KPI покрытия маршрута."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

# type: ignore[attr-defined]
from fire_uav.domain.route.converter import waypoints_from_plan
from fire_uav.domain.route.coverage import coverage_percent
from fire_uav.domain.route.planner import Waypoint


def _load(plan: Path) -> List[Waypoint]:
    # helper не типизирован → добавляем ignore
    return waypoints_from_plan(plan)  # type: ignore[no-any-return]


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: check_coverage.py <mission.plan>")
        sys.exit(1)

    waypoints = _load(Path(argv[0]))
    print(f"Coverage: {coverage_percent(waypoints):.1f}%")  # noqa: T201


if __name__ == "__main__":
    main()
