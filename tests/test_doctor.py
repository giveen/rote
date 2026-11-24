"""Tests for `rote doctor`: the first-run gate before anything is learned.

The checks are pure (`run_checks` returns `Check` objects, never prints),
so every test here runs without a network or a browser: the network and
browser probes are faked or skipped with `--offline`.
"""
from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from rote.client import api_key
from rote.doctor import (Check, check_api_key, check_api_reachable,
                         check_python_version, cmd_doctor, exit_code,
                         format_check, run_checks, shorten)

_FAKE_OK = (True, "")
_FAKE_MISSING = (False, "browsers not installed: Executable doesn't exist")


def _checks(*, offline=True, **kwargs):
    """run_checks with the browser and network probes faked off."""
    kwargs.setdefault("browser_available_fn", lambda: _FAKE_OK)
    kwargs.setdefault("count_tokens_fn", lambda word: 1)
    return run_checks(offline=offline, **kwargs)


def _by_name(checks, needle):
    for c in checks:
        if needle.lower() in c.name.lower():
            return c
    raise AssertionError(f"no check matching {needle!r}: {[c.name for c in checks]}")


class TestPythonVersion(unittest.TestCase):
    def test_old_python_fails(self):
        """A Python older than 3.12 must fail the version check, with a fix."""
        check = check_python_version((3, 11, 0))
        self.assertFalse(check.ok)
        self.assertIn("3.11", check.detail)
        self.assertTrue(check.fix, "a failure must say how to fix it")

    def test_current_python_passes(self):
        """The Python running this suite satisfies the check."""
        check = check_python_version()
        self.assertTrue(check.ok, check.detail)
        # and when driven through run_checks with the real interpreter's version
        via_run = _by_name(_checks(python_version=sys.version_info), "Python")
        self.assertTrue(via_run.ok)
        via_old = _by_name(_checks(python_version=(3, 10, 5)), "Python")
        self.assertFalse(via_old.ok)


class TestApiKeySource(unittest.TestCase):
    def test_environment_variable_is_reported_as_the_source(self):
        """With MODEL_API_KEY set the detail names the environment, never the key."""
        with mock.patch.dict(os.environ, {"MODEL_API_KEY": "env-secret-123"}):
            check = check_api_key()
        self.assertTrue(check.ok, check.detail)
        self.assertIn("MODEL_API_KEY", check.detail)
        self.assertIn("environment", check.detail)
        self.assertNotIn("env-secret-123", check.detail)
        self.assertNotIn("env-secret-123", check.fix)

    def test_config_file_is_reported_as_the_source(self):
        """With only the config file present the detail names the file."""
        with TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "auth.json"
            cfg.write_text(json.dumps(
                {"providers": {"meta": {"api_key": "file-secret-456"}}}))
            with mock.patch.dict(os.environ, {"MODEL_API_KEY": ""}):
                # the path parameter points the lookup at the temporary file
                self.assertEqual(api_key(cfg), "file-secret-456")
                check = check_api_key(cfg)
                via_run = _by_name(_checks(auth_path=cfg), "API key")
        self.assertTrue(check.ok, check.detail)
        self.assertIn("auth.json", check.detail)
        self.assertNotIn("file-secret-456", check.detail)
        self.assertTrue(via_run.ok, via_run.detail)
        self.assertIn("auth.json", via_run.detail)

    def test_missing_key_fails_with_the_export_fix(self):
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            with mock.patch.dict(os.environ, {"MODEL_API_KEY": ""}):
                check = check_api_key(missing)
        self.assertFalse(check.ok)
        self.assertIn("export MODEL_API_KEY", check.fix)


