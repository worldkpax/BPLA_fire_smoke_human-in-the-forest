from __future__ import annotations

from pathlib import Path

from fire_uav.domain.video.camera import Camera


def test_open_close(tmp_path: Path) -> None:
    cam = Camera()
    cam.open()
    assert cam.is_open
    cam.close()
    assert not cam.is_open
