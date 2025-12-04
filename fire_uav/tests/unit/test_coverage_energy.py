from __future__ import annotations

import math

from shapely.geometry import LineString, Polygon

from fire_uav.domain.route.coverage import coverage_percent
from fire_uav.domain.route.energy import EnergyModel


def test_coverage_full() -> None:
    area = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    # горизонтальная линия через весь квадрат
    path = LineString([(-5, 5), (15, 5)])
    pct = coverage_percent(area, path, altitude_m=100.0)
    assert math.isclose(pct, 100.0, abs_tol=0.001)


def test_coverage_none_path() -> None:
    area = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    assert coverage_percent(area, None) == 0.0


def test_energy_model() -> None:
    m = EnergyModel(cruise_speed_mps=12.0, power_cruise_w=45.0, battery_wh=27.0)
    dist = 1_200.0  # м
    assert math.isclose(m.cruise_time_s(dist), 100.0)  # 1 200 / 12
    expect_wh = 100.0 / 3600.0 * 45.0
    assert math.isclose(m.energy_used_wh(dist), expect_wh, rel_tol=1e-6)
