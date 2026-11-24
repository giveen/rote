"""Run the generated automation against fresh data and decide whether it actually worked.

The verdict is not a model's opinion. It is: did the script run, and is the effect the same
effect the recording ended with — with data the recording never contained. That is the
difference between an automation and a recording of one.
"""
from __future__ import annotations

import importlib.util
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1280, "height": 800}


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class ReplayResult:
    passed: bool = False
    checks: list[Check] = field(default_factory=list)
    error: str | None = None
    end_state: Any = None
    page_text: str = ""
    screenshot: Path | None = None
    seconds: float = 0.0

    def as_evidence(self, limit: int = 1200) -> str:
        """What the repair loop gets to see: facts, not the whole page."""
        lines = [f"error: {self.error}"] if self.error else []
        for c in self.checks:
            lines.append(f"{'PASS' if c.ok else 'FAIL'} {c.name}: {c.detail}")
        if self.page_text:
            lines.append("page text after the run:\n" + self.page_text[:limit])
        return "\n".join(lines)


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"rote_gen_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def replay(script: Path, url: str, rows: list[dict[str, str]], *,
           screenshot: Path | None = None, headless: bool = True,
           timeout_ms: int = 15_000) -> ReplayResult:
    """Perform the task with new data, then look for the evidence that it worked."""
    res = ReplayResult()
    t0 = time.time()
    mod = _load(script)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport=VIEWPORT)
        page.set_default_timeout(timeout_ms)
        try:
            page.goto(url)
            mod.run(page, rows)
            page.wait_for_timeout(400)
            res.checks.append(Check("script runs on fresh data", True,
                                    f"{len(rows)} row(s) through {script.name}"))
        except Exception as e:
            res.error = f"{type(e).__name__}: {e}".strip()
            res.checks.append(Check("script runs on fresh data", False, res.error[:400]))
        try:
            res.end_state = page.evaluate("() => window.__submitted ?? null")
            res.page_text = page.inner_text("body")
        except Exception as e:
            res.error = res.error or f"could not read the page: {e}"
        if screenshot:
            try:
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot), full_page=True)
                res.screenshot = screenshot
            except Exception:
                pass
        browser.close()

    res.checks.extend(_judge_effect(res.end_state, res.page_text, rows))
    res.passed = all(c.ok for c in res.checks)
    res.seconds = time.time() - t0
    return res


def _judge_effect(end_state: Any, page_text: str, rows: list[dict[str, str]]) -> list[Check]:
    """The effect checks: did the app end up holding the data we sent, exactly?"""
    checks: list[Check] = []
    haystack = " ".join(page_text.split()).lower()

    missing = []
    for i, row in enumerate(rows):
        for key, value in row.items():
            if str(value).strip().lower() not in haystack:
                missing.append(f"row {i + 1} {key}={value!r}")
    checks.append(Check("every value reached the page", not missing,
                        "all " + str(sum(len(r) for r in rows)) + " values found"
                        if not missing else "missing: " + ", ".join(missing[:6])))

    if isinstance(end_state, dict) and "lines" in end_state:
        got = end_state["lines"]
        same_shape = len(got) == len(rows)
        matched = 0
        for want, have in zip(rows, got):
            if all(str(want.get(k, "")).strip().lower() == str(have.get(k2, "")).strip().lower()
                   for k, k2 in zip(want.keys(), have.keys())):
                matched += 1
        checks.append(Check(
            "the app stored exactly the rows we sent", same_shape and matched == len(rows),
            f"{matched}/{len(rows)} rows stored as sent"
            + ("" if same_shape else f", {len(got)} rows in the app")))
        checks.append(Check("the task was submitted", True,
                            f"{len(got)} line(s) confirmed by the app"))
    return checks
