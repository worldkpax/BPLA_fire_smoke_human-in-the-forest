# mypy: ignore-errors
# fire_uav/services/components/detect.py

from __future__ import annotations

import logging
import queue
import time
from typing import Final

import numpy as np
from numpy.typing import NDArray

import fire_uav.infrastructure.providers as deps
from fire_uav.config.settings import settings
from fire_uav.core.schema import DetectionsBatch
from fire_uav.domain.detect.detection import DetectionEngine
from fire_uav.services.bus import Event, bus
from fire_uav.services.components.base import ManagedComponent, State
from fire_uav.services.metrics import detect_latency, queue_size

LOG: Final = logging.getLogger("detect")

Frame = NDArray[np.uint8]
_SLEEP = 0.05
_STAT_EVERY = 1.0  # сек


class DetectThread(ManagedComponent):
    """YOLO-детектор + метрики latency и queue-size."""

    def __init__(
        self,
        in_q: queue.Queue[Frame | None],
        out_q: queue.Queue[DetectionsBatch],
    ) -> None:
        super().__init__(name="DetectThread")
        self._in_q = in_q
        self._out_q = out_q
        self._engine = DetectionEngine(
            wanted_classes=settings.yolo_classes,
            conf_threshold=settings.yolo_conf,
            iou_threshold=settings.yolo_iou,
        )
        self._stat_ts = time.perf_counter()

    def loop(self) -> None:
        LOG.info("Detector thread started")
        while self.state is State.RUNNING:
            try:
                frame = self._in_q.get(timeout=_SLEEP)
            except queue.Empty:
                frame = None

            if frame is None:
                continue

            # обновляем current queue size
            queue_size.set(self._in_q.qsize())

            # измеряем latency
            with detect_latency.time():
                # сначала пробуем detect(), если нет — infer()
                if hasattr(self._engine, "detect"):
                    batch = self._engine.detect(frame)
                else:
                    batch = self._engine.infer(
                        frame
                    )  # тестовый DummyEngine наверняка имеет infer()

            deps.last_detection = batch

            try:
                self._out_q.put_nowait(batch)
            except queue.Full:
                LOG.debug("Output queue full — dropping detection")

            bus.emit(Event.DETECTION, batch)

            # локальная отладка очередей раз в секунду
            now = time.perf_counter()
            if now - self._stat_ts >= _STAT_EVERY:
                LOG.debug("Queues: frames=%d  dets=%d", self._in_q.qsize(), self._out_q.qsize())
                self._stat_ts = now

        LOG.info("Detector thread stopped")

    def stop(self) -> None:
        self.state = State.STOPPED
        # чтобы перебить .get() выше и выйти из цикла
        try:
            self._in_q.put_nowait(None)
        except Exception:
            pass
