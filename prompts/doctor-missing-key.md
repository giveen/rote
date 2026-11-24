# Task: the API check must not blame the network for a missing key

You are working in the `rote` repository, on the branch where you added `rote doctor`. Read
`rote/doctor.py` first.

## What is wrong

On a machine with no API key at all, the doctor prints:

```
✗ API key present: no API key found (no ~/.config/muse/auth.json) → export MODEL_API_KEY=…
✗ API reachable: unreachable (FileNotFoundError: [Errno 2] No such file or directory: '…/auth.json… → check your network and API key, or run `rote doctor --offline`
```

The second line is wrong twice over: the network is fine, the key is missing, and the failure it
reports is a `FileNotFoundError` from reading the credential file — not a network error. Someone
following this would go and check their Wi-Fi.

Reproduce it:

```
mkdir -p /tmp/fakehome
env -u MODEL_API_KEY HOME=/tmp/fakehome PYTHONPATH=. ./.venv/bin/python -m rote doctor
```

## What to do

1. When the **key check failed**, the **API check must not run**. Report it as a third state —
   skipped, not failed — with the reason being the missing key, for example:

   ```
   ⚠ API reachable: skipped (no API key to test with)
   ```

   The warning mark already exists in this output for `--offline`; use the same shape. A skipped
   check must not make the run fail on its own, but the run is already failing on the key check,
   so the exit code stays 1.

2. Make the API check itself robust: if it does run and the key cannot be read, report that as a
   credential problem in one short line rather than echoing an exception. Keep `--offline`
   behaviour as it is.

3. Add tests in `tests/test_doctor.py`:
   - with a failing key check, the API check is skipped and its detail mentions the missing key;
   - a skipped API check does not by itself turn a passing run into a failing one (drive this
     with fake checks, no network).

## Verification you must run, and report

```
./check.sh
env -u MODEL_API_KEY HOME=/tmp/fakehome PYTHONPATH=. ./.venv/bin/python -m rote doctor ; echo "exit=$?"
./.venv/bin/python -m rote doctor ; echo "exit=$?"
```

Note: run those without piping into `tail` — a pipe hides the exit code, which is how this
mistake survived a review. The first must exit 1 with the API line marked skipped, the second
must exit 0.

## Rules

- Standard library only.
- Do not change which checks exist, only the order of consequences between them.
- Do not touch `results/`, the demo apps, or the verdict checks in `rote/replay.py`.
- Do not commit; leave the tree for review.
