"""Yerel, paylaşılmayan uygulama ayarları.

Kullanıcı tercihlerini (hedef roller, şehirler, kıdem) ayarlar dosyasında saklar.
Veri dizini olarak data/ kullanır; eski konumdaki dosyalar varsa uyumluluk sağlanır.
"""
from __future__ import annotations

import json
from pathlib import Path

from depolama import DATA_DIR, data_file, load_json, write_json

ROOT = Path(__file__).resolve().parent
SETTINGS_FILE = data_file("ayarlar.json")
LEGACY_SETTINGS_FILE = ROOT / "ayarlar.json"

DEFAULTS = {
    "initial_review_limit": 10,
    "detailed_review_mode": "esnek",
    "welcome_shown": False,
    "target_roles": [],
    "target_sectors": [],
    "target_countries": [],
    "target_cities": [],
    "seniority": [],
    "work_arrangements": ["ofis", "hibrit", "uzaktan"],
    "remote_ok": True,
}

VALID_MODES = {"kati", "esnek", "cok_esnek"}


def _migrate_legacy() -> dict | None:
    """Eski konumdaki ayarlar.json varsa data/ altına taşır (kayıpsız)."""
    if LEGACY_SETTINGS_FILE.exists() and not SETTINGS_FILE.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(LEGACY_SETTINGS_FILE.read_text(encoding="utf-8"))
            write_json(SETTINGS_FILE, data)
            return data
        except (OSError, json.JSONDecodeError):
            pass
    return None


def load_settings() -> dict:
    """Ayarları yükler; data/ altında yoksa eski konumu kontrol eder."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not SETTINGS_FILE.exists():
        migrated = _migrate_legacy()
        if migrated is None:
            return DEFAULTS.copy()
        stored = migrated
    else:
        try:
            stored = load_json(SETTINGS_FILE, DEFAULTS.copy())
        except OSError:
            return DEFAULTS.copy()

    result = {**DEFAULTS, **stored}
    result["initial_review_limit"] = max(1, min(30, int(result["initial_review_limit"])))
    if result["detailed_review_mode"] not in VALID_MODES:
        result["detailed_review_mode"] = DEFAULTS["detailed_review_mode"]
    # Liste alanları güvenli dönüşüm
    for key in ("target_roles", "target_sectors", "target_countries", "target_cities", "seniority", "work_arrangements"):
        if not isinstance(result.get(key), list):
            result[key] = DEFAULTS[key]
    return result


def save_settings(values: dict) -> dict:
    """Ayarları birleştirir ve data/ayarlar.json'a yazar."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings = {**load_settings(), **values}
    settings["initial_review_limit"] = max(1, min(30, int(settings["initial_review_limit"])))
    if settings["detailed_review_mode"] not in VALID_MODES:
        settings["detailed_review_mode"] = DEFAULTS["detailed_review_mode"]
    for key in ("target_roles", "target_sectors", "target_countries", "target_cities", "seniority", "work_arrangements"):
        if not isinstance(settings.get(key), list):
            settings[key] = DEFAULTS[key]
    write_json(SETTINGS_FILE, settings)
    return settings


def has_user_preferences() -> bool:
    """Kullanıcının hedef rol/şehir tercihlerini girip girmediğini kontrol eder."""
    settings = load_settings()
    return bool(settings.get("target_roles")) and bool(settings.get("target_cities"))


def get_preference_summary() -> str:
    """Kullanıcı tercihlerinin özet metnini döndürür."""
    settings = load_settings()
    roles = ", ".join(settings.get("target_roles", [])) or "(belirtilmemiş)"
    sectors = ", ".join(settings.get("target_sectors", [])) or "(belirtilmemiş)"
    countries = ", ".join(settings.get("target_countries", [])) or "(belirtilmemiş)"
    cities = ", ".join(settings.get("target_cities", [])) or "(belirtilmemiş)"
    seniority = ", ".join(settings.get("seniority", [])) or "(belirtilmemiş)"
    work = ", ".join(settings.get("work_arrangements", [])) or "(belirtilmemiş)"
    return f"Roller: {roles} | Sektörler: {sectors} | Ülkeler: {countries} | Şehirler: {cities} | Kıdem: {seniority} | Çalışma: {work}"
