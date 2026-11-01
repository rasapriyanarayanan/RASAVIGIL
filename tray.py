"""System tray icon (pystray). The app still works without it if pystray is missing."""
from __future__ import annotations

from pathlib import Path


def start_tray(app):
    try:
        import pystray
        from PIL import Image
    except ImportError:
        print("pystray/Pillow not installed - running without a tray icon.")
        return None

    from .paths import OWL
    try:
        icon_img = Image.open(OWL).convert("RGBA").resize((64, 64))
    except Exception:
        icon_img = Image.new("RGBA", (64, 64), "#F5A623")

    menu = pystray.Menu(
        pystray.MenuItem("RASAVIGIL - owl on watch", None, enabled=False),
        pystray.MenuItem("Today's report", lambda: app.show_report(True)),
        pystray.MenuItem("Pause for 30 minutes", lambda: app.pause(30)),
        pystray.MenuItem("Resume watching", lambda: app.resume()),
        pystray.MenuItem("Edit settings", lambda: app.open_config()),
        pystray.MenuItem("Quit", lambda: app.request_quit()),
    )
    icon = pystray.Icon("RASAVIGIL", icon_img, "RASAVIGIL - watching your focus", menu)
    icon.run_detached()
    return icon
