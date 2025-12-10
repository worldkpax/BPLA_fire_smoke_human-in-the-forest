from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Protocol

from fire_uav.module_core.schema import Route, TelemetrySample


class IUavTelemetryConsumer(Protocol):
    async def on_telemetry(self, sample: TelemetrySample) -> None:
        """Called when new telemetry is received from the UAV."""


class IUavAdapter(ABC):
    """
    Abstract adapter between module_app and a concrete UAV backend
    (real autopilot, simulator like Unreal/AirSim, or client's software).
    """

    @abstractmethod
    async def start(self, telemetry_callback: IUavTelemetryConsumer) -> None:
        """
        Start the adapter and begin receiving telemetry.
        The adapter must call telemetry_callback.on_telemetry(sample)
        whenever new telemetry is available.
        """

    @abstractmethod
    async def stop(self) -> None:
        """Stop the adapter and release resources."""

    @abstractmethod
    async def push_route(self, route: Route) -> None:
        """
        Send or update the current route/mission on the UAV side.
        For a real autopilot this may upload a mission, for a simulator it may
        set a path to follow.
        """

    @abstractmethod
    async def send_simple_command(self, command: str, payload: dict | None = None) -> None:
        """
        Send a simple control command, e.g.:
          - "ARM", "DISARM"
          - "TAKEOFF", "LAND"
          - "ABORT_MISSION"
        Exact mapping is up to concrete adapters.
        """

