#!/usr/bin/env bash
# Post-install verification — run after install.sh or on CI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

copycat_banner() {
  echo "== $1 =="
}

copycat_step() {
  echo "-- $1"
}

copycat_ok() {
  echo "✓ $1"
}

copycat_warn() {
  echo "⚠ $1"
}

copycat_fail() {
  echo "✗ $1" >&2
}

copycat_info() {
  echo "· $1"
}

copycat_summary() {
  copycat_banner "$1"
}

copycat_banner "verify"
COPYCAT_STEP_TOTAL=5

fail=0

copycat_step "Python package import"
if python3 -c "import daffodil_kit; print(daffodil_kit.__version__)" 2>/dev/null; then
  copycat_ok "daffodil_kit importable"
else
  copycat_fail "Cannot import daffodil_kit"
  fail=1
fi

copycat_step "CLI entrypoint"
if command -v daffodil-kit >/dev/null 2>&1; then
  daffodil-kit version
  copycat_ok "daffodil-kit CLI on PATH"
else
  copycat_warn "daffodil-kit not on PATH — activate venv first"
fi

copycat_step "Security modules"
python3 -m pytest "${SCRIPT_DIR}/tests/test_security.py" "${SCRIPT_DIR}/tests/test_copycat_guard.py" -q \
  && copycat_ok "Security tests passed" || { copycat_fail "Security tests failed"; fail=1; }

copycat_step "Config directory permissions"
cfg="$HOME/.daffodil-kit"
if [[ -d "$cfg" ]]; then
  perm=$(stat -c '%a' "$cfg" 2>/dev/null || stat -f '%OLp' "$cfg" 2>/dev/null || echo "?")
  copycat_info "~/.daffodil-kit mode: $perm"
  copycat_ok "Config directory exists"
else
  copycat_warn "Config directory not created yet (normal before first pair)"
fi

copycat_step "Audit log writable"
python3 - <<'PY'
from daffodil_kit.audit import log_event, read_audit_tail
e = log_event("install.verify", detail={"ok": True})
assert e["event"] == "install.verify"
assert isinstance(read_audit_tail(1), list)
print("audit-ok")
PY
copycat_ok "Audit log read/write OK"

[[ "$fail" -eq 0 ]] && copycat_summary "verified" || exit 1
