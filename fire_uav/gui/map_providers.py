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
    def set_provider(self, provider: str, *, offline: bool, cache_dir: Path | None) -> None: ...


class FoliumMapProvider:
    """
    Leaflet/Folium map provider with tile caching/offline toggle and provider switch.
    """

    TILESETS: dict[str, tuple[str, str]] = {
        "osm": ("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "OpenStreetMap"),
        "terrain": (
            "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
            "Stamen Terrain",
        ),
        "toner": ("https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png", "Stamen Toner"),
        "sat": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Esri World Imagery",
        ),
    }

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

    def __init__(
        self,
        provider: str = "osm",
        *,
        offline: bool = False,
        cache_dir: Path | None = None,
    ) -> None:
        self._map_path: Path = Path(tempfile.gettempdir()) / "plan_map.html"
        self._radius_px = 18  # match QML card radius
        self._provider = provider if provider in self.TILESETS else "osm"
        self._offline = offline
        self._cache_dir = cache_dir or Path(tempfile.gettempdir()) / "tile-cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def bridge_script(self) -> str:
        return self._BRIDGE_JS

    def set_provider(self, provider: str, *, offline: bool, cache_dir: Path | None = None) -> None:
        self._provider = provider if provider in self.TILESETS else "osm"
        self._offline = offline
        if cache_dir:
            self._cache_dir = cache_dir
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _tile_layer(self) -> tuple[str, str]:
        if self._offline:
            url = f"file://{self._cache_dir.as_posix()}" + "/{z}/{x}/{y}.png"
            return url, f"Offline cache ({self._provider})"
        url, attr = self.TILESETS.get(self._provider, self.TILESETS["osm"])
        return url, attr

    def render_map(self, path: list[tuple[float, float]], token: int) -> Path:
        center = path[0] if path else (56.02, 92.9)
        tiles_url, attr = self._tile_layer()

        fmap = folium.Map(
            center,
            zoom_start=13,
            control_scale=False,
            zoom_control=True,
            prefer_canvas=True,
            tiles=None,
        )

        folium.raster_layers.TileLayer(
            tiles=tiles_url,
            attr=attr,
            name=self._provider,
            overlay=False,
            control=False,
        ).add_to(fmap)

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
    """

    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def bridge_script(self) -> str:
        return ""

    def set_provider(self, provider: str, *, offline: bool, cache_dir: Path | None = None) -> None:
        raise NotImplementedError

    def render_map(self, path: list[tuple[float, float]], token: int) -> Path:
        raise NotImplementedError("Unreal map provider is not implemented yet")
