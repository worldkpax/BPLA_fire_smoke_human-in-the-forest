# fire_uav

**Fire Smoke Human Detection & UAV Mission Planning**

Инструментарий для обнаружения дыма/огня/людей и планирования миссий БПЛА. Используются Ultralytics YOLOv11 (PyTorch), OR-Tools + Shapely для маршрутов, FastAPI для REST, и GUI на PySide6/Qt WebEngine.

---
powershell -ExecutionPolicy Bypass -File scripts/setup_env.ps1
```
Скрипт создаст `.venv`, установит зависимости через Poetry и проверит доступность Qt WebEngine. Добавьте флаг `-RuntimeOnly`, если не нужны dev-зависимости (pytest, pre-commit).

## Запуск GUI
```powershell
poetry run python -m fire_uav.main
```

## Запуск CLI (обработка видео/картинки)
```powershell
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

