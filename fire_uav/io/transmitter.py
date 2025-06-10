"""
Очень простой TCP/UDP передатчик (строки JSON с разделителем `\\n`).
"""
from __future__ import annotations

import json
import logging
import socket
from typing import Any

_log = logging.getLogger(__name__)


class Transmitter:
    def __init__(self, host: str = "127.0.0.1", port: int = 9000, *, udp: bool = False) -> None:
        self.addr = (host, port)
        self.udp = udp
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM if udp else socket.SOCK_STREAM)
        if not udp:
            self.sock.connect(self.addr)
        _log.info("Transmitter connected %s:%d (%s)", host, port, "udp" if udp else "tcp")

    def send(self, obj: Any) -> None:
        data = (json.dumps(obj) + "\n").encode()
        if self.udp:
            self.sock.sendto(data, self.addr)
        else:
            self.sock.sendall(data)

    def close(self) -> None:
        self.sock.close()
