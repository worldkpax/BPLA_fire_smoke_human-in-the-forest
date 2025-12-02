from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Sequence, Tuple

from pydantic import BaseModel, Field

from fire_uav.config import settings
from fire_uav.core.schema import GeoDetection, TelemetrySample
from fire_uav.domain.fusion import GeoProjector
from fire_uav.domain.video.camera import CameraParams
from fire_uav.services.detections.aggregator import DetectionAggregator, DetectionEvent
from fire_uav.services.telemetry.transmitter import Transmitter

logger = logging.getLogger(__name__)


class RawDetectionPayload(BaseModel):
    class_id: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: Tuple[int, int, int, int]
    frame_id: str
    timestamp: datetime


class DetectionBatchPayload(BaseModel):
    frame_id: str
    frame_width: int = Field(..., gt=0)
    frame_height: int = Field(..., gt=0)
    captured_at: datetime
    telemetry: TelemetrySample
    detections: List[RawDetectionPayload]


class DetectionPipeline:
    """
    Связывает сырые детекции модели с телеметрией, выполняет агрегацию
    и отправляет подтверждённые цели на наземную станцию.
    """

    def __init__(
        self,
        *,
        aggregator: DetectionAggregator | None = None,
        projector: GeoProjector | None = None,
        transmitter: Transmitter | None = None,
        camera_params: CameraParams | None = None,
    ) -> None:
        self.aggregator = aggregator or DetectionAggregator(
            window=settings.agg_window,
            votes_required=settings.agg_votes_required,
            min_confidence=settings.agg_min_confidence,
            max_distance_m=settings.agg_max_distance_m,
            ttl_seconds=settings.agg_ttl_seconds,
        )
        self.projector = projector or GeoProjector(camera_params)
        self.transmitter = transmitter

    def process_batch(self, payload: DetectionBatchPayload) -> List[GeoDetection]:
        if not payload.detections:
            return []

        events: List[DetectionEvent] = []
        for det in payload.detections:
            coord = self.projector.project(
                det.bbox,
                (payload.frame_width, payload.frame_height),
                payload.telemetry,
            )
            events.append(
                DetectionEvent(
                    class_id=det.class_id,
                    confidence=det.confidence,
                    location=coord,
                    frame_id=det.frame_id or payload.frame_id,
                    timestamp=det.timestamp or payload.captured_at,
                )
            )

        aggregated = self.aggregator.add_many(events)
        self._transmit(aggregated)
        return aggregated

    # ------------------------------------------------------------------ #
    def _transmit(self, detections: Sequence[GeoDetection]) -> None:
        if not self.transmitter or not detections:
            return
        for det in detections:
            payload = {
                "class_id": det.class_id,
                "confidence": det.confidence,
                "lat": det.location.lat,
                "lon": det.location.lon,
                "timestamp": det.captured_at.isoformat(),
                "frame": det.source_frame,
            }
            try:
                self.transmitter.send(payload)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to transmit detection")
