# mypy: ignore-errors
from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QLabel, QWidget

_log = logging.getLogger(__name__)


def toast(parent: QWidget, text: str, timeout: int = 3000) -> None:
    """Неблокирующее всплывающее сообщение-подсказка."""
    lab = QLabel(text, parent)
    lab.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    lab.adjustSize()
    lab.move(
        (parent.width() - lab.width()) // 2,
        parent.height() - lab.height() - 20,
    )
    lab.setWindowOpacity(0)
    lab.show()

    fade_in = QPropertyAnimation(lab, b"windowOpacity", parent)
    fade_in.setDuration(400)
    fade_in.setStartValue(0)
    fade_in.setEndValue(1)
    fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade_in.start()

    def _fade_out() -> None:
        fade = QPropertyAnimation(lab, b"windowOpacity", parent)
        fade.setDuration(400)
        fade.setStartValue(1)
        fade.setEndValue(0)
        fade.finished.connect(lab.deleteLater)
        fade.start()

    QTimer.singleShot(timeout, _fade_out)


# ─────────────── экспорт ─────────────── #
show_toast: Callable[[QWidget, str, int], None] = toast

__all__ = ["toast", "show_toast"]
