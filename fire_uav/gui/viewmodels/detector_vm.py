"""
DetectorVM �?" �?�>�?�� ViewModel �?�>�? �?��'���'�?�?�.

�?� �?�?�+�>���?��' �?�?�+�<�'��? APP_START / APP_STOP / CONF_CHANGE �ؐ�?��� EventBus
�?� �?�?��?��?����' �����ؐ�� �?��'���Ő��, ���?�?�+�?���?�<�?����' ��: �? GUI:
    �"? ���?�>�?�<�� batch   ��' �?��?�?���> detection
    �"? �?����?�?�� bbox'�?�? ��' �?��?�?���> bboxes  (�?�>�? VideoPane)
"""

from __future__ import annotations

import logging
from typing import Any, Final, List, Tuple

from PySide6.QtCore import QObject, Signal

from fire_uav.config import settings
from fire_uav.services.bus import Event, bus

_log: Final = logging.getLogger(__name__)

# x1, y1, x2, y2
BBox = Tuple[int, int, int, int]


class DetectorVM(QObject):
    # -------- ���?�+�>��ؐ?�<�� �?��?�?���>�< �?�>�? GUI -------- #
    detection = Signal(object)  # �?��?�? batch
    bboxes = Signal(list)  # List[BBox]

    def __init__(self) -> None:
        super().__init__()
        self._conf = getattr(settings, "yolo_conf", 0.25)
        # mypy ����>�?��'�?�? �?�� �?��?�?�?�����?��?��� �'����� ��?�>�+�?��� �?" ���?�?���?�>�?��?
        bus.subscribe(Event.DETECTION, self._on_detection)  # type: ignore[arg-type]
        _log.info("DetectorVM subscribed to Event.DETECTION")

    def start(self) -> None:
        """�-�����?�?�'��'�? �?��'���'�?�? (���?�?��>�?�ؐ�'�? EventBus, �� �'.��.)."""
        bus.emit(Event.APP_START)
        _log.debug("APP_START emitted")

    def stop(self) -> None:
        """�?�?�'���?�?�?��'�? �?��'���'�?�?."""
        bus.emit(Event.APP_STOP)
        _log.debug("APP_STOP emitted")

    def set_conf(self, value: float) -> None:
        """Update detection confidence threshold (broadcast via EventBus)."""
        self._conf = value
        bus.emit(Event.CONF_CHANGE, value)
        _log.debug("CONF_CHANGE emitted -> %.2f", value)

    def _on_detection(self, batch: Any) -> None:
        """�?�?��?�'�> batch ��' ���?�?�+�?���?�<�?����? �?��?�?���>�< �?���?��?�:."""
        self.detection.emit(batch)

        # ����?�>������? bbox'�< ��� batch.detections
        bxs: List[BBox] = []
        for d in getattr(batch, "detections", []):
            if hasattr(d, "bbox") and isinstance(getattr(d, "bbox"), tuple):
                x1, y1, x2, y2 = getattr(d, "bbox")
                bxs.append((int(x1), int(y1), int(x2), int(y2)))
            elif all(hasattr(d, k) for k in ("x1", "y1", "x2", "y2")):
                bxs.append((int(d.x1), int(d.y1), int(d.x2), int(d.y2)))

        self.bboxes.emit(bxs)
