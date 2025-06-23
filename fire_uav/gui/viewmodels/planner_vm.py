# mypy: ignore-errors
from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import fire_uav.infrastructure.providers as deps


class PlannerVM:
    """
    MVVM-слой: хранит/отдаёт маршрут, импортирует GeoJSON LineString
    и экспортирует QGroundControl-совместимый mission.plan.
    """

    # ------------------------------------------------------------------ #
    #                     базовые set / get
    # ------------------------------------------------------------------ #
    def save_plan(self, pts: list[Tuple[float, float]]) -> None:
        """Записать путь (lat, lon) во «внешнее» хранилище (deps)."""
        deps.plan_data = {"path": pts}

    def get_path(self) -> list[Tuple[float, float]]:
        """Вернуть текущий путь или [] если его ещё нет."""
        return (deps.plan_data or {}).get("path", [])

    # ------------------------------------------------------------------ #
    #                       generate (по кнопке)
    # ------------------------------------------------------------------ #
    def generate_path(self) -> list[Tuple[float, float]]:
        """
        Покликал → двойной клик завершил линию → жмём «Generate Path».
        Здесь просто убеждаемся, что polyline действительно есть.
        """
        path = self.get_path()
        if not path:
            raise RuntimeError("Draw polyline first")
        return path

    # ------------------------------------------------------------------ #
    #                        IMPORT / EXPORT
    # ------------------------------------------------------------------ #
    def import_geojson(self, fn: Path) -> None:
        """Импортировать LineString (или Feature-обёртку) из GeoJSON."""
        gj = json.loads(fn.read_text())
        if gj.get("type") == "Feature":
            gj = gj["geometry"]

        if gj["type"] != "LineString":
            raise RuntimeError("Only LineString supported")

        # Leaflet даёт (lon, lat) — разворачиваем в (lat, lon)
        pts = [(lat, lon) for lon, lat in gj["coordinates"]]
        self.save_plan(pts)

    def export_json(self, fn: Path) -> None:
        """Сохранить «сырой» JSON вида {"path": [[lat, lon], …]}."""
        Path(fn).write_text(json.dumps(deps.plan_data, indent=2))

    # ------------------------------------------------------------------ #
    #                QGroundControl mission.plan в artifacts/
    # ------------------------------------------------------------------ #
    def export_qgc_plan(self, alt_m: float = 120.0) -> Path:
        """
        Сформировать QGC-совместимый файл mission.plan и положить его
        в <root>/artifacts/mission.plan. Возвращает путь к файлу.
        """
        path = self.get_path()
        if not path:
            raise RuntimeError("Draw polyline first")

        items = []
        for idx, (lat, lon) in enumerate(path):
            items.append(
                {
                    "AMSLAltAboveTerrain": None,
                    "Altitude": alt_m,
                    "AltitudeMode": 1,
                    "Command": 16,  # MAV_CMD_NAV_WAYPOINT
                    "DoJumpId": idx,
                    "Frame": 3,  # MAV_FRAME_GLOBAL
                    "Params": [0, 0, 0, 0, lat, lon, alt_m],
                    "Type": "SimpleItem",
                }
            )

        qgc = {
            "fileType": "Plan",
            "version": 2,
            "geoFence": {},
            "rallyPoints": {},
            "mission": {"items": items},
        }

        # <root>/artifacts/
        root_dir = Path(__file__).resolve().parents[3]
        artifacts = root_dir / "data" / "artifacts"
        artifacts.mkdir(exist_ok=True)
        fn = artifacts / "mission.plan"
        fn.write_text(json.dumps(qgc, indent=2))
        return fn
