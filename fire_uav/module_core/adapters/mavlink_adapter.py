from __future__ import annotations

import logging

from fire_uav.module_core.adapters.interfaces import IUavAdapter, IUavTelemetryConsumer
from fire_uav.module_core.schema import Route


class MavlinkUavAdapter(IUavAdapter):
    """
    Skeleton MAVLink adapter for real drones (PX4/ArduPilot).

    Intended to be expanded with pymavlink/DroneKit or similar libraries.
    """

    def __init__(self, connection_string: str, logger: logging.Logger | None = None) -> None:
        """
        connection_string examples:
          - "udp:127.0.0.1:14550"
          - "serial:/dev/ttyACM0:57600"
        """
        self.connection_string = connection_string
        self.log = logger or logging.getLogger(self.__class__.__name__)
        self._running = False

    async def start(self, telemetry_callback: IUavTelemetryConsumer) -> None:
        """
        TODO:
        - Connect to MAVLink endpoint.
        - Spawn a reader loop that parses MAVLink messages.
        - On each update, build TelemetrySample and call telemetry_callback.on_telemetry(sample).
        """
        self._running = True
        self.log.info("Mavlink adapter stub started (connection=%s)", self.connection_string)

    async def stop(self) -> None:
        """TODO: Close connection and stop background tasks."""
        if not self._running:
            return
        self._running = False
        self.log.info("Mavlink adapter stub stopped")

    async def push_route(self, route: Route) -> None:
        """
        TODO:
        - Convert Route into a MAVLink mission or guided waypoints.
        - Upload to the autopilot.
        """
        self.log.debug("push_route called (waypoints=%d)", len(route.waypoints))

    async def send_simple_command(self, command: str, payload: dict | None = None) -> None:
        """
        TODO:
        - Map simple command names to MAVLink commands (e.g. MAV_CMD_COMPONENT_ARM_DISARM).
        """
        self.log.debug("send_simple_command called: %s payload=%s", command, payload)


__all__ = ["MavlinkUavAdapter"]

