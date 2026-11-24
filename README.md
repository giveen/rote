# rote

**Show it once. It does it forever — and proves it.**

`rote` watches a screen recording of a repetitive task in a web app, works out what was
done, writes the automation, and then *proves* it by replaying it against fresh data.

Built for the [Meta Muse Ember Hackathon](https://cerebralvalley.ai/e/muse-ember-hackathon)
(Nov 23 – Dec 2, 2026). Every model call runs on `muse-ember-1.0` through the Meta Model
API, inside a $10 credit.

## Who wrote what

`git log` is the audit trail: every commit carries the prompt that produced it, and
`PROMPTS.md` explains the convention plus the commits that predate it. The runtime model is
`muse-ember-1.0`; parts of this repository, including `rote/certify.py` and its tests, were
written by it through Muse Code, with the session exported in `prompts/`.

Status: in development.
