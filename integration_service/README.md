## Integration Service (stub)

This folder will host thin bridge services (HTTP/gRPC/etc.) that connect client flight software to our backend via `CustomSdkUavAdapter`.

Key notes:
- Bridges should translate client protocols into our internal primitives: `TelemetrySample`, `Route`, and simple commands handled by `IUavAdapter`.
- On-wire schemas should reuse the planned message set (`TelemetryMessage`, `RouteMessage`, `ObjectMessage`) from `core/protocol.py` once that protocol module is formalised.
- The rest of the system (module_core, module_app, ground_app) remains unchanged; only the adapter layer is swapped per client.

