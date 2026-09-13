#!/usr/bin/env bash
# Linux ve macOS icin kurulum: sanal ortam olusturur ve bagimliliklari kurar.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"

# Eksik sistem paketi icin isletim sistemine uygun kurulum komutunu yazar.
install_hint() {
  local debian="$1" fedora="$2" arch="$3" mac="$4"
  if [ "$(uname -s)" = "Darwin" ]; then
    echo "  macOS (Homebrew): brew install $mac"
    echo "  ya da python.org'daki resmi Python yukleyicisini kullanin (Tk dahildir)."
  elif command -v apt-get >/dev/null 2>&1; then
    echo "  sudo apt install $debian"
  elif command -v dnf >/dev/null 2>&1; then
    echo "  sudo dnf install $fedora"
  elif command -v pacman >/dev/null 2>&1; then
    echo "  sudo pacman -S $arch"
  else
    echo "  Paket yoneticinizde su paketi arayin: $debian"
  fi
}

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "python3 bulunamadi. Python 3.11 veya daha yenisini kurun." >&2
  exit 1
fi

if ! "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
  echo "Python 3.11 veya daha yenisi gerekli; bulunan: $("$PYTHON" --version 2>&1)" >&2
  exit 1
fi

missing=0
if ! "$PYTHON" -c 'import venv, ensurepip' >/dev/null 2>&1; then
  echo "Python sanal ortam modulu (venv/ensurepip) eksik. Kurmak icin:" >&2
  install_hint "python3-venv" "python3" "python" "python" >&2
  missing=1
fi
if ! "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
  echo "Masaustu arayuzu icin Tkinter eksik. Kurmak icin:" >&2
  install_hint "python3-tk" "python3-tkinter" "tk" "python-tk" >&2
  missing=1
fi
if [ "$missing" -ne 0 ]; then
  echo "Eksik paketleri kurduktan sonra bu betigi yeniden calistirin." >&2
  exit 1
fi

# Onceki basarisiz bir denemeden kalan, pip'i olmayan yarim ortami yeniden kur.
if [ -x ".venv/bin/python" ] && ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
  echo "Yarim kalmis .venv bulundu, yeniden olusturuluyor."
  rm -rf .venv
fi
if [ ! -x ".venv/bin/python" ]; then
  "$PYTHON" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Kurulum tamamlandi. Simdi ./scripts/start.sh calistirabilirsiniz."
echo "Not: DOCX dosyalarini uygulama icinden acmak icin LibreOffice onerilir; yoksa sistemin varsayilan programi kullanilir."
