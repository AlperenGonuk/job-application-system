"""Yerel çalışma verileri için tek, güvenli depolama noktası.

Kaynak kodu ile kullanıcı verisini ayırır. Eski sürümlerde proje kökünde
bulunan çalışma dosyaları yalnızca ilk okumada data/ altına kopyalanır;
orijinal dosyalar silinmez. JSON yazımları atomiktir, böylece uygulama
kapanırsa yarım dosya bırakılmaz.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


def data_file(name: str) -> Path:
    """data/ altındaki dosyayı döndürür; varsa eski kök kopyasını taşır."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = DATA_DIR / name
    legacy = ROOT / name
    if not destination.exists() and legacy.is_file():
        shutil.copy2(legacy, destination)
    return destination


def data_dir(name: str) -> Path:
    """data/ altındaki klasörü döndürür; eski klasörü kayıpsız kopyalar."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = DATA_DIR / name
    legacy = ROOT / name
    if not destination.exists() and legacy.is_dir():
        shutil.copytree(legacy, destination)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value) -> None:
    """JSON'u aynı disk üzerinde atomik olarak yazar."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
