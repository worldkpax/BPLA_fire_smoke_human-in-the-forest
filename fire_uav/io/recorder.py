"""
Сохраняем кадры (jpg) + JSON-пакеты детекций.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import cv2

from ..core.schema import DetectionsBatch
from .serializer import dump_to_file

_log = logging.getLogger(__name__)


class Recorder:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        (self.root / "images").mkdir(parents=True, exist_ok=True)
        (self.root / "detections").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    def save_frame(self, frame, *, timestamp: datetime | None = None) -> Path:
        ts = (timestamp or datetime.utcnow()).isoformat(timespec="milliseconds").replace(":", "-")
        fname = self.root / "images" / f"{ts}.jpg"
        cv2.imwrite(str(fname), frame)
        _log.debug("Saved image %s", fname)
        return fname

    def save_detections(self, batch: DetectionsBatch, *, compress: bool = False) -> Path:
        ts = batch.frame.timestamp.isoformat(timespec="milliseconds").replace(":", "-")
        suffix = ".json.gz" if compress else ".json"
        fname = self.root / "detections" / f"{ts}{suffix}"
        dump_to_file(batch, fname)
        _log.debug("Saved detections %s", fname)
        return fname
