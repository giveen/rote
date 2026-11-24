"""Standalone HTML certificate for a finished run.

One file, no network, so a judge can open it from disk and see exactly what
rote learned and how the replay proved it — without needing the repo or a server.
"""
from __future__ import annotations

import base64
import html
import json
import re
from pathlib import Path

from .client import MODEL

_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0d1117;
  color: #e6edf3;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.55;
  padding: 28px 18px;
}
.wrap { max-width: 900px; margin: 0 auto; }
header { margin-bottom: 16px; }
h1 { margin: 0 0 6px; font-size: 1.6rem; line-height: 1.3; }
.goal { margin: 0 0 14px; color: #c9d1d9; max-width: 72ch; }
.badge {
  display: inline-block;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 6px 16px;
  border-radius: 999px;
  border: 1px solid transparent;
}
.badge-passed { background: #0a3324; color: #3fb950; border-color: #1f6f3f; }
.badge-not-passed { background: #3d0a0a; color: #f85149; border-color: #7a2b2b; }
.cost { color: #a5d6ff; margin: 0 0 24px; }
section { margin: 0 0 26px; }
h2 { font-size: 1.15rem; margin: 0 0 10px; }
.table-wrap { overflow-x: auto; border: 1px solid #30363d; border-radius: 8px; background: #161b22; }
table { border-collapse: collapse; width: 100%; font-size: 0.95rem; }
th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #21262d; vertical-align: top; }
thead th { background: #1c2333; }
tbody tr:last-child td { border-bottom: none; }
figure { margin: 14px 0 0; }
img { max-width: 100%; height: auto; display: block; border: 1px solid #30363d; border-radius: 8px; }
pre {
  white-space: pre-wrap;
  word-break: break-word;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  font-size: 0.85rem;
}
footer { border-top: 1px solid #30363d; padding-top: 14px; color: #8b949e; font-size: 0.85rem; }
@media (max-width: 600px) {
  body { padding: 16px 12px; }
  h1 { font-size: 1.35rem; }
}
@media print {
  body { background: #fff; color: #000; }
  .table-wrap, pre, img { border-color: #ccc; }
  .badge { border: 1px solid #000; }
}
""".strip()


def _e(value: object) -> str:
    """Escape report text so it can never become markup."""
    if value is None:
        return ""
    return html.escape(str(value))


def _latest_proof(run_dir: Path) -> Path | None:
    """The newest replay screenshot — highest attempt number, name tie-break for determinism."""
    proofs = list(run_dir.glob("proof_attempt*.png"))
    if not proofs:
        return None

    def attempt_no(p: Path) -> int:
        m = re.search(r"proof_attempt(\d+)\.png", p.name)
        return int(m.group(1)) if m else -1

    return sorted(proofs, key=lambda p: (attempt_no(p), p.name))[-1]


def _script_source(report: dict, run_dir: Path) -> str | None:
    """Generated automation source, wherever the report points — or nothing if it is gone."""
    script = report.get("script")
    if not script:
        return None
    p = Path(str(script))
    candidates = [p] if p.is_absolute() else [p, run_dir / p, run_dir / p.name]
    for cand in candidates:
        try:
            if cand.exists() and cand.is_file():
                return cand.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return None


def write_certificate(run_dir: Path, out: Path) -> Path:
    """Write a standalone HTML certificate for a finished run and return its path."""
    run_dir = Path(run_dir)
    out = Path(out)
    report_path = run_dir / "report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"report.json not found in {run_dir}")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    plan = report.get("plan") or {}
    app = str(plan.get("app") or "")
    goal = str(plan.get("goal") or "")
    steps: list = plan.get("steps") or []
    ledger = report.get("ledger") or {}
    try:
        spent = float(ledger.get("spent_usd") or 0.0)
    except (TypeError, ValueError):
        spent = 0.0
    try:
        calls = int(ledger.get("calls") or 0)
    except (TypeError, ValueError):
        calls = 0
    try:
        cache_hit_pct = float(ledger.get("cache_hit_pct") or 0.0)
    except (TypeError, ValueError):
        cache_hit_pct = 0.0
    passed = bool(report.get("passed"))
    fresh_data = bool(report.get("fresh_data"))
    attempts = report.get("attempts") or []
    last_checks: list = []
    if attempts:
        last = attempts[-1]
        if isinstance(last, dict):
            last_checks = last.get("checks") or []

    verdict = "PASSED" if passed else "NOT PASSED"
    badge_cls = "badge-passed" if passed else "badge-not-passed"

    # Tables — one row per step/check, values escaped, empty when the report has none.
    step_rows = "\n".join(
        "<tr>"
        f"<td>{_e(s.get('action'))}</td>"
        f"<td>{_e(s.get('target'))}</td>"
        f"<td>{_e(s.get('value'))}</td>"
        f"<td>{_e(s.get('scope'))}</td>"
        "</tr>"
        for s in steps if isinstance(s, dict)
    )
    check_rows = "\n".join(
        "<tr>"
        f"<td>{_e(c.get('name'))}</td>"
        f"<td>{_e('\u2705' if c.get('ok') else '\u274c')}</td>"
        f"<td>{_e(c.get('detail'))}</td>"
        "</tr>"
        for c in last_checks if isinstance(c, dict)
    )

    # Proof image — embedded so the file works offline from disk.
    proof_html = ""
    proof = _latest_proof(run_dir)
    if proof is not None:
        try:
            data = base64.b64encode(proof.read_bytes()).decode("ascii")
            alt = html.escape("Proof screenshot")
            proof_html = f'\n<figure><img alt="{alt}" src="data:image/png;base64,{data}"></figure>'
        except OSError:
            proof_html = ""

    # Generated source — shown only when the file still exists.
    script_html = ""
    source = _script_source(report, run_dir)
    if source is not None:
        script_html = (
            "\n<section>\n<h2>Generated automation</h2>\n"
            f"<pre>{html.escape(source)}</pre>\n</section>"
        )

    if fresh_data:
        how = (
            f"The recording is read by {_e(MODEL)}, the automation is compiled from "
            "the plan, and the replay ran against data the recording never "
            "contained \u2014 so a pass proves the automation generalises beyond the video."
        )
    else:
        how = (
            f"The recording is read by {_e(MODEL)}, the automation is compiled from "
            "the plan, and the replay ran against the recording\u2019s own data "
            "\u2014 so a pass proves it runs, not that it generalises."
        )

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(app)} \u2014 certificate</title>
<style>
{_CSS}
</style>
</head>
<body>
<main class="wrap">
<header>
<h1>{_e(app)}</h1>
<p class="goal">{_e(goal)}</p>
<span class="badge {badge_cls}">{_e(verdict)}</span>
</header>
<p class="cost">Spent ${_e(f'{spent:.5f}')} \u00b7 {_e(calls)} model calls \u00b7 {_e(f'{cache_hit_pct:.1f}')}% cache hit</p>
<section>
<h2>What it learned</h2>
<div class="table-wrap">
<table>
<thead><tr><th>action</th><th>target</th><th>value</th><th>scope</th></tr></thead>
<tbody>
{step_rows}
</tbody>
</table>
</div>
</section>
<section>
<h2>Proof</h2>
<div class="table-wrap">
<table>
<thead><tr><th>name</th><th>result</th><th>detail</th></tr></thead>
<tbody>
{check_rows}
</tbody>
</table>
</div>{proof_html}
</section>{script_html}
<section>
<h2>How it was produced</h2>
<p>{how}</p>
</section>
<footer>rote \u00b7 {_e(MODEL)}</footer>
</main>
</body>
</html>
"""

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    return out
