"""Daily usage report: a single self-contained HTML file."""
from __future__ import annotations

import html
from pathlib import Path

from . import quotes, __version__


def _fmt(seconds: float) -> str:
    seconds = int(seconds)
    h, m = divmod(seconds // 60, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {seconds % 60:02d}s"


def summarize(data: dict) -> dict:
    cats = data.get("categories", {})
    prod = cats.get("productive", 0.0)
    dist = cats.get("distraction", 0.0)
    neutral = cats.get("neutral", 0.0)
    idle = cats.get("idle", 0.0)
    tracked = prod + dist
    score = round(100 * prod / tracked) if tracked > 0 else (100 if neutral else 0)
    longest = max((e["seconds"] for e in data.get("episodes", [])), default=0.0)
    return {"productive": prod, "distraction": dist, "neutral": neutral, "idle": idle,
            "score": score, "longest": longest, "warnings": data.get("warnings", 0),
            "max_level": data.get("max_level", 0)}


def _rows(apps: dict, category: str, limit: int = 8) -> str:
    items = sorted(((n, r["seconds"]) for n, r in apps.items() if r["category"] == category),
                   key=lambda x: -x[1])[:limit]
    if not items:
        return '<tr><td colspan="3" class="muted">Nothing recorded</td></tr>'
    top = items[0][1] or 1
    cls = "bad" if category == "distraction" else "good" if category == "productive" else "mid"
    return "".join(
        f'<tr><td>{html.escape(n)}</td><td class="num">{_fmt(s)}</td>'
        f'<td class="barcell"><div class="bar {cls}" style="width:{max(3, int(100 * s / top))}%"></div></td></tr>'
        for n, s in items)


def build_html(data: dict) -> str:
    s = summarize(data)
    verdict, quote = quotes.verdict(s["score"])
    apps = data.get("apps", {})
    ring = f"conic-gradient(var(--good) {s['score'] * 3.6}deg, var(--bad) 0)"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RASAVIGIL Daily Report - {data['date']}</title>
<style>
:root{{--bg:#0b0f1a;--card:#131a2b;--line:#222c45;--text:#e8ecf5;--muted:#8b97b3;--gold:#f5a623;--good:#3ecf8e;--bad:#ef4b5f;--mid:#5b7cfa}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 "Segoe UI",system-ui,sans-serif;padding:32px 16px}}
.wrap{{max-width:960px;margin:auto}}
header{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:24px}}
h1{{margin:0;letter-spacing:.28em;font-size:22px;color:var(--gold)}}
.sub{{color:var(--muted)}}
.hero{{display:flex;gap:28px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px;margin-bottom:20px;flex-wrap:wrap}}
.ring{{width:140px;height:140px;border-radius:50%;background:{ring};display:grid;place-items:center;flex:none}}
.ring div{{width:108px;height:108px;border-radius:50%;background:var(--card);display:grid;place-items:center;font-size:32px;font-weight:700}}
.ring small{{display:block;font-size:11px;font-weight:400;color:var(--muted);text-align:center}}
.verdict{{flex:1;min-width:240px}}
.verdict h2{{margin:0 0 6px;font-size:20px}}
.verdict q{{color:var(--muted);font-style:italic}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:20px}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}}
.stat b{{display:block;font-size:24px;margin-top:4px}}
.stat span{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}}
.panel h3{{margin:0 0 10px;font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}}
table{{width:100%;border-collapse:collapse}}
td{{padding:6px 4px;border-top:1px solid var(--line)}}
.num{{text-align:right;white-space:nowrap;color:var(--muted);width:90px}}
.barcell{{width:35%}}
.bar{{height:8px;border-radius:4px}}
.bar.good{{background:var(--good)}}.bar.bad{{background:var(--bad)}}.bar.mid{{background:var(--mid)}}
.muted{{color:var(--muted)}}
footer{{margin-top:28px;text-align:center;color:var(--muted);font-size:12px}}
</style></head><body><div class="wrap">
<header><h1>RASAVIGIL</h1><div class="sub">Daily report &middot; {data['date']}</div></header>
<section class="hero">
  <div class="ring"><div><span>{s['score']}%<small>focus score</small></span></div></div>
  <div class="verdict"><h2>{html.escape(verdict)}</h2><q>{html.escape(quote)}</q></div>
</section>
<section class="stats">
  <div class="stat"><span>Productive</span><b style="color:var(--good)">{_fmt(s['productive'])}</b></div>
  <div class="stat"><span>Distracted</span><b style="color:var(--bad)">{_fmt(s['distraction'])}</b></div>
  <div class="stat"><span>Other / neutral</span><b>{_fmt(s['neutral'])}</b></div>
  <div class="stat"><span>Away / idle</span><b>{_fmt(s['idle'])}</b></div>
  <div class="stat"><span>Warnings issued</span><b>{s['warnings']}</b></div>
  <div class="stat"><span>Longest streak</span><b>{_fmt(s['longest'])}</b></div>
</section>
<section class="cols">
  <div class="panel"><h3>Top distractions</h3><table>{_rows(apps, 'distraction')}</table></div>
  <div class="panel"><h3>Top productive apps</h3><table>{_rows(apps, 'productive')}</table></div>
  <div class="panel"><h3>Other apps</h3><table>{_rows(apps, 'neutral')}</table></div>
</section>
<footer>Generated by RASAVIGIL v{__version__} &middot; The owl never sleeps.</footer>
</div></body></html>"""


def write_report(data: dict, folder: Path) -> Path:
    path = Path(folder) / f"report-{data['date']}.html"
    path.write_text(build_html(data), encoding="utf-8")
    return path
