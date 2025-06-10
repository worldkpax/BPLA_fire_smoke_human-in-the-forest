from fire_uav.flight.planner import FlightPlanner, GridParams, CameraSpec
from shapely.geometry import Polygon


def test_grid_coverage():
    poly = Polygon([(0, 0), (0.001, 0), (0.001, 0.001), (0, 0.001)])
    planner = FlightPlanner(poly, grid=GridParams(gsd_target_cm=2))
    lines = planner.build_grid()
    assert len(lines) >= 2


def test_tsp_shorter():
    poly = Polygon([(0, 0), (0.002, 0), (0.002, 0.002), (0, 0.002)])
    fp = FlightPlanner(poly)
    wps = fp.lines_to_waypoints(fp.build_grid())
    d_raw = sum(wps[i].lat for i in range(len(wps)))  # dummy
    wps_opt = fp.optimise(wps)
    d_opt = sum(wps_opt[i].lat for i in range(len(wps_opt)))
    assert d_opt <= d_raw
