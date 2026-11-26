# Task: the caption band must stop covering the evidence, and the cut needs two more beats

You are working in the `rote` repository on the branch where you built the film
(`tools/film_timeline.py`, `tools/film_render.py`, `tools/film.py`). Read all three first, then
watch what you built:

```
ffmpeg -v quiet -y -ss 62 -i results/video/rote-demo.mp4 -frames:v 1 /tmp/f62.png
ffmpeg -v quiet -y -ss 72 -i results/video/rote-demo.mp4 -frames:v 1 /tmp/f72.png
```

## Problem 1 — the band hides the thing it describes

At 62 s the caption says "Attempt 1 — both rows in one form, one line stored", and the frame it
sits on top of shows the toast "Intake submitted — 1 line recorded" — which the black caption
band **covers**. The same at 72 s. The evidence and the words are fighting for the same pixels.

Fix it in the geometry, not per-segment:

- every rendered frame stays 1280×800 and 30 fps;
- reserve a **96 px band at the bottom** for the caption, drawn on the card background;
- **content is never drawn inside that band**: scale clips and images to fit inside
  1280×704, centred horizontally, letterboxed on the background colour, and let the band sit
  below them;
- cards may draw their headline anywhere in the top 704 px;
- the terminal renderer gets the same treatment: the terminal window is 1280×704, band below.

A test can check the arithmetic without looking at pixels: assert that every segment's computed
content rectangle has `y + height <= 800 - 96` (add a small pure helper, e.g.
`content_box(kind) -> (x, y, w, h)`, and test it for all four kinds).

## Problem 2 — two cards sit too long on a still frame

The numbers card runs **30 s** and the close **15 s**. Nothing changes on screen for half a
minute. Bring the numbers card to 12 s and the close to 10 s.

## Problem 3 — two beats are missing

The cut has no third-party app and no certificate:

- after the triage clip, add `results/broll/sauce-paced.mp4` (7.1 s) with the caption
  `Not our app — saucedemo.com, three rows, three checkouts`;
- after that, add a still of `docs/certificate.png` (8 s) with the caption
  `Every run leaves a certificate — what it understood, what was proven, what it cost`.

Keep the total between 120 and 170 seconds, and keep the order sensible: title, human, terminal,
automation proof, failure frames, triage, sauce, certificate, numbers, close.

## Verification you must run, and report

```
./check.sh
./.venv/bin/python tools/film.py --plan
./.venv/bin/python tools/film.py
ffprobe -v quiet -show_entries format=duration:stream=width,height,r_frame_rate -of default=nw=1 results/video/rote-demo.mp4
```

Then extract frames at the start of the two failure segments and look at the file sizes to confirm
they rendered:

```
ffmpeg -v quiet -y -ss <start-of-attempt-1> -i results/video/rote-demo.mp4 -frames:v 1 /tmp/a1.png
ffmpeg -v quiet -y -ss <start-of-certificate> -i results/video/rote-demo.mp4 -frames:v 1 /tmp/cert.png
ls -la /tmp/a1.png /tmp/cert.png
```

Report the new total duration and the two timestamps you used. Do not drop a segment to hit the
duration — adjust the numbers card, then the close, then the certificate still.

## Rules

- Standard library only; ffmpeg and Playwright only, no new dependencies.
- Do not touch `results/submission/`, the recordings, `docs/certificate.png` itself, the demo apps,
  or the verdict checks in `rote/replay.py`.
- Keep the modules under ~160 lines each.
- Do not commit; leave the tree for review.
