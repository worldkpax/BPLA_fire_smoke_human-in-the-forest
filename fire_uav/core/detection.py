"""
YOLOv8 wrapper  ·  + class-filter  ·  + auto-GPU  ·  + runtime conf update
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Sequence

import numpy as np
import torch
from fire_uav.config.settings import settings  # ← новая pydantic-конфигурация

from .camera import CameraParams
from .schema import Detection, FrameMeta, DetectionsBatch

_log = logging.getLogger(__name__)


class DetectionEngine:
    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        wanted_classes: Sequence[int] | None = None,
        conf_threshold: float | None = None,
        iou_threshold: float | None = None,
        device: str | None = None,
    ) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as err:
            raise RuntimeError("Install `ultralytics` to use DetectionEngine") from err

        model_path = model_path or settings.yolo_model
        conf_threshold = conf_threshold or settings.yolo_conf
        iou_threshold = iou_threshold or settings.yolo_iou

        # auto-gpu
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self._yolo = YOLO(str(model_path))
        self._yolo.overrides |= {
            "conf": conf_threshold,
            "iou": iou_threshold,
            "device": device,
        }
        self._wanted = set(wanted_classes or settings.yolo_classes)

        _log.info(
            "YOLO %s loaded (device=%s, conf=%.2f, classes=%s)",
            model_path,
            device,
            conf_threshold,
            sorted(self._wanted) if self._wanted else "ALL",
        )

    # ────────────────────────────────────────────────────────────────── #
    def infer(
        self,
        frame_bgr: np.ndarray,
        *,
        camera_id: str = "cam0",
        cam_params: CameraParams | None = None,
        return_batch: bool = False,
    ) -> List[Detection] | DetectionsBatch:
        h, w = frame_bgr.shape[:2]
        results = self._yolo(frame_bgr, verbose=False)

        detections: list[Detection] = []
        for r in results:
            for cls, conf, xyxy in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxy):
                if self._wanted and int(cls) not in self._wanted:
                    continue
                x1, y1, x2, y2 = map(int, xyxy)
                detections.append(
                    Detection(
                        camera_id=camera_id,
                        class_id=int(cls),
                        confidence=float(conf),
                        bbox=(x1, y1, x2, y2),
                    )
                )

        if return_batch:
            return DetectionsBatch(
                frame=FrameMeta(camera_id=camera_id, width=w, height=h),
                detections=detections,
            )
        return detections
