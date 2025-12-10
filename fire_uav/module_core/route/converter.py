"""
fire_uav.domain.route.converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Преобразование миссий между внутренним представлением, JSON-форматом
QGroundControl (`mission.plan`) и текстовым файлом MAVLink (`mission.txt`).

• to_qgc()      – список Waypoint-ов → dict
• dump_qgc()    – сохранить dict → .plan
• qgc2mav()     – mission.plan  → mission.txt
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Union

from fire_uav.module_core.schema import Waypoint


# ───────────── QGroundControl → JSON ───────────── #
def to_qgc(missions: Sequence[Sequence[Waypoint]]) -> Dict[str, Any]:
    seq = 0
    items = []
    for mission in missions:
        for wp in mission:
            items.append(
                {
                    "AMSLAltAboveTerrain": None,
                    "Altitude": wp.alt,
                    "AltitudeMode": 1,
                    "Command": 16,  # MAV_CMD_NAV_WAYPOINT
                    "DoJumpId": seq,
                    "Frame": 3,  # GLOBAL_RELATIVE_ALT
                    "Params": [0, 0, 0, 0, wp.lat, wp.lon, wp.alt],
                    "Type": "SimpleItem",
                }
            )
            seq += 1

    return {
        "fileType": "Plan",
        "geoFence": {},
        "mission": {"items": items},
        "rallyPoints": {},
        "version": 2,
    }


def dump_qgc(missions: Sequence[Sequence[Waypoint]], path: str | Path) -> None:
    """Сохранить список маршрутов в QGC-формат (`mission.plan`)."""
    path = Path(path)
    path.write_text(json.dumps(to_qgc(list(missions)), indent=2), encoding="utf-8")


# ───────────── QGroundControl JSON → MAVLink WPL ───────────── #
def _item_to_wpl(seq: int, item: dict[str, Any]) -> str:
    """QGC-item → строка 'mission.txt'."""
    lat, lon, alt = item["Params"][4:7]
    return (
        f"{seq}\t"  # seq
        f"0\t"  # current WP (0 – нет, 1 – начинать отсюда)
        f"{item['Frame']}\t"
        f"{item['Command']}\t"
        "0\t0\t0\t0\t"  # params 1-4 (не нужны для обычного WP)
        f"{lat:.7f}\t{lon:.7f}\t{alt:.2f}\t"
        "1"  # autocontinue
    )


def qgc2mav(
    qgc_source: Union[str, Path, dict[str, Any]],
    out_path: str | Path,
) -> int:
    """
    Преобразовать QGroundControl-миссию в текстовый файл MAVLink Waypoint List
    (`mission.txt`, формат *QGC WPL 120* / *110*).

    Parameters
    ----------
    qgc_source : путь к `mission.plan` **или** уже загруженный dict.
    out_path   : куда сохранить `mission.txt`.

    Returns
    -------
    int – количество Waypoint-ов.
    """
    # --- читаем вход ---
    if isinstance(qgc_source, (str, Path)):
        data = json.loads(Path(qgc_source).read_text(encoding="utf-8"))
    else:
        data = qgc_source

    items = data.get("mission", {}).get("items", [])
    if not items:
        raise ValueError("No 'mission.items' in QGC plan")

    # --- генерируем строки WPL ---
    wpl_lines = ["QGC WPL 120"]
    for seq, it in enumerate(items):
        wpl_lines.append(_item_to_wpl(seq, it))

    # --- сохраняем ---
    out_path = Path(out_path)
    out_path.write_text("\n".join(wpl_lines) + "\n", encoding="utf-8")

    return len(items)


# ───────────── mission.plan → Waypoint[] ───────────── #
def waypoints_from_plan(plan_path: str | Path) -> List[Waypoint]:
    """
    Извлекает Waypoint-ы из QGroundControl mission.plan.

    Поддерживает как «Params», так и «params» (некоторые экспортёры
    пишут ключи строчными).
    """
    data = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    items = data.get("mission", {}).get("items", [])
    wps: List[Waypoint] = []
    for it in items:
        params = it.get("Params") or it.get("params")
        if not params or len(params) < 7:
            continue
        lat, lon, alt = params[4:7]
        wps.append(Waypoint(lat=float(lat), lon=float(lon), alt=float(alt)))
    return wps
