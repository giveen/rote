# The three minutes

A shot list for the demo video. Record at 1080p or better, terminal font ≥ 16pt, browser at
1280×800. Everything below is one take per section; cut between them.

Total budget: **3:00**. Hard stop — the rules ask for three minutes.

---

## Before you press record

```bash
cd /mnt/storage/Projects/rote
python3 -m http.server 8765 --directory app &
rm -rf results/demo && mkdir -p results/demo
```

Have open: a terminal in the repo, the browser at `http://127.0.0.1:8765/`, and
`results/submission/intake/certificate.html` in a tab.

---

## 0:00 – 0:25 — The problem, said plainly

On screen: the Stockroom page, empty form.

> "Every team has a task like this. Someone copies rows from a spreadsheet into a web form.
> It takes four minutes, it's boring, and nobody automates it, because writing the automation
> costs more than doing the task."

> "So the person does this instead."

**Play `results/recordings/intake.mp4`** — the real 10-second recording of the task.

---

## 0:25 – 1:00 — It watches once

Terminal:

```bash
PYTHONPATH=. ./.venv/bin/python -m rote learn results/recordings/intake.mp4 \
  --url http://127.0.0.1:8765/app.html --rows results/fresh_rows.json
```

While it runs, say:

> "rote shows the recording to Muse Ember — one call, about a tenth of a cent — and asks what
> the procedure was. Not what was in the pixels: the fields, the order, and which part repeats."

Cut to `results/demo/…/report.md`, the "What it learned" table:

> "Six controls, one click that commits a line, one submit. That's the whole task, as data."

---

## 1:00 – 1:40 — The proof is the point

Cut to the replay. Say:

> "Now the part that matters. It runs the automation it just wrote — against data that was
> never in the recording. Different SKUs, different suppliers, different quantities."

Show `results/fresh_rows.json` for two seconds, then the passing checks:

> "Four checks: the script ran, every value was accepted, the app stored exactly the rows we
> sent, and the task was submitted. Not a model's opinion — the app's own state."

Open `results/demo/…/certificate.html`:

> "Which produces this: a certificate per task. What it understood, what was proven, what it
> cost."

---

## 1:40 – 2:20 — The failure is also the point

Terminal:

```bash
PYTHONPATH=. ./.venv/bin/python -m rote learn results/recordings/sauce.mp4 \
  --url https://www.saucedemo.com/ --rows results/sauce_fresh.json
```

> "This is a real site — a public automation sandbox — with a login, a cart and a checkout."

When attempt 1 fails and the repair runs, do **not** cut it. Say:

> "The first plan was wrong: it treated the password as data the user supplies. So the replay
> fails, and the failure — plus the app's real controls — goes back to Ember, which fixes the
> plan. Not the code: the plan."

When attempt 2 passes:

> "Two calls. Four thousandths of a dollar. This is the honest version of the demo: the first
> answer is often wrong, and the system is built to notice and retry."

---

## 2:20 – 2:50 — Why it's cheap enough to be boring

Cut to `results/submission/trace.md`.

> "Five model calls for three tasks. Nine thousand eight hundred forty-four
> ten-thousandths of a dollar — under a cent. Ten kilobytes of input, of which a third was
> served from the prompt cache."

> "And the important number: zero. Once the automation is proven, no model runs at all. What
> you keep is a small Python file that will work next year."

---

## 2:50 – 3:00 — Close

Cut to the repo, `rote/` open.

> "Ember reads recordings and repairs plans. A compiler writes the code. A browser decides
> whether it's true. Show it once — and it proves it can do it forever."

---

## Footage you do not have to shoot

Recorded replays of the automation doing the work with fresh data. Two speeds, deliberately:

- the **plain** clip is how fast the automation actually runs;
- the **`-paced`** clip was recorded with `--slow-mo 300`, so a person can follow it. Say so on
  screen if you use it;
- the **`-slow`** cut is the same footage at half speed, for a tighter edit.

| file | length |
|---|---|
| `results/broll/intake-slow.mp4` | 5.4 s |
| `results/broll/intake.mp4` | 2.7 s |
| `results/broll/sauce-paced-slow.mp4` | 14.1 s |
| `results/broll/sauce-paced.mp4` | 7.1 s |
| `results/broll/sauce-slow.mp4` | 6.3 s |
| `results/broll/sauce.mp4` | 3.2 s |
| `results/broll/triage-paced-slow.mp4` | 15.0 s |
| `results/broll/triage-paced.mp4` | 7.5 s |
| `results/broll/triage-slow.mp4` | 5.4 s |
| `results/broll/triage.mp4` | 2.7 s |
| `results/broll/vendors-slow.mp4` | 5.2 s |
| `results/broll/vendors.mp4` | 2.6 s |

Regenerate any of them with `tools/broll.py <task>` (real speed) or
`tools/broll.py <task> --slow-mo 300` (paced). For the video, use the paced clips for sauce and
triage: at real speed three checkouts finish in under a second and the interesting screens are
gone before the eye finds them.

## Numbers to have ready, and where they come from

| number | value | source |
|---|---|---|
| cost, four tasks | $0.026179 | `results/submission/trace.md` |
| model calls | 9 | same |
| input / cached | 19,826 / 9,976 tokens | same |
| spread across runs | $0.0098 – $0.0356 | git history, `results/submission/` |
| one recording read | ~$0.001 | `results/submission/*/report.json` |
| video input length-independence | ~169 tokens | `results/gate/video_tokens.py` |
| tests | 45 passing | `./check.sh` |

## Two things not to say

- Don't say it works on "any app". Say what it did, on the three it did it on.
- Don't say the automation is AI. It is the opposite: the AI's job ends when the proof passes.
