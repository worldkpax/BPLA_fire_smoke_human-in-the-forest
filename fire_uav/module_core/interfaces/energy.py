from __future__ import annotations

from abc import ABC, abstractmethod

from fire_uav.module_core.schema import Route, TelemetrySample


class IEnergyModel(ABC):
    """Abstract interface for estimating energy usage and remaining energy."""

    @abstractmethod
    def energy_cost(self, route: Route) -> float:
        """Estimate energy needed for this route."""

    @abstractmethod
    def remaining_energy(self, telemetry: TelemetrySample) -> float:
        """Estimate remaining energy in the same units as energy_cost."""

