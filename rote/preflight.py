"""A cheap reachability check before anything is spent.

The model cannot fix an app that does not answer, so `learn` opens the URL itself once
before `understand`: a navigation failure is the app's absence, not the plan's fault, and
must not cost a single repair call.
"""
from __future__ import annotations

from playwright.sync_api import sync_playwright


def reachable(url: str, *, timeout_ms: int = 15_000) -> tuple[bool, str]:
    """True when the app loads, otherwise the reason it did not."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, timeout=timeout_ms)
            finally:
                browser.close()
    except Exception as e:
        return False, f"{type(e).__name__}: {e}".strip()
    return True, ""
