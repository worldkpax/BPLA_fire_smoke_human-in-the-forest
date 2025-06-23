"""Bootstrap и запуск GUI."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

import fire_uav.infrastructure.providers as deps
from fire_uav.bootstrap import init_core
from fire_uav.gui.windows.main_window import MainWindow
from fire_uav.logging_setup import setup_logging


def main() -> None:  # noqa: D401
    setup_logging()
    init_core()  # создаёт очереди, lifecycle, bus-binding

    app = QApplication(sys.argv)
    win = MainWindow()

    # регистрируем только реально существующие компоненты
    for comp in (getattr(win, "cam_thr", None), getattr(win, "det_thr", None)):
        if comp is not None:
            deps.get_lifecycle().register(comp)

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
