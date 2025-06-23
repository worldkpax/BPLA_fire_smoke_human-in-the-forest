# mypy: ignore-errors
from __future__ import annotations

import logging
from typing import Final

import numpy as np
from numpy.typing import NDArray
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import fire_uav.infrastructure.providers as deps
from fire_uav.config import settings
from fire_uav.domain.video.recorder import Recorder
from fire_uav.gui.themes.themes import STYLE_STEAM_DARK, STYLE_STEAM_LIGHT
from fire_uav.gui.utils.gui_toast import show_toast
from fire_uav.gui.viewmodels.detector_vm import DetectorVM
from fire_uav.gui.viewmodels.planner_vm import PlannerVM
from fire_uav.gui.widgets.plan_widget import PlanWidget
from fire_uav.gui.widgets.video_pane import VideoPane

_log: Final = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#                               MainWindow (View)
# --------------------------------------------------------------------------- #
class MainWindow(QMainWindow):
    """
    Главный GUI-класс.  Никакой бизнес-логики: только View-слой,
    вся работа делается во ViewModel-ах.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("fire_uav")
        self.resize(1440, 820)
        self._apply_theme("dark")

        # ---------- ViewModels ----------
        self.det_vm = DetectorVM()
        self.plan_vm = PlannerVM()

        # ---------- сервисы ----------
        self.recorder = Recorder(settings.output_root)
        self._frame_q = deps.frame_queue

        # ---------- опциональные потоки ----------
        try:
            self.cam_thr = deps.get_camera()
            self.det_thr = deps.get_detector()
            self._have_camera = True
            # сигналы подключаем только если камера есть
            self.cam_thr.frame.connect(self._on_frame)
            self.cam_thr.error.connect(lambda msg: show_toast(self, msg))
        except RuntimeError:
            # камеры нет — работаем без видео
            self.cam_thr = None
            self.det_thr = None
            self._have_camera = False

        # ---------- UI & меню ----------
        self._build_ui()
        self._build_menu()

        # ---------- лог-handler ----------
        from fire_uav.gui.utils.gui_logger import attach_handler

        attach_handler(self.log_box)

        # ---------- подписки VM → GUI ----------
        self.det_vm.detection.connect(self._on_detections)
        # ---------- helper for optional camera ----------

    def _maybe_set_bboxes(self, bxs):  # noqa: ANN001
        if self._have_camera:
            self.video_pane.set_bboxes(bxs)

    # ------------------------------------------------------------------ #
    #                               UI
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # ---------------- DETECTOR TAB ----------------
        self.det_tab = QWidget()
        vbox = QVBoxLayout(self.det_tab)

        self.video_pane = VideoPane()
        vbox.addWidget(self.video_pane, 5)

        hbox = QHBoxLayout()
        self.lbl_conf = QLabel("Conf: 0.25")
        self.slider = QSlider(Qt.Orientation.Horizontal, value=25, maximum=100)
        self.slider.valueChanged.connect(self._on_slider)

        self.btn_start = QPushButton("Start", clicked=self.det_vm.start)
        self.btn_stop = QPushButton("Stop", clicked=self.det_vm.stop)

        hbox.addWidget(self.lbl_conf)
        hbox.addWidget(self.slider, 2)
        hbox.addWidget(self.btn_start)
        hbox.addWidget(self.btn_stop)
        vbox.addLayout(hbox)

        tabs.addTab(self.det_tab, "Detector")

        # ---------------- PLANNER TAB -----------------
        self.plan_tab = QWidget()
        vbox_plan = QVBoxLayout(self.plan_tab)
        self.plan_widget = PlanWidget(self.plan_vm)
        vbox_plan.addWidget(self.plan_widget)
        tabs.addTab(self.plan_tab, "Planner")

        # ---------------- LOG TAB ---------------------
        self.log_tab = QWidget()
        self.log_box = QTextEdit(readOnly=True)
        QVBoxLayout(self.log_tab).addWidget(self.log_box)
        tabs.addTab(self.log_tab, "Logs")

    # ---------------------- MENU ------------------------------ #
    def _build_menu(self) -> None:
        menu = self.menuBar()

        view_menu = menu.addMenu("&View")
        view_menu.addAction(
            QAction("Dark theme", self, triggered=lambda: self._apply_theme("dark"))
        )
        view_menu.addAction(
            QAction("Light theme", self, triggered=lambda: self._apply_theme("light"))
        )

        help_menu = menu.addMenu("&Help")
        help_menu.addAction(QAction("About", self, triggered=self._show_about))

    # ---------------------- helpers --------------------------- #
    def _apply_theme(self, name: str) -> None:
        self.setStyleSheet(STYLE_STEAM_DARK if name == "dark" else STYLE_STEAM_LIGHT)

    def _show_about(self) -> None:
        show_toast(
            self,
            "BPLA Fire & Smoke Detector\nResearch prototype, 2025\n"
            "github.com/worldkpax/BPLA_fire_smoke_human-in-the-forest",
        )

    # ------------------- callbacks ---------------------------- #
    def _on_slider(self, value: int) -> None:
        self.lbl_conf.setText(f"Conf: {value / 100:.2f}")
        self.det_vm.set_conf(value / 100)

    def _on_frame(self, frame: NDArray[np.uint8]) -> None:
        # пишем в очередь для детектора
        if self._frame_q is not None:
            try:
                self._frame_q.put_nowait(frame)
            except Exception:
                pass
        self.video_pane.set_frame(frame)

    def _on_detections(self, dets) -> None:  # noqa: ANN001
        """
        Колбэк приходит из DetectorVM после каждого batch-inference.

        * Логируем статистику
        * Показываем короткий toast-баннер
        * (при желании здесь можно запустить автозапись видео и т.д.)
        """
        det_list = getattr(dets, "detections", [])  # универсально для любого Batch-класса
        if not det_list:
            return

        count = len(det_list)
        # максимальная уверенность в батче
        best_conf = max(getattr(d, "score", 0.0) for d in det_list)

        _log.info("Detected %d object(s), best conf = %.2f", count, best_conf)

        # короткое ненавязчивое сообщение в GUI
        show_toast(self, f"Detections: {count} (best {best_conf:.2f})", 1200)
