from prometheus_client import REGISTRY, Gauge, Histogram

# Camera / detector
fps_gauge = Gauge("camera_fps", "Frames per second from camera")
detect_latency = Histogram(
    "detector_latency_seconds",
    "Time spent in DetectionEngine.detect()",
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2),
)
queue_size = Gauge("detector_queue_size", "Items in detection queue")

# Planner
coverage_percent = Gauge("coverage_percent", "Planner coverage %")

__all__ = [
    "fps_gauge",
    "detect_latency",
    "queue_size",
    "coverage_percent",
    "REGISTRY",
]
