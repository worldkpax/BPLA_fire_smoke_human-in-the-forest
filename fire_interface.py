import sys
import socket
import json
import base64
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QTextEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_filename = datetime.now().strftime("fire_log_%Y-%m-%d_%H-%M-%S.txt")
LOG_FILE = os.path.join(log_dir, log_filename)

def append_log(entry: str):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + "\n")

class VideoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Detection — Видео")
        self.image_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def update_image_from_base64(self, image_base64):
        if not image_base64:
            return
        try:
            image_data = base64.b64decode(image_base64)
            q_image = QImage.fromData(image_data)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
        except Exception as e:
            print(f"Ошибка отображения изображения: {e}")

class InfoWindow(QWidget):
    update_data_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Detection — Информация")
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        self.update_data_signal.connect(self.update_data)

    def update_data(self, data):
        try:
            timestamp = data.get("timestamp", "—")
            msg = data.get("message", "")
            detections = data.get("detections", [])
            output = f"⏱ Время: {timestamp}\n📢 Сообщение: {msg}\n"
            if detections:
                det = detections[0]
                output += f"Класс: {det.get('class_id', '?')}\n"
                output += f"Уверенность: {det.get('confidence', 0):.2f}\n"
                coords = det.get("object_coordinates", {})
                output += f"Координаты: {coords.get('latitude', '?')}, {coords.get('longitude', '?')}\n"
                output += f"Азимут: {det.get('object_direction', {}).get('azimuth', '?')}\n"
                output += f"Угол места: {det.get('object_direction', {}).get('elevation', '?')}\n"
            else:
                output += "Объекты не обнаружены."
            self.text_edit.setPlainText(output)
            append_log(output)
        except Exception as e:
            print(f"Ошибка при обновлении текста: {e}")

class SocketServer(QThread):
    def __init__(self, info_window, video_window):
        super().__init__()
        self.info_window = info_window
        self.video_window = video_window

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("127.0.0.1", 5005))
        server_socket.listen(1)
        print("Ожидание подключения клиента...")
        conn, addr = server_socket.accept()
        print(f"Клиент подключён: {addr}")

        buffer = ""
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    try:
                        json_data = json.loads(line)
                        self.info_window.update_data_signal.emit(json_data)
                        self.video_window.update_image_from_base64(json_data.get("image_base64", ""))
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                print(f"Ошибка при получении данных: {e}")
                break

        conn.close()
        print("Клиент отключился")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    video_window = VideoWindow()
    info_window = InfoWindow()

    video_window.resize(640, 480)
    info_window.resize(400, 300)

    video_window.show()
    info_window.show()

    listener = SocketServer(info_window, video_window)
    listener.start()

    sys.exit(app.exec_())