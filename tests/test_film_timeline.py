"""Timeline invariants: non-empty, positive, 120-180s, known kinds, files exist, deterministic."""
from __future__ import annotations
import sys
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from film_timeline import (BAND, CONTENT_H, FRAME_H, FRAME_W, CAPTION_WRAP,
                           MAX_CAPTION_LINES, build_timeline, content_box)

KNOWN = {"card", "terminal", "clip", "image"}

class TestFilmTimeline(unittest.TestCase):
    def test_non_empty_and_fields(self):
        segs = build_timeline()
        self.assertTrue(segs)
        for s in segs:
            self.assertGreater(s.seconds, 0, s)
            self.assertTrue(s.caption and s.caption.strip(), s)

    def test_total_between_120_and_180(self):
        total = sum(s.seconds for s in build_timeline())
        self.assertGreaterEqual(total, 120)
        self.assertLessEqual(total, 180)

    def test_kinds_known(self):
        for s in build_timeline():
            self.assertIn(s.kind, KNOWN)

    def test_file_sources_exist(self):
        for s in build_timeline():
            if s.kind == "card":
                continue
            p = ROOT / s.source
            self.assertTrue(p.exists(), f"missing {s.source}")

    def test_deterministic(self):
        a = build_timeline()
        b = build_timeline()
        self.assertEqual(a, b)

    def test_content_box_reserves_caption_band(self):
        self.assertEqual(BAND, 130)
        self.assertEqual(CONTENT_H, 670)
        self.assertEqual(FRAME_H, 800)
        self.assertEqual(670 + 130, FRAME_H)
        self.assertEqual(FRAME_H - BAND, CONTENT_H)
        for kind in KNOWN:
            x, y, w, h = content_box(kind)
            self.assertGreater(w, 0, kind)
            self.assertGreater(h, 0, kind)
            self.assertLessEqual(x + w, FRAME_W, kind)
            self.assertLessEqual(y + h, 670, kind)
            self.assertLessEqual(y + h, FRAME_H - BAND, kind)
            self.assertEqual((x, y, w, h), (0, 0, 1280, 670), kind)

    def test_captions_fit_two_lines_when_wrapped(self):
        for s in build_timeline():
            lines = textwrap.wrap(s.caption, CAPTION_WRAP)
            self.assertLessEqual(len(lines), MAX_CAPTION_LINES, s)
            for line in lines:
                # 26px DejaVu Sans Mono is ~15.65px/char: 81 chars ≈ 1268px < 1280.
                self.assertLessEqual(len(line), 81, (s, line))

if __name__ == "__main__":
    unittest.main()
