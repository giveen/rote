"""rote command line.

    rote learn intake.mp4 --url http://127.0.0.1:8765/app.html --rows rows.json

Reads the recording, writes the automation, replays it with your data, and repairs itself
until the replay passes or it runs out of attempts.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .certify import write_certificate
from .client import BudgetExceeded, Ledger
from .plan import Plan, align_rows, row_keys
from .preflight import reachable
from .record import intake_session, record, session_from_json, vendor_session
from .replay import ReplayResult, replay, structural_checks
from .repair import diff as plan_diff, repair
from .synth import write_script
from .trace import write as write_trace
from .understand import understand

DEFAULT_BUDGET = 10.0


# Kept for backwards compatibility: alignment now lives in rote.plan as align_rows.
_align_rows = align_rows


def _read_rows_file(path: Path) -> list[dict[str, str]]:
    """Parse a --rows file. Empty data is refused here: a zero-row run proves nothing,
    and every check on it would pass vacuously."""
    data = json.loads(path.read_text())
    rows = data["rows"] if isinstance(data, dict) else data
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path} holds no data rows (0 rows): there is nothing to prove against")
    return [dict(r) for r in rows]


def _load_rows(path: Path | None, plan: Plan) -> tuple[list[dict[str, str]], bool]:
    """Fresh data for the proof. Without a file we can only re-use the video's own data,
    which proves the script runs but not that it generalises — so it is flagged."""
    if path:
        return align_rows(_read_rows_file(path), plan), True
    return plan.rows, False


def cmd_learn(args: argparse.Namespace) -> int:
    video = Path(args.video).resolve()
    if not video.exists():
        print(f"no such recording: {video}")
        return 2
    # Empty data is refused before a single model call: a zero-row replay would pass
    # vacuously, so there is no verdict worth lending money to.
    if args.rows:
        try:
            _read_rows_file(Path(args.rows))
        except (OSError, ValueError) as e:
            print(f"refusing to learn: {e}")
            return 2
    # A dead app is not a plan problem; a preflight stops the run before any repair call
    # can be spent inventing explanations for a navigation failure.
    ok, why = reachable(args.url)
    if not ok:
        if why.startswith("browsers not installed:"):
            print(f"refusing to learn: no Chromium browser is installed ({why[:300]})")
            print("  no model calls spent — run ./.venv/bin/playwright install chromium "
                  "and retry")
        else:
            print(f"refusing to learn: {args.url} did not answer ({why[:300]})")
            print("  no model calls spent — check the app is running and the URL is right")
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(budget=args.budget, path=out / "ledger.jsonl",
                    trace_dir=out / "prompts")
    t0 = time.time()
    plan: Plan | None = None
    result: ReplayResult | None = None
    attempts: list[dict] = []
    script = out / f"{video.stem}.py"
    fresh_rows: list[dict[str, str]] = []
    is_fresh = False
    try:
        print(f"reading {video.name} ({video.stat().st_size / 1e3:.0f} KB)…")
        plan = understand(video, ledger=ledger, effort=args.effort, hint=args.hint)
        print(f"  {plan.goal}")
        print(f"  {len(plan.fields)} controls, {len(plan.rows)} example row(s), "
              f"{len(plan.steps)} steps · ${ledger.spent:.5f}")

        fresh_rows, is_fresh = _load_rows(Path(args.rows) if args.rows else None, plan)
        if not is_fresh:
            print("  ! no --rows given: replaying the recording's own data. "
                  "This proves it runs, not that it generalises.")

        history: list[str] = []
        for attempt in range(args.repairs + 1):
            write_script(plan, script, recording=video.name)
            result = replay(script, args.url, fresh_rows,
                            screenshot=out / f"proof_attempt{attempt + 1}.png",
                            headless=not args.headed,
                            expected_effect=plan.expected_effect)
            # A block that does not commit cannot iterate, whatever the app reports afterwards.
            result.checks.extend(structural_checks(plan.steps, plan.repeat, len(fresh_rows)))
            result.passed = all(c.ok for c in result.checks)
            attempts.append({
                "attempt": attempt,
                "passed": result.passed,
                "checks": [{"name": c.name, "ok": c.ok, "detail": c.detail}
                           for c in result.checks],
                "error": result.error,
                "cost": ledger.spent,
            })
            if result.passed:
                print(f"  attempt {attempt + 1}: replay passed with fresh data")
                break
            if attempt == args.repairs:
                print(f"  attempt {attempt + 1}: still failing — see the report")
                break
            print(f"  attempt {attempt + 1}: failed ({result.error or 'checks failed'}) "
                  f"→ repairing the plan")
            history.append(f"attempt {attempt + 1}: {result.error or 'checks failed'}")
            try:
                fixed = repair(plan, result.as_evidence(), ledger=ledger, attempt=attempt + 1,
                               effort=args.effort, history=history)
            except BudgetExceeded as e:
                print(f"  stopped: {e}")
                break
            changes = plan_diff(plan, fixed)
            for c in changes[:6]:
                print(f"    {c}")
            plan = fixed

        _write_report(out, video, plan, script, result, attempts, ledger, time.time() - t0,
                      fresh=is_fresh)
        s = ledger.summary()
        print(f"\n{s['calls']} model calls · ${s['spent_usd']:.5f} spent · "
              f"{s['cache_hit_pct']:.0f}% cached · {time.time() - t0:.0f}s")
        print(f"{'PASSED' if result and result.passed else 'NOT PASSED'} · "
              f"automation: {script}")
        print(f"report: {out / 'report.md'}")
        return 0 if result and result.passed else 1
    except BudgetExceeded as e:
        # A spent budget is a refusal, not a crash: say so, write what exists, exit non-zero.
        print(f"  stopped: {e}")
        if plan is not None:
            _write_report(out, video, plan, script, result, attempts, ledger,
                          time.time() - t0, fresh=is_fresh)
        return 1


def cmd_trace(args: argparse.Namespace) -> int:
    md, csv_path = write_trace(Path(args.ledger), Path(args.prompts), Path(args.out),
                               title=args.title)
    rows = sum(1 for line in Path(args.ledger).read_text().splitlines() if line.strip()) \
        if Path(args.ledger).exists() else 0
    print(f"{rows} calls traced")
    print(f"  {md}")
    print(f"  {csv_path}")
    return 0


def cmd_certify(args: argparse.Namespace) -> int:
    run_dir = Path(args.run)
    out = Path(args.out) if args.out else run_dir / "certificate.html"
    written = write_certificate(run_dir, out)
    print(written)
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    if not args.session and not (args.url and args.rows):
        print("record needs --session, or --url with --rows")
        return 2
    if args.session:
        session = session_from_json(Path(args.session))
    else:
        data = json.loads(Path(args.rows).read_text())
        if args.task == "vendors":
            session = vendor_session(args.url, data if isinstance(data, dict) else data[0],
                                     name=args.name)
        else:
            rows = data["rows"] if isinstance(data, dict) else data
            session = intake_session(args.url, rows, name=args.name)
    print(f"recording {len(session.steps)} steps, about {session.seconds:.0f}s…")
    mp4 = record(session, Path(args.out), headless=not args.headed)
    print(f"wrote {mp4} ({mp4.stat().st_size / 1e3:.0f} KB)")
    print(f"truth: {mp4.with_suffix('.truth.json')}")
    return 0


def _write_report(out: Path, video: Path, plan: Plan, script: Path,
                  result: ReplayResult | None, attempts: list[dict], ledger: Ledger,
                  elapsed: float, *, fresh: bool) -> None:
    s = ledger.summary()
    lines = [
        f"# rote report — {video.name}", "",
        f"- **{len(attempts)} attempt(s)**, last replay "
        f"{'**passed**' if result and result.passed else '**did not pass**'}",
        f"- **${s['spent_usd']:.5f}** over {s['calls']} model calls "
        f"({s['input_tokens']:,} in / {s['output_tokens']:,} out, "
        f"{s['cache_hit_pct']:.0f}% cached)",
        f"- wall time {elapsed:.0f}s",
        f"- proof data: {'fresh — never in the recording' if fresh else 'the recording’s own data'}",
    ]
    if plan.repeat_rejected:
        # A model error worth surfacing, not one silently repaired into a different loop.
        lines.append(f"- **note:** {plan.repeat_rejected}")
    lines += ["", "## What it understood", "",
        f"**Goal.** {plan.goal}", "",
        f"**Success looks like.** {plan.expected_effect}", "",
        "| step | action | target | value | scope |", "|---|---|---|---|---|",
    ]
    for i, st in enumerate(plan.steps, 1):
        lines.append(f"| {i} | {st.action} | {st.target} | `{st.value or ''}` | {st.scope} |")
    lines += ["", "**Controls found:**",
              ", ".join(f"`{f.get('label')}` ({f.get('control')})" for f in plan.fields), ""]
    if plan.rows:
        lines += ["**Example rows from the recording:**", "",
                  "```json", json.dumps(plan.rows, ensure_ascii=False, indent=1), "```", ""]
    if result:
        lines += ["## Proof", "", "| check | result | detail |", "|---|---|---|"]
        for c in result.checks:
            lines.append(f"| {c.name} | {'✅' if c.ok else '❌'} | {c.detail} |")
        if result.screenshot:
            lines.append("")
            lines.append(f"After the replay: `{result.screenshot.name}`")
        lines.append("")
    lines += ["## Attempts", ""]
    for a in attempts:
        lines.append(f"### Attempt {a['attempt'] + 1} — "
                     f"{'passed' if a['passed'] else 'failed'}")
        if a["error"]:
            lines.append(f"```\n{a['error'][:600]}\n```")
        for c in a["checks"]:
            if not c["ok"]:
                lines.append(f"- ❌ {c['name']}: {c['detail'][:300]}")
        lines.append("")
    lines += ["## Cost", "",
              "| what | calls | tokens in | cached | tokens out | $ |", "|---|---|---|---|---|---|"]
    by_unit: dict[str, list] = {}
    for c in ledger.calls:
        by_unit.setdefault(c.unit, []).append(c)
    for unit, calls in by_unit.items():
        lines.append(f"| {unit} | {len(calls)} | {sum(x.input_tokens for x in calls):,} | "
                     f"{sum(x.cached_tokens for x in calls):,} | "
                     f"{sum(x.output_tokens for x in calls):,} | "
                     f"{sum(x.cost for x in calls):.5f} |")
    lines += ["", f"Raw per-call trace: `{out / 'ledger.jsonl'}`", ""]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    (out / "report.json").write_text(json.dumps({
        "video": str(video), "plan": plan.to_dict(),
        "script": str(script), "attempts": attempts,
        "passed": bool(result and result.passed),
        "ledger": s, "elapsed_s": round(elapsed, 1), "fresh_data": fresh,
    }, indent=2))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rote",
                                description="Show it once, it does it forever.")
    sub = p.add_subparsers(dest="cmd", required=True)

    learn = sub.add_parser("learn", help="learn a task from a screen recording")
    learn.add_argument("video", help="the recording (mp4)")
    learn.add_argument("--url", required=True, help="the app the task runs in")
    learn.add_argument("--rows", help="JSON file with your data for the proof")
    learn.add_argument("--out", default="results/learn")
    learn.add_argument("--repairs", type=int, default=3)
    learn.add_argument("--effort", default="max")
    learn.add_argument("--hint", default=None, help="one line of context, optional")
    learn.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    learn.add_argument("--headed", action="store_true")
    learn.set_defaults(func=cmd_learn)

    rec = sub.add_parser("record", help="record a session against an app")
    rec.add_argument("--url", help="the app to record against (not needed with --session)")
    rec.add_argument("--rows", help="JSON with the data to enter (intake task)")
    rec.add_argument("--session", help="JSON session file for any other task")
    rec.add_argument("--task", default="intake", choices=["intake", "vendors"])
    rec.add_argument("--name", default="intake")
    rec.add_argument("--out", default="results/recordings")
    rec.add_argument("--headed", action="store_true")
    rec.set_defaults(func=cmd_record)

    tr = sub.add_parser("trace", help="build the prompt and token trace from a ledger")
    tr.add_argument("--ledger", default="results/learn/ledger.jsonl")
    tr.add_argument("--prompts", default="results/learn/prompts")
    tr.add_argument("--out", default="results/learn")
    tr.add_argument("--title", default="Prompt and token trace")
    tr.set_defaults(func=cmd_trace)

    cert = sub.add_parser("certify", help="write a standalone HTML certificate for a finished run")
    cert.add_argument("--run", default="results/learn")
    cert.add_argument("--out", default=None)
    cert.set_defaults(func=cmd_certify)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
