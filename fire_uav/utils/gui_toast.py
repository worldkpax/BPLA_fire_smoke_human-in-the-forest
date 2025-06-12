from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer

def show_toast(parent: QWidget, text: str, msec: int = 1800):
    """Неблокирующее всплывающее сообщение."""
    lab = QLabel(text, parent, objectName="toast")
    lab.setAttribute(Qt.WA_TransparentForMouseEvents)
    lab.adjustSize()

    geo = parent.rect()
    lab.move((geo.width() - lab.width()) // 2,
             geo.height() - lab.height() - 50)
    lab.setWindowOpacity(0)
    lab.show()

    fade_in = QPropertyAnimation(lab, b"windowOpacity", parent)
    fade_in.setDuration(250)
    fade_in.setStartValue(0)
    fade_in.setEndValue(1)
    fade_in.setEasingCurve(QEasingCurve.OutCubic)
    fade_in.start()

    def fade_out():
        fade = QPropertyAnimation(lab, b"windowOpacity", parent)
        fade.setDuration(400)
        fade.setStartValue(1)
        fade.setEndValue(0)
        fade.finished.connect(lab.deleteLater)
        fade.start()

    QTimer.singleShot(msec, fade_out)
