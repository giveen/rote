# What the model wrote, and what it was asked

The hackathon asks judges to identify what was built during the event, and to show the Muse
usage behind it. This repository records that narrowly: the briefs the model was given, the
session it ran, and the commits it produced. Nothing else.

## The evidence

| where | what it is |
|---|---|
| `prompts/*.md` | the brief handed to the model, verbatim |
| `prompts/muse-code-trajectory.json` | the session Muse Code exported: every model call and tool call, unedited |
| `<run>/trace.md`, `trace.csv` | per-call tokens and cost at runtime, from the API's own usage object |
| commit trailers | `Built-with:` names the model, the call count and the cost |

## How a commit records it

Commits that a model produced carry a trailer, and nothing else is added:

```
certify: standalone HTML certificate for a run

Built-with: muse-ember-1.0 via Muse Code (31 calls, 96% cached, $0.03)
Brief: prompts/certify-task.md
Trajectory: prompts/muse-code-trajectory.json
```

Commits written by hand carry no trailer. The brief is referenced, not pasted, so the log stays
readable and the evidence lives in one place.

## Why the trajectory matters more than this file

`prompts/muse-code-trajectory.json` is the unedited export (`/export → Trajectory`): 1,028
events, 31 model calls, every tool call including the failed ones. If this document and the
trajectory ever disagree, the trajectory is right.
