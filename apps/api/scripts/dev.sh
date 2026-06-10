#!/usr/bin/env bash
# Start API with reload. Fails fast with a clear message if port 8000 is taken.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${API_PORT:-8000}"
PYTHON="${ROOT}/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing virtualenv at apps/api/.venv — create it and install deps first." >&2
  exit 1
fi

if command -v ss >/dev/null 2>&1; then
  if ss -tlnH "sport = :$PORT" 2>/dev/null | grep -q .; then
    if [[ "${DAFFODIL_API_RESTART:-0}" == "1" ]]; then
      echo "Restarting API on port $PORT..."
      fuser -k "${PORT}/tcp" 2>/dev/null || true
      sleep 1
    elif curl -fsS -m 3 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
      echo "API already running at http://localhost:$PORT (health OK)"
      echo "Restart: DAFFODIL_API_RESTART=1 pnpm dev:api"
      exit 0
    else
      echo "Port $PORT is in use but /health failed — another process may own the port." >&2
      echo "  Stop:  fuser -k ${PORT}/tcp" >&2
      echo "  Then:  pnpm dev:api" >&2
      ss -tlnp "sport = :$PORT" 2>/dev/null || true
      exit 1
    fi
  fi
fi

exec "$PYTHON" -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --reload \
  --log-level critical \
  --no-access-log
