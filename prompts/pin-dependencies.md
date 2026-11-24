# Task: make the dependencies reproducible, and prove it with a test

You are working in the `rote` repository on a branch. Read `docs/AUDIT.md` (section "What the
audit did not find" and the dependency work), `requirements.txt`, `check.sh`, and
`tests/test_dependency_audit.py` before you start.

## The problem

`requirements.txt` says:

```
playwright>=1.40
httpx>=0.27
```

A judge who clones this repository next month will install different code than the code the
results were measured on. That is a reproducibility bug in a submission whose whole point is
that the numbers can be checked.

The audit found **no known advisories** for the exact versions currently installed, so the right
move is to pin them, not to replace them.

## What to do

**1. Pin the direct dependencies** in `requirements.txt`, keeping it readable:

```
playwright==1.65.2
httpx==0.28.1
```

**2. Add `requirements.lock.txt`** with the complete resolved set, exactly as installed here,
alphabetical, excluding `pip` itself:

```
anyio==4.16.0
certifi==2026.11.20
greenlet==3.5.6
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
playwright==1.65.2
typing_extensions==4.16.0
```

Add a short comment at the top of the lock file saying what it is for and how to regenerate it
(`./.venv/bin/pip freeze | grep -v '^pip=='`).

**3. Add `tests/test_requirements.py`** (unittest, matching the existing style) that fails if
this regresses:
- every non-comment, non-empty line in `requirements.txt` matches `name==version` —
  no `>=`, `~=`, `^`, no ranges;
- the versions in `requirements.txt` appear identically in `requirements.lock.txt`;
- every line of the lock is also pinned.

**4. Update the README** in one short paragraph under the install section: that the
dependencies are pinned to the audited versions, that the audit (`tools/dependency_audit.py`)
reports zero known advisories for them, and how to re-run it.

**5. Do not** change `check.sh`, the CI workflow, or any module in `rote/`. This task is about
the files that describe dependencies.

## Verification you must run

```
./check.sh
```

All tests must pass, including your new ones. Then prove the pinning is real:

```
./.venv/bin/pip install --dry-run -r requirements.txt
```

and confirm it resolves without trying to change the versions.

## Rules

- Standard library only; no new dependencies.
- Do not modify generated automations, recordings or anything under `results/`.
- Keep the file formatting plain: one requirement per line, no trailing spaces.
