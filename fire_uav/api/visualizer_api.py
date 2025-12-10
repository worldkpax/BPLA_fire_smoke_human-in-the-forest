from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fire_uav.core.protocol import ObjectMessage, RouteMessage, TelemetryMessage

app = FastAPI(title="UAV Visualizer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

last_telemetry: dict[str, TelemetryMessage] = {}
last_route: dict[str, RouteMessage] = {}
last_objects: dict[str, dict[str, ObjectMessage]] = {}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "uav_visualizer_api"}


@app.post("/api/v1/telemetry")
def ingest_telemetry(msg: TelemetryMessage) -> dict[str, str]:
    last_telemetry[msg.uav_id] = msg
    return {"status": "ok"}


@app.post("/api/v1/route")
def ingest_route(msg: RouteMessage) -> dict[str, str]:
    last_route[msg.uav_id] = msg
    return {"status": "ok"}


@app.post("/api/v1/object")
def ingest_object(msg: ObjectMessage) -> dict[str, str]:
    bucket = last_objects.setdefault(msg.uav_id, {})
    bucket[msg.object_id] = msg
    return {"status": "ok"}


@app.get("/api/v1/telemetry/{uav_id}")
def get_telemetry(uav_id: str) -> TelemetryMessage:
    if uav_id not in last_telemetry:
        raise HTTPException(status_code=404, detail="telemetry not found")
    return last_telemetry[uav_id]


@app.get("/api/v1/route/{uav_id}")
def get_route(uav_id: str) -> RouteMessage:
    if uav_id not in last_route:
        raise HTTPException(status_code=404, detail="route not found")
    return last_route[uav_id]


@app.get("/api/v1/objects/{uav_id}")
def get_objects(uav_id: str) -> list[ObjectMessage]:
    bucket = last_objects.get(uav_id, {})
    return list(bucket.values())


__all__ = ["app", "last_telemetry", "last_route", "last_objects"]

