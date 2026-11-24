"""Tests for the plan contract — the answer Ember gives about a recording."""
from __future__ import annotations

import json
import unittest

from rote.plan import PLAN_SCHEMA, Plan, Step, coverage


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


if __name__ == "__main__":
    unittest.main()
