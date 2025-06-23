# fire_uav/sim/airsim_stub.py
from __future__ import annotations

from typing import Any


def start(server_addr: str = "127.0.0.1", port: int = 41451) -> Any:
    """
    Вернуть клиент AirSim. В настоящем коде здесь бы
    было `return airsim.MultirotorClient(server_addr, port)`.
    """
    import importlib

    airsim: Any = importlib.import_module("airsim")  # runtime-импорт
    client: Any = airsim.MultirotorClient(server_addr, port)
    client.confirmConnection()
    return client
