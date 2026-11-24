"""Tests for the runtime helpers shared by the recorder and every generated script.

These functions are the only thing standing between "a model described the app" and "the
browser did the right thing", so their edge cases are pinned rather than trusted.
"""
from __future__ import annotations

import unittest

from rote.scriptenv import _key, _ns, _to_iso_date, _truthy

to_iso_date = _to_iso_date


class TestDates(unittest.TestCase):
    def test_iso_passes_through(self):
        self.assertEqual(to_iso_date("2026-03-01"), "2026-03-01")

    def test_unambiguous_formats_are_converted(self):
        self.assertEqual(to_iso_date("1 Mar 2026"), "2026-03-01")
        self.assertEqual(to_iso_date("2026/03/01"), "2026-03-01")

    def test_slash_dates_are_refused_because_they_are_ambiguous(self):
        """03/01/2026 is either March 1st or January 3rd. Guessing silently corrupts data."""
        self.assertIsNone(to_iso_date("03/01/2026"))
        self.assertIsNone(to_iso_date("01/03/2026"))

    def test_nonsense_is_refused(self):
        self.assertIsNone(to_iso_date("tomorrow"))
        self.assertIsNone(to_iso_date(""))


class TestTruthy(unittest.TestCase):
    def test_affirmatives(self):
        for value in ("true", "TRUE", "yes", "y", "on", "1", "checked", " True "):
            self.assertTrue(_truthy(value), value)

    def test_everything_else_is_false(self):
        for value in ("false", "no", "", "0", "off", "maybe"):
            self.assertFalse(_truthy(value), value)


class TestRowKeys(unittest.TestCase):
    ROW = {"sku": "A", "Unit Cost": "9.95", "zip": "94107"}

    def test_exact_key(self):
        self.assertEqual(_key(self.ROW, "sku"), "sku")

    def test_case_and_spacing_variants(self):
        self.assertEqual(_key(self.ROW, "SKU"), "sku")
        self.assertEqual(_key(self.ROW, "Sku"), "sku")
        self.assertEqual(_key(self.ROW, "unit_cost"), "Unit Cost")

    def test_missing_key_says_what_exists(self):
        with self.assertRaises(KeyError) as ctx:
            _key(self.ROW, "colour")
        message = str(ctx.exception)
        self.assertIn("colour", message)
        self.assertIn("sku", message, "the error should list what the row does have")


class TestHelpersAreShared(unittest.TestCase):
    def test_the_module_exports_what_generated_scripts_get(self):
        for name in ("_field", "_button", "_fill", "_select", "_tick", "_key", "_first_present"):
            self.assertIn(name, _ns, f"{name} missing from the shared script environment")


if __name__ == "__main__":
    unittest.main()
