# mypy: ignore-errors
from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Final

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
        self._provider: MapProvider = provider or FoliumMapProvider()
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
            self._vm.generate_path()
            self.toastRequested.emit("Path ready")
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

    def __init__(
        self,
        det_vm: DetectorVM,
        map_bridge: MapBridge,
        video_bridge: VideoBridge,
        camera_available: bool,
    ) -> None:
        super().__init__()
        self.det_vm = det_vm
        self.map_bridge = map_bridge
        self.video_bridge = video_bridge

        self._logs: list[str] = []
        self._confidence = getattr(settings, "yolo_conf", 0.25)
        self._detector_running = False
        self._camera_available = camera_available

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

    # ---------- slots ---------- #
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

    # ---------- helpers ---------- #
    def on_frame(self, frame: NDArray[np.uint8]) -> None:
        self.video_bridge.update_frame(frame)

    def set_camera_available(self, flag: bool) -> None:
        self._camera_available = flag
        self.cameraAvailableChanged.emit()

    def _on_detections(self, dets) -> None:  # noqa: ANN001
        det_list = getattr(dets, "detections", [])
        if not det_list:
            return
        best_conf = max(getattr(d, "score", 0.0) for d in det_list)
        self.toastRequested.emit(f"Detections: {len(det_list)} (best {best_conf:.2f})")

    def _append_log(self, line: str) -> None:
        self._logs.append(line)
        # keep log tail reasonable
        if len(self._logs) > 400:
            self._logs = self._logs[-400:]
        self.logsChanged.emit()


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

        # Optional camera/detector threads
        try:
            self.cam_thr = deps.get_camera()
            self.det_thr = deps.get_detector()
            self._have_camera = True
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
            self.det_vm, self._map_bridge, self._video_bridge, camera_available=self._have_camera
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
