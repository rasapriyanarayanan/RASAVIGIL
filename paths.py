"""Resource locations (works from source and from a PyInstaller .exe)."""
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    ASSETS = Path(sys._MEIPASS) / "assets"
else:
    ASSETS = Path(__file__).resolve().parent.parent / "assets"

OWL = ASSETS / "owl.png"
