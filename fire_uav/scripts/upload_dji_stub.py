#!/usr/bin/env python3
# fire_uav/scripts/upload_dji_stub.py
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Загрузить полётный лог в DJI — пока просто выводим аргументы."""
    if len(sys.argv) != 2:
        print("usage: upload_dji_stub.py <log.bin>")
        sys.exit(1)

    log: Path = Path(sys.argv[1])
    if not log.is_file():
        print(f"no such file: {log}")
        sys.exit(1)

    # TODO: real upload here
    print(f"✓ stub-uploaded {log} to DJI cloud")


if __name__ == "__main__":
    main()
