"""Tests for the demo app that recordings are made against.

The app drives itself from ?s=N, replaying the first N actions. That is what makes a
recording reproducible frame by frame, so the action list and the markup must agree.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app" / "app.html"
HTML = APP.read_text()

ACTION_IDS = re.findall(r"const ACTIONS = \[(.*?)\n\];", HTML, re.S)[0]
SET_IDS = re.findall(r"set\('([a-z]+)'", ACTION_IDS)
CLICK_IDS = re.findall(r"getElementById\('([a-z]+)'\)\.click", ACTION_IDS)


class TestDemoApp(unittest.TestCase):
    def test_every_field_a_session_types_into_exists(self):
        for field_id in SET_IDS:
            self.assertIn(f'id="{field_id}"', HTML, f"no element with id {field_id}")

    def test_every_button_a_session_clicks_exists(self):
        self.assertTrue(CLICK_IDS)
        for btn in CLICK_IDS:
            self.assertIn(f'id="{btn}"', HTML, f"no button with id {btn}")

    def test_action_count_matches_recorder(self):
        """rames are captured for s=0..len(ACTIONS); the recorder hard-codes the range."""
        self.assertEqual(len(re.findall(r"\(\) => \{", ACTION_IDS)), 15,
                         "the recorded session changed length without updating the recorder")

    def test_labels_are_visible_text(self):
        """Ember names controls by their visible label, so each input needs a real one."""
        for field_id in SET_IDS:
            self.assertRegex(HTML, rf'<label for="{field_id}">[^<]{{2,}}</label>',
                             f"{field_id} has no visible label")

    def test_light_and_dark_are_both_defined(self):
        self.assertIn("prefers-color-scheme: light", HTML)
        self.assertIn("--bg:#0f1115", HTML)

    def test_narrow_screens_collapse_the_grid(self):
        self.assertIn("max-width: 720px", HTML)
        self.assertIn(".grid { grid-template-columns: 1fr; }", HTML)

    def test_submit_records_end_state_for_the_proof(self):
        """The replay's verdict reads window.__submitted, so the app must expose it."""
        self.assertIn("window.__submitted", HTML)


if __name__ == "__main__":
    unittest.main()
