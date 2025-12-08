# HOW IT WORKS — ПОЛНОЕ ОПИСАНИЕ ПРОЕКТА

В этом документе подробно описана внутренняя архитектура `fire_uav` 2.0: от инициализации до взаимодействия компонентов. Даже если вы впервые открываете проект, после прочтения поймёте, как устроен код и где искать нужные участки.

---

## 1. Общая схема работы

```text
┌──────────┐     ┌────────────┐     ┌───────────┐
│ Bootstrap│──► │ Providers  │──► │ EventBus  │
└──────────┘     └────────────┘     └────┬──────┘
                                         │
                                         ▼
                          ┌───────────┐  ┌──────────┐
                          │ Detection │  │ Planning │
                          └────┬──────┘  └────┬─────┘
                               │              │
                               ▼              ▼
                          ┌──────────┐    ┌─────────┐
                          │ Outputs  │    │ Metrics │
                          └────┬─────┘    └────┬────┘
                               │              │
         ┌──────────────┐      ▼              ▼     ┌────────┐
         │ REST API     │◄────┼───────────────┼────►│ Prom.  │
         │ (FastAPI)    │      │               │    │Client  │
         └──────────────┘      │               │    └────────┘
                               ▼               ▼
                          ┌──────────┐    ┌─────────┐
                          │ GUI (MVVM)│    │ Tests   │
                          └──────────┘    └─────────┘
```

1. **Bootstrap** — точка входа: CLI, REST API или GUI.
2. **Providers** инициализируют «камеры», «детекторы», очереди и управляют жизненным циклом.
3. **EventBus** передаёт события между компонентами: детектирование, планирование, логирование.
4. **Core**:

   * **Detection**: поток камеры → очередь → YOLO-детектор → публикация результатов.
   * **Planning**: слушает события детекции, строит маршруты с помощью OR-Tools и Shapely.
5. **Outputs & Metrics**: результаты сохраняются в `data/outputs`, логи в `data/artifacts`, метрики идут в Prometheus.
6. **REST API** (FastAPI) и **GUI** (Qt Quick на PySide6) позволяют управлять и визуализировать работу системы.
7. **Tests** + **CI**: покрытие ≥ 80%, проверки через GitHub Actions.

---

## 2. Bootstrap & Инициализация

* **Файл**: `fire_uav/bootstrap.py`
* **Задачи**:

  1. Парсинг аргументов CLI (detect, plan, gui, api).
  2. Чтение конфигов из `fire_uav/config/*.yaml`.
  3. Настройка путей: `paths.py` (`PROJECT_ROOT`, `DATA_DIR`, `ARTIFACTS_DIR`, `MODELS_DIR`, `OUTPUTS_DIR`).
  4. Запуск `init_core()`:

     * Создание провайдеров (камера, детектор).
     * Регистрация компонентов в `LifecycleManager`.
     * Подключение `EventBus`.

Пример:

```python
if mode == "detect":
    core = init_core(headless=True)
    core.run_detection_loop()
```

---

## 3. Providers & Lifecycle

### Providers (`infrastructure/providers.py`)

* **CameraProvider**: читает кадры (файл, RTSP) и пушит в очередь.
* **DetectorFactory**: создаёт экземпляры YOLOv11 для каждого потока.
* **LifecycleManager**: стартует и аккуратно завершает все потоки/сервисы.

Процесс регистрации:

1. В `init_core()` провайдер создаётся и передаётся **LifecycleManager**.
2. `LifecycleManager.start_all()` запускает методы `start()` у провайдеров.
3. При завершении — `stop_all()`, закрывает очереди и потоки.

---

## 4. EventBus (pub-sub)

* **Файл**: `fire_uav/services/bus.py`
* **Принцип**: единая шина событий с жёстко типизированными `Enum`-событиями.
* **Подписчики**: компоненты регистрируются на интересующие события.
* **Публикация**: `bus.publish(Event.FRAME, frame_data)`.
* **Логирование**: каждый подписчик может логировать события по своему конфику.

---

## 5. Detection Core

### Поток обработки

1. **CameraProvider** читает кадр ➔ очередь `frame_queue`.
2. **DetectThread** берёт кадры из `frame_queue`, вызывает `ULTRALYTICS_MODEL.predict()`.
3. Результаты (bounding boxes, классы) публикуются: `bus.publish(Event.DETECTION, result)`.

### Модули

* `fire_uav/core/detection.py`: обёртка над Ultralytics, постобработка.
* `fire_uav/core/utils.py`: вспомогательные функции (NMS, фильтрация).

---

## 6. Planning Core

1. Слушает `Event.DETECTION` только по классам «огонь», «дым».
2. Преобразует координаты detections в геопространственные объекты (Shapely).
3. С помощью OR-Tools строит безопасный маршрут, избегая зон риска.
4. Публикует маршрут: `bus.publish(Event.PLAN, path_coords)` и сохраняет в `data/artifacts/mission.plan`.

Файлы:

* `fire_uav/core/planning.py`
* `fire_uav/core/geometry.py`

---

## 7. REST API

* **Файл**: `fire_uav/api/main_rest.py`
* **Фреймворк**: FastAPI + Uvicorn.
* **Эндпойнты**:

  * `POST /start` — запускает core в headless-режиме.
  * `POST /stop` — останавливает все сервисы.
  * `GET /status` — статус (уведомления, uptime).
  * `GET /plan` — возвращает последний маршрут.
  * `GET /metrics` — Prometheus-экспозиция (FPS, задержка, размеры очередей).

---

## 8. GUI (MVVM)

* **Задача**: отделить логику (ViewModel) от представления (View).
* **Структура**:

  * `fire_uav/gui/viewmodels/` содержит `DetectorVM`, `PlannerVM`, которые слушают `EventBus`.
  * `fire_uav/gui/views/` содержит Qt Quick/QML UI, элементы управления.
* **Взаимодействие**:

  1. Пользователь нажимает «Start» ➔ VM вызывает `bootstrap.init_core().run()`.
  2. VM подписан на события детекции/планирования и обновляет View (мешки, карта).

---

## 9. Логи и Метрики

* **Логи**: настраиваются через `config/logging.yaml`, пишутся в `data/artifacts/logs/`.
* **Метрики**: реализованы через `prometheus_client`:

  * `Counter` и `Gauge` для FPS, латентности, очередей.
  * Эндпойнт `/metrics` доступен в API/server.

---

## 10. Тестирование и CI

* **Тесты**: в `fire_uav/tests/` (pytest, фикстуры, monkeypatch).
* **Покрытие**: отчёт HTML и минимум 80%.
* **CI**: GitHub Actions (`.github/workflows/ci.yml`):

  1. pre-commit (Black, isort, Mypy, Flake8).
  2. pytest + coverage.
  3. публикация отчётов.
  4. сборка Docker-образа.

---

