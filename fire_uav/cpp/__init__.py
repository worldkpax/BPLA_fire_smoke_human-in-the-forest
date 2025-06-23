"""
Python-обёртка над C++-модулем `route_planner_cpp` (скомпилированным `.pyd`).

▪ Позволяет писать просто `from fire_uav.cpp import follow_path`.

▪ Если бинарь не найдён — бросает понятный `RuntimeError`, а IDE
  перестаёт подсвечивать *Unresolved reference* благодаря заглушке.
"""

from __future__ import annotations

from types import ModuleType
from typing import Any

__all__ = ["follow_path"]

try:
    # Скомпилированный модуль, собранный через CMake / scikit-build
    from . import route_planner_cpp as _native  # type: ignore

    # Экспортируем наружу, чтобы хватило простого импорта
    follow_path: Any = _native.follow_path  # noqa: F401

except (ImportError, AttributeError):

    def follow_path(*_: Any, **__: Any) -> ModuleType:
        """
        Заглушка, вызываемая если бинарный модуль не подгрузился.
        """
        raise RuntimeError(
            "C-extension 'route_planner_cpp' не найден.\n"
            "Соберите C++-часть проекта:\n"
            "    cd fire_uav/cpp && pip install ."
        )
