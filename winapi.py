"""Thin Windows layer (ctypes + psutil). On other systems it returns an empty sample so the
rest of the app can still be imported, tested and previewed."""
from __future__ import annotations

import sys

from .classifier import Sample

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    try:
        import psutil
    except ImportError:  # only needed for the live watcher
        psutil = None

    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32
    _user32.GetForegroundWindow.restype = wintypes.HWND

    class _LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    def idle_seconds() -> float:
        info = _LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        if not _user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        millis = (_kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF
        return millis / 1000.0

    def foreground_sample() -> Sample:
        hwnd = _user32.GetForegroundWindow()
        if not hwnd:
            return Sample("", "", idle_seconds(), 0)
        length = _user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buf, length + 1)
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        proc = ""
        if psutil is not None:
            try:
                proc = psutil.Process(pid.value).name()
            except (psutil.Error, OSError):
                pass
        return Sample(proc, buf.value, idle_seconds(), int(hwnd))

    def minimize_window(hwnd: int) -> None:
        _user32.ShowWindow(wintypes.HWND(hwnd), 6)  # SW_MINIMIZE

    def close_window(hwnd: int) -> None:
        _user32.PostMessageW(wintypes.HWND(hwnd), 0x0010, 0, 0)  # WM_CLOSE

    def beep(level: int) -> None:
        import winsound
        if level >= 3:
            for _ in range(2):
                winsound.Beep(900, 180)
        else:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    def enable_dpi_awareness() -> None:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
else:
    def idle_seconds() -> float:
        return 0.0

    def foreground_sample() -> Sample:
        return Sample("", "", 0.0, 0)

    def minimize_window(hwnd: int) -> None:
        pass

    def close_window(hwnd: int) -> None:
        pass

    def beep(level: int) -> None:
        pass

    def enable_dpi_awareness() -> None:
        pass
