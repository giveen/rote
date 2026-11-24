"""Record a session the way a person would do it, and keep the ground truth beside it.

The recording is what the model sees. The ground truth is what we score it against, and
it is written by a human (here: by the session script), never by the model.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import sync_playwright

from .locators import perform
from .plan import Step

VIEWPORT = {"width": 1280, "height": 800}


@dataclass
class Session:
    """One run through a task, as a list of actions and the data they carried."""
    name: str
    url: str
    steps: list[Step] = field(default_factory=list)
    rows: list[dict[str, str]] = field(default_factory=list)

    @property
    def seconds(self) -> float:
        return 0.9 * max(len(self.steps), 1) + 2.5

    def describe(self) -> str:
        return "\n".join(f"{s.action:<6} {s.target:<18} {s.value or ''}"
                         for s in self.steps)


def record(session: Session, out_dir: Path, *, headless: bool = True,
           pace: float = 0.55) -> Path:
    """Play the session in a real browser while recording video. Returns the mp4."""
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = out_dir / "raw"
    raw.mkdir(exist_ok=True)
    for old in raw.glob("*.webm"):
        old.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport=VIEWPORT, record_video_dir=str(raw),
                                  record_video_size=VIEWPORT)
        page = ctx.new_page()
        page.goto(session.url)
        page.wait_for_timeout(int(pace * 1400))     # a beat before touching anything
        for step in session.steps:
            perform(page, step.action, step.target, step.value)
            page.wait_for_timeout(int(pace * 1000))
        page.wait_for_timeout(int(pace * 1600))     # let the result land on screen
        state = page.evaluate("() => window.__submitted ?? null")
        video = page.video.path()
        ctx.close()
        browser.close()

    mp4 = out_dir / f"{session.name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
                    "-vf", "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                    str(mp4)], check=True)
    meta = out_dir / f"{session.name}.truth.json"
    meta.write_text(json.dumps({
        "name": session.name,
        "url": session.url,
        "seconds": _duration(mp4),
        "steps": [{"action": s.action, "target": s.target, "value": s.value}
                  for s in session.steps],
        "rows": session.rows,
        "end_state": state,
    }, indent=2))
    return mp4


def _duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 2)
    except ValueError:
        return 0.0


def vendor_session(url: str, data: dict[str, str], *, name: str = "vendors") -> Session:
    """The VendorDesk task: one vendor, with a checkbox, a date and a free-text note."""
    steps = [
        Step("type", "Company name", data["company"]),
        Step("select", "Country", data["country"]),
        Step("type", "Contract start", data["start"]),
        Step("type", "Annual spend", data["spend"]),
        Step("select", "Category", data["category"]),
        Step("type", "Internal reference", data["reference"]),
        Step("type", "Notes", data["notes"]),
        Step("check", "Send welcome pack", "yes"),
        Step("submit", "Create vendor", None),
    ]
    return Session(name=name, url=url, steps=steps, rows=[data])


def session_from_json(path, name: str | None = None) -> Session:
    """Any session, described in a file: {"name","url","steps":[{"action","target","value"}],"rows"}"""
    import json as _json
    spec = _json.loads(Path(path).read_text())
    steps = [Step(s["action"], s["target"], s.get("value")) for s in spec["steps"]]
    return Session(name=name or spec.get("name", "session"), url=spec["url"],
                   steps=steps, rows=spec.get("rows", []))


def intake_session(url: str, rows: list[dict[str, str]], *, name: str = "intake") -> Session:
    """The stockroom task: type each received line, then submit the intake."""
    steps: list[Step] = []
    for row in rows:
        steps += [
            Step("type", "SKU", row["sku"]),
            Step("type", "Description", row["description"]),
            Step("type", "Quantity", row["quantity"]),
            Step("type", "Unit cost", row["unit_cost"]),
            Step("select", "Supplier", row["supplier"]),
            Step("select", "Location", row["location"]),
            Step("click", "Add line", None),
        ]
    steps.append(Step("submit", "Submit intake", None))
    return Session(name=name, url=url, steps=steps, rows=rows)
