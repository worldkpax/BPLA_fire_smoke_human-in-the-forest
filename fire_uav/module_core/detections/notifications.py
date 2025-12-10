from __future__ import annotations

import json
from pathlib import Path

from fire_uav.module_core.detections.registry import TrackedObjectState


class JsonNotificationWriter:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def write_notification(self, obj: TrackedObjectState) -> Path:
        out_dir = self.base_dir / obj.first_seen.strftime("%Y-%m-%d")
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "object_id": obj.object_id,
            "track_id": obj.track_id,
            "class_id": obj.class_id,
            "confidence": obj.confidence,
            "first_seen": obj.first_seen.isoformat(),
            "last_seen": obj.last_seen.isoformat(),
            "lat": obj.lat,
            "lon": obj.lon,
            "alt": obj.alt,
            "frames": obj.frames,
            "uav_id": obj.uav_id,
        }
        out_path = out_dir / f"{obj.object_id}.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return out_path


__all__ = ["JsonNotificationWriter"]
