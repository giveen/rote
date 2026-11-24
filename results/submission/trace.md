# rote — three tasks, one budget

Model: **muse-ember-1.0** through the Meta Model API. Prices: muse-ember-1.0, Standard mode: $0.10 per 1M input tokens, $0.004 per 1M cached input tokens, $0.50 per 1M output tokens (long-context rates above 200K input tokens per request).

## Totals

| | |
|---|---|
| Model calls | **6** |
| Input tokens | **12,829** |
| of which served from cache | 8,464 (66%) |
| Output tokens | **70,244** |
| of which reasoning | 66,051 |
| **Amount spent** | **$0.035592** |

## Every call

| # | stage | what it did | effort | in | cached | out | reasoning | seconds | $ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `intake` | understand | max | 2,812 | 2,748 | 2,514 | 1,905 | 4.9 | 0.001274 |
| 2 | `repair` | repair1 | max | 2,129 | 756 | 28,514 | 27,761 | 60.4 | 0.014397 |
| 3 | `repair` | repair2 | max | 2,111 | 756 | 17,911 | 17,158 | 39.4 | 0.009094 |
| 4 | `vendors` | understand | max | 1,820 | 1,724 | 2,483 | 1,936 | 5.4 | 0.001258 |
| 5 | `sauce` | understand | max | 1,820 | 1,724 | 8,570 | 7,864 | 19.7 | 0.004301 |
| 6 | `repair` | repair1 | max | 2,137 | 756 | 10,252 | 9,427 | 20.9 | 0.005267 |

**Total: $0.035592** (within the $10 credit).

## The prompts themselves

Each call's exact request body is kept beside this file. Large media are referenced by file id, not inlined.

### Call 1 — `intake` / understand

Request: `prompts/000-intake-understand.json`

(prompt file unreadable)

### Call 2 — `repair` / repair1

Request: `prompts/001-repair-repair1.json`

(prompt file unreadable)

### Call 3 — `repair` / repair2

Request: `prompts/002-repair-repair2.json`

(prompt file unreadable)

### Call 4 — `vendors` / understand

Request: `prompts/000-vendors-understand.json`

(prompt file unreadable)

### Call 5 — `sauce` / understand

Request: `prompts/000-sauce-understand.json`

(prompt file unreadable)

### Call 6 — `repair` / repair1

Request: `prompts/001-repair-repair1.json`

(prompt file unreadable)

## Method

The ledger is written by the client on every request, before the response is parsed, so a failed call still appears here. Costs are computed from the usage object the API returns, at the prices above, never from an estimate.

