#!/usr/bin/env bash
# CopyCat Kit (daffodil-kit) — cross-platform installer
# Linux · macOS · Windows (Git Bash / WSL)
#
# One-line install:
#   curl -fsSL https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/packages/daffodil-kit/install.sh | bash
#
# Pin release:
#   DAFFODIL_KIT_VERSION=copycat-v0.1.0 curl -fsSL .../install.sh | bash
#
# Environment:
#   DAFFODIL_KIT_REPO          GitHub repo (default: the-shoaib2/daffodil-intelligence)
#   DAFFODIL_KIT_VERSION       Branch or tag (default: main)
#   DAFFODIL_KIT_NATIVE        1 = build Rust capture backend
#   DAFFODIL_KIT_INSTALL_SERVICE  1 = systemd / launchd / Windows Task
#   DAFFODIL_KIT_API_URL       Pre-fill API URL in ~/.daffodil-kit/config.json
#   DAFFODIL_KIT_USE_LOCAL     1 = pip install from current repo checkout (CI/dev)
#   DAFFODIL_KIT_PREFIX        Install prefix (default: ~/.local)
set -euo pipefail

DAFFODIL_KIT_REPO="${DAFFODIL_KIT_REPO:-the-shoaib2/daffodil-intelligence}"
DAFFODIL_KIT_VERSION="${DAFFODIL_KIT_VERSION:-main}"
DAFFODIL_KIT_NATIVE="${DAFFODIL_KIT_NATIVE:-0}"
DAFFODIL_KIT_INSTALL_SERVICE="${DAFFODIL_KIT_INSTALL_SERVICE:-0}"
DAFFODIL_KIT_USE_LOCAL="${DAFFODIL_KIT_USE_LOCAL:-0}"
INSTALL_PREFIX="${DAFFODIL_KIT_PREFIX:-$HOME/.local}"
RAW_BASE="https://raw.githubusercontent.com/${DAFFODIL_KIT_REPO}/${DAFFODIL_KIT_VERSION}"
GIT_BASE="https://github.com/${DAFFODIL_KIT_REPO}.git"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/install-log.sh
source "${SCRIPT_DIR}/scripts/lib/install-log.sh" 2>/dev/null || {
  # curl | bash — fetch logging lib from GitHub
  LOG_LIB=$(mktemp)
  curl -fsSL "${RAW_BASE}/packages/daffodil-kit/scripts/lib/install-log.sh" -o "$LOG_LIB"
  # shellcheck source=/dev/null
  source "$LOG_LIB"
}

detect_os() {
  case "$(uname -s)" in
    Linux)   echo "linux" ;;
    Darwin)  echo "macos" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *)       echo "unknown" ;;
  esac
}

