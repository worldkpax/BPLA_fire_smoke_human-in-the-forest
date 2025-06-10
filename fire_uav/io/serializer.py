"""JSON (де)сериализация, учитывая pydantic-объекты."""
import json
from typing import Any

from pydantic.json import pydantic_encoder


def to_json(obj: Any, *, indent: int | None = None) -> str:
    return json.dumps(obj, default=pydantic_encoder, ensure_ascii=False, indent=indent)


def dump_to_file(obj: Any, path: str | "os.PathLike[str]"):
    import gzip
    from pathlib import Path

    path = Path(path)
    data = to_json(obj)
    if path.suffix == ".gz":
        with gzip.open(path, "wt", encoding="utf-8") as f:
            f.write(data)
    else:
        path.write_text(data, encoding="utf-8")
