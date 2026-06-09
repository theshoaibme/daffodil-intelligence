#!/bin/sh
# Ensure Python 3.11+ exists — OS packages, then uv (no sudo). Sourced by install.
set -e

copycat_log() { printf '[copycat] %s\n' "$*"; }
copycat_warn() { printf '[copycat] %s\n' "$*" >&2; }

copycat_python_ok() {
  "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null
}

# Echo first working python command (may be multi-word: "py -3")
copycat_find_python() {
  for c in python3.12 python3.11 python3 python; do
    command -v "$c" >/dev/null 2>&1 && copycat_python_ok "$c" && { echo "$c"; return 0; }
  done
  if command -v py >/dev/null 2>&1 && copycat_python_ok py -3; then
    echo "py -3"
    return 0
  fi
  if [ -n "${COPYCAT_UV:-}" ] && [ -x "$COPYCAT_UV" ]; then
    p=$("$COPYCAT_UV" python find 3.12 2>/dev/null || "$COPYCAT_UV" python find 3.11 2>/dev/null || true)
    if [ -n "$p" ] && [ -x "$p" ] && copycat_python_ok "$p"; then
      echo "$p"
      return 0
    fi
  fi
  return 1
}

copycat_run_python() {
  py=$(copycat_find_python) || return 1
  # shellcheck disable=SC2086
  exec $py "$@"
}

copycat_install_python_os() {
  os=$(uname -s 2>/dev/null || echo unknown)
  copycat_log "No Python 3.11+ — installing via OS package manager ($os)..."

  case "$os" in
    Linux)
      if command -v apt-get >/dev/null 2>&1; then
        if command -v sudo >/dev/null 2>&1; then
          sudo apt-get update -qq
          sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv python3-tk curl
          return 0
        fi
        copycat_warn "Need sudo for: sudo apt install python3 python3-pip python3-venv"
        return 1
      fi
      if command -v dnf >/dev/null 2>&1 && command -v sudo >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip python3-tkinter curl
        return 0
      fi
      if command -v pacman >/dev/null 2>&1 && command -v sudo >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python python-pip tk curl
        return 0
      fi
      ;;
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        brew install python@3.12 curl
        return 0
      fi
      copycat_warn "Install Homebrew, then: brew install python@3.12"
      return 1
      ;;
    MINGW*|MSYS*|CYGWIN*)
      copycat_warn "Windows: run install.ps1 or: winget install Python.Python.3.12"
      return 1
      ;;
  esac
  return 1
}

# uv installs Python to ~/.local without sudo (Linux/macOS)
copycat_install_python_uv() {
  copycat_log "Installing Python via uv (no sudo)..."
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if ! command -v uv >/dev/null 2>&1; then
    if ! command -v curl >/dev/null 2>&1; then
      copycat_warn "curl required to bootstrap uv"
      return 1
    fi
    curl -fsSL https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  fi
  COPYCAT_UV=$(command -v uv)
  "$COPYCAT_UV" python install 3.12 || "$COPYCAT_UV" python install 3.11
  export COPYCAT_UV
  return 0
}

copycat_ensure_python() {
  if copycat_find_python >/dev/null 2>&1; then
    return 0
  fi
  copycat_install_python_os 2>/dev/null || true
  if copycat_find_python >/dev/null 2>&1; then
    copycat_log "Python ready (OS packages)"
    return 0
  fi
  copycat_install_python_uv 2>/dev/null || true
  if copycat_find_python >/dev/null 2>&1; then
    copycat_log "Python ready (uv)"
    return 0
  fi
  copycat_warn "Could not install Python automatically."
  copycat_warn "Linux:   sudo apt install python3 python3-pip python3-venv"
  copycat_warn "macOS:   brew install python@3.12"
  copycat_warn "Windows: winget install Python.Python.3.12"
  copycat_warn "Or:      curl -LsSf https://astral.sh/uv/install.sh | sh && uv python install 3.12"
  return 1
}
