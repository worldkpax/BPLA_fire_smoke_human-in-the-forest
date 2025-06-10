from PyQt5.QtWidgets import QTextEdit
import logging


class QtLogHandler(logging.Handler):
    def __init__(self, widget: QTextEdit):
        super().__init__()
        self.widget = widget
        self.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s"))

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)
