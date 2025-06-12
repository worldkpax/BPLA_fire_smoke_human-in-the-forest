from __future__ import annotations
import io, json, logging
from concurrent.futures import ProcessPoolExecutor, Future
from pathlib import Path
from typing import List, Optional

import folium
from folium.plugins import Draw
from shapely import geometry as shp

from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt5.QtGui  import QCursor
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QVBoxLayout, QWidget
)

from fire_uav.utils.gui_toast import show_toast
from fire_uav.flight.converter import dump_qgc, Waypoint
from fire_uav.app.route_process import build_route

TILES = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
ATTR  = "© OpenStreetMap contributors"
CSS_HIDE = "<style>.leaflet-control-attribution{display:none!important}</style>"


class PlanWidget(QWidget):
    mission_ready = pyqtSignal(object)          # list[list[Waypoint]]
    _pool: Optional[ProcessPoolExecutor] = None

    # ────────────────────────── init ──────────────────────────
    def __init__(self):
        super().__init__()
        logging.getLogger("PyQt5.QtWebEngine").setLevel(logging.CRITICAL)

        self._future: Optional[Future]              = None
        self._latest: Optional[List[List[Waypoint]]] = None
        if PlanWidget._pool is None:
            PlanWidget._pool = ProcessPoolExecutor(max_workers=1)

        self._build_ui(); self._draw_blank()
        self._timer = QTimer(interval=100, timeout=self._poll_future); self._timer.start()

    # ────────────────────────── UI ──────────────────────────
    def _build_ui(self):
        lay = QVBoxLayout(self)
        self.web = QWebEngineView()
        if hasattr(self.web.page(), "setConsoleMessagePattern"):
            self.web.page().setConsoleMessagePattern("")
        lay.addWidget(self.web, 1)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QPushButton("Load path (GeoJSON)", clicked=self._load_file))
        ctrl.addWidget(QLabel("Alt m:"))
        self.sp_alt = QSpinBox(minimum=30, maximum=500, value=120)
        ctrl.addWidget(self.sp_alt)
        ctrl.addStretch(1)
        ctrl.addWidget(QPushButton("Generate Route", clicked=self._generate))
        self.btn_save = QPushButton("Save plan", enabled=False, clicked=self._save)
        ctrl.addWidget(self.btn_save)
        lay.addLayout(ctrl)

    # ────────────────────────── карта ──────────────────────────
    def _folium_html(self, fmap):
        buf = io.BytesIO(); fmap.save(buf, close_file=False)
        html = buf.getvalue().decode()
        map_id = fmap.get_name()
        html = html.replace(f"var {map_id} =", f"var {map_id} = window._map =")
        extras = CSS_HIDE + """
<script>
window.addRoute = function(pts){
  const l = L.polyline(pts,{color:'#ff3d3d'}).addTo(window._map);
  pts.forEach(ll=>L.circleMarker(ll,{radius:3,color:'#2d89ef',fill:true}).addTo(window._map));
  window._map.fitBounds(l.getBounds(),{padding:[20,20]});
};
window.disableDrawing = function(){
  // прячем тулбар и отключаем прослушку событий
  document.querySelectorAll('.leaflet-draw-toolbar').forEach(el=>el.style.display='none');
  window._map.off('click');
};
</script>"""
        return html.replace("</head>", extras + "</head>")

    def _draw_blank(self, center=(56.02, 92.90)):
        fmap = folium.Map(location=center, zoom_start=10, tiles=TILES, attr=ATTR)
        Draw(export=False, position="topleft",
             draw_options={            # только Polyline
                 "polyline": True,
                 "polygon":  False,
                 "circle":   False,
                 "rectangle":False,
                 "marker":   False
             },
             edit_options={}).add_to(fmap)
        self.web.setHtml(self._folium_html(fmap), QUrl(""))

    # ────────────────────────── Load file ──────────────────────────
    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Line GeoJSON", ".", "GeoJSON (*.geojson *.json)")
        if not path: return
        gj = json.load(open(path, encoding="utf-8"))
        self._poly = shp.LineString(gj["coordinates"])
        self._show_path()
        show_toast(self, "Path loaded")

    def _show_path(self):
        fmap = folium.Map(location=[self._poly.centroid.y, self._poly.centroid.x],
                          zoom_start=14, tiles=TILES, attr=ATTR)
        folium.PolyLine([(lat,lon) for lon,lat in self._poly.coords],
                        color="#3388ff").add_to(fmap)
        self.web.setHtml(self._folium_html(fmap), QUrl(""))

    # ────────────────────────── Generate ──────────────────────────
    def _generate(self):
        # JS — берём только Polyline
        js = """
(function(){
  if(!window._map) return null;
  let out=null;
  window._map.eachLayer(l=>{
    if(!out && (l instanceof L.Polyline) && !(l instanceof L.Rectangle))
        out = l.toGeoJSON();
  });
  return out;
})();"""
        self.web.page().runJavaScript(js, self._after_js)

    def _after_js(self, geo):
        if geo is None:
            show_toast(self, "Draw polyline first"); return
        coords = geo["geometry"]["coordinates"]
        self._poly = shp.LineString(coords)

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self._future = PlanWidget._pool.submit(build_route, self._poly.wkt, 0)

    # ────────────────────────── poll Future ──────────────────────────
    def _poll_future(self):
        if self._future and self._future.done():
            QApplication.restoreOverrideCursor()
            try:
                mission_raw = self._future.result()[0]      # список кортежей
            except Exception as e:
                show_toast(self, f"Route error: {e}")
                self._future = None; return

            pts = [[lat, lon] for (lat, lon, _a) in mission_raw]
            self.web.page().runJavaScript(f"window.addRoute({json.dumps(pts)}); window.disableDrawing();")

            mission = [Waypoint(lat, lon, alt) for (lat, lon, alt) in mission_raw]
            self._latest = [mission]
            self.btn_save.setEnabled(True)
            show_toast(self, "Route generated ✓")
            self.mission_ready.emit([mission])
            self._future = None

    # ────────────────────────── Save plan ──────────────────────────
    def _save(self):
        if not self._latest:
            show_toast(self, "Generate route first"); return
        Path("artifacts").mkdir(exist_ok=True)
        dump_qgc(self._latest, "artifacts/mission.plan")
        show_toast(self, "Saved → artifacts/mission.plan")
