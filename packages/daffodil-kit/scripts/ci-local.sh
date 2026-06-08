#!/usr/bin/env bash
# Run full CopyCat Kit CI locally (mirrors GitHub Actions)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Version sync check ==="
V=$(tr -d '[:space:]' < VERSION)
P=$(grep -E '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
I=$(grep -E '^__version__ = ' daffodil_kit/__init__.py | sed 's/__version__ = "\(.*\)"/\1/')
test "$V" = "$P" && test "$V" = "$I"
echo "OK: $V"

echo "=== Lint (ruff) ==="
if command -v ruff >/dev/null 2>&1; then
  ruff check daffodil_kit tests
else
  pip install ruff -q
  ruff check daffodil_kit tests
fi

echo "=== Tests + coverage ==="
pip install -e ".[dev]" pytest-cov ruff -q
pytest tests/ -v --tb=short --cov=daffodil_kit --cov-report=term-missing

echo "=== Install smoke (local) ==="
DAFFODIL_KIT_USE_LOCAL=1 bash install.sh

echo "=== Verify install ==="
bash scripts/verify-install.sh

echo "=== CI local: ALL PASSED ==="
