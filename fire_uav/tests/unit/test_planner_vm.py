# mypy: ignore-errors
import json

import pytest

from fire_uav.gui.viewmodels.planner_vm import PlannerVM


@pytest.fixture(autouse=True)
def clear_deps(monkeypatch):
    # Сбросим хранилище перед каждым тестом
    import fire_uav.infrastructure.providers as deps

    deps.plan_data = None
    yield


def test_generate_path_empty_raises():
    vm = PlannerVM()
    with pytest.raises(RuntimeError, match="Draw polyline first"):
        vm.generate_path()


def test_save_and_get_plan_roundtrip(tmp_path):
    vm = PlannerVM()
    pts = [(55.0, 37.0), (55.1, 37.1)]
    vm.save_plan(pts)
    assert vm.get_path() == pts


def test_export_qgc_plan(tmp_path):
    vm = PlannerVM()
    pts = [(10.0, 20.0), (11.0, 21.0)]
    vm.save_plan(pts)
    # принудительно укажем alt=50
    fn = vm.export_qgc_plan(alt_m=50.0)
    assert fn.exists()
    data = json.loads(fn.read_text())
    # базовые поля
    assert data["fileType"] == "Plan"
    items = data["mission"]["items"]
    assert len(items) == 2
    # проверим Params
    for idx, it in enumerate(items):
        assert it["DoJumpId"] == idx
        assert it["Params"] == [0, 0, 0, 0, pts[idx][0], pts[idx][1], 50.0]
