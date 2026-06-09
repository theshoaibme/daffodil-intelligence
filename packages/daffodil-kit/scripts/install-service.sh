#!/usr/bin/env bash
# Install CopyCat Kit as a user service (systemd on Linux, launchd on macOS)
set -euo pipefail

OS="${1:-$(uname -s | tr '[:upper:]' '[:lower:]')}"
PREFIX="${DAFFODIL_KIT_PREFIX:-$HOME/.local}"
VENV="${PREFIX}/daffodil-kit-venv"
BIN="${VENV}/bin/daffodil-kit"
CFG="$HOME/.daffodil-kit"

if [[ ! -x "$BIN" ]]; then
  echo "daffodil-kit not found at $BIN — run install.sh first" >&2
  exit 1
fi

mkdir -p "$CFG/logs"

case "$OS" in
  linux*)
    UNIT_DIR="$HOME/.config/systemd/user"
    mkdir -p "$UNIT_DIR"
    cat > "$UNIT_DIR/daffodil-kit.service" <<EOF
[Unit]
Description=Daffodil CopyCat Kit daemon
After=network.target graphical-session.target

[Service]
Type=simple
ExecStart=${BIN} start
Restart=on-failure
RestartSec=5
Environment=HOME=${HOME}
WorkingDirectory=${HOME}

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now daffodil-kit.service
    echo "systemd user service enabled: daffodil-kit.service"
    ;;
  darwin*|macos*)
    PLIST="$HOME/Library/LaunchAgents/com.daffodil.kit.plist"
    cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.daffodil.kit</string>
  <key>ProgramArguments</key>
  <array><string>${BIN}</string><string>start</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>${CFG}/logs/kit.stdout.log</string>
  <key>StandardErrorPath</key><string>${CFG}/logs/kit.stderr.log</string>
</dict>
</plist>
EOF
    launchctl unload "$PLIST" 2>/dev/null || true
    launchctl load "$PLIST"
    echo "launchd agent loaded: com.daffodil.kit"
    ;;
  *)
    echo "Service install not supported on OS: $OS — start manually: daffodil-kit start" >&2
    exit 0
    ;;
esac
