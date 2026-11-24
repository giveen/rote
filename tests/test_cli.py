"""Tests for the learn command's refusals and the row aligner.

These pin the cases where `learn` must say no before spending anything: empty data, a
dead app, a spent budget — plus the alignment rule that exact matches always apply.
"""
from __future__ import annotations

import argparse
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from rote import cli
from rote.cli import _align_rows, _load_rows, cmd_learn
from rote.client import BudgetExceeded
from rote.plan import Plan, Step


def make_plan(rows: list[dict[str, str]] | None = None,
              steps: list[Step] | None = None) -> Plan:
    if rows is None:
        rows = [{"sku": "A"}]
    if steps is None:
        steps = [Step("type", "SKU", "{sku}")]
    return Plan(app="Stockroom", goal="log parts", rows=rows,
                steps=steps, expected_effect="a line appears")


def learn_args(video: Path, out: Path, rows: Path | None = None,
               url: str = "http://127.0.0.1:8765/app.html") -> argparse.Namespace:
    return argparse.Namespace(video=str(video), out=str(out),
                              rows=str(rows) if rows else None, url=url,
                              budget=10.0, repairs=0, effort="max", hint=None,
                              headed=False)


class TestEmptyDataRefused(unittest.TestCase):
    def test_load_rows_refuses_an_empty_file(self):
        """A zero-row file hands _load_rows a verdict with nothing in it, so it raises."""
        with TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.json"
            empty.write_text("[]")
            with self.assertRaises(ValueError) as ctx:
                _load_rows(empty, make_plan())
        self.assertIn("0 rows", str(ctx.exception))

    def test_learn_refuses_empty_data_before_any_model_call(self):
        """The refusal happens before understand is ever called: no calls, non-zero exit."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "intake.mp4"
            video.write_bytes(b"fake")
            rows = root / "empty.json"
            rows.write_text("[]")
            buf = io.StringIO()
            with mock.patch("rote.cli.understand") as understand, \
                    mock.patch("rote.cli.reachable", return_value=(True, "")):
                with redirect_stdout(buf):
                    code = cmd_learn(learn_args(video, root / "out", rows))
            self.assertNotEqual(code, 0)
            understand.assert_not_called()
            self.assertIn("0 rows", buf.getvalue())


class TestPreflightRefusal(unittest.TestCase):
    def test_an_unreachable_app_spends_no_model_calls(self):
        """When the preflight fails, learn says which URL failed and exits non-zero
        without ever calling understand."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "intake.mp4"
            video.write_bytes(b"fake")
            rows = root / "rows.json"
            rows.write_text(json.dumps([{"sku": "A"}]))
            buf = io.StringIO()
            with mock.patch("rote.cli.understand") as understand, \
                    mock.patch("rote.cli.reachable",
                               return_value=(False, "Error: connection refused")):
                with redirect_stdout(buf):
                    code = cmd_learn(learn_args(video, root / "out", rows,
                                                url="http://127.0.0.1:9/app.html"))
            self.assertNotEqual(code, 0)
            understand.assert_not_called()
            self.assertIn("http://127.0.0.1:9/app.html", buf.getvalue())
            self.assertIn("connection refused", buf.getvalue())


class TestBudgetRefusal(unittest.TestCase):
    def test_budget_exceeded_from_understand_prints_and_exits_one(self):
        """A spent budget is a printed refusal with exit 1 and a written report when a
        plan exists — not an uncaught traceback."""
        plan = make_plan()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "intake.mp4"
            video.write_bytes(b"fake")
            rows = root / "rows.json"
            rows.write_text(json.dumps([{"sku": "A"}]))
            buf = io.StringIO()
            with mock.patch("rote.cli.reachable", return_value=(True, "")), \
                    mock.patch("rote.cli.understand", return_value=plan), \
                    mock.patch("rote.cli.replay",
                               side_effect=BudgetExceeded("stopping: $0.0000 left")):
                with redirect_stdout(buf):
                    code = cmd_learn(learn_args(video, root / "out", rows))
            self.assertEqual(code, 1)
            self.assertIn("stopping", buf.getvalue())
            self.assertTrue((root / "out" / "report.md").exists(),
                            "the report must still be written when a plan exists")


class TestAlignment(unittest.TestCase):
    def test_exact_and_canonical_match_despite_two_extra_columns(self):
        """The audit case: `sku` must land on plan key `SKU` even with two unrecognised
        columns present — the old `(A or B) if one candidate` parse skipped it."""
        plan = make_plan(rows=[{"SKU": "A"}], steps=[])
        aligned = _align_rows([{"sku": "A", "extra1": "x", "extra2": "y"}], plan)
        self.assertEqual(aligned[0]["SKU"], "A")

    def test_prefix_match_applies_when_one_candidate_left(self):
        """`zip` is a prefix of plan key `zip_postal_code`: alone, it is the only guess
        and it applies."""
        plan = make_plan(rows=[{"zip_postal_code": "94107"}])
        aligned = _align_rows([{"zip": "94107"}], plan)
        self.assertEqual(aligned[0]["zip_postal_code"], "94107")

    def test_prefix_match_stays_off_when_ambiguous(self):
        """With two candidates the prefix guess is ambiguous, so it stays visible rather
        than silently filling the wrong field."""
        plan = make_plan(rows=[{"zip_postal_code": "94107"}])
        aligned = _align_rows([{"zip": "94107", "other": "x"}], plan)
        self.assertNotIn("zip_postal_code", aligned[0])


class TestSingleRowKeys(unittest.TestCase):
    def test_only_plan_defines_row_keys(self):
        """The one key list lives in plan.py; cli and synth import it, never redefine."""
        self.assertFalse(hasattr(cli, "_row_keys"), "rote.cli must not define _row_keys")
        import rote.synth as synth
        self.assertFalse(hasattr(synth, "_row_keys"), "rote.synth must not define _row_keys")


if __name__ == "__main__":
    unittest.main()
