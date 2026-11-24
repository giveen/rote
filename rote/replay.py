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
    inventory: dict = field(default_factory=dict)
    screenshot: Path | None = None
    seconds: float = 0.0

    def as_evidence(self, limit: int = 900) -> str:
        """What the repair loop gets to see: facts, and the app's real interface."""
        lines = [f"error: {self.error}"] if self.error else []
        for c in self.checks:
            lines.append(f"{'PASS' if c.ok else 'FAIL'} {c.name}: {c.detail}")
        if self.inventory:
            inv = self.inventory
            if inv.get("labels"):
                lines.append("form controls actually on the page: "
                             + ", ".join(inv["labels"]))
            if inv.get("buttons"):
                lines.append("buttons actually on the page: " + ", ".join(inv["buttons"]))
            for label, options in (inv.get("selects") or {}).items():
                lines.append(f"options in {label!r}: " + ", ".join(options))
            odd = {k: v for k, v in (inv.get("details") or {}).items()
                   if v.get("type") not in ("text", "number", "select")
                   or (v.get("value") and not v.get("valid"))}
            for label, d in odd.items():
                lines.append(f"control {label!r} is <input type={d['type']}> and holds "
                             f"{d['value']!r} (valid={d['valid']})")
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
            res.inventory = inventory(page)
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


TRUE_WORDS = ("true", "yes", "y", "on", "1", "checked", "enabled")
FALSE_WORDS = ("false", "no", "off", "0", "unchecked", "disabled")


def _norm(value: Any) -> tuple[str, Any]:
    """Typed comparison. An app renders a ticked box as 'yes', 'true', 'on' or a check
    mark depending on who wrote it, so booleans must not be compared as raw strings —
    that is how a verifier ends up calling a correct run a failure."""
    text = " ".join(str(value).split()).lower()
    if text in TRUE_WORDS:
        return ("bool", True)
    if text in FALSE_WORDS:
        return ("bool", False)
    return ("text", text)


def _matches(want: Any, candidates: list[str]) -> bool:
    kind, norm = _norm(want)
    if kind == "bool":
        words = TRUE_WORDS if norm else FALSE_WORDS
        return any(c in words for c in candidates)
    return any(norm in " ".join(c.split()) or " ".join(c.split()) in norm
               for c in candidates if c)


def _judge_effect(end_state: Any, page_text: str, rows: list[dict[str, str]]) -> list[Check]:
    """The effect checks: did the app end up holding the data we sent?

    Deliberately tolerant about *how* an app renders a value, strict about whether it did.
    """
    checks: list[Check] = []
    tokens = [" ".join(page_text.split()).lower()]
    flat = " ".join(page_text.split()).lower()

    missing = []
    for i, row in enumerate(rows):
        for key, value in row.items():
            kind, norm = _norm(value)
            if kind == "bool":
                present = any(w in flat.split() or w in flat for w in
                              (TRUE_WORDS if norm else FALSE_WORDS))
            else:
                present = str(norm) in flat
            if not present:
                missing.append(f"row {i + 1} {key}={value!r}")
    checks.append(Check("every value reached the page", not missing,
                        f"all {sum(len(r) for r in rows)} values found" if not missing
                        else "missing: " + ", ".join(missing[:6])))

    records = _records(end_state)
    if records is not None:
        if len(records) != len(rows):
            checks.append(Check("the app stored exactly the rows we sent", False,
                                f"sent {len(rows)} row(s), the app holds {len(records)}"))
        else:
            bad = 0
            for i, (row, record) in enumerate(zip(rows, records)):
                candidates = [str(v).strip().lower() for v in record.values()]
                if not all(_matches(v, candidates) for v in row.values()):
                    bad += 1
            checks.append(Check("the app stored exactly the rows we sent", bad == 0,
                                f"{len(rows) - bad}/{len(rows)} rows stored as sent"))
        checks.append(Check("the task was submitted", True,
                            f"{len(records)} record(s) confirmed by the app"))
    return checks


def _records(end_state: Any) -> list[dict] | None:
    """Whatever the app says it now holds, if it says anything."""
    if isinstance(end_state, dict):
        for key in ("lines", "vendors", "records", "items", "entries", "rows"):
            value = end_state.get(key)
            if isinstance(value, list):
                return [v for v in value if isinstance(v, dict)]
        if all(isinstance(v, dict) for v in end_state.values()) and end_state:
            return list(end_state.values())
    return None


INVENTORY_JS = """() => {
  const clean = (s) => (s || "").replace(/\\s+/g, " ").trim();
  const labels = [];
  const details = {};
  for (const el of document.querySelectorAll("input, select, textarea")) {
    const byFor = el.id ? document.querySelector(`label[for="${el.id}"]`) : null;
    const wrap = el.closest("label");
    const name = clean(byFor?.textContent || wrap?.textContent || el.getAttribute("aria-label")
                       || el.getAttribute("placeholder") || el.getAttribute("name") || "");
    if (name) {
      labels.push(name);
      const type = el.tagName === "SELECT" ? "select" : (el.getAttribute("type") || "text");
      details[name] = {type, value: el.value, valid: el.checkValidity ? el.checkValidity() : true};
    }
  }
  const buttons = [];
  for (const b of document.querySelectorAll("button, [role=button], input[type=submit]")) {
    const t = clean(b.textContent || b.value || b.getAttribute("aria-label") || "");
    if (t) buttons.push(t);
  }
  const selects = {};
  for (const el of document.querySelectorAll("select")) {
    const byFor = el.id ? document.querySelector(`label[for="${el.id}"]`) : null;
    const wrap = el.closest("label");
    const name = clean(byFor?.textContent || wrap?.textContent || el.getAttribute("name") || "");
    selects[name] = [...el.options].map(o => clean(o.textContent)).filter(Boolean);
  }
  return {labels, buttons, selects, details};
}"""


def inventory(page) -> dict:
    """What the app actually offers: labels, buttons, and each dropdown's options."""
    try:
        return page.evaluate(INVENTORY_JS)
    except Exception:
        return {}
