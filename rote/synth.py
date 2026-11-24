"""Compile a plan into browser automation.

Deliberately not "ask the model for code". The model has already done the part it is good
at — reading a recording — and the part it is bad at — emitting a hundred lines with no
typos — is done by a compiler here. The output is a small, readable Python file that
anyone can keep, review and run without rote or without a model at all.
"""
from __future__ import annotations

import re
from pathlib import Path

from .plan import Plan, Step

HEADER = '''"""Automation for {app}, written by rote from {recording}.

Procedure: {goal}
What success looks like: {effect}

Data comes in through `rows`: one dict per repetition, keyed by {fields}.
No model is involved in running this file.
"""
from __future__ import annotations

from playwright.sync_api import Page


def _field(page: Page, label: str):
    """A control by its visible label, falling back to placeholder or name."""
    for locator in (page.get_by_label(label, exact=False),
                    page.get_by_placeholder(label, exact=False),
                    page.locator(f"[name='{{label}}']")):
        if locator.count() > 0:
            return locator.first
    raise LookupError(f"no form control labelled {{label!r}} on {{page.url}}")


def _button(page: Page, name: str):
    """A button by its accessible name, falling back to visible text."""
    for locator in (page.get_by_role("button", name=name, exact=False),
                    page.get_by_text(name, exact=False)):
        if locator.count() > 0:
            return locator.first
    raise LookupError(f"no button named {{name!r}} on {{page.url}}")


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on", "checked")


def _tick(page: Page, label: str, want: bool, action: str) -> None:
    control = _field(page, label)
    (control.check if want else control.uncheck)()


DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y")


def _to_iso_date(value: str) -> str | None:
    """Only formats with no ambiguity. 03/01/2026 is refused on purpose: it is either
    March 1st or January 3rd, and silently picking one corrupts the user's data."""
    from datetime import datetime
    text = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _fill(page: Page, label: str, value: str) -> None:
    """Fill a control, giving a date input the form it actually accepts."""
    control = _field(page, label)
    kind = (control.get_attribute("type") or "text").lower()
    text = "" if value is None else str(value)
    if kind == "date":
        iso = _to_iso_date(text)
        if not iso:
            raise ValueError(f"{{label!r}} is a date field; {{text!r}} is not an "
                             f"unambiguous date. Give it YYYY-MM-DD.")
        control.fill(iso)
        if not control.input_value():
            raise ValueError(f"the date field {{label!r}} rejected {{iso!r}}")
        return
    control.fill(text)


def _select(page: Page, label: str, value: str) -> None:
    """Choose an option, and say which ones exist when the value is not among them."""
    control = _field(page, label)
    options = [t.strip() for t in control.locator("option").all_inner_texts()]
    if value not in options:
        raise LookupError(f"{{label!r}} has no option {{value!r}}. "
                          f"Available: {{options}}")
    control.select_option(label=value)
'''

FOOTER = '''

def run(page: Page, rows: list[dict[str, str]]) -> None:
    """Perform the task once for every row."""
    for row in rows:
        _one(page, row)
    {once}
'''


def _py_str(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _placeholder(step: Step) -> str | None:
    """`{sku}` -> `sku`: the row key a step takes its value from."""
    if not step.value:
        return None
    m = re.fullmatch(r"\{(\w+)\}", str(step.value).strip())
    return m.group(1) if m else None


def _line(step: Step, indent: str = "    ") -> str:
    key = _placeholder(step)
    if step.action == "type":
        expr = f'row[_key(row, {_py_str(key)})]' if key else _py_str(step.value or "")
        return f"{indent}_fill(page, {_py_str(step.target)}, {expr})"
    if step.action == "select":
        expr = f'row[_key(row, {_py_str(key)})]' if key else _py_str(step.value or "")
        return f"{indent}_select(page, {_py_str(step.target)}, {expr})"
    if step.action in ("click", "submit"):
        return f"{indent}_button(page, {_py_str(step.target)}).click()"
    if step.action in ("check", "uncheck"):
        key = _placeholder(step)
        if key:
            expr = f'_truthy(row[_key(row, {_py_str(key)})])'
        else:
            expr = _py_str("true" if step.action == "check" else "false")
        return (f"{indent}_tick(page, {_py_str(step.target)}, {expr}, "
                f"{_py_str(step.action)})")
    if step.action == "navigate":
        return f'{indent}page.goto({_py_str(step.value or "")})'
    if step.action == "read":
        return f"{indent}pass  # read {_py_str(step.target)}"
    raise ValueError(f"unsupported action {step.action!r}")


def _key_lookup(plan: Plan) -> str:
    """Generated helper: accept rows keyed by `sku` or by the visible label `SKU`."""
    return '''

def _key(row: dict, key: str) -> str:
    """Accept the row key in any casing, and the visible label as a fallback."""
    if key in row:
        return key
    for candidate in (key.lower(), key.upper(), key.title(), key.replace("_", " ")):
        if candidate in row:
            return candidate
    raise KeyError(f"row has no value for {key!r}: {sorted(row)}")
'''


def compile_plan(plan: Plan, *, recording: str = "a recording") -> str:
    """Plan to a standalone Playwright module."""
    row_steps = [s for s in plan.steps if s.scope != "once"]
    once_steps = [s for s in plan.steps if s.scope == "once"]

    body = [
        "",
        "def _one(page: Page, row: dict[str, str]) -> None:",
        '    """One repetition of the task."""',
    ]
    body += [_line(s) for s in row_steps] or ["    pass"]

    once = "\n    ".join(_line(s, "") for s in once_steps) or "pass"

    parts = [
        HEADER.format(app=plan.app or "the app", recording=recording,
                      goal=plan.goal or "(no goal recorded)",
                      effect=plan.expected_effect or "(not stated)",
                      fields=", ".join(f"`{k}`" for k in _row_keys(plan)) or "the fields"),
        _key_lookup(plan),
        "\n".join(body),
        FOOTER.format(once=once),
    ]
    return "\n".join(parts)


def _row_keys(plan: Plan) -> list[str]:
    keys: list[str] = []
    for row in plan.rows:
        for k in row:
            if k not in keys:
                keys.append(k)
    for s in plan.steps:
        k = _placeholder(s)
        if k and k not in keys:
            keys.append(k)
    return keys


def write_script(plan: Plan, out: Path, *, recording: str = "a recording") -> Path:
    code = compile_plan(plan, recording=recording)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(code)
    compile(code, str(out), "exec")   # never write a file that cannot run
    return out
