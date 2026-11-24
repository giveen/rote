# rote — four tasks, one budget

Model: **muse-ember-1.0** through the Meta Model API. Prices: muse-ember-1.0, Standard mode: $0.10 per 1M input tokens, $0.004 per 1M cached input tokens, $0.50 per 1M output tokens (long-context rates above 200K input tokens per request).

## Totals

| | |
|---|---|
| Model calls | **9** |
| Input tokens | **19,826** |
| of which served from cache | 9,976 (50%) |
| Output tokens | **50,308** |
| of which reasoning | 43,829 |
| **Amount spent** | **$0.026179** |

## Every call

| # | stage | what it did | effort | in | cached | out | reasoning | seconds | $ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `intake` | understand | max | 2,812 | 2,748 | 2,543 | 1,799 | 6.5 | 0.001289 |
| 2 | `repair` | repair1 | max | 2,162 | 756 | 4,932 | 4,188 | 9.3 | 0.002610 |
| 3 | `vendors` | understand | max | 1,820 | 1,724 | 4,447 | 3,651 | 10.8 | 0.002240 |
| 4 | `sauce` | understand | max | 1,820 | 1,724 | 3,931 | 3,125 | 9.5 | 0.001982 |
| 5 | `repair` | repair1 | max | 2,168 | 756 | 4,351 | 3,710 | 8.2 | 0.002320 |
| 6 | `repair` | repair2 | max | 2,623 | 756 | 6,518 | 5,610 | 12.5 | 0.003449 |
| 7 | `triage` | understand | max | 1,820 | 0 | 2,947 | 2,337 | 6.5 | 0.001656 |
| 8 | `repair` | repair1 | max | 2,162 | 756 | 10,794 | 10,181 | 22.2 | 0.005541 |
| 9 | `repair` | repair2 | max | 2,439 | 756 | 9,845 | 9,228 | 20.4 | 0.005094 |

**Total: $0.026179** (within the $10 credit).

## The prompts themselves

Each call's exact request body is kept beside this file. Large media are referenced by file id, not inlined.

### Call 1 — `intake` / understand

Request: `prompts/000-intake-understand.json`

(prompt file unreadable)

### Call 2 — `repair` / repair1

Request: `prompts/001-repair-repair1.json`

(prompt file unreadable)

### Call 3 — `vendors` / understand

Request: `prompts/000-vendors-understand.json`

(prompt file unreadable)

### Call 4 — `sauce` / understand

Request: `prompts/000-sauce-understand.json`

(prompt file unreadable)

### Call 5 — `repair` / repair1

Request: `prompts/001-repair-repair1.json`

(prompt file unreadable)

### Call 6 — `repair` / repair2

Request: `prompts/002-repair-repair2.json`

(prompt file unreadable)

### Call 7 — `triage` / understand

Request: `prompts/000-triage-understand.json`

(prompt file unreadable)

### Call 8 — `repair` / repair1

Request: `prompts/001-repair-repair1.json`

(prompt file unreadable)

### Call 9 — `repair` / repair2

Request: `prompts/002-repair-repair2.json`

(prompt file unreadable)

## Method

The ledger is written by the client on every request, before the response is parsed, so a failed call still appears here. Costs are computed from the usage object the API returns, at the prices above, never from an estimate.

