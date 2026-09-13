#!/usr/bin/env bash
# Linux ve macOS icin kurulum: sanal ortam olusturur ve bagimliliklari kurar.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 bulunamadi. Python 3.11 veya daha yenisini kurun." >&2
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Kurulum tamamlandi. Simdi ./scripts/start.sh calistirabilirsiniz."
echo "Not: DOCX dosyalarini uygulama icinden acmak icin LibreOffice kurulu olmalidir."
