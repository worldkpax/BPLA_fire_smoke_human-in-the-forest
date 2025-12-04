# mypy: ignore-errors
import re

from fastapi.testclient import TestClient

from fire_uav.api.main_rest import app

client = TestClient(app)


def test_metrics_endpoint_ok():
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.text

    # базовые метрики присутствуют
    assert re.search(r"^camera_fps\s+\d+", text, re.MULTILINE)
    assert re.search(r"^detector_latency_seconds_bucket", text, re.MULTILINE)
    assert re.search(r"^detector_queue_size\s+\d+", text, re.MULTILINE)
    assert re.search(r"^coverage_percent\s+\d+(\.\d+)?", text, re.MULTILINE)
