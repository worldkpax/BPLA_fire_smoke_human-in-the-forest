# fire_uav

**Fire Smoke Human Detection & UAV Mission Planning**

Инструментарий для обнаружения дыма/огня/людей и планирования миссий БПЛА. Используются Ultralytics YOLOv11 (PyTorch), OR-Tools + Shapely для маршрутов, FastAPI для REST, и GUI на PySide6/Qt WebEngine.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_env.ps1
```
```bash
bash scripts/setup_env.sh  # macOS/Linux
```
Скрипт создаст `.venv`, установит зависимости через Poetry и проверит доступность Qt WebEngine. Добавьте флаг `-RuntimeOnly` (Windows) или `--runtime-only` (macOS/Linux), если не нужны dev-зависимости (pytest, pre-commit).

## Запуск GUI
```powershell
poetry run python -m fire_uav.main
```

## Запуск CLI (обработка видео/картинки)
powershell
poetry run python -m fire_uav.bootstrap detect `
  --input path\to\video.mp4 `
  --model data\models\fire_detector.pt `
  --output data\outputs\results.mp4
```

## Запуск REST API + метрики
```powershell
poetry run uvicorn fire_uav.api.main_rest:app --host 0.0.0.0 --port 8000
```
Эндпоинты: `POST /start`, `POST /stop`, `GET /status`, `GET /plan`, `GET /metrics` (Prometheus).

## Тесты
```powershell
poetry run pytest --cov=fire_uav --cov-report=term-missing
```

## Native core (C++ ускорения)
- Модуль `cpp/native_core` даёт быстрые гео-утилиты: расстояние, проекция bbox→земля с yaw/pitch/roll и `offset_latlon`.  
- `fire_uav/module_core/detections/pipeline.py` использует `NativeGeoProjector`, когда собран модуль и включён флаг `use_native_core` в `config/settings_default.json` (иначе остаётся Python-реализация); планировщик аналогично переключает `NativeEnergyModel`.
- Трекинг детекций может работать через `native_core.BBoxTracker` (переключение тем же флагом `use_native_core`); в Python остаётся тот же интерфейс `assign_and_smooth`.
- Сборка на Jetson/ARM64:
  ```bash
  cd cpp/native_core
  cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  cmake --build build
  # добавить собранный .so в PYTHONPATH или скопировать рядом с fire_uav/module_core/native_core.*.so
  ```
- Зависимости для сборки на Jetson: `sudo apt install cmake libpython3-dev`, `pip install pybind11`; при сборке внутри venv убедитесь, что активированы нужные include-пути Python.
- Включение в рантайме: поставьте `use_native_core` в `config/settings_default.json` в `true` или пробросьте переменную окружения `FIRE_UAV_ROLE`/конфиг с тем же ключом, чтобы пайплайн и планировщик автоматически выбрали native-модули.
