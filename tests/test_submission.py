"""Tests for the submission packaging.

The form caps each written answer at 3,000 characters and the trajectory upload at 10 MB, and
it takes .json rather than .json.gz. Each of those is a way to discover a problem at the moment
of submitting, which is the worst moment. They are pinned here instead.
"""
from __future__ import annotations

import gzip
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission-upload"
CAP = 3000


class TestSubmissionBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["bash", str(ROOT / "tools" / "submission_files.sh")],
                       cwd=ROOT, check=True, capture_output=True, text=True)

    def test_answers_exist_and_fit_the_form(self):
        text = (OUT / "answers.md").read_text()
        sections = re.split(r"\n## ", text)[1:]
        self.assertGreaterEqual(len(sections), 3, "expected three written answers")
        for section in sections:
            title = section.splitlines()[0]
            body = section.split("\n", 1)[1].split("TXT")[0].strip()
            self.assertLessEqual(len(body), CAP,
                                 f"{title} is {len(body)} characters, over the {CAP} cap")
            self.assertGreater(len(body), 200, f"{title} looks empty")

    def test_trajectory_is_expanded_and_valid(self):
        """The form takes .json; the repository stores .json.gz. Expanding must not corrupt."""
        path = OUT / "muse-code-trajectory.json"
        self.assertTrue(path.exists(), "trajectory was not expanded")
        self.assertLess(path.stat().st_size, 10 * 1024 * 1024, "over the 10 MB upload limit")
        data = json.loads(path.read_text())
        source = json.load(gzip.open(ROOT / "prompts" / "muse-code-trajectory.json.gz", "rt"))
        self.assertEqual(len(data["events"]), len(source["events"]))

    def test_usage_screenshot_is_picked_up(self):
        """Kept in results/usage/ so rebuilding the bundle cannot silently lose it."""
        source = list((ROOT / "results" / "usage").glob("*.png"))
        self.assertTrue(source, "no usage screenshot in results/usage/ — capture one on Dec 2")
        shot = OUT / "usage-dashboard.png"
        self.assertTrue(shot.exists(), "the bundle did not pick the screenshot up")
        self.assertLess(shot.stat().st_size, 10 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
