import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(*, debug: bool = False, file: str | None = None) -> None:
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s | %(levelname)8s | %(name)s:%(lineno)d > %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if file:
        Path(file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(file))
    logging.basicConfig(level=level, format=fmt, handlers=handlers)

    # Приглушаем болтливые библиотеки
    logging.getLogger("ultralytics").setLevel(logging.WARNING)
    logging.getLogger("shapely").setLevel(logging.WARNING)
