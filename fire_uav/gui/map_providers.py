# mypy: ignore-errors
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Protocol, runtime_checkable

import folium
from folium.plugins import Draw


@runtime_checkable
class MapProvider(Protocol):
    """Protocol for interchangeable map backends."""

    def render_map(self, path: list[tuple[float, float]], token: int) -> Path: ...
    @property
    def bridge_script(self) -> str: ...


class FoliumMapProvider:
    """
    Default Leaflet/Folium map provider.

    Generates a local HTML with draw controls and returns the file path.
    """

    _BRIDGE_JS = """\
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
  if (attr) attr.style.display = 'none';
})();"""

    def __init__(self) -> None:
        self._map_path: Path = Path(tempfile.gettempdir()) / "plan_map.html"
        self._radius_px = 18  # match QML card radius

    @property
    def bridge_script(self) -> str:
        return self._BRIDGE_JS

    def render_map(self, path: list[tuple[float, float]], token: int) -> Path:
        center = path[0] if path else (56.02, 92.9)

        fmap = folium.Map(
            center,
            zoom_start=13,
            control_scale=False,
            zoom_control=True,
            prefer_canvas=True,
        )

        Draw(
            export=False,
            draw_options={
                "polyline": {"shapeOptions": {"color": "#67d3ff"}},
                "polygon": False,
                "rectangle": False,
                "circle": False,
                "circlemarker": False,
                "marker": False,
            },
            edit_options={"edit": True, "remove": True},
        ).add_to(fmap)

        if path:
            folium.PolyLine(path, color="#67d3ff", weight=3).add_to(fmap)

        # match rounded QML container so corners aren't square
        fmap.get_root().header.add_child(
            folium.Element(
                f"""
<style>
.folium-map, .leaflet-container {{
    border-radius: {self._radius_px}px !important;
    overflow: hidden;
    background: transparent !important;
}}
html, body {{
    background: transparent !important;
}}
</style>
"""
            )
        )

        fmap.save(self._map_path)
        return self._map_path


class UnrealMapProvider:
    """
    Placeholder for Unreal/remote map integration.

    In this mode, render_map could be adapted to call an external service or
    simply return a static URL provided by Unreal. Not implemented yet.
    """

    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def bridge_script(self) -> str:
        return ""

    def render_map(self, path: list[tuple[float, float]], token: int) -> Path:
        raise NotImplementedError("Unreal map provider is not implemented yet")
