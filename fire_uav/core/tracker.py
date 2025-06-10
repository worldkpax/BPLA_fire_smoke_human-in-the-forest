"""
Плагин-точка для трекеров (SORT / ByteTrack).
Сейчас это «заглушка», чтобы не тащить лишние зависимости.
"""
from typing import List

import numpy as np

from .schema import Detection


class BaseTracker:
    def update(self, detections: List[Detection], frame: np.ndarray) -> List[Detection]:
        raise NotImplementedError("Implement in subclass")
