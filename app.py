"""Application wiring: monitor thread -> event queue -> Tk UI on the main thread."""
from __future__ import annotations

import os
import queue
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import tkinter as tk

from . import quotes, winapi, __version__
from .config import data_dir, load_config, user_config_path
from .engine import Engine, Event
from .report import write_report
from .storage import UsageStore
from .ui import Toast, WarningWindow

from .paths import OWL


class App:
    def __init__(self):
        winapi.enable_dpi_awareness()
        self.cfg = load_config()
        self.data = data_dir()
        self.store = UsageStore(self.data / "usage")
        self.engine = Engine(self.cfg, self.store)
        self.events: "queue.Queue[Event | tuple]" = queue.Queue()
        self.root = tk.Tk()
        self.root.withdraw()
        self.window: WarningWindow | None = None
        self.stop = threading.Event()
        self._report_day = ""
        self.tray = None

    # ---- monitor thread ----------------------------------------------
    def _monitor(self):
        interval = float(self.cfg["poll_interval_seconds"])
        while not self.stop.is_set():
            try:
                sample = winapi.foreground_sample()
                for ev in self.engine.tick(sample, time.monotonic()):
                    self.events.put(ev)
            except Exception as exc:  # never let the watcher die
                print("monitor error:", exc, file=sys.stderr)
            self._check_daily_report()
            self.stop.wait(interval)

    def _check_daily_report(self):
        stamp = datetime.now()
        if stamp.strftime("%H:%M") == self.cfg["daily_report_time"] and self._report_day != stamp.date().isoformat():
            self._report_day = stamp.date().isoformat()
            self.events.put(("report", True))

    # ---- UI thread -----------------------------------------------------
    def _pump(self):
        try:
            while True:
                item = self.events.get_nowait()
                if isinstance(item, Event):
                    self._handle(item)
                elif item[0] == "report":
                    self.show_report(open_browser=item[1], toast=True)
                elif item[0] == "quit":
                    self.quit()
                    return
        except queue.Empty:
            pass
        self.root.after(250, self._pump)

    def _handle(self, ev: Event):
        if ev.kind == "warn":
            self._warn(ev)
        elif ev.kind == "limit":
            self._show(ev.level, "DAILY LIMIT REACHED",
                       quotes.limit_message(ev.app, ev.extra["limit"]), ev)
        elif ev.kind == "restrict":
            if ev.action == "close":
                winapi.close_window(ev.hwnd)
            else:
                winapi.minimize_window(ev.hwnd)
        elif ev.kind == "recovered":
            Toast(self.root, heading="Welcome back",
                  message=quotes.recovery_message(ev.app, ev.minutes), owl_path=OWL)

    def _warn(self, ev: Event):
        self._show(ev.level, quotes.warning_title(ev.level),
                   quotes.warning_message(ev.level, ev.app, ev.minutes), ev)

    def _show(self, level: int, title: str, message: str, ev: Event):
        if self.window and self.window.alive():
            self.window.close()
        quote, author = quotes.random_quote()
        ov = self.cfg["overlay"]
        if ov["play_sound"]:
            winapi.beep(level)
        self.window = WarningWindow(
            self.root, level=level, title=title, message=message, quote=quote, author=author,
            owl_path=OWL, strict=level >= int(ov["strict_from_level"]),
            lock_seconds=int(ov["lock_seconds"]),
            snoozes_left=max(0, self.engine.max_snoozes - self.engine.snoozes_used),
            on_back=lambda: None, on_snooze=self._snooze)

    def _snooze(self):
        if self.engine.snooze(time.monotonic()):
            Toast(self.root, heading="Snooze granted",
                  message=quotes.SNOOZE_MESSAGES[0].format(minutes=self.cfg["snooze_minutes"]),
                  owl_path=OWL, color="#F5A623")
        else:
            Toast(self.root, heading="No snoozes left", message=quotes.NO_SNOOZE_MESSAGE,
                  owl_path=OWL, color="#EF4B5F")

    # ---- actions used by the tray -------------------------------------
    def show_report(self, open_browser: bool = True, toast: bool = False):
        self.store.flush()
        path = write_report(self.store.data, self.data / "reports")
        if open_browser:
            webbrowser.open(path.as_uri())
        if toast:
            Toast(self.root, heading="Daily report ready",
                  message="Your RASAVIGIL usage report for today is ready. Click to open.",
                  owl_path=OWL, color="#5B7CFA", on_click=lambda: webbrowser.open(path.as_uri()))
        return path

    def pause(self, minutes: int):
        self.engine.pause(time.monotonic(), minutes)

    def resume(self):
        self.engine.resume()

    def open_config(self):
        path = user_config_path()
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            webbrowser.open(path.as_uri())

    def request_quit(self):
        self.events.put(("quit",))

    def quit(self):
        self.stop.set()
        self.store.flush()
        if self.tray:
            self.tray.stop()
        self.root.destroy()

    # ---- run -----------------------------------------------------------
    def run(self):
        from .tray import start_tray
        self.tray = start_tray(self)
        threading.Thread(target=self._monitor, daemon=True, name="rasavigil-monitor").start()
        self.root.after(250, self._pump)
        Toast(self.root, heading="RASAVIGIL is watching",
              message=f"Focus guard v{__version__} is active. Stay on task.", owl_path=OWL,
              color="#F5A623", seconds=5)
        self.root.mainloop()
        self.store.flush()
