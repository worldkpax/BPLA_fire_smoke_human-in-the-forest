import cv2
import socket
import json
import math
import base64
import numpy as np
from datetime import datetime
from ultralytics import YOLO

model = YOLO("best_yolo11.pt")

cap = cv2.VideoCapture(0)

camera_params = {
    "fov_horizontal": 70.0,
    "fov_vertical": 60.0,
    "gps_coordinates": {"latitude": 55.7558, "longitude": 37.6173},
    "azimuth": 90.0,
    "elevation": 0.0
}

def get_object_angles(x_pixel, y_pixel, image_width, image_height, fov_horizontal, fov_vertical):
    center_x = image_width / 2
    center_y = image_height / 2
    delta_x = x_pixel - center_x
    delta_y = center_y - y_pixel
    angle_x = (delta_x / center_x) * (fov_horizontal / 2)
    angle_y = (delta_y / center_y) * (fov_vertical / 2)
    return angle_x, angle_y

def calculate_object_coordinates(gps_coordinates, azimuth, elevation, distance):
    azimuth_rad = math.radians(azimuth)
    elevation_rad = math.radians(elevation)
    delta_x = distance * math.cos(elevation_rad) * math.sin(azimuth_rad)
    delta_y = distance * math.cos(elevation_rad) * math.cos(azimuth_rad)
    delta_z = distance * math.sin(elevation_rad)
    earth_radius = 6378137.0
    delta_latitude = (delta_z / earth_radius) * (180 / math.pi)
    delta_longitude = (
        delta_x / (earth_radius * math.cos(math.pi * gps_coordinates['latitude'] / 180))
    ) * (180 / math.pi)
    return {
        "latitude": gps_coordinates['latitude'] + delta_latitude,
        "longitude": gps_coordinates['longitude'] + delta_longitude
    }

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 5005))

frame_count = 0
buffer = ""

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % 2 != 0:
        continue

    resized = cv2.resize(frame, (640, 640))
    results = model(source=resized, save=False, verbose=False, device="cpu")

    detections = []
    for result in results:
        if result.boxes is None or not result.boxes.xyxy.shape[0]:
            continue
        for box in result.boxes:
            if not hasattr(box, 'xyxy') or box.xyxy.shape[0] == 0:
                continue
            class_id = int(box.cls)
            confidence = box.conf.item()
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            angle_x, angle_y = get_object_angles(center_x, center_y, frame.shape[1], frame.shape[0],
                                                 camera_params['fov_horizontal'], camera_params['fov_vertical'])

            azimuth = (camera_params['azimuth'] + angle_x) % 360
            elevation = camera_params['elevation'] + angle_y
            distance = 100.0

            coords = calculate_object_coordinates(camera_params['gps_coordinates'], azimuth, elevation, distance)

            detections.append({
                "timestamp": datetime.now().isoformat(),
                "class_id": class_id,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2],
                "gps_coordinates": camera_params['gps_coordinates'],
                "camera_direction": {
                    "azimuth": camera_params['azimuth'],
                    "elevation": camera_params['elevation']
                },
                "object_direction": {
                    "azimuth": azimuth,
                    "elevation": elevation
                },
                "object_coordinates": coords
            })

    _, buffer_img = cv2.imencode('.jpg', frame)
    image_base64 = base64.b64encode(buffer_img).decode('utf-8')

    payload = {
        "timestamp": datetime.now().isoformat(),
        "message": "Object(s) detected" if detections else "No objects detected",
        "detections": detections,
        "image_base64": image_base64
    }

    try:
        sock.sendall((json.dumps(payload) + "\n").encode('utf-8'))
    except Exception as e:
        print(f"Ошибка отправки: {e}")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
sock.close()
cv2.destroyAllWindows()