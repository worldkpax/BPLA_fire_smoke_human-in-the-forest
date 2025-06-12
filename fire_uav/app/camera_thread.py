from PyQt5.QtCore import QThread, pyqtSignal
import cv2, time


class CameraThread(QThread):
    frame = pyqtSignal(object)   # numpy.ndarray (BGR)

    def __init__(self, src=0, fps=30):
        super().__init__()
        self.src = src
        self.period = 1 / fps
        self._running = True

    def run(self):
        cap = cv2.VideoCapture(self.src)
        while self._running:
            ok, frame = cap.read()
            if ok:
                self.frame.emit(frame)
            time.sleep(self.period)

    def stop(self):
        self._running = False
