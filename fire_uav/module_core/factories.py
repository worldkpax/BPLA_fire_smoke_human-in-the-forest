from __future__ import annotations

import logging

from fire_uav.module_core.energy.python_energy_model import PythonEnergyModel
from fire_uav.module_core.fusion.python_projector import PythonGeoProjector
from fire_uav.module_core.interfaces.energy import IEnergyModel
from fire_uav.module_core.interfaces.geo import IGeoProjector
from fire_uav.module_core.native import NATIVE_AVAILABLE
from fire_uav.module_core.native.energy import NativeEnergyModel
from fire_uav.module_core.native.geo import NativeGeoProjector

log = logging.getLogger(__name__)


def get_geo_projector(settings) -> IGeoProjector:  # noqa: ANN001
    if getattr(settings, "use_native_core", False) and NATIVE_AVAILABLE:
        log.info("Native core enabled for geo.")
        return NativeGeoProjector()
    if getattr(settings, "use_native_core", False) and not NATIVE_AVAILABLE:
        log.warning("Native core requested but unavailable, falling back to PythonGeoProjector.")
    else:
        log.info("Using PythonGeoProjector (native disabled).")
    return PythonGeoProjector()


def get_energy_model(settings) -> IEnergyModel:  # noqa: ANN001
    if getattr(settings, "use_native_core", False) and NATIVE_AVAILABLE:
        log.info("Native core enabled for energy.")
        return NativeEnergyModel()
    if getattr(settings, "use_native_core", False) and not NATIVE_AVAILABLE:
        log.warning("Native core requested but unavailable, falling back to PythonEnergyModel.")
    else:
        log.info("Using PythonEnergyModel (native disabled).")
    return PythonEnergyModel()


__all__ = ["get_geo_projector", "get_energy_model"]

