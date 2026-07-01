#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_BIN tidak ditemukan di PATH." >&2
  exit 1
fi

if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
  echo "ERROR: modul venv tidak tersedia." >&2
  echo "Install dulu paket venv, misalnya:" >&2
  echo "  sudo apt install python3.14-venv" >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Membuat virtualenv .venv..."
  if ! "$PYTHON_BIN" -m venv .venv; then
    echo "ERROR: gagal membuat .venv." >&2
    echo "Di Ubuntu biasanya perlu:" >&2
    echo "  sudo apt install python3.14-venv" >&2
    exit 1
  fi
fi

echo "Meng-upgrade pip dan memasang dependency..."
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

mkdir -p data/runs data/logs

if [ ! -f data/tara-caraka-form.config.json ]; then
  cp data/tara-caraka-form.config.example.json data/tara-caraka-form.config.json
fi

if [ ! -f data/form-profile.json ]; then
  cp data/form-profile.example.json data/form-profile.json
fi

echo "Setup selesai."
echo "Jalankan server dengan:"
echo "  ./scripts/start_ubuntu.sh"
