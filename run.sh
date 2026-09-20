#!/usr/bin/env bash
# ── ORCA backend launcher ────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

HOST="${ORCA_HOST:-0.0.0.0}"
PORT="${ORCA_PORT:-8000}"

if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

exec uvicorn main:app --reload --host "$HOST" --port "$PORT"
