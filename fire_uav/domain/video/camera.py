from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final


# ──────────────────────────────────────────────────────────────────────────────
# Параметры оптики
# ──────────────────────────────────────────────────────────────────────────────
@dataclass(slots=True)
class CameraParams:
    """
    Оптические параметры камеры (по умолчанию – DJI Mini 4 Pro) + утилиты
    для расчёта GSD и полосы охвата.
    """

    sensor_width_mm: float = 6.3
    resolution_px: int = 8_064  # длинная сторона
    focal_length_mm: float = 5.7
    fov_deg: float = 82.1  # диагональ, °

    # ─────────── производные значения ─────────── #
    def gsd_cm_per_px(self, altitude_m: float) -> float:
        """Ground-sampling distance, cm/px, на высоте ``altitude_m``."""
        return 100 * altitude_m * self.sensor_width_mm / (self.focal_length_mm * self.resolution_px)

    def swath_m(self, altitude_m: float) -> float:
        """Ширина охвата (по диагонали) при заданной высоте, м."""
        return 2 * altitude_m * math.tan(math.radians(self.fov_deg / 2))


# ──────────────────────────────────────────────────────────────────────────────
# Минимальный класс Camera – только то, что нужно тестам
# ──────────────────────────────────────────────────────────────────────────────
class Camera:
    """
    Заглушка камеры, удовлетворяющая тестам (`open`, `close`, `is_open`).

    Если позже понадобится полноценная работа с видео-потоком ‒ расширяйте
    этот класс или подменяйте его реализацией, но оставляйте тот же API.
    """

    _DEFAULT_NAME: Final[str] = "Camera"

    def __init__(self, params: CameraParams | None = None) -> None:
        self.params: CameraParams = params or CameraParams()
        self._opened: bool = False

    # --- публичные методы ----------------------------------------------------
    def open(self) -> None:
        """Открыть камеру (эмуляция)."""
        self._opened = True

    def close(self) -> None:
        """Закрыть камеру (эмуляция)."""
        self._opened = False

    # --- свойства ------------------------------------------------------------
    @property
    def is_open(self) -> bool:
        """True ‒ камера открыта, False ‒ закрыта."""
        return self._opened


__all__ = ["Camera", "CameraParams"]
