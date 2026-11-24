"""When the replay fails, fix the plan — not the code.

Repairing at the plan level is cheap and honest: the plan is a dozen short fields, the app
has just told us what its real controls are, and the same compiler produces the script
again. Fixing generated code directly would let the model rewrite large parts of a file
whose only guarantee is a test we already know it fails.
"""
from __future__ import annotations

import json

from .client import Ledger, create
from .plan import PLAN_SCHEMA, Plan

INSTRUCTIONS = """You are correcting a plan for automating a web task, after the automation \
was run and did not succeed.

You get the plan, and the evidence from the failed run: the error, which values did not \
reach the page, and the app's real controls (labels, buttons and dropdown options) as the \
browser reported them.

Rules:
- Change only what the evidence shows is wrong. Keep everything that already worked.
- Name controls exactly as the app reports them. Do not invent labels or options.
- If a dropdown rejected a value, the data was wrong for that app — keep the plan and say \
so in the step's note instead of changing the target.
- Keep `rows` as they are: the values are the user's data, not something to edit.
- Inside the `repeat` range, keep every `{field}` placeholder exactly as it is. Never
  replace one with the literal text from the recording: the point of the automation is that
  it takes different data.
- Outside the `repeat` range, a literal value from the recording is correct: signing in and
  navigating do not change per row. A `{placeholder}` outside the range demands data the user
  has no reason to supply.
- Keep `repeat` pointing at the steps that repeat per row. If the run failed because a row
  was missing a value, the step probably sits outside the range and should not be asking for
  data.
- If a control is a date or number input, its value must be in the form that control
  accepts (dates as YYYY-MM-DD), regardless of how it was displayed on screen.
- If the evidence shows a control named with a count or a state ("Cart, 1 item",
  "Cart, empty"), that name moves as the page changes: use only its stable part ("Cart").
- A `navigate` step needs the URL in `value`; if you cannot supply one, drop the step. The
  replay already opens the app before running.

Return the corrected plan as JSON matching the schema."""


def repair(plan: Plan, evidence: str, *, ledger: Ledger, attempt: int = 1,
           effort: str = "max", history: list[str] | None = None) -> Plan:
    prompt = ""
    if history:
        prompt += ("WHAT HAS ALREADY BEEN TRIED — do not undo a change that fixed an earlier "
                   "failure, and do not repeat one that did not help:\n"
                   + "\n".join(history[-5:]) + "\n\n")
    prompt += (
        "THE PLAN THAT FAILED\n```json\n"
        + json.dumps(plan.to_dict(), ensure_ascii=False, indent=1)
        + "\n```\n\nEVIDENCE FROM THE RUN\n```\n" + evidence[:4000] + "\n```"
    )
    raw = create(unit="repair", purpose=f"repair{attempt}", input_=prompt,
                 ledger=ledger, instructions=INSTRUCTIONS, effort=effort,
                 schema=PLAN_SCHEMA, schema_name="plan",
                 cache_key="rote-repair-v1",
                 note=f"attempt {attempt}")
    fixed = Plan.from_json(raw)
    fixed.raw = raw
    return fixed


def diff(before: Plan, after: Plan) -> list[str]:
    """What the repair actually changed, for the report."""
    out: list[str] = []
    b = [(s.action, s.target, s.value, s.scope) for s in before.steps]
    a = [(s.action, s.target, s.value, s.scope) for s in after.steps]
    if b != a:
        for i in range(max(len(b), len(a))):
            old = b[i] if i < len(b) else None
            new = a[i] if i < len(a) else None
            if old != new:
                out.append(f"step {i + 1}: {old} -> {new}")
    if before.rows != after.rows:
        out.append("rows changed")
    for field in ("app", "goal", "expected_effect"):
        if getattr(before, field) != getattr(after, field):
            out.append(f"{field} changed")
    return out
