# RASAVIGIL

> *The owl that never sleeps.* A strict focus guard for Windows that detects time-wasting, warns you, restricts distractions and reports on your day.

RASAVIGIL watches the window you are using. When you spend **five continuous minutes** on a distraction (YouTube, Instagram, games, ...), the owl appears on your desktop with a warning and a quote. Ignore it, and the warnings escalate to a full-screen strict overlay and finally to restricting the distracting window. At the end of the day you get a usage report with a focus score.

## Features

| Feature | What it does |
|---|---|
| **Distraction detection** | Reads the active window title and process every second (ctypes + psutil). Idle time is not counted. |
| **5-minute trigger** | Warning fires after 5 continuous minutes of distraction. A short glance back at work (under 20 s) does not reset the timer. |
| **4 escalating warning levels** | Level 1 card, level 2 strict full-screen overlay with a reflection lock, level 3 final warning + restriction, level 4 restricted. Each has its own messages and a rotating quote. |
| **Restrictions** | From level 3 the distracting window is minimized (or closed, configurable). A daily distraction budget (default 60 min) locks distractions for the rest of the day once spent. |
| **Smart study exemption** | "Python tutorial - YouTube" counts as productive, not a distraction. |
| **After-distraction messages** | When you return to work you get a "Welcome back" notification saying how many minutes you lost. |
| **Daily usage report** | Self-contained HTML report with focus score, top distractions, productive apps, warnings and longest streak. Opens automatically at 21:00 (configurable) or from the tray menu. |
| **Snooze with limits** | 2 snoozes of 5 minutes per day. |
| **System tray** | Open report, pause 30 minutes, resume, edit settings, quit. |
| **Auto-start** | Optional start at Windows login. |

## Quick start (Windows 10/11)

1. Install [Python 3.10+](https://www.python.org/downloads/) (tick *Add Python to PATH*).
2. Open a terminal in this folder and run:

```bat
pip install -r requirements.txt
python main.py --preview    :: see all four warning levels without waiting 5 minutes
python main.py              :: start watching
```

Or double-click `run.bat` to start with no console window.

### Start with Windows

```bat
python main.py --install-startup
python main.py --remove-startup
```

### Build a standalone `RASAVIGIL.exe`

Double-click `build_exe.bat`. The program appears in `dist\RASAVIGIL.exe` and runs without Python installed.

## Settings

Settings are stored in `%APPDATA%\RASAVIGIL\config.json` (tray menu -> *Edit settings*). Restart after editing.

```json
{
  "threshold_seconds": 300,
  "grace_seconds": 20,
  "repeat_interval_seconds": 120,
  "restrictions": { "enabled": true, "start_at_warning_level": 3,
                    "action": "minimize", "daily_distraction_limit_minutes": 60 },
  "distraction": { "apps": ["netflix.exe", "steam.exe"], "title_keywords": ["youtube", "instagram"] },
  "productive":  { "apps": ["code.exe"], "title_keywords": ["github", "tutorial", "lecture"] }
}
```

Set `"action": "close"` to close distracting windows instead of minimizing them. Add your own sites and apps to the lists.

Usage data (`usage\YYYY-MM-DD.json`) and reports (`reports\`) are saved in the same folder. Everything stays on your computer; nothing is uploaded.

## The owl picture

`assets/owl.png` is a generated placeholder illustration. For a realistic owl, replace it with any owl photograph (PNG, transparent or dark background works best). It is rescaled automatically. `python tools/make_assets.py` regenerates the placeholder and `owl.ico`.

## Project structure

```
RASAVIGIL/
├── main.py                  entry point and CLI
├── rasavigil/
│   ├── engine.py            timer, escalation, restrictions, snooze (pure logic)
│   ├── classifier.py        productive / distraction / neutral / idle
│   ├── winapi.py            Windows foreground window, idle time, minimize/close
│   ├── ui.py                warning card, strict overlay, toast
│   ├── quotes.py            quotes and escalating messages
│   ├── storage.py           daily usage JSON
│   ├── report.py            HTML daily report
│   ├── tray.py              system tray icon
│   ├── app.py               wiring: monitor thread -> UI
│   ├── config.py            config loading
│   └── default_config.json
├── assets/                  owl.png, owl.ico
├── tests/test_engine.py     unit tests (python -m unittest discover -s tests)
├── tools/make_assets.py
├── requirements.txt  run.bat  build_exe.bat  install_startup.bat
```

## Tests

```bat
python -m unittest discover -s tests
```

## Roadmap

- Website blocking through the hosts file (needs admin rights)
- Weekly trend report
- Focus sessions (Pomodoro mode)
- Per-site detection via the browser URL instead of the window title

## Notes

- Detection by window title is a heuristic. Tune the keyword lists to your own habits.
- Quotes are widely attributed to the named authors.

## License

MIT, see `LICENSE`.
