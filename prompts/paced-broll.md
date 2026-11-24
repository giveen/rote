# Task: give b-roll a paced recording mode

You are working in the `rote` repository on the branch where you added the row alignment and the
CI cache. Read `tools/broll.py` completely before changing it.

## Why

The sauce clip is unusable as demo footage. With three rows the automation completes three whole
checkouts in under a second, and Playwright records at 25 fps, so the carts, the checkout form
and the confirmation pages flash past — a viewer sees the login page, a flicker, and the product
list. The clip is *accurate* and *useless*.

`tools/broll.py` records at full speed. The fix is Playwright's own lever for this:
`p.chromium.launch(headless=True, slow_mo=<ms>)` inserts a delay after every browser action, so
the same unmodified automation plays at a watchable pace.

## What to do

Add an option, keeping the default behaviour exactly as it is today:

```
./.venv/bin/python tools/broll.py sauce --slow-mo 250
```

- `--slow-mo MS` (default `0`) is passed to `chromium.launch(slow_mo=MS)`.
- When `MS > 0`, write the clip to `<task>-paced.mp4` **instead of** overwriting `<task>.mp4`, so
  the real-speed clip is never lost.
- The half-speed cut made by `slow_down()` should still be produced, from whichever file was just
  written, as `<stem>-slow.mp4` (for a paced run that means `sauce-paced-slow.mp4`).
- Print what was written, as it does now.
- Update the module docstring and the `--help` text briefly: the real-speed clip shows how fast
  the automation actually is; the paced clip is for footage a person can follow.

## Verification you must run

```
./check.sh
./.venv/bin/python tools/broll.py triage --slow-mo 250
ls -la results/broll/triage-paced.mp4 results/broll/triage-paced-slow.mp4
ffprobe -v quiet -show_entries format=duration -of csv=p=0 results/broll/triage-paced.mp4
```

The paced triage clip must exist, be > 20 KB, and be noticeably longer than the real-speed
`triage.mp4` (which is 2.7 s). Also confirm `./.venv/bin/python tools/broll.py triage` with no
flags still writes `results/broll/triage.mp4` and does not create a `-paced` file.

## Rules

- Standard library only; the only new dependency is the `slow_mo` argument already available in
  the installed Playwright.
- Do not change the TASKS table, the row alignment you added, or `tools/demo.sh`.
- Do not touch `results/submission/`, `rote/`, or the recordings in `results/recordings/`.
- Do not commit; leave the tree for review.
