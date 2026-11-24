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

from .client import BudgetExceeded, Ledger
from .plan import Plan
from .record import intake_session, record, session_from_json, vendor_session
from .replay import ReplayResult, replay
from .repair import diff as plan_diff, repair
from .synth import write_script
from .trace import write as write_trace
from .understand import understand

DEFAULT_BUDGET = 10.0


def _load_rows(path: Path | None, plan: Plan) -> tuple[list[dict[str, str]], bool]:
    """Fresh data for the proof. Without a file we can only re-use the video's own data,
    which proves the script runs but not that it generalises — so it is flagged."""
    if path:
        data = json.loads(path.read_text())
        rows = data["rows"] if isinstance(data, dict) else data
        return [dict(r) for r in rows], True
    return plan.rows, False


def cmd_learn(args: argparse.Namespace) -> int:
    video = Path(args.video).resolve()
    if not video.exists():
        print(f"no such recording: {video}")
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(budget=args.budget, path=out / "ledger.jsonl",
                    trace_dir=out / "prompts")
    t0 = time.time()

    print(f"reading {video.name} ({video.stat().st_size / 1e3:.0f} KB)…")
    plan = understand(video, ledger=ledger, effort=args.effort, hint=args.hint)
    print(f"  {plan.goal}")
    print(f"  {len(plan.fields)} controls, {len(plan.rows)} example row(s), "
          f"{len(plan.steps)} steps · ${ledger.spent:.5f}")

    fresh_rows, is_fresh = _load_rows(Path(args.rows) if args.rows else None, plan)
    if not is_fresh:
        print("  ! no --rows given: replaying the recording's own data. "
              "This proves it runs, not that it generalises.")

    attempts: list[dict] = []
    result: ReplayResult | None = None
    script = out / f"{video.stem}.py"
    for attempt in range(args.repairs + 1):
        write_script(plan, script, recording=video.name)
        result = replay(script, args.url, fresh_rows,
                        screenshot=out / f"proof_attempt{attempt + 1}.png",
                        headless=not args.headed)
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
        try:
            fixed = repair(plan, result.as_evidence(), ledger=ledger, attempt=attempt + 1,
                           effort=args.effort)
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


def cmd_trace(args: argparse.Namespace) -> int:
    md, csv_path = write_trace(Path(args.ledger), Path(args.prompts), Path(args.out),
                               title=args.title)
    rows = sum(1 for line in Path(args.ledger).read_text().splitlines() if line.strip()) \
        if Path(args.ledger).exists() else 0
    print(f"{rows} calls traced")
    print(f"  {md}")
    print(f"  {csv_path}")
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
        "", "## What it understood", "",
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
    learn.add_argument("--repairs", type=int, default=2)
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

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
