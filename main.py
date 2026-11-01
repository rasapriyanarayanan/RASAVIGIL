"""RASAVIGIL entry point.

  python main.py                    start watching (tray icon + warnings)
  python main.py --preview          show every warning level once, no monitoring
  python main.py --report           open today's report
  python main.py --install-startup  start automatically when you log in to Windows
  python main.py --remove-startup   undo the above
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pyw = Path(sys.executable).with_name("pythonw.exe")
    exe = pyw if pyw.exists() else Path(sys.executable)
    return f'"{exe}" "{Path(__file__).resolve()}"'


def set_startup(enable: bool) -> None:
    if sys.platform != "win32":
        print("Auto-start is only supported on Windows.")
        return
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    if enable:
        winreg.SetValueEx(key, "RASAVIGIL", 0, winreg.REG_SZ, startup_command())
        print("RASAVIGIL will now start when you log in.")
    else:
        try:
            winreg.DeleteValue(key, "RASAVIGIL")
        except FileNotFoundError:
            pass
        print("Auto-start removed.")


def preview() -> None:
    import tkinter as tk
    from rasavigil import quotes
    from rasavigil.paths import OWL
    from rasavigil.ui import Toast, WarningWindow

    root = tk.Tk()
    root.withdraw()
    levels = [1, 2, 3, 4]

    def step(i: int = 0):
        if i >= len(levels):
            Toast(root, heading="Welcome back", message=quotes.recovery_message("YouTube", 9),
                  owl_path=OWL, seconds=4)
            root.after(5000, root.destroy)
            return
        lv = levels[i]
        q, a = quotes.random_quote()
        WarningWindow(root, level=lv, title=quotes.warning_title(lv),
                      message=quotes.warning_message(lv, "YouTube", 5 + 2 * (lv - 1)),
                      quote=q, author=a, owl_path=OWL, strict=lv >= 2, lock_seconds=3,
                      snoozes_left=2, on_back=lambda: step(i + 1), on_snooze=lambda: step(i + 1))

    step()
    root.mainloop()


def main() -> None:
    ap = argparse.ArgumentParser(description="RASAVIGIL - the owl that guards your focus")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--install-startup", action="store_true")
    ap.add_argument("--remove-startup", action="store_true")
    args = ap.parse_args()

    if args.install_startup or args.remove_startup:
        set_startup(args.install_startup)
    elif args.preview:
        preview()
    elif args.report:
        import webbrowser
        from rasavigil.config import data_dir
        from rasavigil.report import write_report
        from rasavigil.storage import UsageStore
        d = data_dir()
        path = write_report(UsageStore(d / "usage").data, d / "reports")
        print("Report written to", path)
        webbrowser.open(path.as_uri())
    else:
        from rasavigil.app import App
        App().run()


if __name__ == "__main__":
    main()
