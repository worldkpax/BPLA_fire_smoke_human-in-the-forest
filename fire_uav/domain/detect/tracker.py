from __future__ import annotations

from typing import Dict, Final, TypeAlias

import numpy as np
from numpy.typing import NDArray

# ────────────────────────────────────────────────────────────────
# Типовые alias-ы
# ────────────────────────────────────────────────────────────────
BBox: TypeAlias = NDArray[np.float32]  # (x1, y1, x2, y2)
TrackId: TypeAlias = int
Track: TypeAlias = Dict[TrackId, BBox]


# ────────────────────────────────────────────────────────────────
# Класс трекера
# ────────────────────────────────────────────────────────────────
class Tracker:
    """
    Простейший трекер: каждой детекции (BBox) присваиваем уникальный ID.
    Нужен лишь для примера — при настоящем использовании замените SORT/DeepSORT.
    """

    _INIT_ID: Final[int] = 0

    def __init__(self) -> None:
        self._next_id: TrackId = self._INIT_ID

    def update(self, detections: list[BBox]) -> dict[TrackId, BBox]:
        """
        Считывает новый список detections и возвращает словарь track_id -> BBox.

        Parameters
        ----------
        detections : list[BBox]
            Список прямоугольников [x1, y1, x2, y2].

        Returns
        -------
        dict[TrackId, BBox]
            Словарь отображения ID треков на боксы.
        """
        tracks: dict[TrackId, BBox] = {}
        for det in detections:
            tracks[self._next_id] = det
            self._next_id += 1
        return tracks
