"""Configuration loading. A user copy lives in the data folder and is merged over the defaults."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).with_name("default_config.json")


def data_dir() -> Path:
    """Where config, daily usage files and reports are stored."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".config"
    path = base / "RASAVIGIL"
    path.mkdir(parents=True, exist_ok=True)
    (path / "usage").mkdir(exist_ok=True)
    (path / "reports").mkdir(exist_ok=True)
    return path


def user_config_path() -> Path:
    return data_dir() / "config.json"


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config() -> dict:
    defaults = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    path = user_config_path()
    if not path.exists():
        path.write_text(json.dumps(defaults, indent=2), encoding="utf-8")
        return defaults
    try:
        user = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaults
    return _merge(defaults, user)
