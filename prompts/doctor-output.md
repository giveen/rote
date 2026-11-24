# Task: make the doctor output clean enough to hand to a newcomer

You are working in the `rote` repository, on the branch where you added `rote doctor`. Read
`rote/doctor.py` and the `browser_available()` reason strings in `rote/preflight.py` first.

## What is wrong

Run this:

```
PLAYWRIGHT_BROWSERS_PATH=/tmp/none ./.venv/bin/python -m rote doctor
```

The Chromium line prints Playwright's whole installation banner — a box drawn with `╔══╗`
characters and six lines of text — in the middle of the checklist:

```
✗ Chromium installed: Chromium not installed (browsers not installed: Error: BrowserType.launch: Executable doesn't exist at /tmp/none/…/chrome-headless-shell
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
…
```

A first-run tool should read like a checklist, not like a stack trace. The fix command is already
correct; it is buried.

## What to do

1. Keep each check's output to **one line**: the mark, the check name, and a short reason capped
   at about 100 characters, with the `→ fix` after it. Collapse anything longer onto one line and
   truncate with an ellipsis.
2. Strip the box-drawing banner from a browser reason before printing it. A reason that consists
   of multiple lines should keep only its first meaningful line.
3. Add `--verbose` to the subcommand. With it, print the full, untruncated reason on the following
   lines, indented, so a person debugging can still see the detail. Default output stays clean.
4. Keep the exit codes as they are (0 ready, 1 not ready), and keep `--offline` working.
5. If `run_checks()` currently embeds formatting, separate the data (name, ok, detail, fix) from
   the rendering so the shortening is testable: add a pure helper, e.g.
   `shorten(reason: str, limit: int = 100) -> str`, and test it against a multi-line reason with
   a box in it.

## Verification you must run

```
./check.sh
./.venv/bin/python -m rote doctor
PLAYWRIGHT_BROWSERS_PATH=/tmp/none ./.venv/bin/python -m rote doctor ; echo "exit=$?"
PLAYWRIGHT_BROWSERS_PATH=/tmp/none ./.venv/bin/python -m rote doctor --verbose | head -12
```

Report all four. The default failing run must be five or six clean lines with no box characters;
`--verbose` must still show the detail. Exit codes: 0, 0, 1, 1.

## Rules

- Standard library only.
- Do not change what the checks test, only how much of the reason is shown by default.
- Do not touch `results/`, the demo apps, `tools/` or the verdict checks in `rote/replay.py`.
- Do not commit; leave the tree for review.
