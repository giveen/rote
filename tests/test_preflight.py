"""Tests for the reachability preflight: a dead app must stop the run before it costs.

The preflight exists because the repair loop cannot fix an app that does not answer, so
an unreachable URL must be a clean refusal rather than four model calls spent discovering
it.
"""
from __future__ import annotations

import functools
import http.server
import os
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from rote.preflight import browser_available, reachable

_HAS_BROWSER = browser_available()[0]


@unittest.skipUnless(_HAS_BROWSER,
                     "no Chromium build installed (run playwright install chromium)")
class TestReachable(unittest.TestCase):
    def test_a_dead_port_is_not_reachable(self):
        """Port 9 (discard) has nothing listening: the answer is False and the reason
        says why, so the caller can print a useful message."""
        ok, why = reachable("http://127.0.0.1:9/app.html")
        self.assertFalse(ok)
        self.assertTrue(why, "a refusal must carry its reason")
        self.assertTrue(why.startswith("unreachable: "),
                        f"a dead port is unreachable, not a missing browser: {why}")

    def test_a_live_server_is_reachable(self):
        """A real answering server on a local port must come back True with no complaint."""
        with TemporaryDirectory() as tmp:
            Path(tmp, "app.html").write_text("<html><body>ok</body></html>")

            class Quiet(http.server.SimpleHTTPRequestHandler):
                def log_message(self, *args):  # keep access logs out of the test output
                    pass

            handler = functools.partial(Quiet, directory=tmp)
            with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                thread = threading.Thread(target=server.handle_request, daemon=True)
                thread.start()
                ok, why = reachable(f"http://127.0.0.1:{server.server_port}/app.html")
        self.assertTrue(ok, why)
        self.assertEqual(why, "")


class TestBrowserAvailable(unittest.TestCase):
    def test_no_browser_install_returns_a_browsers_reason(self):
        """With PLAYWRIGHT_BROWSERS_PATH pointed at an empty directory there is no
        Chromium build to launch, so browser_available says so — and the reason must
        be recognisably about browsers, not about the network. The environment is
        restored by patch.dict so other tests are unaffected."""
        with TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"PLAYWRIGHT_BROWSERS_PATH": tmp}):
                ok, why = browser_available()
        self.assertFalse(ok)
        self.assertTrue(why, "a refusal must carry its reason")
        self.assertIn("browsers not installed", why)


if __name__ == "__main__":
    unittest.main()
