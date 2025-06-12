from pathlib import Path
import json, os, importlib.resources as pkg

def load_settings() -> dict:
    # ① сначала — путь в переменной окружения
    env = os.environ.get("FIRE_UAV_SETTINGS")
    if env and Path(env).expanduser().exists():
        return json.load(open(env, encoding="utf-8"))

    # ② иначе берём …/fire_uav/config/settings_default.json
    root = Path(__file__).resolve().parents[2]          # fire_uav/
    cfg = root / "fire_uav" / "config" / "settings_default.json"
    if not cfg.exists():
        raise FileNotFoundError(f"Settings file not found: {cfg}")
    return json.load(cfg.open(encoding="utf-8"))
