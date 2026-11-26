"""One renderer per kind. Font for captions: DejaVu Sans Mono (fc-match monospace).

Geometry: every frame is 1280x800 at 30 fps; content lives in the top
1280x670 (see film_timeline.content_box) and the bottom 130 px is a caption
band drawn on the card background. Nothing is drawn inside the band except
the caption itself.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from playwright.sync_api import sync_playwright
from film_timeline import (BAND, CONTENT_H, FRAME_H, FRAME_W, CAPTION_FONT_SIZE,
                           CAPTION_WRAP, content_box)

ROOT = Path(__file__).resolve().parents[1]
VIEWPORT = {"width": FRAME_W, "height": CONTENT_H}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BG = "0x0e1116"
SCALE = (f"scale={FRAME_W}:{CONTENT_H}:force_original_aspect_ratio=decrease,"
         f"pad={FRAME_W}:{CONTENT_H}:(ow-iw)/2:(oh-ih)/2:color={BG}")
PAD = f"pad={FRAME_W}:{FRAME_H}:0:0:color={BG}"
CARDS = {
    "title": ("rote", "recordings in — automation out"),
    "numbers": ("9 calls · $0.026 · 19,826 tokens",
                "50% cached — then zero model calls. Once proven, a Python file runs forever."),
    "close": ("Show it once", "and it proves it can do it forever."),
}
TERM_CMD = ("rote learn results/recordings/intake.mp4 --url "
            "http://127.0.0.1:8765/app.html --rows results/fresh_rows.json")

def _wrap(cap: str) -> str:
    return "\n".join(textwrap.wrap(cap, CAPTION_WRAP)) if cap else ""

def _draw(cap: str) -> tuple[str, str]:
    txt = _wrap(cap)
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(txt); f.close()
    filt = (f"drawbox=x=0:y={CONTENT_H}:w={FRAME_W}:h={BAND}:color={BG}:thickness=fill,"
            f"drawtext=fontfile={FONT}:textfile={f.name}:fontsize={CAPTION_FONT_SIZE}:"
            f"fontcolor=white:"
            f"x=(w-text_w)/2:y={CONTENT_H}+({BAND}-text_h)/2:line_spacing=6")
    return filt, f.name

def _ff(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + args, check=True)

def _enc(src: str, out: Path, cap: str, *extra: str) -> None:
    filt, tf = _draw(cap)
    out.parent.mkdir(parents=True, exist_ok=True)
    _ff([*extra, "-i", src, "-vf", f"{SCALE},{PAD},fps=30,{filt},format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
         "-pix_fmt", "yuv420p", str(out)])
    try: Path(tf).unlink()
    except: pass

def _play(html: str, seconds: float) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="film-"))
    (tmp / "page.html").write_text(html, encoding="utf-8")
    raw = tmp / "raw"; raw.mkdir(exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport=VIEWPORT, record_video_dir=str(raw),
                             record_video_size=VIEWPORT)
        pg = ctx.new_page()
        pg.goto((tmp / "page.html").as_uri())
        pg.wait_for_timeout(int(seconds * 1000))
        vid = pg.video.path(); ctx.close(); br.close()
        dest = tmp / "in.webm"; shutil.copy(vid, dest)
    return dest

def render_card(segment, out) -> None:
    head, sub = CARDS.get(segment.source, (segment.source, ""))
    html = (f"<!doctype html><html><body style=\"margin:0;height:{CONTENT_H}px;display:flex;"
            "flex-direction:column;align-items:center;justify-content:center;"
            "background:#0e1116;color:#fff;font-family:-apple-system,BlinkMacSystemFont,"
            "\"Segoe UI\",Roboto,Inter,sans-serif;text-align:center\">"
            f"<div style=\"font-size:72px;font-weight:800;letter-spacing:-1px\">{head}</div>"
            f"<div style=\"font-size:32px;margin-top:18px;opacity:.85\">{sub}</div>"
            "</body></html>")
    webm = _play(html, segment.seconds)
    _enc(str(webm), Path(out), segment.caption)
    shutil.rmtree(webm.parent, ignore_errors=True)

def render_terminal(segment, out) -> None:
    lines = (ROOT / segment.source).read_text(encoding="utf-8").splitlines()
    events = [json.loads(l) for l in lines[1:] if l.strip()]
    total = max((float(e[0]) for e in events), default=0) + 1
    js_ev = json.dumps(events, ensure_ascii=False)
    html = ("<!doctype html><html><body style=\"margin:0;background:#0e1116;color:#d8dee9;"
            f"font-family:ui-monospace,Menlo,monospace;height:{CONTENT_H}px;display:flex;"
            "flex-direction:column\">"
            "<div style=\"height:38px;display:flex;align-items:center;gap:10px;"
            "background:#1a1f2a;padding:0 14px;border-bottom:1px solid #263043\">"
            "<span style=\"width:12px;height:12px;border-radius:50%;background:#ff5f56;display:inline-block\"></span>"
            "<span style=\"width:12px;height:12px;border-radius:50%;background:#ffbd2e;display:inline-block\"></span>"
            "<span style=\"width:12px;height:12px;border-radius:50%;background:#27c93f;display:inline-block\"></span>"
            f"<span style=\"margin-left:12px;font-size:15px;opacity:.9\">{TERM_CMD}</span></div>"
            "<pre id=t style=\"margin:0;padding:18px;font-size:14px;line-height:1.42;"
            "white-space:pre;overflow:hidden\"></pre>"
            f"<script>const E={js_ev};const T=document.getElementById('t');"
            "E.forEach(e=>{if(e[1]==='o')setTimeout(()=>{T.textContent+=e[2]},e[0]*1000)});</script>"
            "</body></html>")
    webm = _play(html, total)
    _enc(str(webm), Path(out), segment.caption)
    shutil.rmtree(webm.parent, ignore_errors=True)

def render_clip(segment, out) -> None:
    _enc(str(ROOT / segment.source), Path(out), segment.caption)

def render_image(segment, out) -> None:
    filt, tf = _draw(segment.caption)
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    _ff(["-loop", "1", "-framerate", "30", "-i", str(ROOT / segment.source),
         "-vf", f"{SCALE},{PAD},fps=30,{filt},format=yuv420p", "-t", str(segment.seconds),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
         "-pix_fmt", "yuv420p", str(out)])
    try: Path(tf).unlink()
    except: pass
