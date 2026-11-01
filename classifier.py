"""Decide whether the foreground window is productive, a distraction, or neutral."""
from __future__ import annotations

from dataclasses import dataclass

PRODUCTIVE = "productive"
DISTRACTION = "distraction"
NEUTRAL = "neutral"
IDLE = "idle"


@dataclass(frozen=True)
class Sample:
    """One look at the desktop."""
    process: str          # e.g. "chrome.exe"
    title: str            # window title
    idle_seconds: float   # seconds since last keyboard/mouse input
    hwnd: int = 0         # window handle (Windows)


class Classifier:
    def __init__(self, config: dict):
        d, p = config["distraction"], config["productive"]
        self.d_apps = {a.lower() for a in d["apps"]}
        self.d_words = [w.lower() for w in d["title_keywords"]]
        self.p_apps = {a.lower() for a in p["apps"]}
        self.p_words = [w.lower() for w in p["title_keywords"]]
        self.idle_limit = float(config["idle_seconds"])

    def classify(self, s: Sample) -> str:
        if s.idle_seconds >= self.idle_limit:
            return IDLE
        proc, title = s.process.lower(), s.title.lower()
        if proc in self.p_apps:
            return PRODUCTIVE
        if proc in self.d_apps:
            return DISTRACTION
        if any(w in title for w in self.d_words):
            # "Python tutorial - YouTube" is study, not a distraction.
            if any(w in title for w in self.p_words):
                return PRODUCTIVE
            return DISTRACTION
        if any(w in title for w in self.p_words):
            return PRODUCTIVE
        return NEUTRAL

    @staticmethod
    def label(s: Sample) -> str:
        """Friendly name for reports and warnings."""
        t = s.title.strip()
        low = t.lower()
        for site in ("youtube", "instagram", "facebook", "netflix", "reddit", "tiktok",
                     "twitch", "snapchat", "prime video", "hotstar", "jiocinema",
                     "pinterest", "crunchyroll", "twitter"):
            if site in low:
                return site.title() if site != "jiocinema" else "JioCinema"
        name = s.process.rsplit(".", 1)[0] if s.process else "Unknown"
        return name[:1].upper() + name[1:]
