# mypy: ignore-errors
"""
CameraThread с метрикой FPS: каждые 5 с пишет INFO «Camera FPS: xx»,
и при каждом кадре инкрементирует Prometheus-Gauge.
"""

from __future__ import annotations

import logging
import time
from typing import Final

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from fire_uav.services.components.base import ManagedComponent, State
from fire_uav.services.metrics import fps_gauge

LOG: Final = logging.getLogger("camera")


class _CameraQtThread(QThread):
    frame: Signal = Signal(np.ndarray)
    error: Signal = Signal(str)

    _LOG_EVERY: Final[float] = 5.0  # сек

    def __init__(self, src: int | str, fps: int, out_q=None) -> None:
        super().__init__()
        self._src, self._fps, self._q = src, fps, out_q
        self._sleep = 1 / fps if fps else 0
        self._running = True

        # статистика локального лога
        self._stat_ts = time.perf_counter()
        self._stat_frames = 0

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        cap = cv2.VideoCapture(self._src)
        if not cap.isOpened():
            self.error.emit("Camera not opened")
            return

        while self._running:
            ok, frame = cap.read()
            if not ok:
                self.error.emit("Failed to read frame")
                break

            # отдадим кадр UI и в очередь
            self.frame.emit(frame)
            if self._q is not None:
                try:
                    self._q.put_nowait(frame)
                except Exception:
                    pass

            # ---- Prometheus метрика ----
            fps_gauge.inc()

            # ---- локальная статистика каждые 5 с ----
            self._stat_frames += 1
            now = time.perf_counter()
            if now - self._stat_ts >= self._LOG_EVERY:
                fps = self._stat_frames / (now - self._stat_ts)
                LOG.info("Camera FPS: %.1f", fps)
                self._stat_ts, self._stat_frames = now, 0

            if self._sleep:
                time.sleep(self._sleep)

        cap.release()


class CameraThread(ManagedComponent):
    """Managed-компонент для интеграции в LifecycleManager."""

    def __init__(self, index: int | str = 0, fps: int = 30, out_queue=None) -> None:
        super().__init__(name="CameraThread")
        self.index = index
        self.fps = fps
        self._qt = _CameraQtThread(index, fps, out_queue)

        # прокидываем Qt-сигналы наружу
        self.frame = self._qt.frame
        self.error = self._qt.error

    def loop(self) -> None:
        self._qt.start()
        self._qt.wait()

    def stop(self) -> None:
        self._qt.stop()
        self._qt.wait()
        self.state = State.STOPPED
