"""Tek dosya çalıştırılabilir sürüm üretir (PyInstaller gerekir).

Kullanım:
    pip install pyinstaller
    python scripts/build_exe.py

Çıktı ``dist/`` altına yazılır. Uygulama verisini çalıştırılabilir dosyanın
yanındaki ``data/`` klasöründe tutar; depoyla gelen ``docs/`` ve ``examples/``
klasörleri paketin içine gömülür.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEPARATOR = ";" if sys.platform.startswith("win") else ":"
APP_NAME = "JobApplicationSystem"


def main() -> None:
    if shutil.which("pyinstaller") is None:
        raise SystemExit("PyInstaller bulunamadı. Kurmak için: pip install pyinstaller")
    command = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", APP_NAME,
        "--add-data", f"{ROOT / 'docs'}{SEPARATOR}docs",
        "--add-data", f"{ROOT / 'examples'}{SEPARATOR}examples",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        str(ROOT / "main.py"),
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    print(f"Hazır: {ROOT / 'dist'}")


if __name__ == "__main__":
    main()
