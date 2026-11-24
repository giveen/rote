"""First-run doctor: are you ready to learn?

    rote doctor [--offline] [--verbose]

Checks, in order, that Python, the dependencies, Chromium, an API key and
the API itself are all in place — each failure with the exact command that
fixes it. Exit 0 when everything passes, 1 otherwise. `run_checks` is the
pure core: it returns a list of `Check` and never prints, so it is testable
without a network or a browser (pass fakes or patch the module functions).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from .preflight import browser_available
except Exception:  # pragma: no cover - playwright not installed
    browser_available = None  # type: ignore[assignment]

try:
    from .client import api_key, count_tokens
except Exception:  # pragma: no cover - httpx not installed
    api_key = None  # type: ignore[assignment]
    count_tokens = None  # type: ignore[assignment]

MIN_PYTHON = (3, 12)

KEY_FIX = "export MODEL_API_KEY=…  (or run `muse` once to sign in)"
BROWSER_FIX = "./.venv/bin/playwright install chromium"
DEPS_FIX = "./.venv/bin/pip install -r requirements.txt"
PYTHON_FIX = ("install Python 3.12 or newer and recreate the virtualenv "
              "(e.g. python3.12 -m venv .venv && ./.venv/bin/pip install -r requirements.txt)")
API_FIX = "check your network and API key, or run `rote doctor --offline`"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""
    fix: str = ""


def check_python_version(version_info: tuple[int, ...] | None = None, *,
                         python_version: tuple[int, ...] | None = None) -> Check:
    """True when the running Python is 3.12 or newer."""
    vi = version_info or python_version or sys.version_info
    major, minor = int(vi[0]), int(vi[1])
    micro = int(vi[2]) if len(vi) > 2 else 0
    version = f"{major}.{minor}.{micro}"
    ok = (major, minor) >= MIN_PYTHON
    if ok:
        return Check("Python version", True, f"Python {version} (>= 3.12)")
    return Check("Python version", False,
                 f"Python {version} (< 3.12)", PYTHON_FIX)


def check_dependencies() -> Check:
    """True when `playwright` and `httpx` import."""
    missing: list[str] = []
    for module in ("playwright", "httpx"):
        try:
            __import__(module)
        except Exception:
            missing.append(module)
    if missing:
        return Check("Dependencies", False,
                     "missing: " + ", ".join(missing), DEPS_FIX)
    return Check("Dependencies", True, "playwright, httpx imported")


def check_browser(browser_available_fn: Callable | None = None, *,
                  browser_fn: Callable | None = None) -> Check:
    """True when a Chromium build can be launched (reuse preflight)."""
    fn = browser_available_fn or browser_fn or browser_available
    if fn is None:
        return Check("Chromium installed", False,
                     "Chromium not installed (playwright unavailable)", BROWSER_FIX)
    try:
        available, reason = fn()
    except Exception as e:
        return Check("Chromium installed", False,
                     f"Chromium not installed ({type(e).__name__}: {e})", BROWSER_FIX)
    if available:
        return Check("Chromium installed", True, "Chromium launched")
    detail = f"Chromium not installed ({reason})" if reason else "Chromium not installed"
    return Check("Chromium installed", False, detail, BROWSER_FIX)


def check_api_key(auth_path: Path | str | None = None, *,
                  config_path: Path | str | None = None,
                  config_file: Path | str | None = None) -> Check:
    """True when an API key exists, by environment or config file.

    Never prints the key; the detail names where it was found.
    """
    cfg = auth_path or config_path or config_file
    if os.environ.get("MODEL_API_KEY"):
        return Check("API key present", True, "found in MODEL_API_KEY (environment)")
    try:
        if cfg is not None:
            import json
            data = json.loads(Path(cfg).read_text())
            key = data["providers"]["meta"]["api_key"]
        elif api_key is not None:
            key = api_key()
        else:  # pragma: no cover - client unavailable
            return Check("API key present", False,
                         "no API key found (client unavailable)", KEY_FIX)
    except FileNotFoundError:
        return Check("API key present", False,
                     f"no API key found (no ~/.config/muse/auth.json)", KEY_FIX)
    except Exception as e:
        return Check("API key present", False,
                     f"no API key found ({type(e).__name__}: {e})", KEY_FIX)
    if not key:
        return Check("API key present", False,
                     "no API key found (empty key)", KEY_FIX)
    return Check("API key present", True,
                 "found in ~/.config/muse/auth.json")


def check_api_reachable(count_tokens_fn: Callable | None = None, *,
                        token_count_fn: Callable | None = None,
                        offline: bool = False) -> Check:
    """True when the API answers one token-count request (costs nothing)."""
    if offline:
        return Check("API reachable", True, "skipped (--offline)")
    fn = count_tokens_fn or token_count_fn or count_tokens
    if fn is None:
        return Check("API reachable", False,
                     "unreachable (client unavailable)", API_FIX)
    try:
        n = fn("hi")
    except (FileNotFoundError, PermissionError, KeyError):
        return Check("API reachable", False,
                     "unreachable (API key file not found)", KEY_FIX)
    except Exception as e:
        return Check("API reachable", False,
                     f"unreachable ({type(e).__name__}: {e})", API_FIX)
    return Check("API reachable", True, f"answered ({n} tokens for one word)")


def run_checks(*, offline: bool = False,
               python_version: tuple[int, ...] | None = None,
               version_info: tuple[int, ...] | None = None,
               auth_path: Path | str | None = None,
               config_path: Path | str | None = None,
               config_file: Path | str | None = None,
               browser_available_fn: Callable | None = None,
               browser_fn: Callable | None = None,
               count_tokens_fn: Callable | None = None,
               token_count_fn: Callable | None = None) -> list[Check]:
    """Run the five checks in order. Never touches the network when `offline`."""
    cfg = auth_path or config_path or config_file
    vi = python_version or version_info
    python_check = check_python_version(vi)
    deps_check = check_dependencies()
    browser_check = check_browser(browser_available_fn or browser_fn)
    key_check = check_api_key(cfg)
    count_fn = count_tokens_fn or token_count_fn
    if offline:
        api_check = check_api_reachable(count_fn, offline=True)
    elif not key_check.ok:
        api_check = Check("API reachable", True,
                          "skipped (no API key to test with)")
    else:
        api_check = check_api_reachable(count_fn, offline=False)
    return [python_check, deps_check, browser_check, key_check, api_check]


def exit_code(checks: list[Check]) -> int:
    """0 when every required check passes, 1 otherwise."""
    return 0 if all(c.ok for c in checks) else 1


_BOX_CHARS = "╔╗╚╝║═│─"


def shorten(reason: str, limit: int = 100) -> str:
    """Collapse a possibly multi-line reason to one line, capped at *limit*.

    Playwright's missing-browser banner draws after the first error line, so
    only the first meaningful line is kept: empty lines and box-drawing
    banner lines are skipped, and a line that only exists to carry box
    characters contributes nothing. The kept line has its whitespace
    collapsed and is truncated with an ellipsis when it is too long.
    """
    if not reason or limit <= 0:
        return ""
    lines = reason.splitlines()
    if not lines:
        return ""
    candidate: str | None = None
    for line in lines:
        if any(c in _BOX_CHARS for c in line):
            continue
        collapsed = " ".join(line.split())
        if collapsed:
            candidate = collapsed
            break
    if candidate is None:
        for line in lines:
            cleaned = "".join(c for c in line if c not in _BOX_CHARS)
            cleaned = " ".join(cleaned.split())
            if cleaned:
                candidate = cleaned
                break
    if candidate is None:
        return ""
    if len(candidate) <= limit:
        return candidate
    if limit == 1:
        return "…"
    return candidate[: limit - 1].rstrip() + "…"


def format_check(check: Check) -> str:
    """One line: tick, cross, or warning (the skipped API check)."""
    if check.ok:
        symbol = "⚠" if "skipped" in check.detail else "✓"
    else:
        symbol = "✗"
    short = shorten(check.detail) if check.detail else ""
    line = f"{symbol} {check.name}: {short}" if short else f"{symbol} {check.name}"
    if not check.ok and check.fix:
        line += f" → {check.fix}"
    return line


def cmd_doctor(args) -> int:
    raw_verbose = getattr(args, "verbose", False)
    verbose = raw_verbose if isinstance(raw_verbose, bool) else False
    checks = run_checks(offline=bool(getattr(args, "offline", False)))
    for check in checks:
        print(format_check(check))
        if verbose and check.detail:
            for detail_line in check.detail.splitlines() or [check.detail]:
                print(f"  {detail_line}" if detail_line else "  ")
    if exit_code(checks) == 0:
        print("ready to learn")
        return 0
    print("not ready — fix the items marked ✗")
    return 1
