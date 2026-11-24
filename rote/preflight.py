"""A cheap reachability check before anything is spent.

The model cannot fix an app that does not answer, so `learn` opens the URL itself once
before `understand`: a navigation failure is the app's absence, not the plan's fault, and
must not cost a single repair call.
"""
from __future__ import annotations

from playwright.sync_api import sync_playwright

# Playwright reports a missing Chromium build this way; the text in the error is the
# signal, so the launch probe and the preflight both match on it.
_MISSING_BROWSER_MARKERS = (
    "Executable doesn't exist",
    "Looks like Playwright was just installed",
)


def _browsers_missing(error: BaseException) -> bool:
    """True when a launch failure is Playwright saying no build exists on this machine."""
    message = str(error)
    return any(marker in message for marker in _MISSING_BROWSER_MARKERS)


def browser_available() -> tuple[bool, str]:
    """True when a Chromium build can actually be launched, otherwise why not."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
    except Exception as e:
        reason = f"{type(e).__name__}: {e}".strip()
        if _browsers_missing(e):
            return False, f"browsers not installed: {reason}"
        return False, reason
    return True, ""


def reachable(url: str, *, timeout_ms: int = 15_000) -> tuple[bool, str]:
    """True when the app loads, otherwise the reason it did not.

    The reason is prefixed so the caller can tell the cases apart: "browsers not
    installed: ..." when this machine has no Chromium build to launch, "unreachable:
    ..." when a browser ran but the app did not answer.
    """
    available, reason = browser_available()
    if not available:
        return False, reason
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, timeout=timeout_ms)
            finally:
                browser.close()
    except Exception as e:
        if _browsers_missing(e):
            return False, f"browsers not installed: {type(e).__name__}: {e}".strip()
        return False, f"unreachable: {type(e).__name__}: {e}".strip()
    return True, ""
