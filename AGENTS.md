# Working in this repository

`rote` turns a screen recording of a repetitive web task into browser automation that proves
itself by replaying it against fresh data. Read `README.md` for what it does and `SUBMISSION.md`
for the state of the hackathon entry.

## Before you change anything

```
./check.sh
```

That is the project's check: it compiles every module, runs the unittest suite, and validates the
demo apps. It must pass before and after your change. Add tests for behaviour you add; the suite
is the only thing keeping the verifier honest, so do not weaken a check in `rote/replay.py` to
make something pass.

Browser-dependent tests skip themselves when Playwright's Chromium is absent. Install it with
`./.venv/bin/playwright install chromium`.

## The commit convention — read this before committing

**Every commit message carries the prompt it came from, as one quoted line**, and nothing else
about the conversation:

```
certify: standalone HTML certificate for a run

Prompt to Muse: "add rote certify — a self-contained HTML certificate for a run"

Built by: muse-ember-1.0 via Muse Code (31 calls, 96% cached, $0.03)
```

Rules that follow from it:

- Use `tools/commit.sh -s "<subject>" -p "<one line prompt>" [-m "<who and what it cost>"]`.
  It refuses to commit without the prompt line and cannot accept a multi-line transcript.
- The prompt is the instruction the change came from — one line, imperative. The *full* brief
  belongs in `prompts/<task>.md`, and the message points at it rather than pasting it.
- **Never put the human's own words, or any conversation transcript, in a commit message.** The
  repository is public. Briefs and model traces are evidence and belong here; a conversation does
  not.
- A change made by the model says so: `Built by: muse-ember-1.0 via Muse Code (…)`, with the
  session exported to `prompts/`.

`PROMPTS.md` explains the evidence: briefs, trajectories, and the runtime token trace.

## Where things belong

| path | what goes in it |
|---|---|
| `rote/` | the product: client, plan, understand, synth, replay, repair, certify, trace, cli |
| `rote/scriptenv.py` | runtime helpers, embedded into every generated script *and* used by the recorder — one implementation, never two |
| `app/` | demo fixtures only. They are the stage, not the product |
| `prompts/` | the brief for each model task, and the session trajectory it produced |
| `results/submission/` | the committed evidence bundle: reports, certificates, trace |
| `results/broll/` | recorded replays for the demo video, plain and paced |
| `docs/` | the audit, the demo shot list, the dependency snapshot |

## Two rules that are easy to get wrong

1. **Do not edit a plan, a generated script, or a proof's data by hand** to make a run pass. If it
   fails, the fix is in the harness — decomposition, evidence, instructions — not in the artifact
   under test. Say so and change the harness.
2. **A check that cannot observe something must say so** rather than passing silently. Verdicts
   in `rote/replay.py` are the credibility of the whole project; a false pass is worse than a
   visible failure.
