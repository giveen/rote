# rote — three tasks, one budget

Model: **muse-ember-1.0** through the Meta Model API. Prices: muse-ember-1.0, Standard mode: $0.10 per 1M input tokens, $0.004 per 1M cached input tokens, $0.50 per 1M output tokens (long-context rates above 200K input tokens per request).

## Totals

| | |
|---|---|
| Model calls | **5** |
| Input tokens | **10,583** |
| of which served from cache | 3,868 (37%) |
| Output tokens | **18,314** |
| of which reasoning | 14,942 |
| **Amount spent** | **$0.009844** |

## Every call

| # | stage | what it did | effort | in | cached | out | reasoning | seconds | $ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `intake` | understand | max | 2,812 | 316 | 1,788 | 1,186 | 4.5 | 0.001145 |
| 2 | `repair` | repair1 | max | 2,122 | 756 | 4,490 | 3,738 | 9.6 | 0.002385 |
| 3 | `vendors` | understand | max | 1,820 | 316 | 2,107 | 1,575 | 5.1 | 0.001205 |
| 4 | `sauce` | understand | max | 1,820 | 1,724 | 3,746 | 3,002 | 8.1 | 0.001889 |
| 5 | `repair` | repair1 | max | 2,009 | 756 | 6,183 | 5,441 | 12.7 | 0.003220 |

**Total: $0.009844** (within the $10 credit).

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

## Method

The ledger is written by the client on every request, before the response is parsed, so a failed call still appears here. Costs are computed from the usage object the API returns, at the prices above, never from an estimate.