class TestOffline(unittest.TestCase):
    def test_offline_never_reports_the_api_check_as_a_failure(self):
        """--offline skips the network probe: the API check cannot fail."""
        with mock.patch("rote.doctor.count_tokens") as count, \
                mock.patch("rote.doctor.browser_available",
                           return_value=_FAKE_OK):
            check = _by_name(run_checks(offline=True), "API reachable")
        self.assertTrue(check.ok, check.detail)
        self.assertNotIn("unreachable", check.detail)
        count.assert_not_called()

    def test_online_fakes_it_via_injection(self):
        """Without --offline a faked answering API passes, no network touched."""
        with mock.patch.dict(os.environ, {"MODEL_API_KEY": "test-key"}):
            checks = _checks(offline=False, count_tokens_fn=lambda word: 2)
            self.assertTrue(_by_name(checks, "API reachable").ok)
            checks = _checks(offline=False,
                             count_tokens_fn=mock.Mock(side_effect=RuntimeError("down")))
            self.assertFalse(_by_name(checks, "API reachable").ok)


class TestSkippedApiWhenKeyMissing(unittest.TestCase):
    def test_failing_key_check_skips_api_check(self):
        """A missing key skips the API probe instead of blaming the network."""
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            calls: list[str] = []

            def fake_count(word):
                calls.append(word)
                return 1

            with mock.patch.dict(os.environ, {"MODEL_API_KEY": ""}):
                checks = _checks(offline=False, auth_path=missing,
                                 count_tokens_fn=fake_count)
        key = _by_name(checks, "API key")
        api = _by_name(checks, "API reachable")
        self.assertFalse(key.ok)
        self.assertTrue(api.ok, api.detail)
        self.assertIn("skipped", api.detail.lower())
        self.assertIn("no api key", api.detail.lower())
        self.assertEqual(calls, [])
        self.assertTrue(format_check(api).startswith("⚠"),
                        format_check(api))
        self.assertEqual(exit_code(checks), 1)

    def test_skipped_api_check_does_not_fail_passing_run(self):
        """A skipped API check alone never flips a passing run to exit 1."""
        checks = [
            Check("Python version", True, "Python 3.14.0 (>= 3.12)"),
            Check("Dependencies", True, "playwright, httpx imported"),
            Check("Chromium installed", True, "Chromium launched"),
            Check("API key present", True,
                  "found in ~/.config/muse/auth.json"),
            Check("API reachable", True,
                  "skipped (no API key to test with)"),
        ]
        self.assertEqual(exit_code(checks), 0)

    def test_unreadable_key_is_credential_problem_not_network(self):
        """If the key file vanishes under the API probe, blame the key."""
        def fake_count(word):
            raise FileNotFoundError(
                "[Errno 2] No such file or directory: '/fake/auth.json'")

        check = check_api_reachable(count_tokens_fn=fake_count)
        self.assertFalse(check.ok)
        self.assertIn("API key", check.detail)
        self.assertIn("MODEL_API_KEY", check.fix)
        self.assertNotIn("FileNotFoundError", check.detail)
        self.assertNotIn("No such file", check.detail)
        self.assertNotIn("check your network", check.fix)
        line = format_check(check)
        self.assertNotIn("FileNotFoundError", line)
        self.assertNotIn("No such file", line)


class TestExitCode(unittest.TestCase):
    def test_failing_list_exits_one(self):
        """One failing check in a fake list is exit 1."""
        checks = [Check("Python version", True, "3.14"),
                  Check("Chromium installed", False, "not installed", "fix it")]
        self.assertEqual(exit_code(checks), 1)

    def test_passing_list_exits_zero(self):
        checks = [Check("Python version", True, "3.14"),
                  Check("Chromium installed", True, "launched")]
        self.assertEqual(exit_code(checks), 0)

    def test_cmd_doctor_maps_the_fake_list_to_the_exit_code(self):
        """cmd_doctor over a fake list prints the verdict and returns 0 or 1."""
        buf = io.StringIO()
        with mock.patch("rote.doctor.run_checks",
                        return_value=[Check("Python version", True, "3.14")]):
            with redirect_stdout(buf):
                code = cmd_doctor(mock.Mock(offline=False, verbose=False))
        self.assertEqual(code, 0)
        self.assertIn("ready to learn", buf.getvalue())

        buf = io.StringIO()
        with mock.patch("rote.doctor.run_checks",
                        return_value=[Check("Chromium installed", False,
                                            "not installed",
                                            "./.venv/bin/playwright install chromium")]):
            with redirect_stdout(buf):
                code = cmd_doctor(mock.Mock(offline=False, verbose=False))
        self.assertEqual(code, 1)
        self.assertIn("not ready", buf.getvalue())
        self.assertIn("playwright install chromium", buf.getvalue())


