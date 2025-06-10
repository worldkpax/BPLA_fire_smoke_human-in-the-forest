"""
Простейший PyQt5 GUI: показывает камеру + bbox-ы.
Фокус проекта не GUI, но есть рабочий пример.
"""
from __future__ import annotations
import sys
from pathlib import Path

import cv2
import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow

from ...core.detection import DetectionEngine
from ...utils.logging import setup_logging


class MainWindow(QMainWindow):
    def __init__(self, model_path: str):
        super().__init__()
        self.setWindowTitle("fire_uav – demo")
        self.label = QLabel(self)
        self.setCentralWidget(self.label)

        self.engine = DetectionEngine(model_path)
        self.cap = cv2.VideoCapture(0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)

    # -------------------------------------------------------------- #
    def tick(self):
        ok, frame = self.cap.read()
        if not ok:
            return
        dets = self.engine.infer(frame)
        for d in dets:
            x1, y1, x2, y2 = d.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        img = QImage(rgb.data, w, h, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(img))


def main():
    setup_logging()
    app = QApplication(sys.argv)
    wnd = MainWindow("best_yolo11.pt")
    wnd.resize(960, 720)
    wnd.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
