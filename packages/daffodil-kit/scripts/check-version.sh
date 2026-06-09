#!/usr/bin/env bash
# Verify VERSION matches pyproject.toml, __init__.py, and native/Cargo.toml
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

V=$(tr -d '[:space:]' < "$ROOT/VERSION")
P=$(grep -E '^version = ' "$ROOT/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
I=$(grep -E '^__version__ = ' "$ROOT/daffodil_kit/__init__.py" | sed 's/__version__ = "\(.*\)"/\1/')
C=$(grep -E '^version = ' "$ROOT/native/Cargo.toml" | head -1 | sed 's/version = "\(.*\)"/\1/')

echo "VERSION=$V pyproject=$P __init__=$I cargo=$C"
test -n "$V"
test "$V" = "$P"
test "$V" = "$I"
test "$V" = "$C"
echo "Version sync OK: $V"
