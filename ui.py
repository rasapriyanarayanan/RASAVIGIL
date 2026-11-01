"""Desktop UI: the warning card, the strict full-screen overlay and the small toast."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

try:
    from PIL import Image, ImageTk
except ImportError:  # Pillow is optional for the UI itself
    Image = ImageTk = None

BG = "#0B0F1A"
CARD = "#111827"
TEXT = "#E8ECF5"
MUTED = "#8B97B3"
GOLD = "#F5A623"
FONT = "Segoe UI"

LEVEL_COLOR = {1: "#F5A623", 2: "#F28C28", 3: "#EF4B5F", 4: "#C81E3A"}


def load_owl(path: Path, max_w: int, max_h: int):
    """Load the owl picture scaled to fit. Replace assets/owl.png with any photo you like."""
    if not Path(path).exists():
        return None
    try:
        if Image is not None:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        photo = tk.PhotoImage(file=str(path))
        factor = max(photo.width() // max_w, photo.height() // max_h, 1)
        return photo.subsample(factor) if factor > 1 else photo
    except Exception:
        return None


def _fade_in(win: tk.Toplevel, target: float = 1.0, step: float = 0.12):
    try:
        alpha = float(win.attributes("-alpha"))
        if alpha < target:
            win.attributes("-alpha", min(target, alpha + step))
            win.after(25, lambda: _fade_in(win, target, step))
    except tk.TclError:
        pass


class WarningWindow:
    """Warning card (levels 1-2) or full-screen strict overlay (level >= strict_from_level)."""

    def __init__(self, root: tk.Tk, *, level: int, title: str, message: str, quote: str,
                 author: str, owl_path: Path, strict: bool, lock_seconds: int,
                 snoozes_left: int, on_back: Callable[[], None],
                 on_snooze: Callable[[], None]):
        self.root, self.level, self.strict = root, level, strict
        self.on_back, self.on_snooze = on_back, on_snooze
        color = LEVEL_COLOR.get(level, LEVEL_COLOR[4])
        self.win = tk.Toplevel(root)
        win = self.win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=BG)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()

        if strict:
            win.geometry(f"{sw}x{sh}+0+0")
            win.attributes("-alpha", 0.0)
            holder = tk.Frame(win, bg=BG)
            holder.place(relx=0.5, rely=0.5, anchor="center")
            card_w, card_h = 820, 460
        else:
            card_w, card_h = 780, 420
            win.geometry(f"{card_w}x{card_h}+{(sw - card_w) // 2}+{(sh - card_h) // 3}")
            win.attributes("-alpha", 0.0)
            holder = win

        card = tk.Frame(holder, bg=CARD, width=card_w, height=card_h,
                        highlightthickness=1, highlightbackground=color)
        card.pack()
        card.pack_propagate(False)
        tk.Frame(card, bg=color, height=5).pack(fill="x")

        body = tk.Frame(card, bg=CARD)
        body.pack(fill="both", expand=True, padx=28, pady=22)

        # left: owl
        left = tk.Frame(body, bg=CARD, width=270)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._owl = load_owl(owl_path, 260, 300)
        if self._owl:
            tk.Label(left, image=self._owl, bg=CARD, bd=0).pack(pady=(4, 0))
        pips = tk.Frame(left, bg=CARD)
        pips.pack(pady=(14, 0))
        for i in range(1, 5):
            tk.Label(pips, text="●", font=(FONT, 12),
                     fg=color if i <= level else "#2A3350", bg=CARD).pack(side="left", padx=3)
        tk.Label(left, text=f"WARNING LEVEL {min(level, 4)} / 4", font=(FONT, 9, "bold"),
                 fg=MUTED, bg=CARD).pack(pady=(4, 0))

        # right: text
        right = tk.Frame(body, bg=CARD)
        right.pack(side="left", fill="both", expand=True, padx=(26, 0))
        tk.Label(right, text="R A S A V I G I L", font=(FONT, 10, "bold"), fg=color,
                 bg=CARD, anchor="w").pack(fill="x")
        tk.Label(right, text=title, font=(FONT, 24, "bold"), fg=TEXT, bg=CARD,
                 anchor="w", justify="left", wraplength=440).pack(fill="x", pady=(6, 10))
        tk.Label(right, text=message, font=(FONT, 12), fg=TEXT, bg=CARD, anchor="w",
                 justify="left", wraplength=440).pack(fill="x")
        tk.Frame(right, bg="#222C45", height=1).pack(fill="x", pady=16)
        tk.Label(right, text=f"“{quote}”", font=(FONT, 11, "italic"), fg=MUTED,
                 bg=CARD, anchor="w", justify="left", wraplength=440).pack(fill="x")
        tk.Label(right, text=f"— {author}", font=(FONT, 10), fg=color, bg=CARD,
                 anchor="w").pack(fill="x", pady=(4, 0))

        btns = tk.Frame(right, bg=CARD)
        btns.pack(side="bottom", fill="x", pady=(14, 0))
        self.back_btn = tk.Button(btns, font=(FONT, 11, "bold"), bg=color, fg="#0B0F1A",
                                  activebackground=color, relief="flat", bd=0, padx=18, pady=9,
                                  cursor="hand2", command=self._back)
        self.back_btn.pack(side="left")
        if snoozes_left > 0 and level < 3:
            tk.Button(btns, text=f"Snooze 5 min ({snoozes_left} left today)",
                      font=(FONT, 10), bg="#1F2940", fg=MUTED, activebackground="#2A3350",
                      activeforeground=TEXT, relief="flat", bd=0, padx=14, pady=9,
                      cursor="hand2", command=self._snooze).pack(side="left", padx=(12, 0))

        self._remaining = lock_seconds if strict else 0
        self._tick_lock()
        win.lift()
        win.focus_force()
        _fade_in(win, 0.97 if strict else 1.0)

    def _tick_lock(self):
        try:
            if self._remaining > 0:
                self.back_btn.configure(text=f"Please reflect... {self._remaining}s",
                                        state="disabled", disabledforeground="#0B0F1A")
                self._remaining -= 1
                self.win.after(1000, self._tick_lock)
            else:
                self.back_btn.configure(text="I am going back to work", state="normal")
        except tk.TclError:
            pass

    def _back(self):
        self.close()
        self.on_back()

    def _snooze(self):
        self.close()
        self.on_snooze()

    def close(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass

    def alive(self) -> bool:
        try:
            return bool(self.win.winfo_exists())
        except tk.TclError:
            return False


class Toast:
    """Small bottom-right notification used for recovery messages and reports."""

    def __init__(self, root: tk.Tk, *, heading: str, message: str, owl_path: Path,
                 color: str = "#3ECF8E", seconds: int = 9, on_click: Optional[Callable] = None):
        self.win = tk.Toplevel(root)
        win = self.win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.0)
        win.configure(bg=CARD, highlightthickness=1, highlightbackground=color)
        w, h = 400, 120
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{sw - w - 24}+{sh - h - 72}")
        tk.Frame(win, bg=color, width=5).pack(side="left", fill="y")
        self._owl = load_owl(owl_path, 76, 76)
        if self._owl:
            tk.Label(win, image=self._owl, bg=CARD).pack(side="left", padx=(12, 6))
        col = tk.Frame(win, bg=CARD)
        col.pack(side="left", fill="both", expand=True, padx=(6, 14), pady=12)
        tk.Label(col, text=heading, font=(FONT, 11, "bold"), fg=color, bg=CARD,
                 anchor="w").pack(fill="x")
        tk.Label(col, text=message, font=(FONT, 10), fg=TEXT, bg=CARD, anchor="w",
                 justify="left", wraplength=250).pack(fill="x", pady=(4, 0))
        for widget in (win, col):
            widget.bind("<Button-1>", lambda _e: (on_click() if on_click else None, self.close()))
        _fade_in(win, 0.98)
        win.after(seconds * 1000, self.close)

    def close(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass
