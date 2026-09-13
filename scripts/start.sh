#!/usr/bin/env bash
# Linux ve macOS icin baslatici.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/python" ]; then
  echo "Ilk kullanim icin once ./scripts/setup.sh calistirin." >&2
  exit 1
fi

exec .venv/bin/python main.py "$@"
