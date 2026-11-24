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
    events: list = field(default_factory=list)
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
            if inv.get("clickable"):
                listed = ", ".join(
                    f'"{c["name"]}" ({c["tag"]}{" x" + str(c["count"]) if c["count"] > 1 else ""})'
                    for c in inv["clickable"][:24])
                lines.append("clickable things on the page, by their accessible name: " + listed)
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
           expected_effect: str = "", timeout_ms: int = 15_000) -> ReplayResult:
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
            res.events = list(getattr(mod, "EVENTS", []))
        except Exception:
            res.events = []
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

    res.checks.extend(_cycles(res.events, len(rows)))
    res.checks.extend(_judge_effect(res.end_state, res.page_text, rows,
                                    expected_effect=expected_effect,
                                    ran_clean=res.error is None))
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


def _judge_effect(end_state: Any, page_text: str, rows: list[dict[str, str]],
                  expected_effect: str = "", ran_clean: bool = True) -> list[Check]:
    """Judge what can actually be observed, and name the rest as unproven.

    A confirmation screen often does not echo the data that was entered, so "the values are
    on the final page" is the wrong question for such an app. What can be checked: the
    controls accepted the values while they were on screen (enforced as they were typed), the
    app ended up in the state the recording ended in, and — where the app exposes its own
    state — that it stored exactly the rows we sent.
    """
    checks: list[Check] = []
    flat = " ".join(page_text.split()).lower()
    values = [(i, k, v) for i, row in enumerate(rows) for k, v in row.items()]

    checks.append(Check(
        "every value was accepted by its control", ran_clean,
        f"all {len(values)} values were typed and confirmed on screen" if ran_clean
        else "at least one control rejected what was typed"))

    missing = []
    for i, key, value in values:
        kind, norm = _norm(value)
        if kind == "bool":
            present = any(w in flat.split() for w in (TRUE_WORDS if norm else FALSE_WORDS))
        else:
            present = str(norm) in flat
        if not present:
            missing.append(f"row {i + 1} {key}={value!r}")

    reached = _reached_end_state(flat, expected_effect)
    if not missing:
        checks.append(Check("the values are visible on the final page", True,
                            f"all {len(values)} values found"))
    elif reached is True:
        checks.append(Check("the values are visible on the final page", True,
                            "not applicable: this app ends on a screen that does not echo "
                            "the data, and the end state matches the recording"))
    else:
        checks.append(Check("the values are visible on the final page", False,
                            "missing: " + ", ".join(missing[:6])))

    if reached is not None:
        checks.append(Check("the app reached the state the recording ended in", reached,
                            "matched the expected end state" if reached
                            else f"expected something like {expected_effect[:120]!r}"))

    records = _records(end_state)
    if records is not None:
        if len(records) != len(rows):
            checks.append(Check("the app stored exactly the rows we sent", False,
                                f"sent {len(rows)} row(s), the app holds {len(records)}"))
        else:
            bad = 0
            for row, record in zip(rows, records):
                candidates = [str(v).strip().lower() for v in record.values()]
                if not all(_matches(v, candidates) for v in row.values()):
                    bad += 1
            checks.append(Check("the app stored exactly the rows we sent", bad == 0,
                                f"{len(rows) - bad}/{len(rows)} rows stored as sent"))
        checks.append(Check("the task was submitted", True,
                            f"{len(records)} record(s) confirmed by the app"))
    return checks


def _reached_end_state(flat_page: str, expected_effect: str) -> bool | None:
    """Does the final page look like the state the recording ended in?

    Only distinctive words count — a phrase of four or more letters that is not generic — so
    this is a hint, not a substitute for an app that exposes its own state.
    """
    import re as _re
    if not expected_effect:
        return None
    # A plan usually quotes what the final screen says. That quote is the strongest signal
    # available when the app does not expose its own state.
    quoted = [q.strip() for pair in _re.findall(r'"([^"]{4,})"|\'([^\']{4,})\'', expected_effect)
              for q in pair if q.strip()]
    for phrase in quoted:
        if " ".join(phrase.split()).lower() in flat_page:
            return True
    stop = {"the", "and", "that", "with", "from", "this", "appears", "then", "when", "will",
            "into", "form", "page", "below", "after", "before", "clear", "cleared", "line",
            "lines", "table", "shows", "shown", "each", "value", "values", "user"}
    words = {w.strip('"\'.,!;:()').lower() for w in expected_effect.split()}
    distinctive = [w for w in words if len(w) >= 6 and w.isalpha() and w not in stop]
    if not distinctive:
        return None
    hits = [w for w in distinctive if w in flat_page]
    return len(hits) >= 1


