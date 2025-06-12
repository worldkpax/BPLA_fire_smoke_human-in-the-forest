from PyQt5.QtCore import QThread, pyqtSignal
from fire_uav.flight.planner import FlightPlanner
from shapely.geometry import Polygon


class PlannerThread(QThread):
    mission_ready = pyqtSignal(object)   # list[list[Waypoint]]

    def __init__(self, aoi_poly: Polygon):
        super().__init__()
        self.poly = aoi_poly

    def run(self):
        missions = FlightPlanner(self.poly).generate()
        self.mission_ready.emit(missions)
