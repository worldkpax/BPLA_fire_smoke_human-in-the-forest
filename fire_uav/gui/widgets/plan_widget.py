from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Final

import folium
from folium.plugins import Draw
from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from fire_uav.gui.utils.gui_toast import show_toast
from fire_uav.gui.viewmodels.planner_vm import PlannerVM

# mypy: disable-error-code=call-arg


_log: Final = logging.getLogger(__name__)


class _Page(QWebEnginePage):
    consoleMessage = Signal(int, str, int, str)  # level, msg, line, source

    def javaScriptConsoleMessage(self, level: int, msg: str, line: int, source: str) -> None:
        """Перехват сообщений из JS-консоли и эмит в Qt."""
        self.consoleMessage.emit(level, msg, line, source)


class PlanWidget(QWidget):
    """Карта с полилинией и трёхкнопочным интерфейсом."""

    def __init__(self, vm: PlannerVM) -> None:
        super().__init__()
        self._vm = vm
        self._tmp_html: Path = Path(tempfile.gettempdir()) / "plan_map.html"

        self.setObjectName("planWidgetRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._btn_gen = QPushButton("Generate Path")
        self._btn_save = QPushButton("Save Plan")
        self._btn_imp = QPushButton("Import GeoJSON")

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 8)
        top.setSpacing(10)
        top.addWidget(self._btn_gen)
        top.addWidget(self._btn_save)
        top.addWidget(self._btn_imp)
        top.addStretch()

        # Map view
        self._view = QWebEngineView()
        self._page = _Page(self._view)
        self._view.setPage(self._page)
        self._view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(top)
        lay.addWidget(self._view)

        # Signals
        self._btn_gen.clicked.connect(self._on_generate)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_imp.clicked.connect(self._on_import)

        self._page.consoleMessage.connect(self._js_bridge)
        self._view.loadFinished.connect(self._after_load)

        self._render_map()

    def _render_map(self) -> None:
        """Создаёт карту с рисованием и сохраняет её во временный HTML."""
        path = self._vm.get_path()
        center = path[0] if path else (56.02, 92.9)

        fmap = folium.Map(
            center,
            zoom_start=13,
            control_scale=False,
            zoom_control=True,
            prefer_canvas=True,
            attributionControl=False,
        )

        Draw(
            export=False,
            draw_options={
                "polyline": {"shapeOptions": {"color": "#3388ff"}},
                "polygon": False,
                "rectangle": False,
                "circle": False,
                "circlemarker": False,
                "marker": False,
            },
            edit_options={"edit": True, "remove": True},
        ).add_to(fmap)

        if path:
            folium.PolyLine(path, color="red", weight=4).add_to(fmap)

        fmap.get_root().header.add_child(
            folium.Element(
                """
<style>
.leaflet-control-attribution { display: none !important; }
</style>
"""
            )
        )

        fmap.save(self._tmp_html)
        self._view.setUrl(QUrl.fromLocalFile(str(self._tmp_html)))

    @Slot(int, str, int, str)
    def _js_bridge(self, level: int, message: str, line: int, source: str) -> None:
        """
        JS → Python bridge: ловим сообщения 'PY_PATH ' + GeoJSON
        и сохраняем план.
        """
        if message.startswith("PY_PATH "):
            gj = json.loads(message.split(" ", 1)[1])
            pts = [(lat, lon) for lon, lat in gj["coordinates"]]
            self._vm.save_plan(pts)
            self._render_map()

    def _after_load(self, ok: bool) -> None:
        """После загрузки HTML устанавливаем JS-обработчики."""
        if not ok:
            _log.error("Map load failed")
            return

        js = """\
(() => {
  if (!window.L) { console.error('Leaflet failed to load'); return; }
  const map = Object.values(window).find(v => v instanceof L.Map);
  if (!map) { console.error('Map instance not found'); return; }

  function send(gj) { console.log('PY_PATH ' + JSON.stringify(gj)); }

  map.on(L.Draw.Event.CREATED, e => {
      if (e.layerType === 'polyline')
          send(e.layer.toGeoJSON().geometry);
  });

  map.on(L.Draw.Event.EDITED, e => {
      e.layers.eachLayer(l => {
          if (l instanceof L.Polyline)
              send(l.toGeoJSON().geometry);
      });
  });

  map.on(L.Draw.Event.DELETED, () => {
      send({type:'LineString', coordinates:[]});
  });

  const attr = document.querySelector('.leaflet-control-attribution');
  if (map.attributionControl) map.attributionControl.remove();
  if (attr) attr.remove();
})();"""
        self._view.page().runJavaScript(js)

    def _on_generate(self) -> None:
        """Генерация пути по current polygon."""
        try:
            fn = self._vm.generate_path()
            rel = fn
            try:
                rel = fn.relative_to(fn.parents[1])
            except Exception:
                pass
            show_toast(self, f"Path saved -> {rel}")
        except Exception as exc:
            show_toast(self, str(exc))

    def _on_save(self) -> None:
        """Экспорт плана в формат QGC и сохранение файла."""
        try:
            fn = self._vm.export_qgc_plan(alt_m=120.0)
            show_toast(self, f"Mission saved → {fn.relative_to(fn.parents[1])}")
        except Exception as exc:
            show_toast(self, str(exc))

    def _on_import(self) -> None:
        """Импорт GeoJSON and re-render."""
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Import GeoJSON",
            filter="GeoJSON (*.geojson *.json)",
        )
        if not fn:
            return
        try:
            self._vm.import_geojson(Path(fn))
            self._render_map()
            show_toast(self, "Polyline imported")
        except Exception as exc:
            show_toast(self, f"Error: {exc}")
