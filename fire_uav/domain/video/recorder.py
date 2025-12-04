"""
Видео-рекордер (OpenCV) + JSON-логер детекций.

Recorder
    • start(frame_shape)  — создать/открыть MP4-файл
    • write(frame)        — добавить BGR-кадр (np.uint8 H×W×3)
    • stop()              — закрыть файл
    • is_recording()      — True/False
    • current_file()      — Path | None

DetectionRecorder
    • add(list[dict])     — накопить результаты
    • dump_to_file()      — сохранить одним JSON-массивом
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from numpy.typing import NDArray

# ───────────────────────────── Video ──────────────────────────────


class Recorder:
    def __init__(self, output_dir: str | Path = "outputs", fps: float = 20.0) -> None:
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._fps = fps

        self._writer: Optional[cv2.VideoWriter] = None
        self._file_path: Optional[Path] = None

    # -------------------------------------------------------------- #
    def start(self, frame_shape: tuple[int, ...]) -> None:
        if self._writer is not None:
            return  # уже пишем

        h, w = frame_shape[:2]
        self._file_path = (self._dir / f"record_{datetime.now():%Y%m%d_%H%M%S}.mp4").resolve()

        fourcc: int = int(cv2.VideoWriter_fourcc(*"mp4v"))
        self._writer = cv2.VideoWriter(str(self._file_path), fourcc, self._fps, (w, h))

    def write(self, frame: NDArray[np.uint8]) -> None:
        if self._writer is None:
            self.start(frame.shape)
        assert self._writer is not None  # для mypy
        self._writer.write(frame)

    def stop(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None
            self._file_path = None

    # -------------------------------------------------------------- #
    def is_recording(self) -> bool:
        return self._writer is not None

    def current_file(self) -> Optional[Path]:
        return self._file_path


# ───────────────────── JSON-логер детекций ────────────────────────


class DetectionRecorder:
    """Накопление детекций (dict) и дамп в один JSON-файл."""

    def __init__(self, json_path: str | Path) -> None:
        self._path = Path(json_path)
        self._buf: List[Dict[str, Any]] = []

    def add(self, detections: List[Dict[str, Any]]) -> None:
        self._buf.extend(detections)

    def dump_to_file(self) -> None:
        self._path.write_text(json.dumps(self._buf, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = ["Recorder", "DetectionRecorder"]
