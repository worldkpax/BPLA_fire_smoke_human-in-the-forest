from __future__ import annotations

from typing import List, cast

from fire_uav.domain.route.converter import to_qgc
from fire_uav.domain.route.planner import Waypoint


class DummyWP:
    """Минимальная «заглушка» Waypoint для unit-теста."""

    def __init__(self, lat: float, lon: float, alt: float) -> None:
        self.lat = lat
        self.lon = lon
        self.alt = alt


def test_to_qgc_basic() -> None:
    mission = cast(List[List[Waypoint]], [[DummyWP(55.0, 37.0, 120)]])
    plan_dict = to_qgc(mission)
    item = plan_dict["mission"]["items"][0]

    assert plan_dict["fileType"] == "Plan"
    assert item["Params"][-1] == 120
