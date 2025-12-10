## UAV Visualizer API (for Unreal / tools)

The visualizer API exposes lightweight UAV state (telemetry, route, confirmed objects) for external engines such as Unreal. Run it on the ground machine (e.g. `uvicorn fire_uav.api.visualizer_api:app --host 0.0.0.0 --port 8000`).

Base URL: `http://127.0.0.1:8000`

### Endpoints

- `GET /api/v1/telemetry/{uav_id}` – latest telemetry  
  Example response:
  ```json
  {
    "type": "telemetry",
    "uav_id": "uav1",
    "timestamp": "2024-01-01T12:00:00Z",
    "lat": 55.0,
    "lon": 37.0,
    "alt": 120.0,
    "yaw": 90.0,
    "battery": 0.82
  }
  ```

- `GET /api/v1/route/{uav_id}` – current route  
  ```json
  {
    "type": "route",
    "uav_id": "uav1",
    "version": 1,
    "waypoints": [
      { "lat": 55.0, "lon": 37.0, "alt": 120.0 },
      { "lat": 55.001, "lon": 37.002, "alt": 120.0 }
    ],
    "active_index": 0
  }
  ```

- `GET /api/v1/objects/{uav_id}` – confirmed objects list  
  ```json
  [
    {
      "type": "object",
      "uav_id": "uav1",
      "object_id": "obj_000001",
      "class_id": 1,
      "confidence": 0.91,
      "lat": 55.0005,
      "lon": 37.0005,
      "alt": 90.0,
      "status": "confirmed"
    }
  ]
  ```

### Message fields
- **TelemetryMessage:** `type`, `uav_id`, `timestamp`, `lat`, `lon`, `alt`, `yaw`, `battery`.
- **RouteMessage:** `type`, `uav_id`, `version`, `waypoints[] {lat, lon, alt}`, `active_index`.
- **ObjectMessage:** `type`, `uav_id`, `object_id`, `class_id`, `confidence`, `lat`, `lon`, `alt`, `status`.

### Using with Unreal Engine Blueprints
1. Add an HTTP plugin (e.g. VaRest). Poll endpoints every 0.1–0.2 s.
2. Parse JSON into Blueprint structs (TelemetryMessage, RouteMessage, ObjectMessage).
3. Move your UAV actor along `route.waypoints`, highlighting `active_index`.
4. Spawn markers/decals for entries from `/objects/{uav_id}`.

Flat-earth lat/lon → Unreal mapping (choose reference `lat0`, `lon0` at level load):
- `dLat = lat - lat0`
- `dLon = lon - lon0`
- `y_m = dLat * 111000`
- `x_m = dLon * 111000 * cos(lat0 radians)`
- Map to Unreal (1 UU = 1 cm): `X = x_m * 100`, `Y = y_m * 100`, `Z = alt * 100`.

The API is read-only for visualization; mission logic stays in Python (module/ground apps).

