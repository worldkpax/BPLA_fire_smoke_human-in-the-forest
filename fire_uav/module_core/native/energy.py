from __future__ import annotations

import logging

from fire_uav.module_core.interfaces.energy import IEnergyModel
from fire_uav.module_core.native import NATIVE_AVAILABLE, _native_core
from fire_uav.module_core.schema import Route, TelemetrySample

log = logging.getLogger(__name__)


BATTERY_WH_PLACEHOLDER = 100.0  # TODO: pull from platform config or UAV telemetry


if NATIVE_AVAILABLE:

    class NativeEnergyModel(IEnergyModel):
        """Native-backed energy estimator."""

        def energy_cost(self, route: Route) -> float:
            lats = [wp.lat for wp in route.waypoints]
            lons = [wp.lon for wp in route.waypoints]
            alts = [wp.alt for wp in route.waypoints]
            return float(_native_core.route_energy_cost(lats, lons, alts, 1.0, 1.0))

        def remaining_energy(self, telemetry: TelemetrySample) -> float:
            remaining = telemetry.battery * BATTERY_WH_PLACEHOLDER
            # TODO: refine with actual battery telemetry metrics.
            return float(remaining)

else:

    class NativeEnergyModel(IEnergyModel):  # type: ignore[misc]
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            raise RuntimeError("Native core is not available. Build the C++ extension or disable native usage.")

        def energy_cost(self, route: Route) -> float:
            raise RuntimeError("Native core is not available.")

        def remaining_energy(self, telemetry: TelemetrySample) -> float:
            raise RuntimeError("Native core is not available.")


__all__ = ["NativeEnergyModel", "BATTERY_WH_PLACEHOLDER"]

