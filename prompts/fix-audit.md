# Task: fix the ten findings in docs/AUDIT.md

You are working in the `rote` repository, on a branch. Read `docs/AUDIT.md` first — every
finding has a reproduction and a stated fix. Then read the modules you will touch:
`rote/cli.py`, `rote/client.py`, `rote/plan.py`, `rote/synth.py`, `rote/replay.py`.

Match the existing style: type hints, short docstrings that say *why*, standard library only.
Add tests to `tests/` for each behaviour you change, in the style of the existing tests.

## What to fix, and what "fixed" means

**A1 — empty data must not pass.** `rote learn … --rows empty.json` where the file holds `[]`
currently replays zero iterations and reports PASSED. Refuse empty data in `_load_rows` (or in
`cmd_learn` before any model call) with a clear message and a non-zero exit code. Add a test for
the refusal. Also add a verdict check so a run with no rows can never be reported as passed.

**A2 — an unreachable app must not burn repairs.** Add a preflight in `cmd_learn`: open the URL
once with Playwright before `understand`; if `page.goto` raises, print which URL failed and why,
spend nothing on repairs, and exit non-zero. Put the preflight in a function (e.g.
`rote/preflight.py: reachable(url) -> tuple[bool, str]`) so it can be tested with a bad URL.

**A3 — row alignment must honour exact matches.** In `rote/cli.py::_align_rows`, the current
expression parses as `(exact or prefix) if len(cands) == 1 else None`, so exact matches are
skipped whenever more than one unrecognised key is present. Rewrite so:
1. an exact match applies always,
2. a punctuation/case-insensitive canonical match applies always,
3. the prefix heuristic applies only when exactly one candidate is left.
Add a test with a row like `{"sku": "A", "extra1": "x", "extra2": "y"}` against a plan key
`SKU` proving the exact match still lands.

**A4 — delete dead code.** Remove `_extract_code`, `_key_lookup` and any `HEADER` leftovers in
`rote/synth.py` that nothing references. Do not remove `DOC_TEMPLATE`, `SCRIPT_ENV` or
`compile_plan`.

**A5 — bound the wait.** In `rote/scriptenv.py::_first_present`, replace per-candidate 4 s with a
total budget: default `timeout_ms=4000` for the whole lookup, spreading it across candidates
(e.g. `max(600, timeout_ms // len(candidates))` each). The happy path must stay immediate.

**A6 — reserve what a call can actually cost.** In `rote/client.py::Ledger`, replace the flat
`estimate: float = 0.05` in `guard()` with a reserve based on the largest single call seen so far
(`max(0.05, 2 * largest)`), so a long-context call cannot be admitted and then overrun the cap.
Keep the existing message wording.

**A7 — keep a running total.** `Ledger.spent` recomputes a sum on every request. Keep a running
total updated in `record()`, still correct after `guard()` and `summary()`.

**A8 — a spent budget must not traceback.** Wrap the body of `cmd_learn` so `BudgetExceeded`
prints the message, writes whatever report exists (the existing `_write_report` call), and
returns 1. Do the same for `cmd_record` if it can trigger it.

**A9 — validate `Plan.repeat`.** In `rote/plan.py::Plan.from_dict`, reject a repeat whose
`first` or `last` is < 1, or whose `first > last`, by setting `repeat = None` and recording the
reason on the Plan (a new field, e.g. `repeat_rejected: str | None`). Add a test.

**A10 — one `_row_keys`.** `rote/cli.py` and `rote/synth.py` both define it. Keep the one in
`rote/plan.py` (move it there as `row_keys(plan)`), and import it in both places.

## Verification you must run before finishing

```
./check.sh
```

All tests must pass, including the ones you add. Then confirm the two reproductions behave:

```
cd /mnt/storage/Projects/rote-audit
echo '[]' > /tmp/empty.json
PYTHONPATH=. ./.venv/bin/python -m rote learn results/recordings/intake.mp4 \
    --url http://127.0.0.1:8765/app.html --rows /tmp/empty.json --out /tmp/empty-run
# expect: a clear refusal, non-zero exit, no model calls
```

```
PYTHONPATH=. ./.venv/bin/python -m rote learn results/recordings/intake.mp4 \
    --url http://127.0.0.1:9/app.html --rows results/fresh_rows.json --out /tmp/dead-run
# expect: an unreachable-app message, no repair calls
```

A local server for the fixtures may not be running; if `http://127.0.0.1:8765` is unreachable,
start one with `python3 -m http.server 8765 --directory app &` before the tests that need it, or
skip that check and say so in your final message.

## Rules

- Standard library only; do not add dependencies.
- Do not change the demo apps in `app/`, the recordings, or anything in `results/`.
- Do not touch `rote/certify.py` or `tests/test_certify.py`.
- Keep every generated automation working: `tools/demo.sh intake` must still pass.
- If a fix would change the report format, update `_write_report` and `tools/demo.sh` to match.
