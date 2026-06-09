#!/usr/bin/env bash
# Run full CopyCat Kit CI locally (mirrors GitHub Actions)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="${ROOT}/.venv-ci"
if [[ ! -x "${VENV}/bin/python" ]]; then
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "${VENV}/bin/activate"
pip install -q -U pip wheel setuptools
pip install -q -e ".[dev]" pytest-cov ruff

echo "=== Version sync check ==="
bash scripts/check-version.sh

echo "=== Lint (ruff) ==="
ruff check daffodil_kit tests --select E,F,I,W --ignore E501
ruff format --check tests

echo "=== Tests + coverage ==="
pytest tests/ -v --tb=short --cov=daffodil_kit --cov-report=term-missing

echo "=== Install smoke (local) ==="
DAFFODIL_KIT_USE_LOCAL=1 bash install.sh

echo "=== Verify install ==="
bash scripts/verify-install.sh

echo "=== CI local: ALL PASSED ==="
