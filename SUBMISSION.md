# Submission pack

What the Muse Ember Hackathon asks for, and where each piece is.

```mermaid
checklist
    [x] Public repository | github.com/giveen/rote, clean history from Nov 23
    [x] Built on Muse Ember | every call muse-ember-1.0 via the Model API
    [x] Prompt and token trace | results/submission/trace.md + trace.csv + the exact request bodies
    [x] Muse Code trajectory | prompts/muse-code-trajectory.json.gz, 1,028 events
    [x] Project description | the text below, and README.md
    [x] Within the $10 credit | $9.11 of $10 remaining, $0.89 spent
    [?] Usage screenshot | captured for Nov 23–24; must be re-taken on Dec 2 for the full window
    [-] 3-minute demo video | to record — shot list in docs/DEMO.md
    [x] Certificate command in main | merged from feature/certificate, trajectory gzipped
```

## Description, for the form

**rote — show it once, and it proves it can do it forever.**

Every team has a repetitive web task nobody automates, because the automation costs more than
the task. rote watches a screen recording of that task once, works out the procedure, writes
readable Playwright automation, and then *proves* the automation by replaying it against data
that was never in the recording.

The model's job is deliberately small: read the recording, and return a plan of fields,
actions and one repeating block. A compiler turns that plan into a 70-line Python file. A real
browser runs it and the app's own state decides whether it passed. When the plan is wrong — on
two of the three tasks below it was — the failure evidence and the app's real controls go back
to Muse Ember, which repairs *the plan*, not the code.

Four tasks, four apps — two fixtures, a record-editing queue, and a public automation sandbox
with a login, a cart and a checkout across three rows. **Nine model calls, $0.026179**, four
passes. Once proven, no model runs at all. Across runs the same work has cost between one and
four cents, because a plan that needs repairing costs more.

What is left unproven is stated in the README: one row of fresh data on the third-party app,
a single contiguous repeating block, and anything whose controls have no accessible name.

## The numbers, and where they come from

| claim | value | file |
|---|---|---|
| total spend, four tasks | $0.026179 over 9 calls | `results/submission/trace.md` |
| input / cached / output tokens | 19,826 / 9,976 / 50,308 | same |
| credit left of $10 | $9.11 | Meta billing page, Nov 23 |
| whole account usage on Nov 23 | ~2.7M tokens, 2M output | `results/submission/usage-2026-11-24.png` |
| tests | 45 passing | `./check.sh` |
| trajectory | 1,028 events, 31 model calls | `prompts/muse-code-trajectory.json.gz` |

Why the account total is far larger than the submission run: the exploratory work in this
repository was deliberately expensive — reasoning at `max` effort over real libraries — and
most of those tokens are cached reads. The product's own run is the cheap one.

## The form, read from the live page

Checked on the actual submit form, not from the guide.

| field | required | limit / format |
|---|---|---|
| Team name | yes | free text |
| Project description | yes | **3,000 characters**, live counter |
| Public GitHub repository | yes | URL |
| Demo video | yes | **a link, not an upload** — the placeholder is `https://youtube.com/watch?v=…`, so it must be hosted (YouTube, unlisted is fine) |
| Meta team ID | yes | `1857589511891749` (the `?team_id=` in the dev.meta.ai URL) |
| Use of Meta products | yes | 3,000 characters |
| Why Meta's models matter | yes | 3,000 characters |
| Link to X post | no | URL; they ask you to tag @MetaForDevs and @cerebral_valley |
| Usage screenshot | yes | image upload, JPG/PNG/WEBP/GIF, ≤10 MB, up to 10 |
| Muse Code JSON export | if used | file upload, ≤10 MB — **accepts `.json`, not `.json.gz`**, so the repository's gzipped trajectory must be expanded first |
| Two opinion radios + a permissions checkbox | yes | — |

`tools/submission_files.sh` builds exactly those files into `submission-upload/`, expands the
trajectory, and writes `answers.md` with drafts for all three 3,000-character fields (1,158 /
1,128 / 931 characters, so there is room to add).

## To do on December 2, before submitting

1. **Re-take the usage screenshot** with the range Nov 23 – Dec 2 and the model filter set to
   `muse-ember-1.0`. The current one covers Nov 23–24 only, because the calendar will not
   select days that have not happened.
2. **Record the video** from `docs/DEMO.md`, three minutes, no more.
3. **Re-run `tools/demo.sh all`** the day you record, so the numbers in the video match the
   certificates on disk.
4. Confirm the repository is public and the video link opens in a private window.
