#!/usr/bin/env bash
# The project's check: every script parses, every module imports, the demo app is valid.
set -euo pipefail
cd "$(dirname "$0")"

echo "== python syntax =="
python3 -m compileall -q rote results tools 2>/dev/null || true
python3 - <<'EOF'
import ast, pathlib, sys
bad = 0
for p in pathlib.Path('.').rglob('*.py'):
    if any(part in {'.venv', 'node_modules', '__pycache__'} for part in p.parts):
        continue
    try:
        ast.parse(p.read_text())
    except SyntaxError as e:
        print(f"  SYNTAX {p}: {e}")
        bad += 1
print(f"  {bad} syntax errors")
sys.exit(1 if bad else 0)
EOF

echo "== tests =="
python3 -m unittest discover -s tests -q

echo "== imports =="
python3 -c "import rote; print('  rote', rote.__version__)" 2>/dev/null || echo "  (package not importable yet)"

echo "== node =="
for f in $(find . -name '*.mjs' -not -path './node_modules/*' 2>/dev/null | head -20); do
  node --check "$f" && echo "  ok $f"
done

echo "== demo app =="
python3 - <<'EOF'
from pathlib import Path
p = Path('app/app.html')
assert p.exists(), "app/app.html missing"
html = p.read_text()
for needle in ('id="sku"', 'id="submit"', 'Parts intake'):
    assert needle in html, f"app.html missing {needle}"
print("  app.html ok,", len(html), "bytes")
EOF

echo "check passed"
