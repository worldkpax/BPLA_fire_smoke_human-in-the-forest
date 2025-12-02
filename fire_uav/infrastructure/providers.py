from __future__ import annotations

from queue import Queue
from typing import TYPE_CHECKING, Any, Callable, Optional

from fire_uav.services.lifecycle.manager import LifecycleManager

if TYPE_CHECKING:  # imports only for type checking to avoid circular deps
    from fire_uav.services.components.camera import CameraThread
    from fire_uav.services.components.detect import DetectThread

# ────────── очереди ────────── #
frame_queue: Optional[Queue] = None  # кадры camera → detector
dets_queue: Optional[Queue] = None  # детекции detector → GUI/API

# ────────── фабрики компонентов ────────── #
camera_factory: Callable[[], "CameraThread"] | None = None
detect_factory: Callable[[], "DetectThread"] | None = None
plan_widget_factory: Callable[..., object] | None = None

# ────────── lifecycle ────────── #
lifecycle_manager: "LifecycleManager | None" = None

# ────────── API-shared data ────────── #
plan_data: Any | None = None  # хранит JSON-план (List[waypoints])
last_detection: Any | None = None  # последняя пачка детекций


# ────────── helpers ────────── #
def get_camera() -> "CameraThread":
    if camera_factory is None:
        raise RuntimeError("camera_factory not configured")
    return camera_factory()


def get_detector() -> "DetectThread":
    if detect_factory is None:
        raise RuntimeError("detect_factory not configured")
    return detect_factory()


def get_lifecycle() -> "LifecycleManager":
    if lifecycle_manager is None:
        raise RuntimeError("lifecycle_manager not configured")
    return lifecycle_manager
