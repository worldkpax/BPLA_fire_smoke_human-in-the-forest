# mypy: ignore-errors
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class VideoPane(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("videoPane")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        QVBoxLayout(self).addWidget(self._label)

        self._last_frame: NDArray[np.uint8] | None = None
        self._bboxes: list[tuple[int, int, int, int]] = []

    # ---------- slots from threads / VM ---------- #
    def set_frame(self, frame: NDArray[np.uint8]) -> None:
        self._last_frame = frame
        self._render()

    def set_bboxes(self, bxs: list[tuple[int, int, int, int]]) -> None:
        self._bboxes = bxs
        self._render()

    # ---------- internal ---------- #
    def _render(self) -> None:
        if self._last_frame is None:
            return
        h, w, _ = self._last_frame.shape
        img = QImage(self._last_frame.data, w, h, 3 * w, QImage.Format.Format_BGR888)

        pix = QPixmap.fromImage(img)
        if self._bboxes:
            painter = QPainter(pix)
            pen = QPen(Qt.GlobalColor.red, 2)
            painter.setPen(pen)
            for x1, y1, x2, y2 in self._bboxes:
                painter.drawRect(x1, y1, x2 - x1, y2 - y1)
            painter.end()

        self._label.setPixmap(
            pix.scaled(
                self._label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
