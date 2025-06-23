"""Сериализация метаданных кадров в JSON (правились только аннотации)."""

from __future__ import annotations

import json
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List


def to_json(frames: List[Dict[str, Any]]) -> str:
    """Вернуть JSON-строку с отступами."""
    return json.dumps(frames, indent=2, ensure_ascii=False)


def dump_to_file(frames: List[Dict[str, Any]], path: PathLike[str]) -> None:
    """Сохранить метаданные кадров в `path` (UTF-8)."""
    Path(path).write_text(to_json(frames), encoding="utf-8")
