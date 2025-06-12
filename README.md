# fire\_uav

> **fire\_uav** — настольное приложение для подготовки и выполнения автономных миссий БПЛА по поиску очагов пожара, дыма и людей в лесистой местности. Проект объединяет:
>
> * детекцию в реальном времени на YOLO v11 (Ultralytics);
> * планирование и визуализацию маршрута (C++ / pybind11 / Leaflet);
> * экспорт миссии в QGroundControl / DJI;
> * удобный GUI на PyQt5.



---

## 1  Установка

```bash
# 1 — виртуальное окружение
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2 — зависимости
pip install -r requirements.txt                     # CUDA‑сборку torch устанавливайте вручную

# 3 — Сборка C++‑модуля (Windows MSVC / Ninja) !НЕОБЯЗАТЕЛЬНО!
cd fire_uav/cpp
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release \
      -DPYTHON_EXECUTABLE=%VIRTUAL_ENV%/Scripts/python.exe
cmake --build build --config Release               # → route_planner_cpp*.pyd

# 4 — Запуск GUI
python -m fire_uav.app.main_window
```

### Примечания

* **CUDA** — скачайте соответствующий whl с [https://download.pytorch.org/whl](https://download.pytorch.org/whl) и установите `pip install torch‑2.2.1+cu121*.whl`.
* На Linux/macOS замените MSVC на `gcc/clang`, флаги те же:

  ```bash
  sudo apt install build-essential ninja-build cmake
  cd fire_uav/cpp && cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)
  ```

---

## 2  Запуск и интерфейс

| Вкладка         | Назначение                                                                                                                                                                                                                                                                                                                                          |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Detector**    | Захват видео + детекция YOLO v11. Слайдер «Conf» — порог уверенности. Start / Stop запускают/останавливают оба потока. Кадры и JSON‑детекции пишутся в `output_root`.                                                                                                                                                                               |
| **Flight Plan** | Встроенная карта Leaflet. Нарисуйте **Broken Line** (Polyline) → *Generate Route* строит точную последовательность Waypoint‑ов в фоновом процессе и наслаивает её на карту. После генерации рисование блокируется, чтобы избежать случайных изменений. *Save plan* сохраняет `artifacts/mission.plan` (формат QGC) и `mission.txt` (plain MAVLink). |
| **Log / JSON**  | Лог Python и JSON‑события (детекции, маршрут, служебные сообщения).                                                                                                                                                                                                                                                                                 |



---

## 3  Структура репозитория

```
fire_uav/
├── app/           # Qt‑виджеты, main_window, планировщик маршрута (GUI)
├── assets/        # svg/иконки для меню
├── config/        # YAML / pydantic‑настройки
├── core/          # (зарезервировано под будущий бэкенд состояния)
├── cpp/           # route_planner.cpp + CMakeLists.txt
├── data/          # примеры GeoJSON / видео
├── flight/        # CameraSpec, coverage, конвертеры
├── io/            # запись видео и детекций
├── sim/           # AirSim / Gazebo (заглушки)
├── tests/         # pytest‑тесты
├── ui/            # QSS‑темы, html‑шаблоны
└── utils/         # логирование, toast‑нотификации, misc.
```

---

## 4  Технические детали

* **C++‑модуль** `route_planner_cpp` (pybind11) содержит две функции:

  * `follow_path(path_latlon, altitude)` — возвращает Waypoint‑ы ровно по нарисованной линии.
  * `generate_route(poly_latlon, swath, altitude)` — простая «змейка» (оставлена «про запас»).
* Все тяжёлые вычисления выполняются в `ProcessPoolExecutor`, GUI не блокируется.
* Данные между процессами передаются как кортежи `(lat, lon, alt)` — без проблем пиклирования.

---

