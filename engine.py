"""The decision engine. Pure logic with an injectable clock, so it is fully unit-testable."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .classifier import Classifier, Sample, DISTRACTION, IDLE


@dataclass
class Event:
    kind: str                       # "warn" | "restrict" | "limit" | "recovered" | "snooze_denied"
    level: int = 0
    app: str = ""
    minutes: int = 0
    hwnd: int = 0
    action: str = ""                # for "restrict": "minimize" | "close"
    extra: dict = field(default_factory=dict)


class Engine:
    def __init__(self, config: dict, store=None):
        self.cfg = config
        self.classifier = Classifier(config)
        self.store = store                      # optional UsageStore
        self.threshold = float(config["threshold_seconds"])
        self.grace = float(config["grace_seconds"])
        self.repeat = float(config["repeat_interval_seconds"])
        r = config["restrictions"]
        self.restrict_on = bool(r["enabled"])
        self.restrict_level = int(r["start_at_warning_level"])
        self.restrict_action = r["action"]
        self.daily_limit = float(r["daily_distraction_limit_minutes"]) * 60
        self.max_snoozes = int(config["max_snoozes_per_day"])
        self.snooze_seconds = float(config["snooze_minutes"]) * 60

        self.paused_until = 0.0
        self.snoozed_until = 0.0
        self.snoozes_used = 0
        self.distraction_today = 0.0
        self._last_tick: Optional[float] = None
        self._limit_announced = False
        self._last_restrict = 0.0
        self._reset_episode()

    # ---- episode state -------------------------------------------------
    def _reset_episode(self):
        self.level = 0
        self.accumulated = 0.0       # distraction seconds in the current streak
        self._last_warn_at = 0.0     # value of `accumulated` at the last warning
        self._last_seen = 0.0
        self._in_episode = False
        self._app = ""
        self._app_seconds: dict[str, float] = {}

    @property
    def current_app(self) -> str:
        if not self._app_seconds:
            return self._app or "a distraction"
        return max(self._app_seconds, key=self._app_seconds.get)

    # ---- controls ------------------------------------------------------
    def pause(self, now: float, minutes: float):
        self.paused_until = now + minutes * 60

    def resume(self):
        self.paused_until = 0.0

    def snooze(self, now: float) -> bool:
        """Postpone warnings. Returns False when the daily allowance is spent."""
        if self.snoozes_used >= self.max_snoozes:
            return False
        self.snoozes_used += 1
        self.snoozed_until = now + self.snooze_seconds
        return True

    # ---- main entry point ---------------------------------------------
    def tick(self, sample: Sample, now: float) -> list[Event]:
        events: list[Event] = []
        dt = 0.0 if self._last_tick is None else min(max(now - self._last_tick, 0.0), 5.0)
        self._last_tick = now

        if now < self.paused_until:
            return events

        category = self.classifier.classify(sample)
        app = self.classifier.label(sample)
        if self.store:
            self.store.add(app if category != IDLE else "Idle", category, dt)

        if category == DISTRACTION:
            self.distraction_today += dt
            self._in_episode = True
            self._last_seen = now
            self.accumulated += dt
            self._app = app
            self._app_seconds[app] = self._app_seconds.get(app, 0.0) + dt
            events += self._on_distraction(sample, now)
        elif self._in_episode and now - self._last_seen >= self.grace:
            events += self._end_episode()
        return events

    def _on_distraction(self, s: Sample, now: float) -> list[Event]:
        out: list[Event] = []
        app = self.current_app
        mins = max(1, round(self.accumulated / 60))

        # Daily budget: once spent, every distraction is restricted immediately.
        if self.restrict_on and self.daily_limit and self.distraction_today >= self.daily_limit:
            if not self._limit_announced:
                self._limit_announced = True
                out.append(Event("limit", level=4, app=app, minutes=mins, hwnd=s.hwnd,
                                 extra={"limit": int(self.daily_limit // 60)}))
            if now - self._last_restrict >= 10:
                self._last_restrict = now
                out.append(Event("restrict", level=4, app=app, hwnd=s.hwnd, action=self.restrict_action))
            return out

        if now < self.snoozed_until:
            return out

        if self.level == 0:
            if self.accumulated >= self.threshold:
                self.level = 1
                self._last_warn_at = self.accumulated
                out.append(Event("warn", 1, app, mins, s.hwnd))
        elif self.accumulated - self._last_warn_at >= self.repeat:
            self.level += 1
            self._last_warn_at = self.accumulated
            out.append(Event("warn", self.level, app, mins, s.hwnd))
            if self.restrict_on and self.level >= self.restrict_level:
                out.append(Event("restrict", self.level, app, mins, s.hwnd, self.restrict_action))
        if self.store and out:
            self.store.record_warning(app, self.level)
        return out

    def _end_episode(self) -> list[Event]:
        out: list[Event] = []
        if self.store and self.accumulated > 0:
            self.store.record_episode(self.current_app, self.accumulated, self.level)
        if self.level >= 1:
            out.append(Event("recovered", self.level, self.current_app,
                             max(1, round(self.accumulated / 60))))
        self._reset_episode()
        return out
