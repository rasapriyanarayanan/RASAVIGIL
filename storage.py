"""Daily usage storage, one JSON file per day."""
from __future__ import annotations

import json
import threading
import time
from datetime import date
from pathlib import Path


def empty_day(day: str) -> dict:
    return {
        "date": day,
        "apps": {},          # name -> {"seconds": float, "category": str}
        "categories": {},    # category -> seconds
        "warnings": 0,
        "max_level": 0,
        "episodes": [],      # {"app", "seconds", "level"}
    }


class UsageStore:
    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._last_flush = time.monotonic()
        self.day = date.today().isoformat()
        self.data = self._load(self.day)

    def path_for(self, day: str) -> Path:
        return self.folder / f"{day}.json"

    def _load(self, day: str) -> dict:
        p = self.path_for(day)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        return empty_day(day)

    def load_day(self, day: str) -> dict:
        return self.data if day == self.day else self._load(day)

    def _roll_over(self):
        today = date.today().isoformat()
        if today != self.day:
            self.flush()
            self.day, self.data = today, self._load(today)

    def add(self, app: str, category: str, seconds: float):
        if seconds <= 0:
            return
        with self._lock:
            self._roll_over()
            rec = self.data["apps"].setdefault(app, {"seconds": 0.0, "category": category})
            rec["seconds"] += seconds
            rec["category"] = category
            cats = self.data["categories"]
            cats[category] = cats.get(category, 0.0) + seconds
            if time.monotonic() - self._last_flush > 30:
                self._write()

    def record_warning(self, app: str, level: int):
        with self._lock:
            self.data["warnings"] += 1
            self.data["max_level"] = max(self.data["max_level"], level)

    def record_episode(self, app: str, seconds: float, level: int):
        with self._lock:
            self.data["episodes"].append({"app": app, "seconds": round(seconds, 1), "level": level})

    def _write(self):
        self._last_flush = time.monotonic()
        try:
            self.path_for(self.day).write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def flush(self):
        with self._lock:
            self._write()
