# Task: make first-run setup real — a doctor command and a getting-started path

You are working in the `rote` repository on a branch. Read `README.md` (the "Run it" section),
`rote/client.py` (how the API key is found), `rote/preflight.py` (how a missing browser is
detected), `rote/cli.py` (how subcommands are wired), `check.sh` and `AGENTS.md` first.

## The problem

Today a newcomer has to know five things that are written down nowhere in one place: that Python
3.12+ is needed, that a virtualenv is expected, that `playwright install chromium` is a separate
step, that `MODEL_API_KEY` comes from the environment *or* from `~/.config/muse/auth.json`, and
that the demo fixtures need a local server. When one of those is missing they get a stack trace
or a misleading message. Nobody should have to read the source to start.

## Deliverable 1 — `rote doctor`

Add a subcommand:

```
rote doctor
```

It checks, in this order, and prints one line per check with a tick, a cross, or a warning:

1. **Python version** — 3.12 or newer.
2. **Dependencies importable** — `playwright` and `httpx`.
3. **Chromium installed** — reuse `rote/preflight.py::browser_available()`.
4. **API key present** — from `MODEL_API_KEY`, else from `~/.config/muse/auth.json`
   (`providers.meta.api_key`). Never print the key; print where it was found.
5. **API reachable** — send one token-count request to the API
   (`rote/client.py::count_tokens` with a one-word input) and report whether it answered. This
   costs nothing: the endpoint tokenizes only.

Then a final line: `ready to learn` or `not ready — fix the items marked ✗`.

Exit code 0 when everything passes, 1 otherwise. Each failure line must carry the exact command
or action that fixes it, for example:

```
✗ Chromium not installed      → ./.venv/bin/playwright install chromium
✗ no API key found            → export MODEL_API_KEY=…  (or run `muse` once to sign in)
```

Support `--offline` to skip check 5, for a machine with no network.

Put the checks in a new module `rote/doctor.py` with a pure core
(`run_checks() -> list[Check]`, where a `Check` has `name`, `ok`, `detail`, `fix`) so it is
testable without a network or a browser.

## Deliverable 2 — tests

Add `tests/test_doctor.py` proving, without touching the network:

- the Python-version check fails for an old version and passes for the current one;
- the key check reports the environment variable as the source when `MODEL_API_KEY` is set
  (patch the environment) and reports the config file when only that exists (point the lookup at
  a temporary file — if the lookup needs a path parameter for that, add one with the current
  behaviour as the default);
- `--offline` never reports the API check as a failure;
- the exit code is 1 when any required check fails, 0 when all pass (drive this with a fake list
  of checks, no network).

## Deliverable 3 — the getting-started path in the README

Replace the "Run it" section with "Getting started", in this shape, and keep it short:

1. what you need (Python 3.12+, an API key, a browser);
2. the five commands, in order, including `rote doctor`;
3. what output to expect from `rote doctor` when it is ready;
4. the two common failures and their one-line fixes (no browser, no key);
5. then the existing record → learn example.

## Verification you must run

```
./check.sh
./.venv/bin/python -m rote doctor
PLAYWRIGHT_BROWSERS_PATH=/tmp/none ./.venv/bin/python -m rote doctor ; echo "exit=$?"
MODEL_API_KEY= ./.venv/bin/python -m rote doctor --offline ; echo "exit=$?"
```

The first must print `ready to learn` and exit 0. The second must fail the Chromium check with
the install command and exit 1. The third must fail the key check with the export line and exit 1.
Report all four results in your final message.

## Rules

- Standard library only; no new dependencies.
- Do not change the verdict checks in `rote/replay.py`, the plan format, or `tools/commit.sh`.
- Do not touch `results/`, the demo apps or the recordings.
- Do not commit; leave the tree for review.
