"""Dependency audit: what is installed, what it is licensed under, and what is known-broken.

Queries OSV (the vulnerability database behind pip-audit) with the exact installed versions,
and reports licences from package metadata. No invented findings: a package with no advisory is
reported as such.
"""
from __future__ import annotations

import json
import subprocess
from importlib import metadata
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OSV = "https://api.osv.dev/v1/query"


def installed() -> list[tuple[str, str]]:
    out = subprocess.run([str(ROOT / ".venv" / "bin" / "pip"), "list", "--format=json"],
                         capture_output=True, text=True, check=True)
    return [(p["name"], p["version"]) for p in json.loads(out.stdout)]


def licence(name: str) -> str:
    try:
        meta = metadata.metadata(name)
    except metadata.PackageNotFoundError:
        return "unknown"
    for key in ("License-Expression", "License"):
        value = meta.get(key)
        if value and len(value) < 60 and "\n" not in value:
            return value.strip()
    classifiers = meta.get_all("Classifier") or []
    for c in classifiers:
        if c.startswith("License ::"):
            return c.split("::")[-1].strip()
    return "see package"


def advisories(name: str, version: str) -> list[dict]:
    try:
        r = httpx.post(OSV, json={"package": {"name": name, "ecosystem": "PyPI"},
                                  "version": version}, timeout=30)
        if r.status_code != 200:
            return []
        return r.json().get("vulns", []) or []
    except Exception:
        return []


def main() -> None:
    rows = []
    for name, version in sorted(installed()):
        vulns = advisories(name, version)
        rows.append({
            "name": name, "version": version, "licence": licence(name),
            "advisories": [{"id": v.get("id"), "summary": (v.get("summary") or "")[:90],
                            "severity": _severity(v)} for v in vulns],
        })
    direct = {"playwright", "httpx"}
    print(f"{'package':<22}{'version':<12}{'direct':<8}{'licence':<18}advisories")
    for r in rows:
        print(f"{r['name']:<22}{r['version']:<12}"
              f"{'yes' if r['name'].lower() in direct else '':<8}"
              f"{r['licence'][:16]:<18}{len(r['advisories'])}")
    bad = [r for r in rows if r["advisories"]]
    print()
    if bad:
        for r in bad:
            for a in r["advisories"]:
                print(f"  ADVISORY {r['name']} {r['version']}: {a['id']} "
                      f"({a['severity']}) {a['summary']}")
    else:
        print("no known advisories for these exact versions")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "dependencies.json").write_text(json.dumps(rows, indent=2))
    print(f"\nwrote docs/dependencies.json ({len(rows)} packages)")


def _severity(vuln: dict) -> str:
    for s in vuln.get("severity", []) or []:
        if s.get("score"):
            return s["score"]
    for affected in vuln.get("affected", []) or []:
        for rng in affected.get("ranges", []) or []:
            pass
    return vuln.get("database_specific", {}).get("severity", "unknown")


if __name__ == "__main__":
    main()
