# mypy: ignore-errors
from __future__ import annotations

import queue

import numpy as np

import fire_uav.services.components.detect as detect_mod
from fire_uav.services.components.base import State


class _DummyEngine:  # заменяем тяжёлый YOLO
    def __init__(self, *_, **__) -> None: ...

    def infer(self, frame, *, camera_id="cam0", return_batch=True):
        return {"ok": True, "shape": frame.shape}


def test_detect_thread(monkeypatch) -> None:
    """Поток берёт кадр из очереди и кладёт результат в выходную."""
    monkeypatch.setattr(detect_mod, "DetectionEngine", _DummyEngine)

    in_q: queue.Queue[np.ndarray | None] = queue.Queue()
    out_q: queue.Queue[dict] = queue.Queue()

    thr = detect_mod.DetectThread(in_q=in_q, out_q=out_q)
    thr.start()

    in_q.put(np.zeros((2, 2, 3), dtype=np.uint8))

    res = out_q.get(timeout=1.0)
    assert res["ok"] is True
    assert res["shape"] == (2, 2, 3)

    thr.stop()
    thr.join(timeout=1.0)
    assert thr.state is State.STOPPED
