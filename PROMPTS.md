# What the model was asked, and what it wrote

The hackathon asks judges to identify what was built during the event and to show the Muse
usage behind it. This repository records exactly that, and nothing else.

## In every commit message

One line, quoted:

```
certify: standalone HTML certificate for a run

Prompt to Muse: "add rote certify — a self-contained HTML certificate for a run"

Built by: muse-ember-1.0 via Muse Code (31 calls, 96% cached, $0.03)
```

The prompt is one line on purpose: it says what was asked for, and the log stays a log.

## Where the rest of the evidence lives

| where | what it is |
|---|---|
| `prompts/*.md` | the full brief handed to the model |
| `prompts/muse-code-trajectory.json.gz` | the session Muse Code exported: every model call and tool call, unedited |
| `<run>/trace.md`, `<run>/trace.csv` | per-call tokens and cost at runtime, from the API's own usage object |

## What is deliberately not here

Private conversation is not part of this repository, and `tools/commit.sh` has no way to put
it there.

## Why the trajectory outranks this file

`prompts/muse-code-trajectory.json.gz` is the unedited `/export → Trajectory` output: 1,028
events, 31 model calls to `muse-ember-1.0`, every tool call including the failed ones. If this
document and the trajectory disagree, the trajectory is right.
