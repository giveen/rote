# Task: fit the captions in their band, and stop the terminal wrapping mid-word

You are working in the `rote` repository on the branch where you built the film. Read
`tools/film_timeline.py` and `tools/film_render.py` first, then look at your own output:

```
ffmpeg -v quiet -y -ss 34 -i results/video/rote-demo.mp4 -frames:v 1 /tmp/f34.png
ffmpeg -v quiet -y -ss 94 -i results/video/rote-demo.mp4 -frames:v 1 /tmp/f94.png
```

## Problem 1 — a two-line caption runs out of band

At 34 s the caption is `rote watches the recording once — attempt 1 fails, the verdict catches it`.
It wraps to two lines and the second line (`it`) is clipped by the bottom edge. The certificate
caption at 94 s does the same. The band was sized for one line.

Fix:

- the band is **130 px** tall, drawn on the card background from y=670 to y=800;
- caption text is **26 px**, centred vertically inside the band, wrapped at **100 characters**;
- content is scaled to fit inside **1280×670**, letterboxed, and never drawn in the band;
- if a caption still needs more than two lines at 26 px, shorten the caption in the timeline
  rather than shrinking the font further. Two lines is the maximum.

Update the geometry helper and its test: the content box must satisfy `y + h <= 670`, and the
band must satisfy `670 + 130 == 800`.

## Problem 2 — the terminal wraps mid-word

The cast is 104 columns wide (see its header). The terminal renderer's window is narrower than
that, so the long goal line breaks as `submitting th` / `e intake`. A terminal does not break
words; it scrolls or clips its right edge.

Fix: size the terminal window so all 104 columns fit. Measure it — render a single line of 104
`M` characters and check it does not wrap (compare the page's `scrollWidth` with `clientWidth`
for the line's element, or simply pick a font size that fits: 104 columns at 13 px monospace is
about 811 px, so a 1240 px-wide window at 14 px fits comfortably). Do not alter the cast's text
to make it fit.

## Verification you must run, and report

```
./check.sh
./.venv/bin/python tools/film.py --plan
./.venv/bin/python tools/film.py
ffprobe -v quiet -show_entries format=duration:stream=width,height -of default=nw=1 results/video/rote-demo.mp4
ffmpeg -v quiet -y -ss <terminal start + 14> -i results/video/rote-demo.mp4 -frames:v 1 /tmp/t1.png
ffmpeg -v quiet -y -ss <attempt-1 image start> -i results/video/rote-demo.mp4 -frames:v 1 /tmp/t2.png
ls -la /tmp/t1.png /tmp/t2.png
```

Report the new total duration. Do not change the beats, the order, or the clip sources.

## Rules

- Standard library only; ffmpeg and Playwright only.
- Do not touch `results/submission/`, `results/recordings/`, `docs/certificate.png`, the demo apps,
  or the verdict checks in `rote/replay.py`.
- Keep each module under ~160 lines.
- Do not commit; leave the tree for review.
