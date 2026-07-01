#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-1}"
PUBLIC_URL="${PUBLIC_URL:-https://tara.agusrokyanto.com}"
TUNNEL="${TUNNEL:-0}"
TUNNEL_NAME="${TUNNEL_NAME:-tara-caraka-ceria}"

if [ ! -x ".venv/bin/python" ]; then
  echo "ERROR: .venv belum ada atau belum lengkap." >&2
  echo "Jalankan dulu:" >&2
  echo "  ./scripts/setup_ubuntu.sh" >&2
  exit 1
fi

mkdir -p data/runs data/logs

if [ ! -f data/tara-caraka-form.config.json ]; then
  cp data/tara-caraka-form.config.example.json data/tara-caraka-form.config.json
fi

if [ ! -f data/form-profile.json ]; then
  cp data/form-profile.example.json data/form-profile.json
fi

export APP_ENV="${APP_ENV:-development}"
export TZ="${TZ:-Asia/Jakarta}"
export PYTHONUTF8=1

ARGS=(
  -m uvicorn
  app.main:app
  --host "$HOST"
  --port "$PORT"
)

if [ "$RELOAD" != "0" ]; then
  ARGS+=(--reload)
fi

echo "Starting Tara Local Web Control Panel..."
echo "Local URL: http://$HOST:$PORT"
echo "Public URL: $PUBLIC_URL"
echo "Press Ctrl+C to stop."

if [ "$TUNNEL" = "1" ]; then
  if ! command -v cloudflared >/dev/null 2>&1; then
    echo "ERROR: cloudflared tidak ditemukan di PATH." >&2
    echo "Install cloudflared dan login/connect tunnel dulu." >&2
    exit 1
  fi

  echo "Starting Cloudflare tunnel: $TUNNEL_NAME"
  cloudflared tunnel run "$TUNNEL_NAME" \
    > data/logs/cloudflared-tunnel.stdout.log \
    2> data/logs/cloudflared-tunnel.stderr.log &
  TUNNEL_PID="$!"
  echo "Cloudflare tunnel PID: $TUNNEL_PID"

  cleanup() {
    if kill -0 "$TUNNEL_PID" >/dev/null 2>&1; then
      kill "$TUNNEL_PID"
    fi
  }
  trap cleanup EXIT INT TERM
fi

exec ./.venv/bin/python "${ARGS[@]}"
