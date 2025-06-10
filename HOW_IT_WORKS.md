# HOW IT WORKS ⚙️

> 15‑минутное погружение в кодовую базу fire\_uav

---

## 1. Обзор слоёв

```
fire_uav/
│
├─ core/      # геометрия + детектор + DTO
├─ flight/    # планировщик грид‑покрытия, энергомодель, экспорт QGC
├─ io/        # запись jpg/json, UDP/TCP отправка
├─ ui/        # CLI и PyQt‑GUI (тёмная тема)
├─ utils/     # логирование, Qt‑лог‑хэндлер
└─ tests/     # pytest
```

* **core.geometry.py** — `haversine_m`, `offset_latlon` без зависимостей.
* **core.detection.py** — тонкая обёртка над Ultralytics, фильтр классов, auto‑GPU.
* **flight.planner.py** — генерирует грид‑линии, TSP, делит по батареям.
* **flight.converter.py** — миссия → QGroundControl JSON.

Компоненты общаются через Pydantic‑DTO `Detection`, `DetectionsBatch`.

---

## 2. Запуск потоков

```
   (Thread)                (Main Qt‑thread)
┌─────────────┐      ┌─────────────────────────┐
│  cv2.Video   │ →   │  infer() YOLOv11        │
│  capture     │      │  draw bbox             │
└─────────────┘      │  QImage → QLabel       │
       ▲              └─────────────────────────┘
       │ queue(1)                   │ FPS label
```

*Граббер* кладёт последний кадр в очередь; UI берёт, детектит, рисует.

---

## 3. Порог уверенности On‑the‑fly

`app.py` → `QSlider` меняет `self.engine._yolo.overrides["conf"]` без
рестарта модели.

---

## 4. Экспорт маршрута

```python
from fire_uav.flight.planner import FlightPlanner
from fire_uav.flight.converter import dump_qgc

missions = FlightPlanner(aoi_polygon).generate()
dump_qgc(missions, "mission.plan")
```

Файл совместим с QGroundControl ≥ v4.2.

---

## 5. Как добавить свой трекер

1. Наследуйте `fire_uav.core.tracker.BaseTracker` и реализуйте
   `update(list[Detection], frame) -> list[Detection]`.
2. В GUI добавьте вызов трекера между `infer()` и `_draw_dets()`.

---


**Готово!** Теперь вы понимаете, где что лежит и как это связать.
