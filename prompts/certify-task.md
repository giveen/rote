# Task: add `rote certify` — a self-contained HTML certificate for a run

You are working in the `rote` repository. Read these files first to learn the codebase and
its style: `rote/report.py`-equivalent logic lives in `rote/cli.py` (`_write_report`), and
the plan/cost structures are `rote/plan.py` and `rote/client.py`. Match the existing style:
short docstrings that say *why* a thing exists, type hints, standard library only.

## What rote is

`rote` watches a screen recording of someone doing a repetitive task in a web app, writes
browser automation for it, and proves the automation by replaying it against fresh data.
A run directory is produced by `rote learn` and contains:

- `report.json` — the machine-readable result of the run
- `report.md` — a human-readable report
- `ledger.jsonl` — one JSON object per model call
- `proof_attempt1.png`, `proof_attempt2.png`, … — screenshots taken after each replay

The fields of `report.json` are exactly:

```json
{
  "video": "/abs/path/intake.mp4",
  "plan": {
    "app": "string", "goal": "string",
    "fields": [{"label": "string", "control": "string", "example": "string"}],
    "rows": [{"cells": [{"field": "string", "value": "string"}]}],
    "steps": [{"action": "string", "target": "string", "value": "string|null",
               "note": "string", "scope": "each_row|once"}],
    "expected_effect": "string"
  },
  "script": "/abs/path/generated.py",
  "attempts": [{"attempt": 0, "passed": true,
                "checks": [{"name": "string", "ok": true, "detail": "string"}],
                "error": null, "cost": 0.0011}],
  "passed": true,
  "ledger": {"calls": 1, "spent_usd": 0.00112, "input_tokens": 2756,
             "cached_tokens": 0, "output_tokens": 2205, "reasoning_tokens": 1652,
             "cache_hit_pct": 0.0},
  "elapsed_s": 9.0,
  "fresh_data": true
}
```

## Deliverable 1 — `rote/certify.py`

```python
def write_certificate(run_dir: Path, out: Path) -> Path:
    """Write a standalone HTML certificate for a finished run and return its path."""
```

It must:

1. Read `report.json` from `run_dir`. Raise `FileNotFoundError` with a clear message if it
   is missing.
2. Embed the **most recent** `proof_attempt*.png` found in `run_dir` as a base64 `data:`
   image, inside `<img alt="...">`. If there is no screenshot, skip the image entirely.
3. Include the generated automation's source code in a `<pre>` block, read from the path in
   `report["script"]` — but only if that file exists, otherwise omit that section.
4. Produce **one self-contained file**: no external CSS, JS, fonts or images, no `http://`
   or `https://` anywhere in the output. It must render correctly when opened from disk.
5. Content, in this order:
   - a header: the app name (`plan.app`), the goal, and a large verdict badge reading
     `PASSED` or `NOT PASSED` from `report["passed"]`
   - a cost line: amount spent, number of model calls, cache hit percentage
   - a "What it learned" table of steps: `action`, `target`, `value`, `scope`
   - a "Proof" table of the checks from the last attempt: name, ✅/❌, detail
   - a "How it was produced" short paragraph explaining that the recording is read by
     `muse-ember-1.0`, that the automation is compiled from the plan, and that the replay
     ran against data the recording never contained (`report["fresh_data"]`)
   - a footer naming `rote` and the model id
6. Style: dark page, system font stack, readable at 390px and 1440px wide (single column,
   `max-width: 900px`, tables that scroll horizontally on narrow screens). Use `<style>` in
   the head. Print-friendly is a bonus, not required.
7. **Escape all text from the report** with `html.escape`. A goal containing
   `<script>alert(1)</script>` must appear as inert text, never as markup.
8. Be deterministic: no timestamps in the output, so two runs on the same input produce
   identical bytes.

## Deliverable 2 — CLI

In `rote/cli.py`, add a subcommand:

```
rote certify --run results/submission --out results/submission/certificate.html
```

`--run` defaults to `results/learn`, `--out` defaults to `<run>/certificate.html`. Print
the path written and return exit code 0. Wire it the same way the existing subcommands are
wired (`set_defaults(func=...)`).

## Deliverable 3 — tests

Add `tests/test_certify.py` using `unittest`, matching the style of `tests/test_plan.py`.
It must build a temporary run directory with a small fake `report.json` and assert:

- the file is created and `<html` appears in it
- `PASSED` appears for `passed: true`, and `NOT PASSED` for `passed: false`
- the goal text appears
- a goal containing `<script>alert(1)</script>` appears escaped as
  `&lt;script&gt;alert(1)&lt;/script&gt;` and the raw `<script>alert` does not appear
- the output contains no `http://` and no `https://`
- when a `proof_attempt1.png` exists in the run dir, a `data:image/png;base64,` appears
- when `report["script"]` points at a file that does not exist, nothing breaks

## How to verify your work

Run these from the repository root and make sure they pass before you finish:

```
./check.sh
./.venv/bin/python -m rote certify --run results/learn --out /tmp/cert.html
```

`./check.sh` runs the unit tests, a syntax check and a demo-app check.

## Rules

- Standard library only. Do not add dependencies.
- Do not change `rote/plan.py`, `rote/client.py`, `rote/replay.py`, `rote/synth.py`,
  `rote/understand.py` or the demo app. The only existing file you may edit is
  `rote/cli.py` (to register the subcommand) and `check.sh` (only if it needs no change,
  leave it alone).
- Do not touch anything in `results/`.
- Keep functions small and readable. Comments explain *why*, not *what*.
