"""Tests for the verifier.

These exist because the verifier once called a correct run a failure: the app rendered a
ticked checkbox as "yes", the check looked for the string "true", and the report blamed the
model. A verifier that lies is worse than no verifier, so its behaviour is pinned here.
"""
from __future__ import annotations

import unittest

from rote.replay import Check, _judge_effect, _matches, _norm, _records

ROWS = [{"company_name": "Brightline AB", "country": "Spain",
         "annual_spend": "78000", "send_welcome_pack": "true"}]


class TestNormalisation(unittest.TestCase):
    def test_boolean_spellings_are_one_thing(self):
        for word in ("true", "yes", "on", "1", "checked", "TRUE", " Yes "):
            self.assertEqual(_norm(word), ("bool", True), word)
        for word in ("false", "no", "off", "0", "unchecked"):
            self.assertEqual(_norm(word), ("bool", False), word)

    def test_text_stays_text(self):
        self.assertEqual(_norm("  Spain "), ("text", "spain"))

    def test_matches_boolean_against_how_the_app_rendered_it(self):
        self.assertTrue(_matches("true", ["yes"]))
        self.assertTrue(_matches("yes", ["true"]))
        self.assertFalse(_matches("true", ["no"]))

    def test_matches_text_with_whitespace_differences(self):
        self.assertTrue(_matches("Brightline AB", ["brightline  ab"]))
        self.assertFalse(_matches("Brightline AB", ["other ltd"]))


class TestJudging(unittest.TestCase):
    def test_ticked_checkbox_rendered_as_yes_passes(self):
        """The exact regression: this used to fail and cost two repair calls."""
        state = {"vendors": [{"company_name": "Brightline AB", "country": "Spain",
                              "annual_spend": "78000", "welcome_pack": True}]}
        page = ("Vendor created and welcome pack queued. Created company name "
                "Brightline AB country Spain annual spend 78000 welcome pack yes")
        checks = _judge_effect(state, page, ROWS)
        self.assertTrue(all(c.ok for c in checks),
                        [(c.name, c.detail) for c in checks if not c.ok])

    def test_missing_value_is_named(self):
        """A value that never landed must still fail loudly — the check moved, the verdict
        did not get kinder."""
        state = {"vendors": [{"company_name": "Someone Else", "country": "Spain",
                              "annual_spend": "78000", "welcome_pack": True}]}
        checks = _judge_effect(state, "Someone Else Spain 78000 yes", ROWS)
        visible = next(c for c in checks if c.name == "the values are visible on the final page")
        self.assertFalse(visible.ok)
        self.assertIn("Brightline AB", visible.detail)

    def test_confirmation_screen_that_does_not_echo_data_is_not_a_failure(self):
        """The checkout case: the values were accepted, the app ends on 'Thank you for your
        order' and shows none of them."""
        checks = _judge_effect(None, "Thank you for your order. Back home.",
                               [{"first_name": "Grace", "last_name": "Hopper"}],
                               expected_effect='A confirmation page says "Thank you for your '
                                               'order" once the checkout completes',
                               ran_clean=True)
        visible = next(c for c in checks if c.name.startswith("the values are visible"))
        self.assertTrue(visible.ok)
        self.assertIn("does not echo", visible.detail)

    def test_confirmation_without_a_reached_end_state_still_fails(self):
        """But if the app is not in the expected state either, missing values are a failure."""
        checks = _judge_effect(None, "Something unrelated happened.",
                               [{"first_name": "Grace"}],
                               expected_effect='A confirmation page says "Thank you for your '
                                               'order" once the checkout completes',
                               ran_clean=True)
        visible = next(c for c in checks if c.name.startswith("the values are visible"))
        self.assertFalse(visible.ok)

    def test_wrong_row_count_fails(self):
        state = {"vendors": [{"company_name": "Brightline AB", "country": "Spain",
                              "annual_spend": "78000", "welcome_pack": True}] * 2}
        page = "Brightline AB Spain 78000 78000 yes yes"
        checks = _judge_effect(state, page, ROWS)
        stored = [c for c in checks if c.name == "the app stored exactly the rows we sent"]
        self.assertTrue(stored and not stored[0].ok)

    def test_no_end_state_only_checks_the_page(self):
        checks = _judge_effect(None, "Brightline AB Spain 78000 yes", ROWS)
        self.assertTrue(all(c.ok for c in checks))
        self.assertFalse([c for c in checks if c.name.startswith("the app stored")],
                         "there is nothing to compare against without an end state")

    def test_records_are_found_under_common_keys(self):
        for key in ("lines", "vendors", "records", "items", "entries", "rows"):
            self.assertEqual(_records({key: [{"a": 1}]}), [{"a": 1}], key)
        self.assertIsNone(_records(None))
        self.assertIsNone(_records({"other": "thing"}))


class TestChecks(unittest.TestCase):
    def test_check_carries_its_detail(self):
        c = Check("name", False, "why")
        self.assertFalse(c.ok)
        self.assertEqual(c.detail, "why")


if __name__ == "__main__":
    unittest.main()
