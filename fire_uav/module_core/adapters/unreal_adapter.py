from __future__ import annotations

import logging

from fire_uav.module_core.adapters.interfaces import IUavAdapter, IUavTelemetryConsumer
from fire_uav.module_core.schema import Route


class UnrealSimUavAdapter(IUavAdapter):
    """
    Skeleton adapter for Unreal-based simulators (including AirSim-style bridges).

    Designed to talk to an external bridge process over HTTP/WebSocket.
    """

    def __init__(self, base_url: str, logger: logging.Logger | None = None) -> None:
        """
        base_url: where the Unreal-side bridge is listening, e.g.
            - "http://127.0.0.1:9000" for HTTP/WebSocket bridge,
            - or a WebSocket URL if you use WS directly.
        """
        self.base_url = base_url
        self.log = logger or logging.getLogger(self.__class__.__name__)
        self._running = False

    async def start(self, telemetry_callback: IUavTelemetryConsumer) -> None:
        """
        TODO:
        - Connect to Unreal bridge (HTTP polling or WebSocket).
        - Periodically fetch or receive telemetry from the simulated UAV pawn.
        - For each update, produce TelemetrySample and call telemetry_callback.on_telemetry(sample).
        """
        self._running = True
        self.log.info("Unreal adapter stub started (base_url=%s)", self.base_url)

    async def stop(self) -> None:
        """TODO: Close network connections and stop background tasks."""
        if not self._running:
            return
        self._running = False
        self.log.info("Unreal adapter stub stopped")

    async def push_route(self, route: Route) -> None:
        """
        TODO:
        - Send the route as JSON (e.g. via HTTP POST /set_route) to Unreal bridge.
        - The Unreal side should then move the pawn along this route.
        """
        self.log.debug("push_route called (waypoints=%d)", len(route.waypoints))

    async def send_simple_command(self, command: str, payload: dict | None = None) -> None:
        """
        TODO:
        - Forward simple commands to the Unreal bridge (e.g. \"RESET\", \"PAUSE\", \"RESUME\").
        """
        self.log.debug("send_simple_command called: %s payload=%s", command, payload)


__all__ = ["UnrealSimUavAdapter"]

