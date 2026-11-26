"""One command: render the film.  ./venv/bin/python tools/film.py [--plan]"""
from __future__ import annotations
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from film_render import render_card, render_clip, render_image, render_terminal
from film_timeline import build_timeline

OUT = ROOT / "results" / "video" / "rote-demo.mp4"
PARTS = ROOT / "results" / "video" / "parts"

RENDERERS = {"card": render_card, "terminal": render_terminal,
             "clip": render_clip, "image": render_image}

def print_plan() -> None:
    segs = build_timeline()
    total = 0.0
    for i, s in enumerate(segs, 1):
        total += s.seconds
        print(f"{i:>2}. {s.kind:<8} {s.seconds:>6.2f}s  {s.source}  — {s.caption}")
    print(f"\ntotal: {total:.1f}s ({int(total)//60}:{int(total)%60:02d})  segments: {len(segs)}")

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Build the demo film.")
    ap.add_argument("--plan", action="store_true", help="print timeline, render nothing")
    args = ap.parse_args(argv)
    if args.plan:
        print_plan()
        return
    segs = build_timeline()
    PARTS.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for i, seg in enumerate(segs):
        name = f"{i:02d}-{seg.kind}-{Path(seg.source).name or seg.source}.mp4"
        name = name.replace(" ", "_")
        out = PARTS / name
        print(f"[{i+1}/{len(segs)}] rendering {seg.kind} {seg.source} ({seg.seconds:.1f}s) -> {out.name}")
        RENDERERS[seg.kind](seg, out)
        parts.append(out)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        lst = Path(f.name)
        for p in parts:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", str(lst), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-r", "30", str(OUT)], check=True)
    lst.unlink(missing_ok=True)
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(OUT)], capture_output=True, text=True)
    dur = float(r.stdout.strip() or "0")
    print(f"\nwrote {OUT} — {dur:.1f}s")
    print(f"total duration: {dur:.2f} seconds")

if __name__ == "__main__":
    main()
