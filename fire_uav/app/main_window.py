from __future__ import annotations
import queue, sys, logging, json, time, cv2, numpy as np
from pathlib import Path
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QMenu,
    QPushButton, QSlider, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget, QAction
)

from fire_uav.utils.logging       import setup_logging
from fire_uav.utils.gui_logger     import QtLogHandler
from fire_uav.utils.gui_toast      import show_toast
from fire_uav.app.themes           import STYLE_STEAM_DARK, STYLE_STEAM_LIGHT
from fire_uav.io.recorder          import Recorder
from fire_uav.config.settings      import settings
from fire_uav.app.camera_thread    import CameraThread
from fire_uav.app.detect_thread    import DetectThread
from fire_uav.app.plan_widget      import PlanWidget
from fire_uav.flight.coverage      import coverage_percent
from fire_uav.flight.planner       import CameraSpec, Waypoint

# ─────────── helper video widget ─────────── #
class VideoPane(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel(alignment=Qt.AlignCenter)
        QVBoxLayout(self).addWidget(self.label)
    def update_frame(self, frame: np.ndarray):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        q = QImage(rgb.data, w, h, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q))

# ───────────────── Main Window ───────────────── #
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("fire_uav"); self.resize(1440, 820)
        setup_logging()

        self._apply_theme("dark")

        self.recorder = Recorder(settings.output_root)
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        self._build_detector_tab(); self._build_planner_tab(); self._build_log_tab()
        self._build_menu()

        # threads
        self.q_frames: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=1)
        self.cam_thr = CameraThread(fps=30); self.cam_thr.frame.connect(self._on_frame)
        self.det_thr = DetectThread(settings.yolo_model, settings.yolo_conf)
        self.det_thr._queue = self.q_frames
        self.det_thr.detections.connect(self._on_detections)

        logging.getLogger().addHandler(QtLogHandler(self.log_box))

    # ─────────── build tabs ─────────── #
    def _build_detector_tab(self):
        tab = QWidget(); v = QVBoxLayout(tab)
        self.video_pane = VideoPane(); v.addWidget(self.video_pane, 5)

        h = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal, minimum=5, maximum=95,
                              value=int(settings.yolo_conf*100))
        self.slider.valueChanged.connect(self._on_slider)
        self.lbl_conf = QLabel(f"Conf: {settings.yolo_conf:.2f}")
        self.btn_start = QPushButton("Start", clicked=self._start_all)
        self.btn_stop  = QPushButton("Stop",  clicked=self._stop_all)
        h.addWidget(self.lbl_conf); h.addWidget(self.slider, 2)
        h.addWidget(self.btn_start); h.addWidget(self.btn_stop)
        v.addLayout(h)
        self.tabs.addTab(tab, "Detector")

    def _build_planner_tab(self):
        self.plan = PlanWidget()
        self.plan.mission_ready.connect(
            lambda m: self._log_coverage(self.plan._poly, m))
        self.plan.mission_ready.connect(
            lambda m: setattr(self, "_last_missions", m))
        self.tabs.addTab(self.plan, "Flight Plan")

    def _build_log_tab(self):
        self.log_box = QTextEdit(readOnly=True)
        self.tabs.addTab(self.log_box, "Log / JSON")

    # ─────────── menu ─────────── #
    def _build_menu(self):
        ic = lambda n: QIcon(f"fire_uav/assets/{n}.svg")
        m_actions = self.menuBar().addMenu("&Actions")
        m_actions.addAction(QAction(ic("save"), "Export MAVLink…", self,
                                    triggered=self._export_mavlink))
        m_actions.addAction(QAction(ic("upload"), "Upload DJI (stub)", self,
                                    triggered=self._upload_dji))
        m_actions.addAction(QAction(ic("sim"), "Run AirSim (stub)", self,
                                    triggered=self._run_sim))

        m_theme = self.menuBar().addMenu("&Theme")
        m_theme.addAction(QAction("Night (Steam)", self,
                                  triggered=lambda: self._apply_theme("dark")))
        m_theme.addAction(QAction("Day  (Steam)", self,
                                  triggered=lambda: self._apply_theme("light")))

    def _apply_theme(self, name: str):
        css = STYLE_STEAM_DARK if name == "dark" else STYLE_STEAM_LIGHT
        QApplication.instance().setStyle("Fusion")
        QApplication.instance().setStyleSheet(css)

    # ─────────── menu callbacks ─────────── #
    def _export_mavlink(self):
        if not getattr(self, "_last_missions", None):
            show_toast(self, "Generate route first"); return
        from fire_uav.flight.converter import dump_qgc
        Path("artifacts").mkdir(exist_ok=True)
        dump_qgc(self._last_missions, "artifacts/mission.plan")
        n = self._plan2mav("artifacts/mission.plan")
        show_toast(self, f"mission.txt ({n} wp) saved")

    def _upload_dji(self):
        if not Path("artifacts/mission.plan").exists():
            show_toast(self, "No mission.plan"); return
        show_toast(self, "DJI upload (stub)…"); time.sleep(1)
        show_toast(self, "✓ uploaded (stub)")

    def _run_sim(self):
        if not Path("artifacts/mission.plan").exists():
            show_toast(self, "No mission.plan"); return
        show_toast(self, "AirSim run (stub)…"); time.sleep(1)
        show_toast(self, "✓ done (stub)")

    def _plan2mav(self, plan_path) -> int:
        it = json.load(open(plan_path))["mission"]["items"]
        with open("artifacts/mission.txt", "w", encoding="utf-8") as f:
            f.write("QGC WPL 120\n")
            for i,itm in enumerate(it):
                lat,lon,alt = itm["params"][4:7]
                f.write(f"{i}\t0\t3\t16\t0\t0\t0\t0\t{lat}\t{lon}\t{alt}\t1\n")
        return len(it)

    # ─────────── coverage ─────────── #
    def _log_coverage(self, poly, missions):
        try:
            if not (poly and missions): return
            wps = [wp for ms in missions for wp in ms]
            if not wps: return
            sw = CameraSpec().swath_m(wps[0].alt)
            pc = coverage_percent(poly, wps, sw)
            self.log_box.append(f"Coverage ≈ {pc:.1f} %")
        except Exception as e:
            logging.error("coverage_percent failed: %s", e)
            # не роняем GUI, просто выводим короткий toast
            show_toast(self, "Coverage calc error")

    # ─────────── detector handlers ─────────── #
    def _start_all(self):
        if not self.cam_thr.isRunning(): self.cam_thr.start()
        if not self.det_thr.isRunning(): self.det_thr.start()
        show_toast(self, "Streams started")
    def _stop_all(self):
        self.cam_thr.stop(); self.det_thr.stop()
        show_toast(self, "Streams stopped")
    def _on_slider(self, v):
        conf = v/100; self.lbl_conf.setText(f"Conf: {conf:.2f}")
        self.det_thr.engine._yolo.overrides["conf"] = conf
    def _on_frame(self, frame):
        if not self.q_frames.full(): self.q_frames.put(frame)
    def _on_detections(self, dets):
        if self.q_frames.empty(): return
        frame = self.q_frames.get()
        for d in dets:
            x1,y1,x2,y2=d.bbox
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
        self.video_pane.update_frame(frame)
        self.recorder.save_frame(frame); self.recorder.save_detections(dets)

    def closeEvent(self, ev):
        self.cam_thr.stop(); self.det_thr.stop()
        super().closeEvent(ev)


# ───────────────── entry ───────────────── #
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion"); app.setStyleSheet(STYLE_STEAM_DARK)
    win = MainWindow(); win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
