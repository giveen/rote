# Audit: edge cases, error paths and performance

Run against the code as it stands on `main` after the four tasks. Every finding below has a
reproduction, because an audit without one is an opinion.

## The ones that can produce a false pass

### A1 — Empty data passes vacuously (high)

```
echo '[]' > /tmp/empty_rows.json
python -m rote learn intake.mp4 --url … --rows /tmp/empty_rows.json
→ PASSED, 2 model calls, $0.00248
```

With no rows the loop runs zero times, so there is nothing to check and every check passes.
The verdict is meaningless and the report presents it as a success.

**Fix:** refuse empty data before spending anything — `learn` should stop with a clear message.
If an empty run is somehow reached, the verdict must include a check that there was at least
one row.

### A2 — An unreachable app burns the budget (high)

```
python -m rote learn intake.mp4 --url http://127.0.0.1:9/app.html …
→ 4 model calls, $0.01263, 53 s of waiting, then NOT PASSED
```

`page.goto` fails, and the repair loop treats that as a plan problem, spending four calls to fix
a plan that cannot work because the app does not answer.

**Fix:** a preflight before `understand` — if the URL is unreachable, say so and stop, or at the
very least do not spend a repair call on a navigation failure (it is not the plan's fault).

## The ones that make the wrong thing happen quietly

### A3 — Row alignment ignores exact matches (high)

```python
match = (next(...)                      # A: exact canonical match
         or next(...)                   # B: prefix match
         if len(cands) == 1 else None)  # binds to (A or B), not to B alone
```

`_align_rows` parses as `(A or B) if len(cands) == 1 else None`, so when the user's row has more
than one key the plan does not recognise, *even an exact match is skipped*. The docstring says
matching is "exact, then case-insensitive, then punctuation-insensitive, then prefix — and only
when it is unambiguous". The code does not do that.

**Fix:** exact/canonical matches apply always; only the prefix heuristic is guarded by
unambiguity. Add a test with two extra keys.

### A4 — Dead code that suggests a different design (medium)

`_extract_code` and `_key_lookup` in `synth.py` are unreferenced, and a `HEADER` name is gone.
They are leftovers from the version where the model wrote the script. Someone reading this
codebase would reasonably conclude the model can emit code, which is precisely what the
architecture avoids.

**Fix:** delete them.

## Performance

### A5 — A failing step can wait 20 seconds (medium)

`_first_present` tries five candidate selectors at 4 s each. On the happy path the first
candidate matches immediately and this costs nothing; on a failure it is 20 s per step, and a
four-attempt run can spend minutes waiting. Sauce runs have taken 85 s with repairs.

**Fix:** a total budget per lookup (e.g. 4 s overall, ~1 s per candidate) rather than per
candidate. Keep the happy path unchanged.

### A6 — The budget guard can overrun by one full call (medium)

`Ledger.guard()` reserves a flat $0.05. A single high-effort call has cost up to $0.03 in this
project; a long-context call at the >200K tier could cost far more. The guard cannot stop a
call it has already admitted.

**Fix:** reserve the largest call seen so far (or a configurable multiple), not a constant.

### A7 — `Ledger.spent` is O(n) and called before every request (low)

Fine at today's scale, quadratic in principle. Keep a running total.

## Error paths

### A8 — Budget exhaustion during `understand` is an uncaught traceback (low)

```
python -m rote learn … --budget 0.00001
→ Traceback … BudgetExceeded: stopping: $0.0000 left of $0.00
```

The refusal is correct and the message is good; the presentation is a crash, and the exit path
skips the report.

**Fix:** catch `BudgetExceeded` around the whole run, print the message, write whatever report
exists, exit non-zero.

### A9 — `Plan.repeat` is never validated (low)

`first`/`last` can be inverted, zero or beyond the step list; the compiler clamps silently. A
plan that says "steps 9–3" is a model error worth reporting, not silently repairing into
"steps 9–9".

**Fix:** validate when parsing; reject or normalize with a note in the report.

### A10 — `_row_keys` exists twice (low)

`rote/cli.py` and `rote/synth.py` each define it. They must agree or the alignment and the
docstring disagree about which keys matter.

**Fix:** one implementation, imported.

## What the audit did not find

- The certificate is deterministic (no timestamps) and escapes untrusted text — covered by
  tests.
- No SQL, no shell interpolation of user data, no secrets in the repository.
- `understand` does not send the instruction block twice: it goes in the message, not in
  `instructions`.
