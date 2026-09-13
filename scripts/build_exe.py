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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import TASKS  # noqa: E402  (kök dizin yola eklendikten sonra)

SEPARATOR = ";" if sys.platform.startswith("win") else ":"
APP_NAME = "JobApplicationSystem"


def hidden_imports() -> list[str]:
    """Paket içine zorla alınacak modüller.

    Görev modülleri ``main.py`` içinde ``importlib.import_module`` ile adından
    yüklenir; PyInstaller bu dinamik içe aktarmaları statik analizle göremez.
    Liste doğrudan ``main.TASKS`` kaynağından üretildiği için yeni görev
    eklendiğinde ayrıca güncellenmesi gerekmez.
    """
    return sorted(set(TASKS.values()))


def pyinstaller_command() -> list[str]:
    """PyInstaller komut satırını üretir."""
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", APP_NAME,
        "--add-data", f"{ROOT / 'docs'}{SEPARATOR}docs",
        "--add-data", f"{ROOT / 'examples'}{SEPARATOR}examples",
        "--paths", str(ROOT),
        # Görev modüllerinin kendi alt içe aktarmaları da güvenceye alınır.
        "--collect-submodules", "job_app",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
    ]
    for module in hidden_imports():
        command += ["--hidden-import", module]
    command.append(str(ROOT / "main.py"))
    return command


def main() -> None:
    command = pyinstaller_command()
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        executable = shutil.which("pyinstaller")
        if executable is None:
            raise SystemExit("PyInstaller bulunamadı. Kurmak için: pip install pyinstaller")
        command = [executable, *command[3:]]
    subprocess.run(command, check=True, cwd=ROOT)
    print(f"Hazır: {ROOT / 'dist'}")


if __name__ == "__main__":
    main()
