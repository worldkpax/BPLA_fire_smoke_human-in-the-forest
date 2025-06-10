"""
fire_uav.ui.qt.app – тёмный GUI-демо (Windows friendly) с:
    • выбором модели   • слайдером confidence
    • асинхронной камерой (без фризов)   • лог-панелью
    • индикатором FPS

Запуск:
    python -m fire_uav gui
или
    python -m fire_uav.ui.qt.app
"""
from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import List

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPalette, QPixmap, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from fire_uav.core.detection import DetectionEngine
from fire_uav.utils.gui_logger import QtLogHandler
from fire_uav.utils.logging import setup_logging


# ────────────────────────────────────────────────────────────────────
def _dark_palette() -> QPalette:
    """Палитра а-ля VS Code Dark+."""
    pal = QPalette()
    pal.setColor(QPalette.Window,           Qt.black)
    pal.setColor(QPalette.WindowText,       Qt.white)
    pal.setColor(QPalette.Base,             Qt.black)
    pal.setColor(QPalette.AlternateBase,    QColor(30, 30, 30))
    pal.setColor(QPalette.ToolTipBase,      Qt.white)
    pal.setColor(QPalette.ToolTipText,      Qt.white)
    pal.setColor(QPalette.Text,             Qt.white)
    pal.setColor(QPalette.Button,           QColor(45, 45, 45))
    pal.setColor(QPalette.ButtonText,       Qt.white)
    pal.setColor(QPalette.BrightText,       Qt.red)
    pal.setColor(QPalette.Highlight,        QColor(42, 130, 218))
    pal.setColor(QPalette.HighlightedText,  Qt.black)
    return pal


class VideoWidget(QLabel):
    """QLabel, умеющий принимать numpy(BGR)-кадр."""

    def set_frame(self, frame_bgr: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qimg))


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("fire_uav – detector")

        # ─── виджеты ────────────────────────────────────────────────
        self.video = VideoWidget()
        self.btn_load = QPushButton("Load model…")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(5, 95)  # 0.05–0.95
        self.slider.setValue(40)
        self.lbl_conf = QLabel("Conf: 0.40")
        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.lbl_fps = QLabel("FPS: —")
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)

        # ─── layout ────────────────────────────────────────────────
        ctrl = QVBoxLayout()
        ctrl.addWidget(self.btn_load)
        ctrl.addWidget(self.lbl_conf)
        ctrl.addWidget(self.slider)
        ctrl.addWidget(self.btn_start)
        ctrl.addWidget(self.btn_stop)
        ctrl.addStretch(1)
        ctrl.addWidget(self.lbl_fps)
        ctrl.addWidget(self.log_box, 1)      # лог-панель растягивается

        root = QHBoxLayout(self)
        root.addWidget(self.video, 1)
        root.addLayout(ctrl)

        # ─── Engine + камера ───────────────────────────────────────
        self.model_path = Path("best_yolo11.pt")
        self.engine = DetectionEngine(self.model_path)
        self.cap: cv2.VideoCapture | None = None

        # очередь кадров и поток-граббер
        self._q: queue.Queue[np.ndarray] = queue.Queue(maxsize=1)
        self._grab_thr: threading.Thread | None = None

        # таймер UI-трика
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        self._last_time = time.time()

        # ─── сигналы ───────────────────────────────────────────────
        self.btn_load.clicked.connect(self._select_model)
        self.slider.valueChanged.connect(self._on_slider)
        self.btn_start.clicked.connect(self.start_camera)
        self.btn_stop.clicked.connect(self.stop_camera)

        # ─── перенаправляем логи в QTextEdit ───────────────────────
        import logging
        logging.getLogger().addHandler(QtLogHandler(self.log_box))

    # ================================================================= #
    # slots
    # ================================================================= #
    def _select_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose YOLO model", ".", "PyTorch (*.pt)"
        )
        if path:
            self.model_path = Path(path)
            self.engine = DetectionEngine(self.model_path)  # reload
            self.start_camera()

    def _on_slider(self, value: int):
        conf = value / 100.0
        self.lbl_conf.setText(f"Conf: {conf:.2f}")
        self.engine._yolo.overrides["conf"] = conf

    # ----------------------------------------------------------------- #
    # Camera
    # ----------------------------------------------------------------- #
    def start_camera(self):
        if self._grab_thr is None or not self._grab_thr.is_alive():
            self.cap = cv2.VideoCapture(0)
            self._grab_thr = threading.Thread(target=self._grab_loop, daemon=True)
            self._grab_thr.start()
        if not self.timer.isActive():
            self.timer.start(33)  # ~30 FPS

    def stop_camera(self):
        self.timer.stop()

    def _grab_loop(self):
        """Отдельный поток захвата кадров (не блокирует UI)."""
        assert self.cap is not None
        while True:
            ok, frame = self.cap.read()
            if not ok:
                continue
            if not self._q.full():
                self._q.put(frame)

    # ----------------------------------------------------------------- #
    # main tick (UI-thread)
    # ----------------------------------------------------------------- #
    def _tick(self):
        if self._q.empty():
            return
        frame = self._q.get()

        dets = self.engine.infer(frame)
        self._draw_dets(frame, dets)
        self.video.set_frame(frame)

        # FPS
        now = time.time()
        fps = 1.0 / (now - self._last_time)
        self._last_time = now
        self.lbl_fps.setText(f"FPS: {fps:5.1f}")

    # ----------------------------------------------------------------- #
    @staticmethod
    def _draw_dets(frame: np.ndarray, dets: List) -> None:
        for d in dets:
            x1, y1, x2, y2 = d.bbox
            label = f"{d.class_id}:{d.confidence:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (x1, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )


# ────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> None:  # argv игнорируем
    setup_logging()
    app = QApplication([])
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())
    wnd = MainWindow()
    wnd.resize(1280, 720)
    wnd.show()
    app.exec_()


if __name__ == "__main__":
    main()
