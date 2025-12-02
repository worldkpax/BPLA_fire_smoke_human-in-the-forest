from __future__ import annotations

import logging
from typing import cast

from PySide6.QtWidgets import QTextEdit


class QtLogHandler(logging.Handler):
    """
    Перенаправляет лог-сообщения в QTextEdit.
    Работает только из GUI-потока!
    """

    def __init__(self, widget: QTextEdit) -> None:
        super().__init__()
        self.widget = widget
        self.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        self.widget.append(self.format(record))


def attach_handler(widget: QTextEdit) -> None:
    """
    Подключает QtLogHandler к root-логгеру (только один раз).
    """
    root = logging.getLogger()
    for h in root.handlers:
        if isinstance(h, QtLogHandler) and cast(QtLogHandler, h).widget is widget:
            return
    root.addHandler(QtLogHandler(widget))


__all__ = ["attach_handler"]
