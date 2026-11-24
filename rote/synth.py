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

from .scriptenv import SCRIPT_ENV

DOC_TEMPLATE = '''"""Automation for {app}, written by rote from {recording}.

Procedure: {goal}
What success looks like: {effect}

Data comes in through `rows`: one dict per repetition, keyed by {fields}.
No model is involved in running this file.
"""'''

FOOTER = '''

def run(page: Page, rows: list[dict[str, str]]) -> None:
    """Set the task up once, perform it for every row, then finish once."""
    row = rows[0] if rows else {{}}
{setup}
    for row in rows:
        _one(page, row)
{finish}
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
        if not step.value:
            return f"{indent}pass  # navigate step had no URL; the replay already opened the app"
        return f"{indent}page.goto({_py_str(step.value)})"
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
    """Plan to a standalone Playwright module.

    Setup has to run before the repetition and finishing after it, so the step order in the
    plan decides where each `once` step goes: everything before the first per-row step is
    setup, everything after the last one is teardown.
    """
    n = len(plan.steps)
    if plan.repeat:
        first = min(max(plan.repeat[0] - 1, 0), n)      # to 0-based, clamped
        last = min(max(plan.repeat[1] - 1, first), n - 1)
        setup_steps = plan.steps[:first]
        row_steps = plan.steps[first:last + 1]
        finish_steps = plan.steps[last + 1:]
    else:
        # no repeat range: run the whole thing once, with the first row's data
        setup_steps, row_steps, finish_steps = [], plan.steps, []

    body = [
        "",
        "def _one(page: Page, row: dict[str, str]) -> None:",
        '    """One repetition of the task."""',
    ]
    body += [_line(s) for s in row_steps] or ["    pass"]
    body.append('    _mark(page, "iteration")')

    def block(steps) -> str:
        lines = [_line(s, "    ") for s in steps]
        return "\n".join(lines) if lines else "    pass"

    doc = DOC_TEMPLATE.format(
        app=plan.app or "the app", recording=recording,
        goal=plan.goal or "(no goal recorded)",
        effect=plan.expected_effect or "(not stated)",
        fields=", ".join(f"`{k}`" for k in _row_keys(plan)) or "the fields")

    # Only the docstring is a template: the embedded script helpers contain braces of their
    # own, so they are concatenated, never formatted.
    parts = [doc, SCRIPT_ENV, "\n".join(body),
             FOOTER.format(setup=block(setup_steps), finish=block(finish_steps))]
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
