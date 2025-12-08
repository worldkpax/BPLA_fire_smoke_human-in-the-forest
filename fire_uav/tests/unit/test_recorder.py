# mypy: ignore-errors
from __future__ import annotations

from pathlib import Path

import numpy as np

import fire_uav.domain.video.recorder as rec_mod


class _DummyWriter:
    """Мини-заглушка вместо cv2.VideoWriter: ничего не пишет на диск."""

    def __init__(self, filename: str, fourcc: int, fps: float, size) -> None:
        self.filename = filename
        self.fourcc = fourcc
        self.fps = fps
        self.size = size
        self.released = False
        self.frames: list[np.ndarray] = []

    def write(self, frame: np.ndarray) -> None:
        self.frames.append(frame)

    def release(self) -> None:
        self.released = True


def test_recorder_write_stop(monkeypatch, tmp_path: Path) -> None:
    """Recorder стартует на первом кадре, пишет, корректно стопится."""
    # патчим cv2.*
    monkeypatch.setattr(rec_mod.cv2, "VideoWriter", _DummyWriter)
    monkeypatch.setattr(rec_mod.cv2, "VideoWriter_fourcc", lambda *args: 0)

    rec = rec_mod.Recorder(output_dir=tmp_path)
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    assert not rec.is_recording()

    rec.write(frame)  # автозапуск
    assert rec.is_recording()
    assert isinstance(rec._writer, _DummyWriter)  # type: ignore[attr-defined]

    rec.stop()
    assert not rec.is_recording()
    assert rec._writer is None
    assert rec.current_file() is None
