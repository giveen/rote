# Task: make CI green without making the checks weaker

You are working in the `rote` repository on a branch. Read `check.sh`,
`.github/workflows/check.yml`, `rote/preflight.py`, `rote/cli.py` (the `cmd_learn` preflight
call) and `tests/test_preflight.py` before changing anything.

## What is broken, in CI's words

```
FAIL: test_a_live_server_is_reachable
AssertionError: False is not true : Error: BrowserType.launch: Executable doesn't exist at
/home/runner/.cache/ms-playwright/chromium_headless_shell-1255/…/chrome-headless-shell
```

CI installs the Python dependencies but never installs a browser, so any test that launches one
fails. The same thing happens to a person who clones the repository and runs `./check.sh` before
`playwright install chromium` — which is exactly the order the README gives.

## The bug behind the bug

`rote/preflight.py::reachable()` wraps everything in one `try` and returns
`(False, "BrowserType.launch: …")` when the browser is missing. `cmd_learn` then prints
"no model calls spent — check the app is running and the URL is right", which is wrong: the app
is fine, the machine has no browser. Compare an unreachable port, which really is the app.

## What to do

**1. `rote/preflight.py`** — add:

```python
def browser_available() -> tuple[bool, str]:
    """True when a Chromium build can actually be launched, otherwise why not."""
```

and make `reachable()` report the two cases distinguishably. Keep the `(bool, str)` signature;
put a marker in the reason, e.g. a `why` that starts with `"browsers not installed: "` when the
launch failed because no build exists (detect it from the message containing
`Executable doesn't exist` or `Looks like Playwright was just installed`), and
`"unreachable: "` for a navigation failure. `cmd_learn` prints the matching advice.

**2. `rote/cli.py`** — in the preflight branch of `cmd_learn`:
- browsers missing → print how to fix it (`./.venv/bin/playwright install chromium`) and exit 2;
- app unreachable → keep today's message and exit 2.
Both must still spend nothing.

**3. `tests/test_preflight.py`** — the live-server test must **skip**, not fail, when no browser
is installed (`unittest.skipUnless`). Add a test that, with
`PLAYWRIGHT_BROWSERS_PATH` pointed at an empty directory, `browser_available()` returns False
with a reason that is recognisably about browsers, not about the network — set the environment
variable inside the test with `unittest.mock.patch.dict(os.environ, …)` and restore it
afterwards so other tests are unaffected.

**4. `.github/workflows/check.yml`** — install the browser before the check step:

```yaml
      - name: browsers
        run: ./.venv/bin/playwright install --with-deps chromium
```

placed after the dependency install and before `./check.sh`, so CI runs the browser tests for
real rather than skipping them.

**5. `README.md`** — one sentence in the install section: `./check.sh` skips the two
browser-dependent checks until `playwright install chromium` has been run, and CI installs it.

## Verification you must run, and report

Both of these must pass:

```
./check.sh                                             # with browsers: everything runs
PLAYWRIGHT_BROWSERS_PATH=/tmp/no-browsers ./check.sh   # without: the browser tests skip
```

The second command is the important one: it proves a fresh clone is not broken. Neither run may
report a failure, and the second must not quietly skip more than the browser tests — say in your
final message how many tests ran in each case.

## Rules

- Standard library only; no new dependencies.
- Do not weaken any verdict check in `rote/replay.py`, and do not touch the `rote/` modules other
  than `preflight.py` and the preflight branch of `cli.py`.
- Do not change the demo apps, recordings or anything under `results/`.
