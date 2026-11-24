"""Tests for the dependency audit.

The audit itself needs the network (it asks OSV about exact versions), so what is tested here is
the committed result: it must stay well formed, and it must stay clean. If a dependency later
gains an advisory, re-running the audit changes the file and this test fails — which is the
point of keeping it.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "dependencies.json"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "dependency_audit", ROOT / "tools" / "dependency_audit.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


class TestCommittedAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = json.loads(AUDIT.read_text())

    def test_audit_exists_and_covers_the_dependencies(self):
        self.assertGreaterEqual(len(self.rows), 5, "the audit looks truncated")
        names = {r["name"].lower() for r in self.rows}
        self.assertIn("playwright", names)
        self.assertIn("httpx", names)

    def test_every_package_is_pinned_and_licensed(self):
        for r in self.rows:
            self.assertRegex(r["version"], r"^\d", f"{r['name']} has no version")
            self.assertTrue(r["licence"], f"{r['name']} has no licence recorded")

    def test_no_known_advisories(self):
        flagged = [(r["name"], r["advisories"]) for r in self.rows if r["advisories"]]
        self.assertEqual(flagged, [], f"dependencies gained advisories: {flagged}")


class TestSeverityParsing(unittest.TestCase):
    def test_reads_a_cvss_score(self):
        mod = load_module()
        self.assertEqual(mod._severity({"severity": [{"score": "CVSS:3.1/7.5"}]}),
                         "CVSS:3.1/7.5")

    def test_falls_back_to_database_severity(self):
        mod = load_module()
        self.assertEqual(mod._severity({"database_specific": {"severity": "HIGH"}}), "HIGH")

    def test_unknown_when_silent(self):
        self.assertEqual(load_module()._severity({}), "unknown")


if __name__ == "__main__":
    unittest.main()
