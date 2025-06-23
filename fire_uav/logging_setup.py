# mypy: ignore-errors
"""
Единая точка включения логов.
Читаем YAML-конфиг `fire_uav/config/logging.yaml`,
правим путь до data/artifacts/logs/fire_uav_debug.log,
добавляем каталог, и запускаем dictConfig.
"""

from __future__ import annotations

import logging.config
from pathlib import Path

import yaml


def setup_logging() -> None:
    """
    Загружает YAML-конфиг и настраивает logging.config.dictConfig.
    """
    # ── 1. Читаем YAML
    cfg_file = Path(__file__).resolve().parents[1] / "fire_uav" / "config" / "logging.yaml"
    with cfg_file.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # ── 2. Готовим каталог для логов
    root_dir = Path(__file__).resolve().parents[1]
    log_dir = root_dir / "data" / "artifacts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # ── 3. Подменяем путь у file-handler’а
    handler = cfg["handlers"].get("debug-file")
    if handler:
        handler["filename"] = str(log_dir / "fire_uav_debug.log")

    # ── 4. Активируем конфигурацию
    logging.config.dictConfig(cfg)
