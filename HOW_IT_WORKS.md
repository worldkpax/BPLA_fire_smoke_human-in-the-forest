# Как устроен проект **fire\_uav**

> Этот документ — «глубокое погружение» в исходный код.
> Здесь объяснены предназначение каждого каталога, связь модулей, потоки
> выполнения, обмен данными и т. д.  Если вы впервые открыли репозиторий
> и хотите разобраться, как всё работает — начинайте отсюда.

---

## 0. Краткая карта

```
fire_uav/
├── app/          # Qt‑GUI + фоновые потоки/процессы
├── assets/       # svg/иконки для меню
├── config/       # YAML + pydantic‑модели настроек
├── core/         # (зарезервировано) будущий state‑engine
├── cpp/          # C++ ускорители (pybind11)
├── data/         # тестовые видео/геоданные для demo
├── flight/       # маршрутизация, конвертеры, coverage
├── io/           # запись кадров + детекций
├── sim/          # заглушки под AirSim / Gazebo
├── tests/        # pytest
├── ui/           # QSS‑темы, html шаблоны Map/Toast
└── utils/        # разное вспомогательное
```

---

## 1. GUI‑слой (`fire_uav/app/`)

### 1.1 main\_window\.py

* **QMainWindow** с тремя вкладками:

  * `DetectorTab` — превью камеры + YOLO‑детектор.
  * `PlanWidget` — интерактивная карта Leaflet (рассмотрена ниже).
  * `LogTab`     — QTextEdit, куда льётся Python‑лог + JSON событий.
* Создаёт два фоновых потока:

  * **CameraThread** — снимает OpenCV‑кадры, кидает их в очередь.
  * **DetectThread** — достаёт кадры, гоняет YOLO, отправляет сигналы.
* `QtLogHandler` подключён к `logging` и дублирует log‑сообщения в GUI.

### 1.2 plan\_widget.py

Главная «интересная» часть.

| Компонент           | Что делает                                                                                                            |
| ------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **QWebEngineView**  | Показывает html‑страницу с Leaflet, кнопки Draw.                                                                      |
| **Draw plugin**     | Разрешено рисовать **только Polyline**. После генерации тулбар скрывается (JS → `disableDrawing`).                    |
| **Generate Route**  | 1) Из JS берёт GeoJSON линии. 2) Запускает `ProcessPoolExecutor.submit(build_route, …)`.                              |
| **Process‑polling** | QTimer каждые 100 мс проверяет `future.done()`.                                                                       |
| **on result**       | Получает list\[(lat,lon,alt)] — → рисует polyline через `window.addRoute` и конвертирует в `Waypoint` для сохранения. |

> Почему `ProcessPoolExecutor`, а не `QThread`?
> Код планировщика интенсивный (может десятки тысяч точек).
> Если оставить `QThread`, GIL заблокирует GUI. Отдельный процесс решает это.

### 1.3 route\_process.py

* Слой между Python и C++.
* **Получает**: WKT линии + alt.
* **Вызывает** C++ `follow_path()` → возвращает C++‑объекты `Waypoint`.
* **Сериализует** их в кортежи `(lat,lon,alt)` — ProcessPool умеет их
  пиклить без ошибок.

---

## 2. C++‑ускоритель (`fire_uav/cpp/`)

### 2.1 route\_planner.cpp

* **pybind11** модуль `route_planner_cpp`.
* Экспортирует два метода:

  1. `follow_path(path_latlon, alt)` — копирует каждую точку линии в `Waypoint`.
  2. `generate_route(poly_latlon, swath, alt)` — строит «змейку»; сейчас не используется, но сохранён «про запас».
* Использует простую эквиректанг. проекцию → быстро, без зависимостей.
* `py::gil_scoped_release` — вычисления идут вне GIL.

### 2.2 CMakeLists.txt

1‑файловый проект. Выпускает `.pyd`/`.so` в `build/Release`.
Чтобы Python нашёл модуль, его кладут в корень пакета `fire_uav/` **или** устанавливают через `pip install dist/*.whl` (см. README).

---

## 3. Данные и конвертеры (`fire_uav/flight/`)

| Файл             | Содержание                                                                                                 |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| **planner.py**   | `CameraSpec` (fov, sensor), `GridParams`, вспом. функции.                                                  |
| **converter.py** | `dump_qgc(missions, path)` → QGroundControl *.plan* + `mission.txt` (plain MAVLink).                       |
| **coverage.py**  | `coverage_percent(poly, wps, swath)` — геометрия Shapely; пока отключено, т.к. в Polyline‑режиме не нужно. |

---

## 4. Захват и логирование (`fire_uav/io/`, `utils/`)

* **Recorder** (`io/recorder.py`) — сохраняет кадры и JSON‑детекции на диск.
* **logging** централизован через `utils.logging.setup_logging()` + Qt‑хендлер.
* **gui\_toast.py** — маленькие всплывающие уведомления (через `QToolTip`).
* **themes.py** — QSS «Steam Dark / Light».

---

## 5. Потоки, процессы, сигналы (sequence‑diagram)

```
GUI‑thread        CameraThread        DetectThread        ProcessPool
  |    Start          |                   |                   |
  |<------------------|  frame (Qt signal)|                   |
  | queue.put(frame)  |                   |                   |
  |-------------------------------> detect()                  |
  |             detections (Qt signal) ---------------------->| build_route()
  |--------------update_frame()-> VideoPane                   |
  |<------------------------------------------- list[tuple] --|
  |  JS addRoute()  +  disableDrawing()                       |
```

---

## 6. Расширение/изменения

* Чтобы вернуть Polygon‑режим — используйте уже существующий C++‑метод
  `generate_route()` и снимите блокировку в GUI (удалить `disableDrawing`).
* Любая новая геометрия (спираль, grid‑coverage) добавляется в C++ и
  вызывается из `route_process.py` аналогично `follow_path`.
* Для live‑телеметрии подключите `pymavlink`, передавайте данные через Qt‑сигнал в `pyqtgraph`.

---

## 7. Что происходит при «Generate Route»

1. Пользователь рисует линию → GeoJSON хранится в Leaflet.
2. Нажимается кнопка → JS выдаёт GeoJSON в Python.
3. Python сериализует WKT → `ProcessPoolExecutor.submit()`.
4. Другой процесс:

   * `follow_path()` (C++) строит Waypoint‑ы.
   * Кортежи летят обратно через `pickle`.
5. GUI‑таймер ловит результат → рисует линию в JS.
6. Карта фиксируется, кнопка *Save plan* активна.

---

## 8. Настройки (config/)

`settings.yaml` + `pydantic-settings` → единая точка изменения путей
вывода (`output_root`), модели YOLO, параметров камеры.
Для продакшена можно завести `.env` и переопределять переменные.

---

## 9. Тесты

`tests/` содержит **pytest**:

* smoke‑test детектора на статичном кадре;
* проверку, что `follow_path` возвращает правильный порядок точек;
* round‑trip экспорта `dump_qgc`.

Запуск:

```bash
pytest -q
```

---


