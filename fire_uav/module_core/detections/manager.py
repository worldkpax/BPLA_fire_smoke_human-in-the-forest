from __future__ import annotations

import logging

from fire_uav.module_core.detections.notifications import JsonNotificationWriter
from fire_uav.module_core.detections.registry import ObjectRegistry
from fire_uav.module_core.schema import GeoDetection
from fire_uav.services.bus import Event, bus


class ObjectNotificationManager:
    def __init__(
        self,
        registry: ObjectRegistry,
        writer: JsonNotificationWriter,
        logger: logging.Logger,
        uav_id: str | None,
    ) -> None:
        self.registry = registry
        self.writer = writer
        self.log = logger
        self.uav_id = uav_id

    def handle_confirmed_detection(self, detection: GeoDetection) -> None:
        state = self.registry.create_or_update(
            detection,
            uav_id=self.uav_id,
            track_id=detection.track_id,
        )
        if not state.notified:
            self.writer.write_notification(state)
            self.log.info(
                "Confirmed object %s (class %d, track %s, conf %.2f) at lat=%.6f, lon=%.6f",
                state.object_id,
                state.class_id,
                state.track_id,
                state.confidence,
                state.lat,
                state.lon,
            )
            state.notified = True
            bus.emit(
                Event.OBJECT_CONFIRMED_UI,
                {
                    "object_id": state.object_id,
                    "class_id": state.class_id,
                    "confidence": state.confidence,
                    "lat": state.lat,
                    "lon": state.lon,
                    "track_id": state.track_id,
                    "timestamp": state.last_seen,
                },
            )
        else:
            self.log.debug(
                "Updated object %s (track=%s) last_seen=%s",
                state.object_id,
                state.track_id,
                state.last_seen.isoformat(),
            )


__all__ = ["ObjectNotificationManager"]
