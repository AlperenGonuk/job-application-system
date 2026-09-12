"""Yerel çalışma verileri için tek, güvenli depolama noktası.

Kaynak kodu ile kullanıcı verisini ayırır: üretilen her şey ``data/`` altına
yazılır. JSON yazımları atomiktir, böylece uygulama kapanırsa yarım dosya
bırakılmaz. Tek dosya .exe olarak paketlendiğinde veri klasörü exe'nin yanında,
depoyla gelen salt-okunur örnekler ise paket içinde aranır.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


def project_root() -> Path:
    """Kullanıcı verisinin yazılacağı kök dizin."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource_root() -> Path:
    """Depoyla birlikte gelen salt-okunur dosyaların (examples/, docs/) kökü."""
    bundled = getattr(sys, "_MEIPASS", None)
    return Path(bundled) if bundled else project_root()


ROOT = project_root()
DATA_DIR = ROOT / "data"


def data_file(name: str) -> Path:
    """data/ altındaki dosya yolunu döndürür."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / name


def data_dir(name: str) -> Path:
    """data/ altındaki klasörü oluşturur ve döndürür."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = DATA_DIR / name
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def resource_file(*parts: str) -> Path:
    """Depoyla gelen örnek/şablon dosyasının yolunu döndürür."""
    return resource_root().joinpath(*parts)


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
