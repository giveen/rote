# Narration script

The film is `results/video/rote-demo.mp4`: **2:02.4**, silent, captions burned in. Record your voice
over it. Each block below is one beat; the timings are the segment boundaries from
`tools/film.py --plan`, so they match what is on screen.

Read at a normal pace — every block has more time than words. If a line feels rushed, cut words,
not the pause: the gaps are where the terminal and the browser do their work on screen.

---

## 0:00.0 – 0:12.0 — title card

> Every team has a task like this one. Someone copies rows from a spreadsheet into a web form.
> It takes four minutes, it is boring, and nobody automates it, because writing the automation
> costs more than doing the task.

## 0:12.0 – 0:22.6 — a person doing it by hand

(no words needed — let them watch it happen; the caption says it)

> This is rote. You record the task once, with your phone, or with anything that can capture a
> screen.

## 0:22.6 – 0:55.0 — the terminal: it reads the recording, attempt 1 fails

> rote shows the recording to Muse Ember — one call, about a tenth of a cent — and asks what the
> procedure was. Not what was in the pixels: the fields, the order, and the one block that
> repeats for each row of data.

(the plan appears on screen at about 0:33)

> Inside ten seconds it has the whole task as data. Six controls, a click that commits a line, a
> submit. That is not code yet, and that is deliberate.

(the failure line lands at about 0:34)

> Then it runs the automation it just wrote — against data that was never in the recording.
> And the first plan is wrong: it put the click that commits a line outside the repeating block,
> so both rows went into the same form and only the second one survived.

> Nothing about that was caught by a second model. The app itself stored one line where two were
> sent, and the verdict says so. So the failure goes back to Ember, with the app's real controls,
> and it repairs the plan.

(the run passes at about 0:54)

> Two calls. Half a cent. That is the honest shape of this: the first answer is often wrong, and
> the system is built to notice.

## 0:55.0 – 0:57.7 — the automation running on fresh data

> Now the same task, on data it has never seen.

## 0:57.7 – 1:07.7 — the failure frame, side by side

> One line where there should be two. The toast is the app telling on itself.

## 1:07.7 – 1:17.7 — the repaired frame

> And after the repair, both lines — the same run, the same data, one plan later.

## 1:17.7 – 1:25.3 — triage, a different app

> Same harness, a different app: search a ticket queue, open the matching row, change it, save.

## 1:25.3 – 1:32.4 — saucedemo, not our app

> And not our app at all — a public sandbox, three rows, three checkouts, each one completing
> before the next begins.

## 1:32.4 – 1:40.4 — the certificate

> Every run leaves one of these: what it understood, what the replay actually proved, and what it
> cost. No model is involved in reading that page.

## 1:40.4 – 1:52.4 — the numbers

> Four tasks, nine model calls, two cents. Ten kilobytes of input, half of it served from the
> prompt cache.

> And the number that matters most is the one that comes after: zero. Once the automation is
> proven, no model runs again. What you keep is a small Python file that will still work next
> year.

## 1:52.4 – 2:02.4 — close

> Ember reads recordings and repairs plans. A compiler writes the code. A browser decides whether
> it is true. Show it once — and it proves it can do it forever.

---

## Recording it

1. Play `results/video/rote-demo.mp4` on a second monitor, or with the sound off in any editor, and
   record your voice against it in OBS, Audacity, QuickTime — anything.
2. Keep the levels normal; there is no music to fight.
3. If a take slips, re-record from the start of the block, not the start of the film. The blocks are
   long enough to splice.
4. Export 1080p, H.264, and upload it. The submission form takes a **link**, not a file — unlisted
   YouTube is fine.

## Two things not to say

- Don't say it works on any app. Say what it did, on the four it did it on.
- Don't call the automation AI. The point is the opposite: the model's job ends when the proof
  passes.
