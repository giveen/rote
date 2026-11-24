#!/usr/bin/env bash
# One command to run the whole story, slowly enough to read on camera.
#
#   tools/demo.sh            # all three tasks
#   tools/demo.sh intake     # just one
#
# Prints what matters and nothing else: what it understood, whether the replay passed, and
# what it cost. Everything it produces lands in results/demo/<task>/.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

PY=./.venv/bin/python
[ -x "$PY" ] || PY=python3

serve() {
  if ! curl -sf -o /dev/null http://127.0.0.1:8765/app.html; then
    echo "starting the fixtures on :8765"
    python3 -m http.server 8765 --directory app >/tmp/rote-demo-server.log 2>&1 &
    sleep 1
  fi
}

run() {
  local task=$1 url=$2 rows=$3
  echo
  echo "══════════════════════════════════════════════════════════════════"
  echo "  $task  —  reading $(basename "$(dirname "$rows")")/$(basename "$rows" .json)"
  echo "══════════════════════════════════════════════════════════════════"
  PYTHONPATH=. "$PY" -m rote learn "results/recordings/$task.mp4" \
      --url "$url" --rows "$rows" --out "results/demo/$task"
  local report="results/demo/$task/report.json"
  [ -f "$report" ] || return 0
  echo
  echo "── what it understood ────────────────────────────────────────────"
  "$PY" - "$report" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
p = r["plan"]
print(f'  goal      {p["goal"]}')
print(f'  effect    {p["expected_effect"][:110]}')
rep = p.get("repeat")
if rep:
    print(f'  repeats   steps {rep["first"]}–{rep["last"]}')
for i, s in enumerate(p["steps"], 1):
    inside = rep and rep["first"] <= i <= rep["last"]
    mark = "↻" if inside else " "
    print(f'   {mark} {i:>2} {s["action"]:<7} {s["target"]:<20} {s["value"] or ""}')
print()
print("── verdict ───────────────────────────────────────────────────────")
for c in r["attempts"][-1]["checks"]:
    print(f'  {"PASS" if c["ok"] else "FAIL"}  {c["name"]}: {c["detail"][:80]}')
l = r["ledger"]
print(f'  {l["calls"]} model calls · ${l["spent_usd"]:.5f} · {l["cache_hit_pct"]:.0f}% cached')
PY
  if PYTHONPATH=. "$PY" -m rote certify --run "results/demo/$task" >/dev/null 2>&1; then
    echo "  certificate → results/demo/$task/certificate.html"
  else
    echo "  certificate: built on the feature/certificate branch, not merged into main yet"
  fi
}

serve
case "${1:-all}" in
  intake)  run intake  http://127.0.0.1:8765/app.html     results/fresh_rows.json ;;
  vendors) run vendors http://127.0.0.1:8765/vendors.html results/vendor_fresh.json ;;
  sauce)   run sauce   https://www.saucedemo.com/         results/sauce_fresh.json ;;
  all)
    run intake  http://127.0.0.1:8765/app.html     results/fresh_rows.json
    run vendors http://127.0.0.1:8765/vendors.html results/vendor_fresh.json
    run sauce   https://www.saucedemo.com/         results/sauce_fresh.json
    ;;
  *) echo "usage: $0 [all|intake|vendors|sauce]" >&2; exit 2 ;;
esac

echo
echo "══════════════════════════════════════════════════════════════════"
echo "  trace → results/demo (run: python -m rote trace --help)"
echo "══════════════════════════════════════════════════════════════════"
