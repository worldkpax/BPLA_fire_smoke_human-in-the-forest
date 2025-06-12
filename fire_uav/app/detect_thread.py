from PyQt5.QtCore import QThread, pyqtSignal
from fire_uav.core.detection import DetectionEngine
import numpy as np


class DetectThread(QThread):
    detections = pyqtSignal(list)      # list[Detection]

    def __init__(self, model_path: str, conf: float):
        super().__init__()
        self.engine = DetectionEngine(model_path, conf_threshold=conf)
        self._queue: "queue.Queue[np.ndarray]" = None  # set externally
        self._running = True

    def run(self):
        while self._running:
            frame = self._queue.get()
            dets = self.engine.infer(frame)
            self.detections.emit(dets)

    def stop(self):
        self._running = False
