"""
YOLOv8 обёртка ➜ Detection objects.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import numpy as np

from .camera import CameraParams
from .schema import Detection, FrameMeta, DetectionsBatch

_log = logging.getLogger(__name__)


class DetectionEngine:
    def __init__(
        self,
        model_path: str | Path,
        *,
        conf_threshold: float = 0.4,
        iou_threshold: float = 0.5,
        device: str | None = None,
    ) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as err:  # pragma: no cover
            raise RuntimeError("Install `ultralytics` to use DetectionEngine") from err

        self._yolo = YOLO(str(model_path))
        self._yolo.overrides["conf"] = conf_threshold
        self._yolo.overrides["iou"] = iou_threshold
        if device:
            self._yolo.to(device)
        _log.info("YOLO model %s loaded", model_path)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def infer(
        self,
        frame_bgr: np.ndarray,
        *,
        camera_id: str = "cam0",
        cam_params: CameraParams | None = None,
        return_batch: bool = False,
    ) -> List[Detection] | DetectionsBatch:
        """Run detector → Detection list **или** DetectionsBatch."""
        h, w = frame_bgr.shape[:2]
        res = self._yolo(frame_bgr, verbose=False)

        detections: list[Detection] = []
        for r in res:  # YOLO может вернуть батч, но у нас 1 кадр
            for cls, conf, xyxy in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxy):
                x1, y1, x2, y2 = map(int, xyxy)
                detections.append(
                    Detection(
                        camera_id=camera_id,
                        class_id=int(cls),
                        confidence=float(conf),
                        bbox=(x1, y1, x2, y2),
                    )
                )

        _log.debug("Frame %s -> %d dets", camera_id, len(detections))

        if return_batch:
            batch = DetectionsBatch(
                frame=FrameMeta(camera_id=camera_id, width=w, height=h),
                detections=detections,
            )
            return batch
        return detections
