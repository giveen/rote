"""Turn the ledger into the prompt and token trace the submission requires.

Two artefacts, both derived only from what actually happened:
  trace.md   a table of every call with tokens and cost, and the prompts themselves
  trace.csv  the same numbers for a spreadsheet

Nothing here is estimated. If a call is in the trace, it is in the ledger, and the prompt
file it points at is the exact request body that was sent.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

PRICE_NOTE = ("muse-ember-1.0, Standard mode: $0.10 per 1M input tokens, "
              "$0.004 per 1M cached input tokens, $0.50 per 1M output tokens "
              "(long-context rates above 200K input tokens per request).")


@dataclass
class Row:
    n: int
    unit: str
    purpose: str
    effort: str
    input_tokens: int
    cached_tokens: int
    output_tokens: int
    reasoning_tokens: int
    cost: float
    seconds: float
    prompt_ref: str
    note: str


def load(path: Path) -> list[Row]:
    rows: list[Row] = []
    if not path.exists():
        return rows
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        d = json.loads(line)
        rows.append(Row(
            n=i, unit=d.get("unit", ""), purpose=d.get("purpose", ""),
            effort=d.get("effort", ""), input_tokens=d.get("input_tokens", 0),
            cached_tokens=d.get("cached_tokens", 0),
            output_tokens=d.get("output_tokens", 0),
            reasoning_tokens=d.get("reasoning_tokens", 0),
            cost=d.get("cost", 0.0), seconds=d.get("seconds", 0.0),
            prompt_ref=d.get("prompt_ref", ""), note=d.get("note", "")))
    return rows


def _excerpt(path: Path, limit: int = 1400) -> str:
    """The part of a request a person would want to see, with the media left out."""
    try:
        body = json.loads(path.read_text())
    except Exception:
        return "(prompt file unreadable)"
    parts = []
    if body.get("instructions"):
        parts.append("**instructions**\n```\n" + str(body["instructions"])[:600] + "\n```")
    inp = body.get("input")
    if isinstance(inp, str):
        parts.append("**input**\n```\n" + inp[:limit] + "\n```")
    elif isinstance(inp, list):
        for msg in inp:
            for c in msg.get("content", []):
                kind = c.get("type")
                if kind == "input_text":
                    parts.append("**text**\n```\n" + str(c.get("text", ""))[:limit] + "\n```")
                elif kind == "input_file":
                    parts.append(f"**file** `{c.get('file_id')}` (the recording)")
                elif kind == "input_image":
                    parts.append("**image** (inline still)")
    if body.get("text", {}).get("format"):
        fmt = body["text"]["format"]
        parts.append(f"**structured output** `{fmt.get('name')}` — schema "
                     f"{len(json.dumps(fmt.get('schema', {})))} bytes")
    return "\n\n".join(parts) or "(no text input)"


def write(ledger_path: Path, prompts_dir: Path, out_dir: Path, *,
          title: str = "Prompt and token trace") -> tuple[Path, Path]:
    rows = load(ledger_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    total = sum(r.cost for r in rows)
    tok_in = sum(r.input_tokens for r in rows)
    tok_cached = sum(r.cached_tokens for r in rows)
    tok_out = sum(r.output_tokens for r in rows)
    tok_reason = sum(r.reasoning_tokens for r in rows)

    md = [
        f"# {title}", "",
        f"Model: **muse-ember-1.0** through the Meta Model API. "
        f"Prices: {PRICE_NOTE}", "",
        "## Totals", "",
        "| | |", "|---|---|",
        f"| Model calls | **{len(rows)}** |",
        f"| Input tokens | **{tok_in:,}** |",
        f"| of which served from cache | {tok_cached:,} "
        f"({100 * tok_cached / tok_in:.0f}%) |" if tok_in else "| cached | 0 |",
        f"| Output tokens | **{tok_out:,}** |",
        f"| of which reasoning | {tok_reason:,} |",
        f"| **Amount spent** | **${total:.6f}** |",
        "", "## Every call", "",
        "| # | stage | what it did | effort | in | cached | out | reasoning | seconds | $ |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(f"| {r.n} | `{r.unit}` | {r.purpose} | {r.effort} | {r.input_tokens:,} | "
                  f"{r.cached_tokens:,} | {r.output_tokens:,} | {r.reasoning_tokens:,} | "
                  f"{r.seconds:.1f} | {r.cost:.6f} |")
    md += ["", f"**Total: ${total:.6f}** "
           f"({'within' if total <= 10 else 'OVER'} the $10 credit).", ""]
    md += ["## The prompts themselves", "",
           "Each call's exact request body is kept beside this file. "
           "Large media are referenced by file id, not inlined.", ""]
    for r in rows:
        md.append(f"### Call {r.n} — `{r.unit}` / {r.purpose}")
        md.append("")
        if r.prompt_ref:
            md.append(f"Request: `{prompts_dir.name}/{r.prompt_ref}`")
            md.append("")
            md.append(_excerpt(prompts_dir / r.prompt_ref))
        else:
            md.append("(no request body was kept for this call)")
        md.append("")
    md += ["## Method", "",
           "The ledger is written by the client on every request, before the response is "
           "parsed, so a failed call still appears here. Costs are computed from the usage "
           "object the API returns, at the prices above, never from an estimate.", ""]

    md_path = out_dir / "trace.md"
    md_path.write_text("\n".join(x for x in md if x is not None) + "\n")

    csv_path = out_dir / "trace.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["call", "stage", "purpose", "effort", "input_tokens", "cached_tokens",
                    "output_tokens", "reasoning_tokens", "seconds", "usd", "prompt_file"])
        for r in rows:
            w.writerow([r.n, r.unit, r.purpose, r.effort, r.input_tokens, r.cached_tokens,
                        r.output_tokens, r.reasoning_tokens, r.seconds,
                        f"{r.cost:.6f}", r.prompt_ref])
        w.writerow(["TOTAL", "", "", "", tok_in, tok_cached, tok_out, tok_reason,
                    sum(r.seconds for r in rows), f"{total:.6f}", ""])
    return md_path, csv_path
