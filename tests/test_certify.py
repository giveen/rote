"""Tests for the standalone certificate — one file a judge can open from disk."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rote.certify import write_certificate


def sample_report(*, passed: bool = True, goal: str = "Log two received parts lines",
                  script: str = "/tmp/does-not-exist.py") -> dict:
    return {
        "video": "/tmp/intake.mp4",
        "plan": {
            "app": "Stockroom",
            "goal": goal,
            "fields": [{"label": "SKU", "control": "text", "example": "BRK-2041"}],
            "rows": [{"cells": [{"field": "sku", "value": "BRK-2041"}]}],
            "steps": [
                {"action": "type", "target": "SKU", "value": "BRK-2041",
                 "note": "", "scope": "each_row"},
                {"action": "click", "target": "Add line", "value": None,
                 "note": "", "scope": "each_row"},
            ],
            "expected_effect": "A line appears in the intake table",
        },
        "script": script,
        "attempts": [
            {"attempt": 0, "passed": passed,
             "checks": [{"name": "script runs on fresh data", "ok": passed,
                         "detail": "1 row(s) through fake.py"}],
             "error": None, "cost": 0.0011}
        ],
        "passed": passed,
        "ledger": {"calls": 1, "spent_usd": 0.0011, "input_tokens": 10,
                   "cached_tokens": 0, "output_tokens": 10, "reasoning_tokens": 0,
                   "cache_hit_pct": 5.0},
        "elapsed_s": 1.0,
        "fresh_data": True,
    }


def _run_dir(tmp: Path, report: dict) -> Path:
    run = tmp / "run"
    run.mkdir(parents=True, exist_ok=True)
    (run / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return run


class TestCertificate(unittest.TestCase):
    def test_file_is_created_and_html(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            run = _run_dir(tmp, sample_report())
            out = tmp / "certificate.html"
            written = write_certificate(run, out)
            self.assertEqual(written, out)
            self.assertTrue(out.exists())
            self.assertIn("<html", out.read_text(encoding="utf-8"))

    def test_passed_shows_passed(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            run = _run_dir(tmp, sample_report(passed=True))
            out = tmp / "certificate.html"
            write_certificate(run, out)
            html_text = out.read_text(encoding="utf-8")
            self.assertIn("PASSED", html_text)
            self.assertNotIn("NOT PASSED", html_text)

    def test_not_passed_shows_not_passed(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            run = _run_dir(tmp, sample_report(passed=False))
            out = tmp / "certificate.html"
            write_certificate(run, out)
            self.assertIn("NOT PASSED", out.read_text(encoding="utf-8"))

    def test_goal_text_appears(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            run = _run_dir(tmp, sample_report(goal="Log two received parts lines"))
            out = tmp / "certificate.html"
            write_certificate(run, out)
            self.assertIn("Log two received parts lines",
                          out.read_text(encoding="utf-8"))

    def test_goal_is_escaped(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            evil = "<script>alert(1)</script>"
            run = _run_dir(tmp, sample_report(goal=evil))
            out = tmp / "certificate.html"
            write_certificate(run, out)
            text = out.read_text(encoding="utf-8")
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", text)
            self.assertNotIn("<script>alert", text)

    def test_no_http_or_https(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            run = _run_dir(tmp, sample_report())
            out = tmp / "certificate.html"
            write_certificate(run, out)
            text = out.read_text(encoding="utf-8")
            self.assertNotIn("http://", text)
            self.assertNotIn("https://", text)

    def test_proof_image_is_embedded(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            run = _run_dir(tmp, sample_report())
            (run / "proof_attempt1.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
            out = tmp / "certificate.html"
            write_certificate(run, out)
            self.assertIn("data:image/png;base64,",
                          out.read_text(encoding="utf-8"))

    def test_missing_script_does_not_break(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            run = _run_dir(tmp, sample_report(script=str(tmp / "nope.py")))
            out = tmp / "certificate.html"
            written = write_certificate(run, out)
            self.assertTrue(written.exists())
            self.assertIn("<html", written.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
