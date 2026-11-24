"""Turn a recording into a plan.

The product decision that makes this work: the recording teaches the *procedure*, and the
data is an input the user supplies later. So the model does not have to OCR every value
perfectly — it has to get the fields, the order, the loop and the end effect right, which
is what a fixed frame budget can still carry.
"""
from __future__ import annotations

import json
from pathlib import Path

from .client import Ledger, create, upload
from .plan import PLAN_SCHEMA, Plan

INSTRUCTIONS = """You are watching a screen recording of someone using an internal web \
application, so that the work can be automated afterwards.

Describe the procedure, not the pixels. Someone who has never seen this app must be able
to repeat the task from your description alone, with different data.

Rules:
- Name controls by the label a person sees on screen. Never invent one.
- `rows` holds the data the person entered, one object per repetition, keyed by a short \
lower_snake_case name of the field. If the task was performed once, there is one row.
- `steps` is the procedure for ONE repetition, plus the actions that end the task \
(adding the line, submitting). Use `type`, `select`, `click`, `submit`, `navigate`, `read`.
- Set `value` to the row key that fills that control, written as "{field}", not to the \
literal text from the recording. For clicks and submits, `value` is null.
- `fields` lists every control the person touched, with the kind of control it is.
- `expected_effect` is what is visibly different once the task has succeeded.
- Only describe actions the recording supports. If something is ambiguous, say so in the \
step's `note` instead of guessing silently.

Return JSON matching the schema."""


def build_input(file_id: str, *, hint: str | None = None) -> list[dict]:
    parts = [{"type": "input_text", "text": INSTRUCTIONS}]
    if hint:
        parts.append({"type": "input_text", "text": f"Context from the user: {hint}"})
    parts.append({"type": "input_file", "file_id": file_id})
    return [{"type": "message", "role": "user", "content": parts}]


def understand(video: Path, *, ledger: Ledger, effort: str = "max",
               hint: str | None = None, file_id: str | None = None) -> Plan:
    """Read the recording and return the plan it describes."""
    fid = file_id or upload(video)
    raw = create(unit=video.stem, purpose="understand", input_=build_input(fid, hint=hint),
                 ledger=ledger, effort=effort, schema=PLAN_SCHEMA, schema_name="plan",
                 cache_key="rote-understand-v1", note=f"video {video.name}")
    plan = Plan.from_json(raw)
    plan.raw = raw  # keep the model's own words for the report
    return plan


def understand_stills(frames: list[Path], *, ledger: Ledger, effort: str = "max",
                      hint: str | None = None) -> Plan:
    """The detailed path: a handful of stills, when exact on-screen values matter."""
    import base64
    parts = [{"type": "input_text", "text": INSTRUCTIONS},
             {"type": "input_text",
              "text": "These are stills from the recording, in order. When steps are "
                      "repeated with different data, put each repetition in `rows`."}]
    if hint:
        parts.append({"type": "input_text", "text": f"Context from the user: {hint}"})
    for f in frames:
        b64 = base64.b64encode(f.read_bytes()).decode()
        parts.append({"type": "input_image", "image_url": f"data:image/png;base64,{b64}"})
    raw = create(unit="stills", purpose="understand",
                 input_=[{"type": "message", "role": "user", "content": parts}],
                 ledger=ledger, effort=effort, schema=PLAN_SCHEMA, schema_name="plan",
                 cache_key="rote-understand-v1", note=f"{len(frames)} frames")
    plan = Plan.from_json(raw)
    plan.raw = raw
    return plan


def load_truth(path: Path) -> dict:
    return json.loads(path.read_text())
