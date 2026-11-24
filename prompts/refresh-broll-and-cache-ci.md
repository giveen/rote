# Task: refresh two b-roll clips, and cache the Playwright browser in CI

You are working in the `rote` repository on a branch. Read `tools/broll.py`,
`tools/demo.sh`, `.github/workflows/check.yml`, `requirements.lock.txt` and `docs/DEMO.md`
first. Match the existing style: short docstrings that say *why*, standard library only.

## Deliverable 1 — record the two missing/stale clips

`results/broll/` holds recorded replays of the generated automation doing the task, for the demo
video. The automations changed (sauce now loops three rows, triage two tickets), and the sauce
clip does not exist at all.

Run:

```
# a server is needed for the local apps; skip this line if 8765 already answers
curl -sf -o /dev/null http://127.0.0.1:8765/triage.html || \
  (python3 -m http.server 8765 --directory app & sleep 1)

./.venv/bin/python tools/broll.py sauce triage
```

Then confirm all four files exist and are non-trivial in size:

```
ls -la results/broll/sauce.mp4 results/broll/sauce-slow.mp4 \
       results/broll/triage.mp4 results/broll/triage-slow.mp4
```

Each must be > 20 KB. Report their sizes and durations in your final message
(`ffprobe -v quiet -show_entries format=duration -of csv=p=0 <file>`).

The sauce clip needs the public sandbox, so it needs network access. If it genuinely cannot
reach `https://www.saucedemo.com/`, say so plainly in your final message and still produce the
triage clip — do not fake a recording, and do not edit `tools/broll.py` to point at something
else.

## Deliverable 2 — cache the browser so CI is not eight minutes

`.github/workflows/check.yml` currently runs `./.venv/bin/playwright install --with-deps chromium`
on every push, which pulls both the ~125 MB browser and its apt dependencies. The job went from
15 s to 8m15s because of it.

Add a cache step **before** the install step:

```yaml
      - name: cache playwright browsers
        id: pw-cache
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: pw-${{ runner.os }}-${{ hashFiles('requirements.lock.txt') }}
```

and make the browser step conditional so the download is skipped on a cache hit:

```yaml
      - name: browsers
        if: steps.pw-cache.outputs.cache-hit != 'true'
        run: ./.venv/bin/playwright install --with-deps chromium

      - name: browser system dependencies (cached run)
        if: steps.pw-cache.outputs.cache-hit == 'true'
        run: ./.venv/bin/playwright install-deps chromium
```

The second conditional step matters: `~/.cache/ms-playwright` holds the browser but not the apt
packages, so a cache hit still has to install the system libraries. Without it, the cached run
fails at the first browser launch.

The key is derived from `requirements.lock.txt` on purpose: the browser build is tied to the
pinned Playwright version, so the cache invalidates exactly when the version changes.

## Verification you must run

```
python3 -c "import yaml, sys; yaml.safe_load(open('.github/workflows/check.yml')); print('yaml ok')"
./check.sh
```

`./check.sh` must pass. You cannot run GitHub Actions here, so state in your final message that
the workflow change is unverified until pushed, and list exactly what you changed in it.

## Rules

- Do not change `requirements.txt`, `requirements.lock.txt` or the pinned versions.
- Do not modify `tools/broll.py`'s behaviour or its task table; you are running it, not rewriting it.
- Do not touch `results/submission/`, the recordings in `results/recordings/`, or anything in `rote/`.
- Do not commit; leave the working tree with your changes for review.
