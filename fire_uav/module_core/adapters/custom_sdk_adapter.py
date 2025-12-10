from __future__ import annotations

import logging

from fire_uav.module_core.adapters.interfaces import IUavAdapter, IUavTelemetryConsumer
from fire_uav.module_core.schema import Route


class CustomSdkUavAdapter(IUavAdapter):
    """
    Template adapter for client-provided SDKs or bespoke flight software.

    This is intended to be the foundation for paid integration work where the
    client's software is bridged to our internal protocol.
    """

    def __init__(self, client_config: dict, logger: logging.Logger | None = None) -> None:
        """
        client_config may describe how to talk to the client's software:
          - host/port
          - auth tokens
          - protocol: HTTP/gRPC/ZeroMQ/etc.
        """
        self.client_config = client_config
        self.log = logger or logging.getLogger(self.__class__.__name__)
        self._running = False

    async def start(self, telemetry_callback: IUavTelemetryConsumer) -> None:
        """
        TODO:
        - Connect to the client's system.
        - Subscribe to its telemetry feed.
        - Translate client's telemetry into TelemetrySample objects.
        """
        self._running = True
        self.log.info("Custom SDK adapter stub started (config keys=%s)", list(self.client_config))

    async def stop(self) -> None:
        """TODO: Cleanly disconnect from client's software."""
        if not self._running:
            return
        self._running = False
        self.log.info("Custom SDK adapter stub stopped")

    async def push_route(self, route: Route) -> None:
        """
        TODO:
        - Convert Route into whatever mission representation the client's system expects.
        - Send it through the client's API.
        """
        self.log.debug("push_route called (waypoints=%d)", len(route.waypoints))

    async def send_simple_command(self, command: str, payload: dict | None = None) -> None:
        """
        TODO:
        - Map generic commands to client's command API.
        """
        self.log.debug("send_simple_command called: %s payload=%s", command, payload)


__all__ = ["CustomSdkUavAdapter"]

