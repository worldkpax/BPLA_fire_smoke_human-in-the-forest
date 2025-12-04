from __future__ import annotations

import queue
from typing import Any

from fire_uav.services.components.detect import DetectThread


class Container:
    """
    Мини-IOC: создаёт очереди и компоненты, запускает детектор.
    """

    def __init__(self) -> None:
        self.frames_q: queue.Queue[Any] = queue.Queue()
        self.dets_q: queue.Queue[Any] = queue.Queue()
        self.detector = DetectThread(self.frames_q, self.dets_q)

    # ------------------------------------------------------------------ #
    def start(self) -> None:
        self.detector.start()
