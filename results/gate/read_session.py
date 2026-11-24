"""Feasibility gate: can Muse Ember read a screen recording and say what was done?

Compares the two ways of feeding a session to the model — an mp4 through the Files API,
and a handful of sampled frames — on quality, token cost and latency. The answer decides
whether the project is worth nine days.
"""
from __future__ import annotations

import base64
import json
import subprocess
import time
from pathlib import Path

import httpx

BASE = "https://api.meta.ai/v1"
MODEL = "muse-ember-1.0"
KEY = json.loads(Path.home().joinpath(".config/muse/auth.json").read_text())[
    "providers"]["meta"]["api_key"]
H = {"Authorization": f"Bearer {KEY}"}

ROOT = Path(__file__).resolve().parents[2]   # repo root
FRAMES = ROOT / "results" / "frames"
OUT = ROOT / "results" / "gate"
OUT.mkdir(parents=True, exist_ok=True)

PRICE_IN, PRICE_CACHED, PRICE_OUT = 0.10 / 1e6, 0.004 / 1e6, 0.50 / 1e6

TASK = """These come from one continuous screen recording of a person using an internal \
web app. Frames are in chronological order.

Work out what the person actually did, at the level of intent rather than pixels: which \
field received which value, which control was pressed, and what the goal was.

Rules:
- Use the visible labels for targets ("SKU", "Description", "Supplier", "Add line", \
"Submit intake"). Never invent a label that is not on screen.
- If the same kind of step repeats with different values, emit a `repeat` block with the \
rows instead of listing it twice.
- Only describe actions that the frames support.

Return JSON matching the schema."""

SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {"type": "string"},
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string"},
                    "description": {"type": "string"},
                    "quantity": {"type": "string"},
                    "unit_cost": {"type": "string"},
                    "supplier": {"type": "string"},
                    "location": {"type": "string"},
                },
                "required": ["sku", "description", "quantity", "unit_cost",
                             "supplier", "location"],
                "additionalProperties": False,
            },
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string",
                               "enum": ["type", "select", "click", "submit"]},
                    "target": {"type": "string"},
                    "value": {"type": ["string", "null"]},
                },
                "required": ["action", "target", "value"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["goal", "rows", "steps"],
    "additionalProperties": False,
}

GT_ROWS = [
    {"sku": "BRK-2041", "description": "Brake pad set, front", "quantity": "12",
     "unit_cost": "18.40", "supplier": "Northwind Supply", "location": "Aisle 4 · Bay 2"},
    {"sku": "FLT-1180", "description": "Oil filter, spin-on", "quantity": "40",
     "unit_cost": "6.25", "supplier": "Bergen Parts", "location": "Aisle 7 · Bay 1"},
]


def make_video() -> Path:
    mp4 = OUT / "session.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1",
                    "-pattern_type", "glob", "-i", str(FRAMES / "f*.png"),
                    "-vf", "fps=1,format=yuv420p", "-c:v", "libx264",
                    "-preset", "veryfast", str(mp4)], check=True)
    return mp4


def upload(path: Path) -> dict:
    with path.open("rb") as f:
        r = httpx.post(f"{BASE}/files", headers=H,
                       data={"purpose": "user_data"},
                       files={"file": (path.name, f, "video/mp4")}, timeout=300)
    r.raise_for_status()
    return r.json()


def count_tokens(body: dict) -> int:
    r = httpx.post(f"{BASE}/responses/input_tokens", headers=H, json=body, timeout=300)
    r.raise_for_status()
    return r.json()["input_tokens"]


def ask(body: dict) -> tuple[dict | None, dict, float, str]:
    t0 = time.time()
    r = httpx.post(f"{BASE}/responses", headers=H, json=body, timeout=900)
    dt = time.time() - t0
    if r.status_code != 200:
        return None, {}, dt, f"HTTP {r.status_code}: {r.text[:400]}"
    d = r.json()
    text = "".join(c.get("text", "")
                   for item in d.get("output", []) if item.get("type") == "message"
                   for c in item.get("content", []) if c.get("type") == "output_text")
    try:
        return json.loads(text), d.get("usage") or {}, dt, ""
    except Exception:
        return None, d.get("usage") or {}, dt, f"unparseable: {text[:300]}"


