"""Yerel, paylaşılmayan uygulama ayarları.

Kullanıcı tercihlerini (hedef roller, şehirler, kıdem) ve yapay zeka ajanı
seçimini ``data/settings.json`` içinde saklar. Eski Türkçe adlı ayar dosyası
``job_app.migration`` tarafından bir kez taşınır.
"""
from __future__ import annotations

from job_app.storage import DATA_DIR, data_file, load_json, write_json

SETTINGS_FILE = data_file("settings.json")

DEFAULTS = {
    "initial_review_limit": 10,
    "detailed_review_mode": "flexible",
    "welcome_shown": False,
    "target_roles": [],
    "target_sectors": [],
    "target_countries": [],
    "target_cities": [],
    "seniority": [],
    "work_arrangements": ["onsite", "hybrid", "remote"],
    "remote_ok": True,
    # Yapay zeka ajanı seçimi: "auto" PATH'te bulunan ilk ajanı kullanır.
    "ai_agent": "auto",
    "ai_custom_command": "",
    "ai_provider": "",
    "ai_model_fast": "",
    "ai_model_deep": "",
}

VALID_MODES = {"strict", "flexible", "very_flexible"}
LIST_FIELDS = ("target_roles", "target_sectors", "target_countries", "target_cities", "seniority", "work_arrangements")
TEXT_FIELDS = ("ai_agent", "ai_custom_command", "ai_provider", "ai_model_fast", "ai_model_deep")


def _normalize(values: dict) -> dict:
    """Ayar değerlerini güvenli aralığa ve tipe çeker."""
    result = {**DEFAULTS, **values}
    try:
        result["initial_review_limit"] = max(1, min(30, int(result["initial_review_limit"])))
    except (TypeError, ValueError):
        result["initial_review_limit"] = DEFAULTS["initial_review_limit"]
    if result["detailed_review_mode"] not in VALID_MODES:
        result["detailed_review_mode"] = DEFAULTS["detailed_review_mode"]
    for key in LIST_FIELDS:
        if not isinstance(result.get(key), list):
            result[key] = list(DEFAULTS[key])
    for key in TEXT_FIELDS:
        if not isinstance(result.get(key), str):
            result[key] = DEFAULTS[key]
    return result


def load_settings() -> dict:
    """Ayarları yükler; dosya yoksa varsayılanları döndürür."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stored = load_json(SETTINGS_FILE, None)
    return _normalize(stored if isinstance(stored, dict) else {})


def save_settings(values: dict) -> dict:
    """Ayarları birleştirir ve data/settings.json dosyasına yazar."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings = _normalize({**load_settings(), **values})
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
