"""Tests for the two checks that catch a loop which only pretends to iterate.

Both exist because of one real failure: a plan whose repeating block only filled a form was
reported as PASSED with three rows, while the app received one order.
"""
from __future__ import annotations

import unittest

from rote.plan import Step
from rote.replay import _cycles, structural_checks

FORM_ONLY = [Step("type", "SKU", "{sku}"), Step("type", "Qty", "{qty}")]
WITH_COMMIT = FORM_ONLY + [Step("click", "Add line")]


class TestStructuralChecks(unittest.TestCase):
    def test_a_block_that_only_types_is_refused_for_multiple_rows(self):
        checks = structural_checks(FORM_ONLY, (1, 2), 3)
        self.assertTrue(checks and not checks[0].ok)
        self.assertIn("overwrite", checks[0].detail)

    def test_a_block_with_a_commit_is_accepted(self):
        checks = structural_checks(WITH_COMMIT, (1, 3), 3)
        self.assertTrue(checks[0].ok)

    def test_single_row_needs_no_check(self):
        self.assertEqual(structural_checks(FORM_ONLY, (1, 2), 1), [])

    def test_no_repeat_range_needs_no_check(self):
        self.assertEqual(structural_checks(FORM_ONLY, None, 5), [])


class TestCycleCheck(unittest.TestCase):
    def test_one_cycle_per_row_passes(self):
        events = [("iteration", "https://app/shop.html")] * 3
        checks = _cycles(events, 3)
        self.assertTrue(checks[0].ok)
        self.assertIn("shop.html", checks[0].detail)

    def test_too_few_cycles_fails(self):
        events = [("iteration", "https://app/shop.html")] * 2
        checks = _cycles(events, 3)
        self.assertFalse(checks[0].ok)

    def test_each_iteration_ending_elsewhere_fails(self):
        events = [("iteration", f"https://app/step{i}.html") for i in range(4)]
        checks = _cycles(events, 4)
        self.assertFalse(checks[0].ok)
        self.assertIn("different page", checks[0].detail)

    def test_single_row_needs_no_check(self):
        self.assertEqual(_cycles([("iteration", "x")], 1), [])


if __name__ == "__main__":
    unittest.main()
