# mypy: ignore-errors
from __future__ import annotations

import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Callable, Final

import cv2
import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider

import fire_uav.infrastructure.providers as deps
from fire_uav.config import settings
from fire_uav.gui.map_providers import FoliumMapProvider, MapProvider
from fire_uav.gui.viewmodels.detector_vm import DetectorVM
from fire_uav.gui.viewmodels.planner_vm import PlannerVM
from fire_uav.services.components.camera import CameraThread

_log: Final = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#                            Video helpers
# --------------------------------------------------------------------------- #
class VideoFrameProvider(QQuickImageProvider):
    """Simple QML image provider that keeps last rendered frame."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._image = QImage()

    def requestImage(self, _id, size, requestedSize):  # type: ignore[override]
        if not self._image.isNull():
            if size is not None:
                size.setWidth(self._image.width())
                size.setHeight(self._image.height())
            return self._image

        # fallback placeholder to avoid QML warnings
        placeholder = QImage(
            requestedSize.width() if requestedSize else 1280,
            requestedSize.height() if requestedSize else 720,
            QImage.Format.Format_ARGB32,
        )
        placeholder.fill(QColor("#0a111b"))
        return placeholder

    def set_image(self, image: QImage) -> None:
        self._image = image


class VideoBridge(QObject):
    """Stores last frame + bboxes and notifies QML to refresh the Image."""

    frameReady = Signal(str)

    def __init__(self, provider: VideoFrameProvider) -> None:
        super().__init__()
        self._provider = provider
        self._last_frame: NDArray[np.uint8] | None = None
        self._bboxes: list[tuple[int, int, int, int]] = []
        self._counter = 0

    @Slot(object)
    def set_bboxes(self, boxes: list[tuple[int, int, int, int]] | None) -> None:
        self._bboxes = boxes or []
        self._render()

    def update_frame(self, frame: NDArray[np.uint8]) -> None:
        self._last_frame = frame
        self._render()

    # ---------- internal ---------- #
    def _render(self) -> None:
        if self._last_frame is None:
            return

        h, w, _ = self._last_frame.shape
        img = QImage(self._last_frame.data, w, h, 3 * w, QImage.Format.Format_BGR888).copy()

        if self._bboxes:
            painter = QPainter(img)
            pen = QPen(QColor("#70e0ff"), 2)
            painter.setPen(pen)
            for x1, y1, x2, y2 in self._bboxes:
                painter.drawRect(x1, y1, x2 - x1, y2 - y1)
            painter.end()

        self._provider.set_image(img)
        self._counter += 1
        self.frameReady.emit(f"image://video/live?{self._counter}")


# --------------------------------------------------------------------------- #
#                             Logging bridge
# --------------------------------------------------------------------------- #
class QmlLogHandler(logging.Handler, QObject):
    message = Signal(str)

    def __init__(self) -> None:
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            self.message.emit(self.format(record))
        except Exception:  # noqa: BLE001
            pass


class MapBridge(QObject):
    """Generates Folium map with draw controls and bridges JS→Python via console logs."""

    urlChanged = Signal(QUrl)
    toastRequested = Signal(str)

    def __init__(self, vm: PlannerVM, provider: MapProvider | None = None) -> None:
        super().__init__()
        self._vm = vm
        cache_dir = Path(__file__).resolve().parents[2] / "data" / "cache" / "tiles"
        self._provider: MapProvider = provider or FoliumMapProvider(cache_dir=cache_dir)
        self._map_path: Path = Path(tempfile.gettempdir()) / "plan_map.html"
        self._token = 0
        self.render_map()

    # ----- properties exposed to QML ----- #
    @Property(QUrl, notify=urlChanged)
    def url(self) -> QUrl:
        url = QUrl.fromLocalFile(str(self._map_path))
        url.setQuery(f"v={self._token}")
        return url

    @Property(str, constant=True)
    def bridgeScript(self) -> str:
        return getattr(self._provider, "bridge_script", "")

    # ----- slots for QML ----- #
    @Slot()
    def render_map(self) -> None:
        path = self._vm.get_path()
        self._map_path = self._provider.render_map(path, self._token)
        self._token += 1
        self.urlChanged.emit(self.url)

    @Slot(str)
    def handle_console(self, message: str) -> None:
        if not message.startswith("PY_PATH "):
            return
        gj = json.loads(message.split(" ", 1)[1])
        pts = [(lat, lon) for lon, lat in gj.get("coordinates", [])]
        self._vm.save_plan(pts)
        self.render_map()
        self.toastRequested.emit("Path updated")

    @Slot()
    def generate_path(self) -> None:
        try:
            fn = self._vm.generate_path()
            rel = fn
            try:
                rel = fn.relative_to(fn.parents[1])
            except Exception:
                pass
            self.toastRequested.emit(f"Path saved -> {rel}")
        except Exception as exc:  # noqa: BLE001
            self.toastRequested.emit(str(exc))

    @Slot()
    def save_plan(self) -> None:
        try:
            fn = self._vm.export_qgc_plan(alt_m=120.0)
            self.toastRequested.emit(f"Mission saved → {fn.relative_to(fn.parents[1])}")
        except Exception as exc:  # noqa: BLE001
            self.toastRequested.emit(str(exc))

    @Slot(str)
    def import_geojson(self, fn: str) -> None:
        if not fn:
            return
        try:
            self._vm.import_geojson(Path(fn))
            self.render_map()
            self.toastRequested.emit("Polyline imported")
        except Exception as exc:  # noqa: BLE001
            self.toastRequested.emit(f"Error: {exc}")

    @Slot(str)
    def import_kml(self, fn: str) -> None:
        if not fn:
            return
        try:
            pts = self._parse_kml(Path(fn))
            self._vm.save_plan(pts)
            self.render_map()
            self.toastRequested.emit("KML imported")
        except Exception as exc:  # noqa: BLE001
            self.toastRequested.emit(f"Error: {exc}")

    @Slot(str, bool, str)
    def set_provider(self, provider: str, offline: bool, cache_dir: str = "") -> None:
        cd = Path(cache_dir) if cache_dir else None
        self._provider.set_provider(provider, offline=offline, cache_dir=cd)
        self.render_map()

    # ----- helpers ----- #
    def _parse_kml(self, fn: Path) -> list[tuple[float, float]]:
        text = fn.read_text(encoding="utf-8", errors="ignore")
        if "<coordinates" not in text:
            raise RuntimeError("Coordinates not found in KML")
        coords_block = (
            text.split("<coordinates", 1)[1].split(">", 1)[1].split("</coordinates>", 1)[0]
        )
        pts: list[tuple[float, float]] = []
        for raw in coords_block.strip().replace("\n", " ").split():
            parts = raw.split(",")
            if len(parts) < 2:
                continue
            lon, lat = float(parts[0]), float(parts[1])
            pts.append((lat, lon))
        if not pts:
            raise RuntimeError("No valid points in KML")
        return pts


# --------------------------------------------------------------------------- #
#                             App controller (QML-facing)
# --------------------------------------------------------------------------- #
class AppController(QObject):
    toastRequested = Signal(str)
    frameReady = Signal(str)
    mapUrlChanged = Signal(QUrl)
    logsChanged = Signal()
    confidenceChanged = Signal()
    detectorRunningChanged = Signal()
    cameraAvailableChanged = Signal()
    statsChanged = Signal()

    def __init__(
        self,
        det_vm: DetectorVM,
        map_bridge: MapBridge,
        video_bridge: VideoBridge,
        camera_available: bool,
        camera_switcher: Callable[[], bool] | None = None,
    ) -> None:
        super().__init__()
        self.det_vm = det_vm
        self.map_bridge = map_bridge
        self.video_bridge = video_bridge
        self._camera_switcher = camera_switcher

        self._logs: list[str] = []
        self._confidence = getattr(settings, "yolo_conf", 0.25)
        self._detector_running = False
        self._camera_available = camera_available
        self._fps = 0.0
        self._latency_ms = 0.0
        self._bus_alive = False
        self._detection_conf = 0.0
        self._last_frame_ts: float | None = None
        self._last_detection_ts: float | None = None
        self._ground_station_enabled = bool(getattr(settings, "ground_station_enabled", False))

        # wire signals
        self.det_vm.detection.connect(self._on_detections)
        self.det_vm.bboxes.connect(self.video_bridge.set_bboxes)
        self.video_bridge.frameReady.connect(self.frameReady)
        self.map_bridge.urlChanged.connect(self.mapUrlChanged)
        self.map_bridge.toastRequested.connect(self.toastRequested)

        # logging to QML
        self._log_handler = QmlLogHandler()
        self._log_handler.message.connect(self._append_log)
        root = logging.getLogger()
        if not any(isinstance(h, QmlLogHandler) for h in root.handlers):
            root.addHandler(self._log_handler)

    # ---------- properties ---------- #
    @Property("QStringList", notify=logsChanged)
    def logs(self) -> list[str]:
        return self._logs

    @Property(float, notify=confidenceChanged)
    def confidence(self) -> float:
        return self._confidence

    @Property(bool, notify=detectorRunningChanged)
    def detectorRunning(self) -> bool:
        return self._detector_running

    @Property(bool, notify=cameraAvailableChanged)
    def cameraAvailable(self) -> bool:
        return self._camera_available

    @Property(QUrl, notify=mapUrlChanged)
    def mapUrl(self) -> QUrl:
        return self.map_bridge.url

    @Property(str, constant=True)
    def mapBridgeScript(self) -> str:
        return self.map_bridge.bridgeScript

    @Property(float, notify=statsChanged)
    def fps(self) -> float:
        return self._fps

    @Property(float, notify=statsChanged)
    def latencyMs(self) -> float:
        return self._latency_ms

    @Property(float, notify=statsChanged)
    def detectionConfidence(self) -> float:
        return self._detection_conf

    @Property(bool, notify=statsChanged)
    def busAlive(self) -> bool:
        return self._bus_alive

    @Property(bool, notify=statsChanged)
    def groundStationEnabled(self) -> bool:
        return self._ground_station_enabled

    # ---------- slots ---------- #
    @Slot()
    def cycleCamera(self) -> None:
        if self._camera_switcher is None:
            return
        self._camera_switcher()

    @Slot()
    def startDetector(self) -> None:
        self.det_vm.start()
        self._detector_running = True
        self.detectorRunningChanged.emit()

    @Slot()
    def stopDetector(self) -> None:
        self.det_vm.stop()
        self._detector_running = False
        self.detectorRunningChanged.emit()

    @Slot(float)
    def setConfidence(self, value: float) -> None:
        self._confidence = float(value)
        self.det_vm.set_conf(self._confidence)
        self.confidenceChanged.emit()

    @Slot(str)
    def handleMapConsole(self, message: str) -> None:
        self.map_bridge.handle_console(message)

    @Slot()
    def regenerateMap(self) -> None:
        self.map_bridge.render_map()

    @Slot()
    def generatePath(self) -> None:
        self.map_bridge.generate_path()

    @Slot()
    def savePlan(self) -> None:
        self.map_bridge.save_plan()

    @Slot(str)
    def importGeoJson(self, filename: str) -> None:
        self.map_bridge.import_geojson(filename)

    @Slot(str)
    def importKml(self, filename: str) -> None:
        self.map_bridge.import_kml(filename)

    @Slot(str, bool, str)
    def setMapProvider(self, provider: str, offline: bool, cacheDir: str = "") -> None:
        self.map_bridge.set_provider(provider, offline=offline, cache_dir=cacheDir or None)

    # ---------- helpers ---------- #
    def on_frame(self, frame: NDArray[np.uint8]) -> None:
        now = time.perf_counter()
        if self._last_frame_ts is not None:
            dt = now - self._last_frame_ts
            if dt > 0:
                inst_fps = 1.0 / dt
                self._fps = 0.85 * self._fps + 0.15 * inst_fps if self._fps else inst_fps
        self._last_frame_ts = now
        self._update_stats()
        self.video_bridge.update_frame(frame)

    def set_camera_available(self, flag: bool) -> None:
        self._camera_available = flag
        self.cameraAvailableChanged.emit()

    def _on_detections(self, dets) -> None:  # noqa: ANN001
        det_list = getattr(dets, "detections", [])
        if not det_list:
            self._detection_conf = 0.0
            self._update_stats()
            return
        best_conf = max(getattr(d, "score", getattr(d, "confidence", 0.0)) for d in det_list)
        bbox = getattr(det_list[0], "bbox", None)
        if bbox is None and all(hasattr(det_list[0], k) for k in ("x1", "y1", "x2", "y2")):
            bbox = (
                getattr(det_list[0], "x1"),
                getattr(det_list[0], "y1"),
                getattr(det_list[0], "x2"),
                getattr(det_list[0], "y2"),
            )
        _log.info("GUI detection event: count=%d best=%.2f bbox=%s", len(det_list), best_conf, bbox)
        self.toastRequested.emit(f"Detections: {len(det_list)} (best {best_conf:.2f})")

        now = time.perf_counter()
        self._last_detection_ts = now
        self._detection_conf = best_conf
        if self._last_frame_ts is not None:
            self._latency_ms = max(0.0, (now - self._last_frame_ts) * 1000)
        self._update_stats()

    def _append_log(self, line: str) -> None:
        self._logs.append(line)
        # keep log tail reasonable
        if len(self._logs) > 400:
            self._logs = self._logs[-400:]
        self.logsChanged.emit()

    def _update_stats(self) -> None:
        now = time.perf_counter()
        if self._last_detection_ts is not None and (now - self._last_detection_ts) > 2.0:
            self._detection_conf = 0.0
        bus_alive = self._last_detection_ts is not None and (now - self._last_detection_ts) < 2.0
        if bus_alive != self._bus_alive:
            self._bus_alive = bus_alive
        self.statsChanged.emit()


# --------------------------------------------------------------------------- #
#                               MainWindow facade
# --------------------------------------------------------------------------- #
class MainWindow(QObject):
    """QML-driven UI facade that keeps the existing lifecycle wiring."""

    def __init__(self) -> None:
        super().__init__()
        self.det_vm = DetectorVM()
        self.plan_vm = PlannerVM()
        self._frame_q = deps.frame_queue
        self._cam_fps = getattr(settings, "camera_fps", 30)
        self._camera_index = 0
        self._camera_candidates: list[int] = self._probe_cameras()

        # Optional camera/detector threads
        try:
            self.cam_thr = deps.get_camera()
            self.det_thr = deps.get_detector()
            self._have_camera = True
            self._camera_index = getattr(self.cam_thr, "index", 0)
            if self._camera_index not in self._camera_candidates:
                self._camera_candidates.insert(0, self._camera_index)
            self.cam_thr.frame.connect(self._on_frame)
            self.cam_thr.error.connect(lambda msg: self.app.toastRequested.emit(msg))
        except RuntimeError:
            self.cam_thr = None
            self.det_thr = None
            self._have_camera = False

        # Bridges exposed to QML
        self._video_provider = VideoFrameProvider()
        self._video_bridge = VideoBridge(self._video_provider)
        self._map_bridge = MapBridge(self.plan_vm)
        self.app = AppController(
            self.det_vm,
            self._map_bridge,
            self._video_bridge,
            camera_available=self._have_camera,
            camera_switcher=self._cycle_camera,
        )

        # QML engine + context
        self._engine = QQmlApplicationEngine()
        self._engine.addImageProvider("video", self._video_provider)
        self._engine.rootContext().setContextProperty("app", self.app)

        qml_path = Path(__file__).resolve().parents[1] / "qml" / "main.qml"
        _log.info("Loading QML UI from %s", qml_path)
        self._engine.load(QUrl.fromLocalFile(str(qml_path)))
        if not self._engine.rootObjects():
            raise RuntimeError("Failed to load QML UI")
        self._window = self._engine.rootObjects()[0]

    # ---------- facade API ---------- #
    def show(self) -> None:
        if self._window is not None:
            self._window.show()

    # ---------- slots from threads ---------- #
    def _on_frame(self, frame: NDArray[np.uint8]) -> None:
        if self._frame_q is not None:
            try:
                self._frame_q.put_nowait(frame)
            except Exception:
                pass
        self.app.on_frame(frame)

    # ---------- camera helpers ---------- #
    def _probe_cameras(self, limit: int = 5) -> list[int]:
        found: list[int] = []
        for idx in range(limit):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                found.append(idx)
            cap.release()
        return found

    def _camera_available(self, index: int) -> bool:
        cap = cv2.VideoCapture(index)
        ok = cap.isOpened()
        cap.release()
        return ok

    def _cycle_camera(self) -> bool:
        # Refresh candidate list each time to catch hotplug devices.
        self._camera_candidates = self._probe_cameras()
        if len(self._camera_candidates) <= 1:
            self.app.toastRequested.emit("No alternate camera found")
            return False

        current = (
            self._camera_index
            if self._camera_index in self._camera_candidates
            else self._camera_candidates[0]
        )
        next_idx = self._camera_candidates[
            (self._camera_candidates.index(current) + 1) % len(self._camera_candidates)
        ]
        if next_idx == current and len(self._camera_candidates) == 1:
            self.app.toastRequested.emit("No alternate camera found")
            return False

        return self._switch_camera(next_idx)

    def _switch_camera(self, index: int) -> bool:
        if not self._camera_available(index):
            self._have_camera = False
            self.app.set_camera_available(False)
            self.app.toastRequested.emit(f"Camera #{index} is not available")
            return False

        old_cam = getattr(self, "cam_thr", None)
        if old_cam is not None:
            try:
                old_cam.stop()
                old_cam.join(timeout=2.0)
            except Exception:  # noqa: BLE001
                pass

        try:
            new_cam = CameraThread(index=index, fps=self._cam_fps, out_queue=self._frame_q)
        except Exception as exc:  # noqa: BLE001
            self.cam_thr = None
            self._have_camera = False
            self.app.set_camera_available(False)
            self.app.toastRequested.emit(f"Failed to init camera #{index}: {exc}")
            return False

        new_cam.frame.connect(self._on_frame)
        new_cam.error.connect(lambda msg: self.app.toastRequested.emit(msg))
        deps.get_lifecycle().register(new_cam)
        new_cam.start()

        self.cam_thr = new_cam
        self._camera_index = index
        self._have_camera = True
        self.app.set_camera_available(True)
        self.app.toastRequested.emit(f"Camera switched to #{index}")
        return True
