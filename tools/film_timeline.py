"""The cut as data — the ordered segments of the demo film.

Follows docs/DEMO.md shot list: title, human recording, terminal run
with its failure, browser proof, one-row/two-row frames, triage clip,
third-party app, certificate, numbers card, close. Pure data: no rendering,
deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass

FRAME_W = 1280
FRAME_H = 800
BAND = 130
CONTENT_H = FRAME_H - BAND  # 670; content never enters the band below
CAPTION_WRAP = 100
CAPTION_FONT_SIZE = 26
MAX_CAPTION_LINES = 2


def content_box(kind: str) -> tuple[int, int, int, int]:
    """(x, y, w, h) for *kind* — all kinds share top 1280x670, band below."""
    return (0, 0, FRAME_W, CONTENT_H)


@dataclass
class Segment:
    kind: str          # "card" | "terminal" | "clip" | "image"
    source: str        # file path, or the card's id for kind == "card"
    seconds: float
    caption: str       # the line burned in at the bottom

def build_timeline() -> list[Segment]:
    """Return the film in shot-list order (DEMO.md)."""
    return [
        Segment("card", "title", 12.0,
                "rote — watch a recording once, run it forever"),
        Segment("clip", "results/recordings/intake.mp4", 10.6,
                "A person copies rows by hand — boring, four minutes, unautomated"),
        Segment("terminal", "results/video/learn-take.cast", 32.41,
                "rote watches the recording once — attempt 1 fails, the verdict catches it"),
        Segment("clip", "results/broll/intake.mp4", 2.73,
                "Fresh data, same task — the automation runs in seconds"),
        Segment("image", "results/broll/failing-take/proof_attempt1.png", 10.0,
                "Attempt 1 — both rows in one form, one line stored"),
        Segment("image", "results/broll/failing-take/proof_attempt2.png", 10.0,
                "Attempt 2 — repaired plan, both lines stored — PASSED"),
        Segment("clip", "results/broll/triage-paced.mp4", 7.53,
                "Same harness, different app — triage on fresh data"),
        Segment("clip", "results/broll/sauce-paced.mp4", 7.1,
                "Not our app — saucedemo.com, three rows, three checkouts"),
        Segment("image", "docs/certificate.png", 8.0,
                "Every run leaves a certificate — what was learned, proven, and cost"),
        Segment("card", "numbers", 12.0,
                "9 calls, 19,826 tokens, $0.026 — then zero model calls"),
        Segment("card", "close", 10.0,
                "Ember reads recordings and repairs plans — show it once"),
    ]
