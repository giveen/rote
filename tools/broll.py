"""Record the automation doing the task, for the demo video.

The generated script needs no model to run, so this needs no model either: it plays the
automation in a real browser with fresh data and records the video the way Playwright sees it.

The real-speed clip (<task>.mp4) shows how fast the automation actually is; the paced clip
(<task>-paced.mp4, via --slow-mo) is for footage a person can follow.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rote.plan import Plan, align_rows
VIEWPORT = {"width": 1280, "height": 800}

TASKS = {
    "intake": ("results/submission/intake/intake.py", "http://127.0.0.1:8765/app.html",
               "results/fresh_rows.json"),
    "vendors": ("results/submission/vendors/vendors.py", "http://127.0.0.1:8765/vendors.html",
                "results/vendor_fresh.json"),
    "sauce": ("results/submission/sauce/sauce.py", "https://www.saucedemo.com/",
              "results/sauce_fresh.json"),
    "triage": ("results/submission/triage/triage.py", "http://127.0.0.1:8765/triage.html",
               "results/triage_multi.json"),
}


def load(path: Path):
    spec = importlib.util.spec_from_file_location(f"broll_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def slow_down(mp4: Path, factor: int = 2) -> Path:
    """A half-speed cut, for footage that has to read on video.

    This is an editing convenience, not a trick: the run really does take ~3 seconds, which is
    too fast to follow, so the demo shows it at half speed and says so on screen.
    """
    out = mp4.with_name(f"{mp4.stem}-slow.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4),
                    "-filter:v", f"setpts={factor}*PTS", "-an",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", str(out)],
                   check=True)
    return out


def record(task: str, *, headless: bool = True, slow_mo: int = 0) -> Path | None:
    script_rel, url, rows_rel = TASKS[task]
    script = ROOT / script_rel
    rows = json.loads((ROOT / rows_rel).read_text())
    rows = rows["rows"] if isinstance(rows, dict) else rows

    report_path = ROOT / "results" / "submission" / task / "report.json"
    if not report_path.exists():
        print(f"  {task}: skipping — no report.json at {report_path} "
              f"(cannot align rows without a plan)")
        return None
    try:
        report = json.loads(report_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"  {task}: skipping — could not read {report_path}: {e} "
              f"(cannot align rows without a plan)")
        return None
    plan_dict = report.get("plan") if isinstance(report, dict) else None
    if not plan_dict:
        print(f"  {task}: skipping — {report_path} has no plan "
              f"(cannot align rows without a plan)")
        return None
    plan = Plan.from_dict(plan_dict)
    rows = align_rows(rows, plan)

    mod = load(script)

    out_dir = ROOT / "results" / "broll"
    raw = out_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for old in raw.glob("*.webm"):
        old.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        ctx = browser.new_context(viewport=VIEWPORT, record_video_dir=str(raw),
                                  record_video_size=VIEWPORT)
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_timeout(900)
        mod.run(page, rows)          # the automation, not the recorder
        page.wait_for_timeout(1600)
        video = page.video.path()
        ctx.close()
        browser.close()

    mp4 = out_dir / (f"{task}-paced.mp4" if slow_mo > 0 else f"{task}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
                    "-vf", "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", str(mp4)],
                   check=True)
    slow = slow_down(mp4)
    print(f"  {task}: {mp4.name} ({mp4.stat().st_size / 1e3:.0f} KB), "
          f"{slow.name} (half speed)")
    return mp4


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Record the automation doing the task. The real-speed clip "
                    "shows how fast the automation actually is; the paced clip is "
                    "for footage a person can follow.")
    parser.add_argument("tasks", nargs="*", choices=list(TASKS), metavar="TASK",
                        help="task(s) to record (default: all tasks)")
    parser.add_argument("--slow-mo", type=int, default=0, metavar="MS",
                        help="delay in milliseconds after every browser action, "
                             "passed to chromium.launch(slow_mo=MS) (default: 0); "
                             "when > 0 the clip is written to <task>-paced.mp4 "
                             "instead of <task>.mp4")
    args = parser.parse_args(argv)
    if args.slow_mo < 0:
        parser.error("--slow-mo must be >= 0")
    wanted = args.tasks or list(TASKS)
    for name in wanted:
        record(name, slow_mo=args.slow_mo)


if __name__ == "__main__":
    main()
