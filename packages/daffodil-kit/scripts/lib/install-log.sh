#!/usr/bin/env bash
# Structured install logging for CopyCat Kit — sourced by install.sh / verify-install.sh
# Writes human-readable output + JSON-lines to ~/.daffodil-kit/logs/install-<timestamp>.log

COPYCAT_LOG_DIR="${COPYCAT_LOG_DIR:-$HOME/.daffodil-kit/logs}"
COPYCAT_INSTALL_ID="${COPYCAT_INSTALL_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
COPYCAT_LOG_FILE="${COPYCAT_LOG_FILE:-$COPYCAT_LOG_DIR/install-${COPYCAT_INSTALL_ID}.log}"
COPYCAT_STEP_TOTAL="${COPYCAT_STEP_TOTAL:-7}"
COPYCAT_STEP_NUM=0

_copycat_init_log() {
  mkdir -p "$COPYCAT_LOG_DIR"
  : >"$COPYCAT_LOG_FILE"
  _copycat_json_log "install.start" "info" "{\"install_id\":\"$COPYCAT_INSTALL_ID\"}"
}

_copycat_ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

_copycat_json_log() {
  local event="$1" level="$2" detail="${3:-{}}"
  printf '{"ts":"%s","event":"%s","level":"%s","detail":%s}\n' "$(_copycat_ts)" "$event" "$level" "$detail" >>"$COPYCAT_LOG_FILE"
}

copycat_banner() {
  local version="${1:-unknown}"
  _copycat_init_log
  echo ""
  echo "══════════════════════════════════════════════════════════"
  echo "  CopyCat Kit Installer"
  echo "  Version target: ${version}"
  echo "  Log: ${COPYCAT_LOG_FILE}"
  echo "══════════════════════════════════════════════════════════"
  echo ""
  _copycat_json_log "install.banner" "info" "{\"version\":\"$version\"}"
}

copycat_step() {
  local title="$1"
  COPYCAT_STEP_NUM=$((COPYCAT_STEP_NUM + 1))
  printf '\033[1;36m[%s/%s]\033[0m %s\n' "$COPYCAT_STEP_NUM" "$COPYCAT_STEP_TOTAL" "$title"
  _copycat_json_log "install.step" "info" "{\"step\":$COPYCAT_STEP_NUM,\"title\":\"$title\"}"
}

copycat_ok() {
  printf '  \033[1;32m✓\033[0m %s\n' "$*"
  _copycat_json_log "install.ok" "info" "$(python3 -c 'import json,sys; print(json.dumps({"message":sys.argv[1]}))' "$*" 2>/dev/null || echo "{\"message\":\"ok\"}")"
}

copycat_warn() {
  printf '  \033[1;33m!\033[0m %s\n' "$*" >&2
  _copycat_json_log "install.warn" "warn" "$(python3 -c 'import json,sys; print(json.dumps({"message":sys.argv[1]}))' "$*" 2>/dev/null || echo "{\"message\":\"warn\"}")"
}

copycat_fail() {
  printf '  \033[1;31m✗\033[0m %s\n' "$*" >&2
  _copycat_json_log "install.fail" "error" "$(python3 -c 'import json,sys; print(json.dumps({"message":sys.argv[1]}))' "$*" 2>/dev/null || echo "{\"message\":\"fail\"}")"
  echo ""
  echo "Install failed. Full log: $COPYCAT_LOG_FILE"
  exit 1
}

copycat_info() {
  printf '    · %s\n' "$*"
  _copycat_json_log "install.info" "info" "$(python3 -c 'import json,sys; print(json.dumps({"message":sys.argv[1]}))' "$*" 2>/dev/null || echo "{}")"
}

copycat_summary() {
  local version="$1"
  echo ""
  echo "──────────────────────────────────────────────────────────"
  echo "  Install complete — daffodil-kit $version"
  echo "  Log saved: $COPYCAT_LOG_FILE"
  echo "──────────────────────────────────────────────────────────"
  _copycat_json_log "install.complete" "info" "{\"version\":\"$version\"}"
}
