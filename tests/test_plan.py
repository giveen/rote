"""Tests for the plan contract — the answer Ember gives about a recording."""
from __future__ import annotations

import json
import unittest

from rote.plan import PLAN_SCHEMA, Plan, Step, align_rows, coverage, row_keys


def sample() -> dict:
    return {
        "app": "Stockroom",
        "goal": "Log two received parts lines",
        "fields": [{"label": "SKU", "control": "text", "example": "BRK-2041"}],
        "steps": [
            {"action": "type", "target": "SKU", "value": "BRK-2041", "note": ""},
            {"action": "select", "target": "Supplier", "value": "Northwind Supply",
             "note": ""},
            {"action": "click", "target": "Add line", "value": None, "note": ""},
        ],
        "rows": [{"sku": "BRK-2041"}],
        "expected_effect": "A line appears in the intake table",
    }


class TestPlan(unittest.TestCase):
    def test_roundtrip(self):
        p = Plan.from_dict(sample())
        self.assertEqual(p.goal, "Log two received parts lines")
        self.assertEqual(len(p.steps), 3)
        again = Plan.from_json(json.dumps(p.to_dict()))
        self.assertEqual(again.to_dict(), p.to_dict())

    def test_schema_is_closed(self):
        """Every object in the schema forbids extra keys, so the API cannot return junk
        we then have to guess about."""
        def walk(node, path="$"):
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    self.assertIs(node.get("additionalProperties"), False,
                                  f"{path} does not forbid extra keys")
                for k, v in node.items():
                    walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")
        walk(PLAN_SCHEMA)

    def test_required_fields_present(self):
        for key in ("app", "goal", "fields", "steps", "rows", "expected_effect"):
            self.assertIn(key, PLAN_SCHEMA["required"])

    def test_coverage_full(self):
        p = Plan.from_dict(sample())
        expected = [Step("type", "SKU", "BRK-2041"),
                    Step("select", "Supplier", "Northwind Supply")]
        c = coverage(p, expected)
        self.assertEqual(c["matched"], 2)
        self.assertEqual(c["recall"], 1.0)

    def test_coverage_missing_step(self):
        p = Plan.from_dict(sample())
        expected = [Step("type", "SKU", "BRK-2041"), Step("submit", "Submit intake")]
        c = coverage(p, expected)
        self.assertEqual(c["matched"], 1)
        self.assertEqual(c["recall"], 0.5)
        self.assertIn("submit Submit intake", c["missed"])

    def test_coverage_is_forgiving_about_layout(self):
        p = Plan.from_dict(sample())
        expected = [Step("type", "  sku ", "brk-2041")]
        self.assertEqual(coverage(p, expected)["recall"], 1.0)

    def test_coverage_distinguishes_values(self):
        p = Plan.from_dict(sample())
        expected = [Step("type", "SKU", "FLT-1180")]
        self.assertEqual(coverage(p, expected)["recall"], 0.0)


class TestRepeatValidation(unittest.TestCase):
    """An inverted or impossible repeat range is a model error to report, not a loop to
    silently clamp into a different one (audit A9)."""

    def with_repeat(self, repeat):
        d = sample()
        d["repeat"] = repeat
        return Plan.from_dict(d)

    def test_a_valid_range_is_kept(self):
        p = self.with_repeat({"first": 2, "last": 4})
        self.assertEqual(p.repeat, (2, 4))
        self.assertIsNone(p.repeat_rejected)

    def test_no_range_stays_no_range(self):
        p = self.with_repeat(None)
        self.assertIsNone(p.repeat)
        self.assertIsNone(p.repeat_rejected)

    def test_inverted_range_is_rejected_with_a_reason(self):
        p = self.with_repeat({"first": 3, "last": 2})
        self.assertIsNone(p.repeat)
        self.assertIn("rejected", p.repeat_rejected)

    def test_step_numbers_below_one_are_rejected(self):
        for bad in ({"first": 0, "last": 2}, {"first": 1, "last": 0}, {"first": -1, "last": 3}):
            p = self.with_repeat(bad)
            self.assertIsNone(p.repeat, bad)
            self.assertIn("rejected", p.repeat_rejected, bad)

    def test_the_rejection_survives_a_roundtrip(self):
        p = self.with_repeat({"first": 3, "last": 2})
        again = Plan.from_json(json.dumps(p.to_dict()))
        self.assertEqual(again.to_dict(), p.to_dict())


class TestAlignRows(unittest.TestCase):
    def test_zip_aligns_to_zip_postal_code(self):
        """A user's `zip` column lands on the plan's `zip_postal_code` key."""
        plan = Plan(app="Swag Labs", goal="checkout",
                    rows=[{"first_name": "Ada", "last_name": "Lovelace",
                           "zip_postal_code": "24037"}],
                    steps=[], expected_effect="done")
        aligned = align_rows([{"first_name": "Grace", "last_name": "Hopper",
                               "zip": "20850"}], plan)
        self.assertEqual(aligned[0]["zip_postal_code"], "20850")
        self.assertEqual(aligned[0]["first_name"], "Grace")
        self.assertNotIn("zip", aligned[0])

    def test_matching_keys_returned_unchanged(self):
        """A row that already uses the plan's key names comes back as-is."""
        plan = Plan(app="Swag Labs", goal="checkout",
                    rows=[{"first_name": "Ada", "last_name": "Lovelace",
                           "zip_postal_code": "24037"}],
                    steps=[], expected_effect="done")
        rows = [{"first_name": "Grace", "last_name": "Hopper",
                 "zip_postal_code": "20850"}]
        self.assertEqual(align_rows(rows, plan), rows)


class TestRowKeys(unittest.TestCase):
    def test_row_keys_come_first_then_placeholders(self):
        """The single key list (audit A10): row keys in first-seen order, then {step}
        placeholders the rows never mentioned."""
        p = Plan.from_dict(sample())
        p.steps.append(Step("type", "Qty", "{qty}"))
        p.rows.append({"sku": "FLT-1180", "qty": "3"})
        self.assertEqual(row_keys(p), ["sku", "qty"])


if __name__ == "__main__":
    unittest.main()
