import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rasavigil.classifier import Classifier, Sample, DISTRACTION, PRODUCTIVE, NEUTRAL, IDLE
from rasavigil.engine import Engine
from rasavigil.report import build_html
from rasavigil.storage import empty_day

CFG = json.loads((Path(__file__).resolve().parent.parent / "rasavigil" / "default_config.json").read_text())

YT = Sample("chrome.exe", "Funny cats - YouTube - Google Chrome", 0, 11)
STUDY = Sample("chrome.exe", "Python tutorial for beginners - YouTube", 0, 12)
CODE = Sample("Code.exe", "main.py - Visual Studio Code", 0, 13)
OTHER = Sample("calc.exe", "Calculator", 0, 14)


def run(engine, sample, start, seconds):
    events = []
    for t in range(start, start + seconds):
        events += engine.tick(sample, float(t))
    return events


class ClassifierTests(unittest.TestCase):
    def test_categories(self):
        c = Classifier(CFG)
        self.assertEqual(c.classify(YT), DISTRACTION)
        self.assertEqual(c.classify(STUDY), PRODUCTIVE)
        self.assertEqual(c.classify(CODE), PRODUCTIVE)
        self.assertEqual(c.classify(OTHER), NEUTRAL)
        self.assertEqual(c.classify(Sample("chrome.exe", "x - YouTube", 500)), IDLE)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.e = Engine(json.loads(json.dumps(CFG)))

    def test_no_warning_before_five_minutes(self):
        self.assertEqual(run(self.e, YT, 0, 299), [])

    def test_warning_at_five_minutes(self):
        ev = run(self.e, YT, 0, 302)
        warns = [x for x in ev if x.kind == "warn"]
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0].level, 1)
        self.assertEqual(warns[0].app, "Youtube")

    def test_short_work_break_does_not_reset(self):
        run(self.e, YT, 0, 200)
        run(self.e, CODE, 200, 10)          # shorter than grace
        ev = run(self.e, YT, 210, 130)
        self.assertTrue(any(x.kind == "warn" for x in ev))

    def test_long_work_break_resets(self):
        run(self.e, YT, 0, 200)
        run(self.e, CODE, 200, 60)          # longer than grace
        ev = run(self.e, YT, 260, 200)
        self.assertFalse(any(x.kind == "warn" for x in ev))

    def test_escalation_and_restriction(self):
        ev = run(self.e, YT, 0, 302 + 240 + 5)
        levels = [x.level for x in ev if x.kind == "warn"]
        self.assertEqual(levels, [1, 2, 3])
        self.assertTrue(any(x.kind == "restrict" and x.action == "minimize" for x in ev))

    def test_recovery_message(self):
        run(self.e, YT, 0, 320)
        ev = run(self.e, CODE, 320, 30)
        self.assertTrue(any(x.kind == "recovered" for x in ev))

    def test_snooze_limits(self):
        self.assertTrue(self.e.snooze(0))
        self.assertTrue(self.e.snooze(0))
        self.assertFalse(self.e.snooze(0))

    def test_snooze_suppresses_warning(self):
        self.e.snooze(0)
        self.assertEqual([x for x in run(self.e, YT, 0, 290) if x.kind == "warn"], [])

    def test_idle_not_counted(self):
        away = Sample("chrome.exe", "YouTube", 600)
        self.assertEqual(run(self.e, away, 0, 400), [])

    def test_pause(self):
        self.e.pause(0, 30)
        self.assertEqual(run(self.e, YT, 0, 400), [])

    def test_daily_limit(self):
        cfg = json.loads(json.dumps(CFG))
        cfg["restrictions"]["daily_distraction_limit_minutes"] = 1
        e = Engine(cfg)
        ev = run(e, YT, 0, 90)
        self.assertTrue(any(x.kind == "limit" for x in ev))
        self.assertTrue(any(x.kind == "restrict" for x in ev))


class ReportTests(unittest.TestCase):
    def test_report_renders(self):
        d = empty_day("2026-11-01")
        d["apps"] = {"Youtube": {"seconds": 600, "category": "distraction"},
                     "Code": {"seconds": 3000, "category": "productive"}}
        d["categories"] = {"distraction": 600, "productive": 3000}
        html = build_html(d)
        self.assertIn("RASAVIGIL", html)
        self.assertIn("83%", html)


if __name__ == "__main__":
    unittest.main()
