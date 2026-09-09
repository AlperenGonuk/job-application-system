"""Yapay zeka yüklerinden kişisel verileri (PII) temizler.

İzinli mesleki alanlar: beceriler, deneyim açıklamaları, proje açıklamaları,
eğitim bilgisi, dil seviyeleri, hedef roller/şehirler.
Engellenen: ad-soyad, telefon, e-posta, açık adres, fotoğraf yolu, TC/kimlik, yerel dosya yolu.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

# --- Desenler ---
_PHONE = re.compile(
    r"""(?:\+?\d{1,3}[\s.-]?)?   # ülke kodu
    (?:\(?\d{1,4}\)?[\s.-]?)?     # alan kodu
    \d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,4} # numara gövdesi
    """,
    re.VERBOSE,
)
_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}")
_TC_KIMLIK = re.compile(r"\b[1-9]\d{10}\b")  # 11 haneli TC
_LOCAL_PATH_WIN = re.compile(r"[A-Z]:\\[\w\\. ÇĞİÖŞÜçğıöşü-]+", re.UNICODE)
_LOCAL_PATH_UNIX = re.compile(r"(?:/home/|/Users/|/root/)[\w/. -]+")
_PHOTO_REF = re.compile(r"(?:foto(?:ğraf)?|photo|resim|image|picture)[:\s]*[\w./\\-]+\.(?:png|jpg|jpeg|gif|bmp|webp)", re.IGNORECASE)
_ADDRESS_TR = re.compile(
    r"(?:mahalle|mah\.|sokak|sok\.|cadde|cad\.|bulvar|blv\.|apartman|apt\.|daire|kat|no[:\s]?\d)",
    re.IGNORECASE,
)

# Bilinen PII alanları (JSON anahtarları)
_PII_KEYS = frozenset({
    "name", "ad", "soyad", "ad_soyad", "full_name", "isim",
    "phone", "telefon", "tel", "mobile", "cep",
    "email", "e-posta", "eposta", "mail",
    "address", "adres", "tr_address", "international_location",
    "photo", "foto", "tr_photo", "fotograf", "fotoğraf", "resim",
    "tc", "tc_kimlik", "kimlik_no", "identity_number",
})

# İzinli mesleki alanlar
_ALLOWED_KEYS = frozenset({
    "experience", "deneyim", "projects", "projeler", "proje",
    "skills", "beceriler", "beceri", "education", "egitim", "eğitim",
    "languages", "diller", "dil", "language",
    "headline", "baslik", "başlık", "summary", "ozet", "özet",
    "target_roles", "hedef_roller", "target_cities", "hedef_sehirler",
    "title", "bullets", "label", "value",
    "cv_tipi", "cv_dili", "karar", "uyum_puani", "gerekce",
    "kullanilacak_kanitlar", "eksik_anahtarlar",
    "etiket", "sonnet", "id", "company", "location", "source_url",
    "published_at", "source", "mode",
})


def scrub_text(text: str) -> str:
    """Metin içindeki PII desenlerini maskeler."""
    result = text
    result = _EMAIL.sub("[E-POSTA GİZLİ]", result)
    result = _PHONE.sub(lambda m: "[TELEFON GİZLİ]" if len(re.sub(r"\D", "", m.group())) >= 7 else m.group(), result)
    result = _TC_KIMLIK.sub("[KİMLİK GİZLİ]", result)
    result = _LOCAL_PATH_WIN.sub("[YEREL YOL GİZLİ]", result)
    result = _LOCAL_PATH_UNIX.sub("[YEREL YOL GİZLİ]", result)
    result = _PHOTO_REF.sub("[FOTOĞRAF GİZLİ]", result)
    return result


def scrub_dict(data: dict, *, depth: int = 0) -> dict:
    """Sözlükteki PII anahtarlarını kaldırır, metin değerlerini temizler."""
    if depth > 10:
        return {}
    result = {}
    for key, value in data.items():
        key_lower = key.lower().replace("-", "_")
        if key_lower in _PII_KEYS:
            continue  # PII anahtarını tamamen çıkar
        if isinstance(value, dict):
            result[key] = scrub_dict(value, depth=depth + 1)
        elif isinstance(value, list):
            result[key] = [scrub_dict(item, depth=depth + 1) if isinstance(item, dict)
                          else scrub_text(item) if isinstance(item, str)
                          else item
                          for item in value]
        elif isinstance(value, str):
            result[key] = scrub_text(value)
        else:
            result[key] = value
    return result


def scrub_payload(payload: dict | list | str) -> dict | list | str:
    """Herhangi bir yapay zeka yükünü temizler."""
    if isinstance(payload, dict):
        return scrub_dict(payload)
    if isinstance(payload, list):
        return [scrub_payload(item) for item in payload]
    if isinstance(payload, str):
        return scrub_text(payload)
    return payload


def has_pii(text: str) -> bool:
    """Metinde potansiyel PII bulunup bulunmadığını kontrol eder."""
    if _EMAIL.search(text):
        return True
    phone_match = _PHONE.search(text)
    if phone_match and len(re.sub(r"\D", "", phone_match.group())) >= 7:
        return True
    if _TC_KIMLIK.search(text):
        return True
    if _LOCAL_PATH_WIN.search(text) or _LOCAL_PATH_UNIX.search(text):
        return True
    if _PHOTO_REF.search(text):
        return True
    return False
