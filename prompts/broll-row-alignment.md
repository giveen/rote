# Task: make b-roll feed rows the same way the pipeline does

You are working in the `rote` repository on a branch (the same branch where you added the CI
cache and refreshed the triage clip). Read `tools/broll.py`, `rote/cli.py` (the `_align_rows`
function), `rote/plan.py`, and a run's `report.json` under `results/submission/` before changing
anything.

## The bug

Recording the sauce clip fails:

```
KeyError: "row has no value for 'zip_postal_code': ['first_name', 'last_name', 'zip']"
```

`rote learn` maps a user's column names onto the plan's own key names — that is what
`_align_rows` in `rote/cli.py` does — but `tools/broll.py` loads the generated script and calls
`run(page, rows)` with the raw file contents, so a row keyed `zip` never becomes
`zip_postal_code`. The recording tool is therefore stricter than the product it is filming.

## What to do

**1. Move the alignment where both callers can use it.** In `rote/plan.py`, add a public
function:

```python
def align_rows(rows: list[dict[str, str]], plan: Plan) -> list[dict[str, str]]:
    """Rename a user's columns onto the plan's own key names."""
```

Move the body of `rote/cli.py::_align_rows` (and its helpers `_canon` and `row_keys` if they
live there) into `rote/plan.py`, keeping the behaviour exactly as it is today — including the
rule that exact and canonical matches always apply and only the prefix heuristic is guarded by
unambiguity. `rote/cli.py` should import and call it; nothing about `learn`'s behaviour may
change.

**2. Make `tools/broll.py` use it.** Each task in the table needs the plan to align against, so
read the run's `report.json` (the file is at
`results/submission/<task>/report.json`, and `report["plan"]` has the same shape `Plan.from_dict`
accepts). Load the plan, then align the rows before calling `mod.run(page, rows)`. If a
`report.json` or a plan is missing, say so clearly and skip that task rather than crashing with a
`KeyError`.

**3. Add a test** in `tests/` proving that a row keyed `zip` is aligned to a plan whose key is
`zip_postal_code`, and that a row whose keys already match is returned unchanged. Use the
existing test style.

## Verification you must run

```
./check.sh
```

Then, for the local apps only (no network needed):

```
curl -sf -o /dev/null http://127.0.0.1:8765/triage.html || true
./.venv/bin/python tools/broll.py triage
ls -la results/broll/triage.mp4
```

`triage` must record successfully and the file must be > 20 KB. The sauce task needs the public
internet, which your sandbox may not have; if it fails with a network error, say so and stop —
someone with network access will record it. Do not fake it and do not repoint the task at a
different URL.

## Rules

- Standard library only; no new dependencies.
- Do not change the verdict checks in `rote/replay.py`, the demo apps, the recordings, or
  anything under `results/submission/`.
- Keep `learn`'s behaviour identical: the existing tests for alignment must still pass.
- Do not commit; leave the tree for review.
