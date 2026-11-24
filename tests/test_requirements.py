"""Tests that the dependency files stay pinned and reproducible.

A requirement like ``playwright>=1.40`` would silently install different code
than the code the results were measured on. These tests fail if anyone
reintroduces a range, or if the lock file drifts from the direct requirements.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
LOCK = ROOT / "requirements.lock.txt"

PINNED = re.compile(r"^[A-Za-z0-9._-]+==[A-Za-z0-9][A-Za-z0-9.!+_-]*$")


def read_requirements(path: Path) -> dict[str, str]:
    """Return {name: version} for the pinned lines, failing on anything else."""
    pinned: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        assert PINNED.match(line), f"{path.name}: not pinned as name==version: {line!r}"
        name, version = line.split("==", 1)
        pinned[name.lower()] = version
    return pinned


class TestRequirementsPinned(unittest.TestCase):
    def test_requirements_every_line_is_pinned(self):
        self.assertTrue(read_requirements(REQUIREMENTS),
                        "requirements.txt has no pinned requirements")

    def test_lock_every_line_is_pinned(self):
        self.assertTrue(read_requirements(LOCK),
                        "requirements.lock.txt has no pinned requirements")

    def test_requirements_match_the_lock(self):
        direct = read_requirements(REQUIREMENTS)
        locked = read_requirements(LOCK)
        for name, version in direct.items():
            self.assertIn(name, locked, f"{name} is missing from the lock file")
            self.assertEqual(locked[name], version,
                             f"{name}: requirements.txt says {version}, lock says {locked[name]}")


if __name__ == "__main__":
    unittest.main()
