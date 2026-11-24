"""How does video length translate into tokens? The whole cost story rests on this.

The token-count endpoint only tokenizes: it generates nothing and is not billed as
generation. Safe to measure properly.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import httpx

BASE = "https://api.meta.ai/v1"
KEY = json.loads(Path.home().joinpath(".config/muse/auth.json").read_text())[
    "providers"]["meta"]["api_key"]
H = {"Authorization": f"Bearer {KEY}"}
ROOT = Path(__file__).resolve().parents[2]
FRAMES = ROOT / "results" / "frames"


def make_video(seconds: int, fps: int = 30) -> Path:
    """A real-looking recording: the session frames cycled to fill `seconds`."""
    out = Path(tempfile.mkdtemp()) / f"v{seconds}.mp4"
    listfile = out.with_suffix(".txt")
    names = sorted(FRAMES.glob("f*.png"))
    lines = []
    for i in range(seconds * fps):
        lines.append(f"file '{names[i % len(names)]}'")
        lines.append(f"duration {1/fps}")
    listfile.write_text("\n".join(lines) + "\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(listfile), "-vf", "fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "ultrafast", str(out)], check=True)
    return out


def upload(path: Path) -> str:
    with path.open("rb") as f:
        r = httpx.post(f"{BASE}/files", headers=H, data={"purpose": "user_data"},
                       files={"file": (path.name, f, "video/mp4")}, timeout=600)
    r.raise_for_status()
    d = r.json()
    return d.get("id") or d["file"]["id"]


def tokens(fid: str) -> int:
    body = {"model": "muse-ember-1.0",
            "input": [{"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": "Summarise what happens."},
                {"type": "input_file", "file_id": fid}]}]}
    r = httpx.post(f"{BASE}/responses/input_tokens", headers=H, json=body, timeout=600)
    r.raise_for_status()
    return r.json()["input_tokens"]


if __name__ == "__main__":
    print(f"{'seconds':>8} {'MB':>7} {'tokens':>8} {'tok/s':>8} {'$/read':>10}")
    for secs in (5, 16, 30, 60, 120):
        v = make_video(secs)
        fid = upload(v)
        n = tokens(fid)
        print(f"{secs:>8} {v.stat().st_size/1e6:>7.1f} {n:>8,} {n/secs:>8.1f} "
              f"{n*0.10/1e6:>10.6f}")
