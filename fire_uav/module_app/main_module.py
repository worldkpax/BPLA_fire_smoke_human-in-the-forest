"""Headless onboard runtime entry point."""

from __future__ import annotations

import asyncio
import logging

from fire_uav.bootstrap import init_core
from fire_uav.logging_setup import setup_logging
from fire_uav.module_app.config import load_module_settings
from fire_uav.module_core.adapters import (
    CustomSdkUavAdapter,
    IUavAdapter,
    IUavTelemetryConsumer,
    MavlinkUavAdapter,
    UnrealSimUavAdapter,
)
from fire_uav.module_core.detections import DetectionAggregator, DetectionPipeline
from fire_uav.module_core.factories import get_energy_model, get_geo_projector
from fire_uav.module_core.route.python_planner import PythonRoutePlanner
from fire_uav.module_core.schema import TelemetrySample
from fire_uav.services.bus import Event, bus
from fire_uav.services.visualizer_adapter import VisualizerAdapter
from fire_uav.services.telemetry.transmitter import Transmitter

log = logging.getLogger(__name__)


class _ModuleTelemetryConsumer(IUavTelemetryConsumer):
    """Feeds telemetry into downstream pipelines and keeps latest sample in memory."""

    def __init__(
        self,
        *,
        pipeline: DetectionPipeline,
        planner: PythonRoutePlanner,
        energy_model: PythonEnergyModel,
        visualizer: VisualizerAdapter | None,
    ) -> None:
        self.pipeline = pipeline
        self.planner = planner
        self.energy_model = energy_model
        self.latest: TelemetrySample | None = None
        self.visualizer = visualizer

    async def on_telemetry(self, sample: TelemetrySample) -> None:
        self.latest = sample
        if self.visualizer:
            await self.visualizer.publish_telemetry(sample)
        log.debug(
            "Telemetry update: lat=%.6f lon=%.6f alt=%.1f batt=%.2f",
            sample.lat,
            sample.lon,
            sample.alt,
            sample.battery,
        )


def _make_transmitter() -> Transmitter | None:
    cfg = load_module_settings()
    if not cfg.ground_station_enabled:
        return None
    try:
        return Transmitter(
            host=cfg.ground_station_host,
            port=cfg.ground_station_port,
            udp=cfg.ground_station_udp,
        )
    except Exception:  # noqa: BLE001
        log.exception("Failed to connect transmitter to ground station")
        return None


def _build_adapter(cfg) -> IUavAdapter:
    backend = (getattr(cfg, "uav_backend", "") or "mavlink").lower()
    if backend == "mavlink":
        return MavlinkUavAdapter(cfg.mavlink_connection_string, logger=log)
    if backend == "unreal":
        return UnrealSimUavAdapter(cfg.unreal_base_url, logger=log)
    if backend == "custom":
        return CustomSdkUavAdapter(cfg.custom_sdk_config, logger=log)
    raise ValueError(f"Unknown uav_backend: {cfg.uav_backend}")


async def _run() -> None:
    """Configure shared services and start headless processing loop."""
    setup_logging()
    cfg = load_module_settings()

    init_core()  # queues + lifecycle; camera/detector threads if camera present

    energy_model = get_energy_model(cfg)
    planner = PythonRoutePlanner(energy_model=energy_model, settings=cfg)
    projector = get_geo_projector(cfg)
    visualizer = VisualizerAdapter(cfg)
    transmitter = _make_transmitter()
    aggregator = DetectionAggregator(
        window=cfg.agg_window,
        votes_required=cfg.agg_votes_required,
        min_confidence=cfg.agg_min_confidence,
        max_distance_m=cfg.agg_max_distance_m,
        ttl_seconds=cfg.agg_ttl_seconds,
    )
    pipeline = DetectionPipeline(
        aggregator=aggregator,
        projector=projector,
        transmitter=transmitter,
        visualizer_adapter=visualizer if getattr(cfg, "visualizer_enabled", False) else None,
        loop=loop,
    )

    adapter = _build_adapter(cfg)
    telemetry_consumer = _ModuleTelemetryConsumer(
        pipeline=pipeline,
        planner=planner,
        energy_model=energy_model,
        visualizer=visualizer if getattr(cfg, "visualizer_enabled", False) else None,
    )

    log.info(
        "Module runtime initialised | backend=%s planner=%s energy=%s projector=%s pipeline=%s",
        getattr(cfg, "uav_backend", "unknown"),
        planner.__class__.__name__,
        energy_model.__class__.__name__,
        projector.__class__.__name__,
        pipeline.__class__.__name__,
    )

    # Start capture/detect threads if available.
    bus.emit(Event.APP_START)
    log.info("Started core lifecycle threads")

    await adapter.start(telemetry_consumer)
    log.info("UAV adapter started (%s)", adapter.__class__.__name__)

    try:
        while True:
            await asyncio.sleep(1.0)
    except (KeyboardInterrupt, asyncio.CancelledError):
        log.info("Stopping module runtime...")
    finally:
        bus.emit(Event.APP_STOP)
        try:
            await adapter.stop()
        except Exception:  # noqa: BLE001
            log.exception("Failed to stop UAV adapter cleanly")
        if transmitter:
            try:
                transmitter.close()
            except Exception:  # noqa: BLE001
                log.exception("Failed to close transmitter socket")
        if getattr(cfg, "visualizer_enabled", False) and visualizer:
            try:
                await visualizer.aclose()
            except Exception:  # noqa: BLE001
                log.exception("Failed to close visualizer adapter")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":  # pragma: no cover
    main()
