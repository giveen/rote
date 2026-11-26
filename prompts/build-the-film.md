# Task: build the demo film — a timeline, three renderers, and one command

You are working in the `rote` repository on a branch. Read `docs/DEMO.md` (the shot list — the
film follows it), `tools/broll.py` (how Playwright video is already captured), `rote/scriptenv.py`
(style), `AGENTS.md` and `check.sh` first.

## What exists already

| file | what it is |
|---|---|
| `results/video/learn-take.cast` | an asciinema v2 cast of a real `rote learn` run: 31.4 s, 6 output events, a failed attempt at 12.1 s and PASSED at 31.4 s |
| `results/recordings/intake.mp4` | a human doing the task by hand, 10.6 s |
| `results/broll/intake.mp4` | the automation doing the same task, 2.7 s |
| `results/broll/triage-paced.mp4` | the automation on a different app, 7.5 s |
| `results/broll/failing-take/proof_attempt1.png` and `proof_attempt2.png` | the same run: one row stored vs two |
| `results/submission/trace.md` | the token and cost numbers as committed |

## The design I want

Three small modules under `tools/`, because the cut has to be reviewable before it is three
minutes of video:

**1. `tools/film_timeline.py` — the cut as data.**

```python
@dataclass
class Segment:
    kind: str          # "card" | "terminal" | "clip" | "image"
    source: str        # file path, or the card's id
    seconds: float
    caption: str       # the line burned in at the bottom

def build_timeline() -> list[Segment]: ...
```

It returns the ordered segments of the film, and it is pure: no rendering, no filesystem reads
beyond what it needs to know a duration. Put the beats from `docs/DEMO.md` in it: title card,
the human recording, the terminal run, the browser proof, the failure frames, the triage clip,
the numbers card, the close.

**2. `tools/film_render.py` — one renderer per kind.**

- `render_card(segment, out)` — an HTML card (dark, system font stack, 1280×800) with a big
  headline, an optional subline and the caption; recorded with Playwright's `record_video_dir`
  for `segment.seconds`, then encoded to mp4.
- `render_terminal(segment, out)` — an HTML page styled as a dark terminal that **replays the
  cast at its real timings**: read the cast's JSON events, schedule them with
  `page.evaluate` / `setTimeout` driven from the recorded timings, and record the page with
  Playwright for the cast's full duration plus one second. The text must be the cast's text,
  unmodified — this is a replay of a real session, not a mock-up. Show a title bar with the
  command that was run.
- `render_clip(segment, out)` — reuse the existing mp4, scaled to 1280×800 with letterboxing if
  the aspect differs.
- `render_image(segment, out)` — a still (the proof frames) held for `segment.seconds`, scaled to
  fit, on the card background.

Every renderer takes a caption and burns it in with ffmpeg `drawtext` (black band at the bottom,
white text, 28 px, wrap at ~90 characters). Use a font that exists on this machine
(`fc-match monospace` to find one) and say in the commit message which.

**3. `tools/film.py` — the one command.**

```
./.venv/bin/python tools/film.py                 # → results/video/rote-demo.mp4
./.venv/bin/python tools/film.py --plan          # print the timeline and durations, render nothing
```

It renders every segment into `results/video/parts/`, concatenates them with ffmpeg (same codec,
fps, resolution throughout — 1280×800, 30 fps, yuv420p, H.264), and writes the finished file.
Print the total duration at the end.

## Tests

`tests/test_film_timeline.py`, no network and no browser:

- the timeline is non-empty, every segment has a positive duration and a non-empty caption;
- the total is between 120 and 180 seconds (the rules allow three minutes);
- the kinds are only the four known ones;
- sources referenced as files exist (skip the check for cards);
- `build_timeline()` is deterministic: two calls give the same list.

## What the finished film has to contain

In order: the title, the human recording, the terminal run (with its failure visible), the
browser proof that it works, the one-row/two-row proof frames, the triage clip, the numbers
card, and a close. `--plan` output must let me see that order without rendering.

## Verification you must run, and report

```
./check.sh
./.venv/bin/python tools/film.py --plan
./.venv/bin/python tools/film.py
ffprobe -v quiet -show_entries format=duration:stream=width,height,r_frame_rate -of default=nw=1 results/video/rote-demo.mp4
```

Report the total duration, the resolution and the frame rate. Rendering takes a few minutes; if
`./.venv/bin/python tools/film.py` fails on a segment, fix that segment rather than dropping it
from the timeline.

## Rules

- Standard library only in the Python; ffmpeg and Playwright are already available.
- Do not modify anything under `results/` except `results/video/`; do not touch `results/submission/`,
  the recordings, the demo apps, or the verdict checks in `rote/replay.py`.
- Keep every module under ~150 lines. If a renderer grows past that, it is doing too much.
- Do not commit; leave the tree for review.