class TestShorten(unittest.TestCase):
    _BOXED = (
        "Chromium not installed (browsers not installed: Error: "
        "BrowserType.launch: Executable doesn't exist at "
        "/tmp/none/chromium_headless_shell-1255/chrome-headless-shell-linux64/"
        "chrome-headless-shell\n"
        "╔════════════════════════════════════════════════════════════╗\n"
        "║ Looks like Playwright was just installed or updated.       ║\n"
        "║ Please run the following command to download new browsers: ║\n"
        "║     playwright install                                     ║\n"
        "╚════════════════════════════════════════════════════════════╝)"
    )

    def test_multiline_reason_with_box_collapses_to_first_line(self):
        """Only the first meaningful line survives; no box, no newline."""
        short = shorten(self._BOXED)
        self.assertNotIn("\n", short)
        for box_char in "╔╗╚╝║═":
            self.assertNotIn(box_char, short)
        self.assertNotIn("Please run", short)
        self.assertIn("Chromium not installed", short)
        self.assertIn("Executable", short)
        self.assertLessEqual(len(short), 100)
        self.assertTrue(short.endswith("…"), short)

    def test_short_input_passes_through(self):
        """A reason already within the limit is returned unchanged."""
        self.assertEqual(shorten("Chromium launched"), "Chromium launched")
        self.assertEqual(shorten(""), "")

    def test_leading_banner_is_skipped(self):
        """A banner before the error never becomes the shown line."""
        boxed = ("╔════════════════════════════╗\n"
                 "║ Looks like Playwright was just installed or updated. ║\n"
                 "╚════════════════════════════╝\n"
                 "real error line")
        self.assertEqual(shorten(boxed), "real error line")

    def test_limit_is_respected(self):
        """The result never exceeds the limit, and ends with an ellipsis."""
        out = shorten("x" * 500, limit=100)
        self.assertEqual(len(out), 100)
        self.assertTrue(out.endswith("…"))

    def test_format_check_is_one_line_with_fix(self):
        """The rendered check is one line, capped, with the fix after →."""
        line = format_check(Check("Chromium installed", False,
                                  self._BOXED,
                                  "./.venv/bin/playwright install chromium"))
        self.assertNotIn("\n", line)
        for box_char in "╔╗╚╝║═":
            self.assertNotIn(box_char, line)
        self.assertIn("→ ./.venv/bin/playwright install chromium", line)

    def test_verbose_prints_full_reason_indented(self):
        """--verbose shows the full multi-line detail under the one line."""
        verbose_buf = io.StringIO()
        with mock.patch("rote.doctor.run_checks",
                        return_value=[Check("Chromium installed", False,
                                            self._BOXED,
                                            "./.venv/bin/playwright install chromium")]):
            with redirect_stdout(verbose_buf):
                code = cmd_doctor(mock.Mock(offline=False, verbose=True))
        self.assertEqual(code, 1)
        verbose_out = verbose_buf.getvalue()
        self.assertIn("Please run", verbose_out)
        self.assertTrue(
            any(line.startswith("  ") and "Please run" in line
                for line in verbose_out.splitlines()),
            verbose_out)

        plain_buf = io.StringIO()
        with mock.patch("rote.doctor.run_checks",
                        return_value=[Check("Chromium installed", False,
                                            self._BOXED,
                                            "./.venv/bin/playwright install chromium")]):
            with redirect_stdout(plain_buf):
                code = cmd_doctor(mock.Mock(offline=False, verbose=False))
        self.assertEqual(code, 1)
        plain_out = plain_buf.getvalue()
        self.assertNotIn("Please run", plain_out)
        for box_char in "╔╗╚╝║═":
            self.assertNotIn(box_char, plain_out)


if __name__ == "__main__":
    unittest.main()