find_python() {
  for cmd in python3.12 python3.11 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      ver=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
      major=${ver%%.*}
      minor=${ver##*.}
      if [[ "$major" -eq 3 && "$minor" -ge 11 ]]; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

install_os_packages() {
  local os="$1"
  if [[ "$os" == "linux" ]]; then
    if command -v apt-get >/dev/null 2>&1; then
      local pkgs=(python3 python3-pip python3-venv python3-tk scrot xdotool)
      [[ "$DAFFODIL_KIT_NATIVE" == "1" ]] && pkgs+=(build-essential pkg-config libdbus-1-dev libxcb1-dev libxrandr-dev)
      if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        copycat_info "apt: ${pkgs[*]}"
        if sudo -n apt-get update -qq && sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkgs[@]}"; then
          copycat_ok "OS packages installed (apt)"
        else
          copycat_warn "apt install skipped (no passwordless sudo) — install manually: ${pkgs[*]}"
        fi
      else
        copycat_warn "sudo unavailable or needs password — install manually: ${pkgs[*]}"
      fi
    elif command -v dnf >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
      sudo -n dnf install -y python3 python3-pip python3-tkinter xdotool scrot && copycat_ok "OS packages (dnf)" || copycat_warn "dnf install skipped"
    elif command -v pacman >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
      sudo -n pacman -Sy --noconfirm python python-pip tk xdotool scrot && copycat_ok "OS packages (pacman)" || copycat_warn "pacman install skipped"
    else
      copycat_warn "Unknown Linux package manager — skip OS packages"
    fi
  elif [[ "$os" == "macos" ]]; then
    if command -v brew >/dev/null 2>&1; then
      brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
      copycat_ok "Homebrew Python ready"
    else
      copycat_warn "Install Python 3.11+ from https://www.python.org/downloads/"
    fi
  elif [[ "$os" == "windows" ]]; then
    copycat_warn "Native Windows: use install.ps1 in PowerShell"
  fi
}

setup_venv() {
  local py="$1"
  local venv="${INSTALL_PREFIX}/daffodil-kit-venv"
  if [[ ! -d "$venv" ]]; then
    copycat_info "venv: $venv"
    "$py" -m venv "$venv"
  else
    copycat_info "Reusing venv: $venv"
  fi
  # shellcheck disable=SC1091
  source "$venv/bin/activate"
  python -m pip install --upgrade pip wheel setuptools -q
  copycat_ok "Virtualenv ready ($(python --version 2>&1))"
}

pip_install_kit() {
  local ref="$1"
  if [[ "$DAFFODIL_KIT_USE_LOCAL" == "1" ]]; then
    local root="${SCRIPT_DIR}"
    copycat_info "Local editable install: $root"
    pip install -e "$root" -q
  else
    copycat_info "Remote: git+${GIT_BASE}@${ref}"
    pip install "git+${GIT_BASE}@${ref}#subdirectory=packages/daffodil-kit" -q
  fi
  copycat_ok "daffodil-kit package installed"
}

install_native_backend() {
  local os="$1"
  [[ "$DAFFODIL_KIT_NATIVE" == "1" ]] || { copycat_info "Skipping Rust backend (DAFFODIL_KIT_NATIVE=0)"; return 0; }
  if [[ "$os" == "windows" ]]; then
    copycat_warn "Windows: install Rust from https://rustup.rs then re-run with DAFFODIL_KIT_NATIVE=1"
    return 0
  fi
  if ! command -v cargo >/dev/null 2>&1; then
    copycat_warn "cargo not found — Python capture backend only"
    return 0
  fi
  copycat_info "Building Rust capture extension..."
  pip install maturin -q
  local kit_dir="$SCRIPT_DIR"
  if [[ "$DAFFODIL_KIT_USE_LOCAL" != "1" ]]; then
    local tmp
    tmp=$(mktemp -d)
    git clone --depth 1 --branch "$DAFFODIL_KIT_VERSION" "$GIT_BASE" "$tmp/repo" 2>/dev/null \
      || git clone --depth 1 "$GIT_BASE" "$tmp/repo"
    kit_dir="$tmp/repo/packages/daffodil-kit"
  fi
  (cd "$kit_dir" && maturin develop --release -m native/Cargo.toml) && copycat_ok "Rust backend built" || copycat_warn "Rust build failed — Python fallback active"
}

write_config() {
  local cfg_dir="$HOME/.daffodil-kit"
  mkdir -p "$cfg_dir/logs"
  chmod 700 "$cfg_dir" 2>/dev/null || true
  if [[ -n "${DAFFODIL_KIT_API_URL:-}" && ! -f "$cfg_dir/config.json" ]]; then
    python3 - <<PY
import json, pathlib
p = pathlib.Path("$cfg_dir/config.json")
p.write_text(json.dumps({"api_url": "${DAFFODIL_KIT_API_URL}"}, indent=2))
PY
    copycat_ok "API URL written to config.json"
  else
    copycat_info "Config dir: $cfg_dir (mode 700)"
  fi
}

run_security_checks() {
  copycat_info "Verifying security modules..."
  python3 - <<'PY'
import time
from daffodil_kit.security import sign_command, verify_command, generate_device_secret
secret = generate_device_secret()
ts = time.time()
payload = '{"method":"ping"}'
sig = sign_command(secret, payload, ts)
assert verify_command(secret, payload, ts, sig)
assert not verify_command(secret, payload, ts, "bad")
print("security-ok")
PY
  copycat_ok "HMAC signing / verification OK"
}

run_post_install_verify() {
  local ver bindir="${INSTALL_PREFIX}/daffodil-kit-venv/bin"
  export PATH="${bindir}:$PATH"
  ver=$(daffodil-kit version 2>/dev/null || python3 -c "import daffodil_kit; print(daffodil_kit.__version__)")
  daffodil-kit status >/dev/null 2>&1 && copycat_ok "CLI status check passed (v${ver})" || copycat_warn "CLI status check failed"
  echo "$ver"
}

install_service() {
  local os="$1"
  [[ "$DAFFODIL_KIT_INSTALL_SERVICE" == "1" ]] || return 0
  local svc="${SCRIPT_DIR}/scripts/install-service.sh"
  if [[ -f "$svc" ]]; then
    bash "$svc" "$os" && copycat_ok "Background service installed" || copycat_warn "Service install failed"
  else
    curl -fsSL "${RAW_BASE}/packages/daffodil-kit/scripts/install-service.sh" | bash -s -- "$os" \
      && copycat_ok "Background service installed" || copycat_warn "Service install failed"
  fi
}

print_next_steps() {
  local venv="${INSTALL_PREFIX}/daffodil-kit-venv"
  local bindir="$venv/bin"
  cat <<EOF

Next steps:
  1. Pair:   daffodil-kit pair --api http://localhost:8000 --code <6-digit>
  2. Vault:  daffodil-kit vault set '<sudo-password>'   # local only, encrypted
  3. Start:  daffodil-kit start
  4. Audit:  tail -f ~/.daffodil-kit/logs/copycat_audit.jsonl

Docs: https://github.com/${DAFFODIL_KIT_REPO}/tree/${DAFFODIL_KIT_VERSION}/packages/daffodil-kit
EOF
  if [[ ":$PATH:" != *":$bindir:"* ]]; then
    echo ""
    echo "Add to PATH:"
    echo "  export PATH=\"$bindir:\$PATH\""
  fi
}

main() {
  COPYCAT_STEP_TOTAL=8
  local os
  os=$(detect_os)
  copycat_banner "$DAFFODIL_KIT_VERSION"

  copycat_step "Detect environment"
  copycat_info "OS: $os · repo: $DAFFODIL_KIT_REPO · ref: $DAFFODIL_KIT_VERSION"
  local py
  py=$(find_python) || copycat_fail "Python 3.11+ required — https://www.python.org/downloads/"
  copycat_ok "Python: $py ($($py --version 2>&1))"

  copycat_step "Install OS dependencies"
  install_os_packages "$os"

  copycat_step "Create Python virtualenv"
  setup_venv "$py"

  copycat_step "Install daffodil-kit package"
  pip_install_kit "$DAFFODIL_KIT_VERSION"

  copycat_step "Optional Rust capture backend"
  install_native_backend "$os"

  copycat_step "Configure local directories"
  write_config

  copycat_step "Security self-test"
  run_security_checks

  copycat_step "Verify installation"
  local ver
  ver=$(run_post_install_verify)

  install_service "$os"
  copycat_summary "$ver"
  print_next_steps
}

main "$@"