def cost(u: dict) -> float:
    i = u.get("input_tokens") or 0
    c = (u.get("input_tokens_details") or {}).get("cached_tokens") or 0
    o = u.get("output_tokens") or 0
    return (i - c) * PRICE_IN + c * PRICE_CACHED + o * PRICE_OUT


def score(plan: dict | None) -> str:
    if not plan:
        return "no plan"
    got = plan.get("rows") or []
    hits = 0
    for gt in GT_ROWS:
        for g in got:
            if all(str(g.get(k, "")).strip().lower() == str(v).strip().lower()
                   for k, v in gt.items()):
                hits += 1
                break
    targets = {s.get("target", "").lower() for s in plan.get("steps") or []}
    needed = {"sku", "description", "quantity", "unit cost", "supplier", "location",
              "add line", "submit intake"}
    return (f"rows {hits}/2 exact, step targets found {len(needed & targets)}/{len(needed)}"
            f" ({sorted(needed & targets)})")


def main() -> None:
    print("building the recording…")
    mp4 = make_video()
    size_kb = mp4.stat().st_size / 1024
    print(f"  {mp4.name}: {size_kb:.0f} KB, "
          f"{subprocess.run(['ffprobe','-v','quiet','-show_entries','format=duration',
                             '-of','csv=p=0',str(mp4)],capture_output=True,text=True).stdout.strip()}s")

    print("uploading through the Files API…")
    f = upload(mp4)
    fid = f.get("id") or f.get("file", {}).get("id")
    print(f"  file_id {fid}")

    video_body = {
        "model": MODEL,
        "input": [{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": TASK},
            {"type": "input_file", "file_id": fid}]}],
        "reasoning": {"effort": "max"},
        "text": {"format": {"type": "json_schema", "name": "plan",
                            "schema": SCHEMA, "strict": True}},
    }
    n = count_tokens({k: v for k, v in video_body.items() if k != "text"})
    print(f"  video path: {n:,} input tokens -> ${n * PRICE_IN:.5f} per call")

    picked = ["f00", "f02", "f04", "f06", "f08", "f10", "f12", "f14", "f15"]
    content = [{"type": "input_text", "text": TASK}]
    for name in picked:
        b64 = base64.b64encode((FRAMES / f"{name}.png").read_bytes()).decode()
        content.append({"type": "input_image", "image_url": f"data:image/png;base64,{b64}"})
    frames_body = {
        "model": MODEL,
        "input": [{"type": "message", "role": "user", "content": content}],
        "reasoning": {"effort": "max"},
        "text": {"format": {"type": "json_schema", "name": "plan",
                            "schema": SCHEMA, "strict": True}},
    }
    nf = count_tokens({k: v for k, v in frames_body.items() if k != "text"})
    print(f"  frames path: {nf:,} input tokens -> ${nf * PRICE_IN:.5f} per call "
          f"({len(picked)} frames)")

    for label, body in (("VIDEO", video_body), ("FRAMES", frames_body)):
        plan, usage, dt, err = ask(body)
        c = cost(usage)
        print(f"\n== {label} == {dt:.1f}s  ${c:.5f}")
        if err:
            print("  ERROR:", err)
            continue
        print("  goal:", plan.get("goal"))
        print("  rows:", json.dumps(plan.get("rows"), ensure_ascii=False))
        print("  steps:", len(plan.get("steps") or []))
        for s in (plan.get("steps") or [])[:8]:
            print(f"    - {s['action']:<6} {s['target']:<16} {s['value'] or ''}")
        print("  score:", score(plan))
        (OUT / f"{label.lower()}_plan.json").write_text(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
