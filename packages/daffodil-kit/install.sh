#!/usr/bin/env bash
# CopyCat Kit (daffodil-kit) — cross-platform installer
# Linux · macOS · Windows (Git Bash / WSL)
#
# One-line install (latest main):
#   curl -fsSL https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/packages/daffodil-kit/install.sh | bash
#
# Pin a release tag:
#   DAFFODIL_KIT_VERSION=copycat-v0.1.0 curl -fsSL .../install.sh | bash
#
# Options via env:
#   DAFFODIL_KIT_REPO=the-shoaib2/daffodil-intelligence
#   DAFFODIL_KIT_VERSION=main|copycat-v0.1.0
#   DAFFODIL_KIT_NATIVE=1          # build optional Rust capture backend
#   DAFFODIL_KIT_INSTALL_SERVICE=1 # systemd (Linux) / launchd (macOS)
#   DAFFODIL_KIT_API_URL=...       # pre-configure API URL in ~/.daffodil-kit/config.json
set -euo pipefail

DAFFODIL_KIT_REPO="${DAFFODIL_KIT_REPO:-the-shoaib2/daffodil-intelligence}"
DAFFODIL_KIT_VERSION="${DAFFODIL_KIT_VERSION:-main}"
DAFFODIL_KIT_NATIVE="${DAFFODIL_KIT_NATIVE:-0}"
DAFFODIL_KIT_INSTALL_SERVICE="${DAFFODIL_KIT_INSTALL_SERVICE:-0}"
INSTALL_PREFIX="${DAFFODIL_KIT_PREFIX:-$HOME/.local}"
RAW_BASE="https://raw.githubusercontent.com/${DAFFODIL_KIT_REPO}/${DAFFODIL_KIT_VERSION}"
GIT_BASE="https://github.com/${DAFFODIL_KIT_REPO}.git"

log() { printf '\033[1;34m[copycat]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[copycat]\033[0m %s\n' "$*" >&2; }
err() { printf '\033[1;31m[copycat]\033[0m %s\n' "$*" >&2; exit 1; }

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
  log "Checking OS packages ($os)..."

  if [[ "$os" == "linux" ]]; then
    if command -v apt-get >/dev/null 2>&1; then
      local pkgs=(python3 python3-pip python3-venv python3-tk scrot xdotool)
      if [[ "$DAFFODIL_KIT_NATIVE" == "1" ]]; then
        pkgs+=(build-essential pkg-config libdbus-1-dev libxcb1-dev libxrandr-dev)
      fi
      if command -v sudo >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkgs[@]}" || warn "Some apt packages failed — continuing"
      else
        warn "sudo not available — install manually: ${pkgs[*]}"
      fi
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y python3 python3-pip python3-tkinter xdotool scrot || true
    elif command -v pacman >/dev/null 2>&1; then
      sudo pacman -Sy --noconfirm python python-pip tk xdotool scrot || true
    fi
  elif [[ "$os" == "macos" ]]; then
    if ! command -v brew >/dev/null 2>&1; then
      warn "Homebrew not found — install Python 3.11+ manually"
    else
      brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12 || true
    fi
  elif [[ "$os" == "windows" ]]; then
    warn "On native Windows use install.ps1 in PowerShell"
  fi
}

setup_venv() {
  local py="$1"
  local venv="${INSTALL_PREFIX}/daffodil-kit-venv"
  if [[ ! -d "$venv" ]]; then
    log "Creating virtualenv at $venv"
    "$py" -m venv "$venv"
  fi
  # shellcheck disable=SC1091
  source "$venv/bin/activate"
  python -m pip install --upgrade pip wheel setuptools
}

pip_install_kit() {
  local ref="$1"
  log "Installing daffodil-kit from ${GIT_BASE}@${ref}"
  pip install "git+${GIT_BASE}@${ref}#subdirectory=packages/daffodil-kit"
}

install_native_backend() {
  local os="$1"
  if [[ "$DAFFODIL_KIT_NATIVE" != "1" ]]; then
    return 0
  fi
  if [[ "$os" == "windows" ]]; then
    warn "Rust native backend on Windows: install Rust from https://rustup.rs then re-run with DAFFODIL_KIT_NATIVE=1"
    return 0
  fi
  if ! command -v cargo >/dev/null 2>&1; then
    warn "cargo not found — skipping native backend (Python capture still works)"
    return 0
  fi
  log "Building Rust capture backend..."
  pip install maturin
  local tmp
  tmp=$(mktemp -d)
  git clone --depth 1 --branch "$DAFFODIL_KIT_VERSION" "$GIT_BASE" "$tmp/repo" 2>/dev/null \
    || git clone --depth 1 "$GIT_BASE" "$tmp/repo"
  (cd "$tmp/repo/packages/daffodil-kit" && maturin develop --release -m native/Cargo.toml)
  rm -rf "$tmp"
}

write_config() {
  local cfg_dir="$HOME/.daffodil-kit"
  mkdir -p "$cfg_dir/logs"
  if [[ -n "${DAFFODIL_KIT_API_URL:-}" && ! -f "$cfg_dir/config.json" ]]; then
    log "Writing API URL to $cfg_dir/config.json"
    python3 - <<PY
import json, pathlib
p = pathlib.Path("$cfg_dir/config.json")
data = {"api_url": "${DAFFODIL_KIT_API_URL}"}
p.write_text(json.dumps(data, indent=2))
PY
  fi
}

install_service() {
  local os="$1"
  [[ "$DAFFODIL_KIT_INSTALL_SERVICE" == "1" ]] || return 0
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -f "$script_dir/scripts/install-service.sh" ]]; then
    bash "$script_dir/scripts/install-service.sh" "$os"
  else
    curl -fsSL "${RAW_BASE}/packages/daffodil-kit/scripts/install-service.sh" | bash -s -- "$os"
  fi
}

print_path_hint() {
  local venv="${INSTALL_PREFIX}/daffodil-kit-venv"
  local bindir="$venv/bin"
  if [[ ":$PATH:" != *":$bindir:"* ]]; then
    warn "Add to your shell profile:"
    echo "  export PATH=\"$bindir:\$PATH\""
  fi
}

main() {
  local os
  os=$(detect_os)
  log "CopyCat Kit installer — OS: $os · ref: $DAFFODIL_KIT_VERSION"

  local py
  py=$(find_python) || err "Python 3.11+ required. Install from https://www.python.org/downloads/"

  install_os_packages "$os"
  setup_venv "$py"
  pip_install_kit "$DAFFODIL_KIT_VERSION"
  install_native_backend "$os"
  write_config
  install_service "$os"

  local ver
  ver=$(daffodil-kit status 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print("paired" if d.get("paired") else "ok")' 2>/dev/null || daffodil-kit --help >/dev/null && echo "installed")

  log "CopyCat Kit installed successfully"
  daffodil-kit --help | head -n 3 || true
  print_path_hint
  cat <<EOF

Next steps:
  1. Pair:   daffodil-kit pair --api http://localhost:8000 --code <6-digit>
  2. Vault:  daffodil-kit vault set '<sudo-password>'   # optional, local only
  3. Start:  daffodil-kit start

Docs: https://github.com/${DAFFODIL_KIT_REPO}/tree/${DAFFODIL_KIT_VERSION}/packages/daffodil-kit
EOF
}

main "$@"
