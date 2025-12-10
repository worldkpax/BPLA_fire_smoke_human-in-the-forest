"""
Вычисление процента покрытия полигона маршрутом БПЛА.

Функция теперь «всеядна»: area может быть Polygon либо
последовательностью точек/Waypoint-ов; path — LineString либо
последовательность Waypoint-ов/точек.
"""

from __future__ import annotations

import math
from typing import Any, Sequence, Tuple, Union

from shapely.errors import TopologicalError
from shapely.geometry import LineString, Polygon

# Общий тип «точка»
Point = Tuple[float, float]


# ──────────────────────────────────────────────────────────────
#   utils
# ──────────────────────────────────────────────────────────────
def _p(obj: Any) -> Point:
    """
    Приводим произвольный объект к кортежу координат `(x, y)`.

    Поддерживает:
    • (x, y) / [x, y]
    • объект с атрибутами `.lon`, `.lat`
    • объект с атрибутами `.x`, `.y`
    """
    if isinstance(obj, (tuple, list)) and len(obj) >= 2:
        return float(obj[0]), float(obj[1])

    if hasattr(obj, "lon") and hasattr(obj, "lat"):
        return float(obj.lon), float(obj.lat)  # Waypoint

    if hasattr(obj, "x") and hasattr(obj, "y"):
        return float(obj.x), float(obj.y)

    raise TypeError(f"Unsupported point type: {type(obj)!r}")


def _to_polygon(area: Union[Polygon, Sequence[Point]]) -> Polygon:
    """
    Приводим область к Polygon.
    """
    if isinstance(area, Polygon):
        return area
    return Polygon([_p(pt) for pt in area])


def _to_linestring(path: Union[LineString, Sequence[Point]]) -> LineString:
    """
    Приводим маршрут к LineString.
    """
    if isinstance(path, LineString):
        return path
    return LineString([_p(pt) for pt in path])


# ──────────────────────────────────────────────────────────────
#   PUBLIC API
# ──────────────────────────────────────────────────────────────
def coverage_percent(
    area: Union[Polygon, Sequence[Point]],
    path: Union[LineString, Sequence[Point], None] = None,
    altitude_m: float | None = None,
    *,
    fov_deg: float = 70.0,
) -> float:
    """
    Процент покрытия *area* (0-100).

    Parameters
    ----------
    area : Polygon | Sequence[Point]
        Рабочая зона. Polygon **или** список Waypoint-ов / (x, y).
    path : LineString | Sequence[Point] | None
        Маршрут (None ⇒ 0 %).
    altitude_m : float | None
        Высота полёта; если None, полоса шириной 1 м.
    fov_deg : float, default 70
        Горизонтальное FOV камеры.

    Returns
    -------
    float
        Процент покрытия.
    """
    try:
        poly = _to_polygon(area)
    except (TypeError, ValueError):
        return 0.0

    if not poly.is_valid or poly.area == 0:
        return 0.0

    if not path:
        return 0.0

    try:
        line = _to_linestring(path)
    except (TopologicalError, ValueError, TypeError):
        return 0.0

    if line.length == 0:
        return 0.0

    # Ширина «полосы захвата»
    if altitude_m is None:
        buf_half = 0.5  # 1 м шириной «по умолчанию»
    else:
        width = 2.0 * altitude_m * math.tan(math.radians(fov_deg) / 2.0)
        buf_half = max(0.1, width / 2.0)

    try:
        cover = line.buffer(buf_half, cap_style=2)  # плоские окончания
        covered_area = cover.intersection(poly).area
    except TopologicalError:
        return 0.0

    # Гарантируем, что вернётся float
    result = min(covered_area / poly.area * 100.0, 100.0)
    return float(result)