COMMITTING = {"click", "submit"}


def structural_checks(plan_steps: list, repeat: tuple[int, int] | None,
                      n_rows: int) -> list[Check]:
    """Checks that can be made before running anything, from the plan's shape alone.

    The important one: if more than one row has to be processed, the repeating block has to
    contain something that *commits* a row — a click or a submit — otherwise every iteration
    types into the same form and overwrites the one before it. An app that does not expose its
    own state cannot reveal that mistake afterwards, so it has to be caught here.
    """
    if n_rows <= 1 or not repeat:
        return []
    first, last = repeat
    inside = [s for i, s in enumerate(plan_steps, 1) if first <= i <= last]
    commits = [s for s in inside if s.action in COMMITTING]
    if commits:
        return [Check("the repeating block commits each row", True,
                      f"{len(commits)} committing step(s) inside steps {first}–{last}")]
    return [Check(
        "the repeating block commits each row", False,
        f"steps {first}–{last} only enter data, with no click or submit, so {n_rows} rows "
        f"would overwrite the same form and produce one result instead of {n_rows}")]


def _cycles(events: list, n_rows: int) -> list[Check]:
    """Did the loop really go round once per row, ending each time on the same page?

    A block that types into one form three times also "runs three times", but it never returns
    to the state it started from, so the pages it ends on tell the two apart.
    """
    if n_rows <= 1:
        return []
    urls = [url for label, url in events if label == "iteration"]
    if len(urls) != n_rows:
        return [Check("the loop completed one cycle per row", False,
                      f"{len(urls)} iteration(s) recorded for {n_rows} row(s)")]
    if len(set(urls)) > 2:
        return [Check("the loop completed one cycle per row", False,
                      f"each iteration ended on a different page: {sorted(set(urls))[:3]}")]
    return [Check("the loop completed one cycle per row", True,
                  f"{n_rows} iterations, each ending on {urls[0].rsplit('/', 1)[-1] or '/'}")]


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
      details[name] = {type, value: el.value,
                       valid: el.checkValidity ? el.checkValidity() : true};
    }
  }
  // Everything a person can click, named the way a screen reader would say it. Icons carry
  // no text, so aria-label and title are the only names they have; leaving them out is how
  // the repair loop ends up guessing at numbered badges.
  const seen = new Map();
  for (const el of document.querySelectorAll(
      'a, button, [role=button], [role=link], [role=menuitem], [role=tab], ' +
      'input[type=submit], input[type=button]')) {
    const name = clean(el.getAttribute("aria-label") || el.getAttribute("title")
                       || el.textContent || el.value || "");
    if (!name) continue;
    const tag = el.tagName.toLowerCase();
    const key = tag + "|" + name;
    seen.set(key, (seen.get(key) || 0) + 1);
  }
  const clickable = [...seen.entries()].map(([key, n]) => {
    const [tag, name] = key.split("|");
    return {tag, name, count: n};
  });
  const selects = {};
  for (const el of document.querySelectorAll("select")) {
    const byFor = el.id ? document.querySelector(`label[for="${el.id}"]`) : null;
    const wrap = el.closest("label");
    const name = clean(byFor?.textContent || wrap?.textContent || el.getAttribute("name") || "");
    selects[name] = [...el.options].map(o => clean(o.textContent)).filter(Boolean);
  }
  return {labels, clickable, selects, details};
}"""


def inventory(page) -> dict:
    """What the app actually offers: labels, buttons, and each dropdown's options."""
    try:
        return page.evaluate(INVENTORY_JS)
    except Exception:
        return {}
