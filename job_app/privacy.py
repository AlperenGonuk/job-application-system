"""Yapay zeka yüklerinden kişisel verileri (PII) temizler.

İzinli mesleki alanlar: beceriler, deneyim açıklamaları, proje açıklamaları,
eğitim bilgisi, dil seviyeleri, hedef roller/şehirler.
Bilinen kimlik anahtarları (ad-soyad, telefon, e-posta, adres, fotoğraf, TC/kimlik)
yükten tamamen çıkarılır. Serbest metinde ve bağlantı parametrelerinde telefon,
e-posta, TC kimlik, açık adres, fotoğraf ve yerel dosya yolu desenleri maskelenir.

Sınır: serbest metin temizliği desen tabanlıdır ve en iyi çaba ilkesiyle çalışır;
alışılmadık biçimde yazılmış bir adres veya kimlik bilgisini kaçırabilir. Bu yüzden
serbest alanlara kişisel bilgi yazılmamalıdır.
"""
from __future__ import annotations

import re
from urllib.parse import unquote, unquote_plus

# --- Desenler ---
_PHONE = re.compile(
    r"""(?:\+?\d{1,3}[\s.-]?)?   # ülke kodu
    (?:\(?\d{1,4}\)?[\s.-]?)?     # alan kodu
    \d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,4} # numara gövdesi
    """,
    re.VERBOSE,
)
_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}")
# Herkese açık ilan bağlantıları korunur: LinkedIn ilan numarası gibi uzun sayılar
# telefon numarası sanılıp maskelenirse ilanın kimliği bozulur ve model çıktısı
# hiçbir ilanla eşleşmez. Bağlantı içindeki kişisel parametreler ise ayrıca,
# hedefli olarak maskelenir (bkz. _scrub_url).
_URL = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_URL_PLACEHOLDER = "\x00URL{index}\x00"
_TC_KIMLIK = re.compile(r"\b[1-9]\d{10}\b")  # 11 haneli TC
_LOCAL_PATH_WIN = re.compile(r"[A-Z]:\\[\w\\. ÇĞİÖŞÜçğıöşü-]+", re.UNICODE)
_LOCAL_PATH_UNIX = re.compile(r"(?:/home/|/Users/|/root/)[\w/. -]+")
_PHOTO_REF = re.compile(r"(?:foto(?:ğraf)?|photo|resim|image|picture)[:\s]*[\w./\\-]+\.(?:png|jpg|jpeg|gif|bmp|webp)", re.IGNORECASE)

# Açık adres: "Adres: ..." etiketinden sonra gelen değer satır sonuna kadar
# maskelenir. Etiketsiz adreslerde mahalle/sokak/cadde gibi bir işaretçi ve
# çevresindeki ad ile "No: 4", "Daire 3" gibi birimler birlikte maskelenir.
_ADDRESS_MASK = "[ADRES GİZLİ]"
_ADDRESS_LABEL = re.compile(
    r"(?<!\w)((?:ev |iş |home |postal |mailing )?(?:adres(?:i|im)?|address))(\s*[:=]\s*)"
    r"(?!\[ADRES GİZLİ\])(\S[^\n;|]*)",
    re.IGNORECASE,
)
_ADDRESS_MARKER = (
    r"(?:mahallesi|mah\.|mh\.|sokağı|sokak|sok\.|sk\.|caddesi|cadde|cad\.|cd\.|"
    r"bulvarı|bulvar|blv\.|apartmanı|apt\.)(?:(?<=\.)|(?!\w))"
)
_ADDRESS_UNIT = r"(?:no|daire|kat)\s*[:.]?\s*\d+[a-zçğıöşü]?(?:\s*/\s*\d+[a-zçğıöşü]?)?(?!\w)"
_ADDRESS_PART = rf"(?:(?:[^\W\d_][\w'’-]*\.?\s+){{1,3}}{_ADDRESS_MARKER}|{_ADDRESS_UNIT})"
_ADDRESS = re.compile(rf"(?<!\w){_ADDRESS_PART}(?:[\s,]+{_ADDRESS_PART})*", re.IGNORECASE)
_ADDRESS_MARKER_ONLY = re.compile(_ADDRESS_MARKER, re.IGNORECASE)

# Bağlantı parametrelerinde kişisel veri taşıyan anahtarlar (küçük harf, yalnız harf).
_URL_MASK = "[GİZLİ]"
_SENSITIVE_URL_KEYS = frozenset({
    "email", "mail", "eposta", "emailaddress", "useremail",
    "phone", "phonenumber", "tel", "telephone", "telefon", "mobile", "gsm", "cep",
    "name", "fullname", "firstname", "lastname", "surname", "adsoyad", "soyad", "isim",
    "address", "adres", "tc", "tckimlik", "kimlikno", "identitynumber", "ssn",
})
# Değere göre telefon: yalnız ülke/hat öneki taşıyan biçimler. Önek içermeyen uzun
# sayılar (ilan numarası gibi) telefon sayılmaz.
_TR_PHONE_VALUE = re.compile(r"^(?:\+?90|0090|0)5\d{9}$")
_INTL_PHONE_VALUE = re.compile(r"^\+\d{8,15}$")
_URL_PARTS = re.compile(r"^(?P<scheme>https?://)(?P<authority>[^/?#]*)(?P<path>[^?#]*)(?P<query>\?[^#]*)?(?P<fragment>#.*)?$", re.IGNORECASE)

# Bilinen PII alanları (JSON anahtarları)
_PII_KEYS = frozenset({
    "name", "ad", "soyad", "ad_soyad", "full_name", "isim",
    "phone", "telefon", "tel", "mobile", "cep",
    "email", "e-posta", "eposta", "mail",
    "address", "adres", "tr_address", "international_location",
    "photo", "foto", "tr_photo", "fotograf", "fotoğraf", "resim",
    "tc", "tc_kimlik", "kimlik_no", "identity_number",
})

# İzinli mesleki alanlar. Eski Türkçe adlar, henüz taşınmamış yerel dosyalar
# için listede kalır; yeni şema İngilizce anahtarları kullanır.
_ALLOWED_KEYS = frozenset({
    "experience", "deneyim", "projects", "projeler", "proje",
    "skills", "beceriler", "beceri", "education", "egitim", "eğitim",
    "languages", "diller", "dil", "language",
    "headline", "baslik", "başlık", "summary", "ozet", "özet",
    "target_roles", "hedef_roller", "target_cities", "hedef_sehirler",
    "title", "bullets", "label", "value",
    "cv_focus", "cv_language", "decision", "match_score", "reason",
    "evidence_used", "missing_requirements", "needs_detail",
    "best_cv", "results", "strong_matches", "note", "score",
    "matched_terms", "missing_terms",
    "cv_tipi", "cv_dili", "karar", "uyum_puani", "gerekce",
    "kullanilacak_kanitlar", "eksik_anahtarlar", "etiket", "sonnet",
    "id", "company", "location", "source_url",
    "published_at", "source", "mode",
})


def _is_sensitive_url_value(key: str, value: str) -> bool:
    """Bağlantı parametresinin kişisel veri taşıyıp taşımadığını belirler."""
    if not value:
        return False
    if re.sub(r"[^a-z]", "", key.lower()) in _SENSITIVE_URL_KEYS:
        return True
    if _EMAIL.search(value):
        return True
    compact = re.sub(r"[\s().-]", "", value)
    return bool(_TR_PHONE_VALUE.match(compact) or _INTL_PHONE_VALUE.match(compact))


def _scrub_url_params(section: str) -> str:
    """``a=1&b=2`` biçimindeki bölümde yalnız hassas değerleri değiştirir.

    Diğer parametrelere bayt bayt dokunulmaz; böylece ilan bağlantısının
    kodlaması ve kimliği değişmez.
    """
    pieces = re.split(r"([&;])", section)
    for index, piece in enumerate(pieces):
        if piece in ("&", ";") or "=" not in piece:
            continue
        key, value = piece.split("=", 1)
        if value != _URL_MASK and _is_sensitive_url_value(unquote_plus(key), unquote_plus(value).strip()):
            pieces[index] = f"{key}={_URL_MASK}"
    return "".join(pieces)


def _scrub_url(url: str) -> str:
    """Bağlantıdaki kullanıcı bilgisi, e-posta içeren yol parçaları ve kişisel
    sorgu/parça parametrelerini maskeler; ilan kimliklerini korur."""
    parts = _URL_PARTS.match(url)
    if not parts:
        return url
    authority = parts.group("authority")
    if "@" in authority:
        authority = f"{_URL_MASK}@{authority.rsplit('@', 1)[1]}"
    path = "/".join(
        _URL_MASK if segment != _URL_MASK and _EMAIL.search(unquote(segment)) else segment
        for segment in parts.group("path").split("/")
    )
    query = parts.group("query") or ""
    if query:
        query = "?" + _scrub_url_params(query[1:])
    fragment = parts.group("fragment") or ""
    if fragment:
        body = fragment[1:]
        if "=" in body:
            body = _scrub_url_params(body)
        elif body != _URL_MASK and _EMAIL.search(unquote(body)):
            body = _URL_MASK
        fragment = "#" + body
    return f"{parts.group('scheme')}{authority}{path}{query}{fragment}"


def _stash_urls(text: str) -> tuple[str, list[str]]:
    """Bağlantıları geçici işaretçiyle değiştirir; kişisel parametreleri
    maskelenmiş listesini döndürür."""
    found: list[str] = []

    def keep(match: re.Match) -> str:
        found.append(_scrub_url(match.group()))
        return _URL_PLACEHOLDER.format(index=len(found) - 1)

    return _URL.sub(keep, text), found


def _restore_urls(text: str, urls: list[str]) -> str:
    """Geçici işaretçileri bağlantılarla değiştirir."""
    for index, url in enumerate(urls):
        text = text.replace(_URL_PLACEHOLDER.format(index=index), url)
    return text


def _mask_address(match: re.Match) -> str:
    # "No 1" gibi tek başına birimler adres sayılmaz; en az bir işaretçi gerekir.
    return _ADDRESS_MASK if _ADDRESS_MARKER_ONLY.search(match.group()) else match.group()


def scrub_text(text: str) -> str:
    """Metin içindeki PII desenlerini maskeler; ilan bağlantılarının kimliğini korur."""
    result, urls = _stash_urls(text)
    result = _EMAIL.sub("[E-POSTA GİZLİ]", result)
    result = _PHONE.sub(lambda m: "[TELEFON GİZLİ]" if len(re.sub(r"\D", "", m.group())) >= 7 else m.group(), result)
    result = _TC_KIMLIK.sub("[KİMLİK GİZLİ]", result)
    result = _LOCAL_PATH_WIN.sub("[YEREL YOL GİZLİ]", result)
    result = _LOCAL_PATH_UNIX.sub("[YEREL YOL GİZLİ]", result)
    result = _PHOTO_REF.sub("[FOTOĞRAF GİZLİ]", result)
    result = _ADDRESS_LABEL.sub(lambda m: f"{m.group(1)}{m.group(2)}{_ADDRESS_MASK}", result)
    result = _ADDRESS.sub(_mask_address, result)
    return _restore_urls(result, urls)


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
            result[key] = scrub_payload(value, depth=depth + 1)
        elif isinstance(value, str):
            result[key] = scrub_text(value)
        else:
            result[key] = value
    return result


def scrub_payload(payload: dict | list | str, *, depth: int = 0) -> dict | list | str:
    """Herhangi bir yapay zeka yükünü (iç içe listeler dahil) temizler."""
    if depth > 10:
        return type(payload)() if isinstance(payload, (dict, list, str)) else None
    if isinstance(payload, dict):
        return scrub_dict(payload, depth=depth)
    if isinstance(payload, list):
        return [scrub_payload(item, depth=depth + 1) for item in payload]
    if isinstance(payload, str):
        return scrub_text(payload)
    return payload


def has_pii(text: str) -> bool:
    """Metinde potansiyel PII bulunup bulunmadığını kontrol eder.

    Bağlantıların ilan kimliği kapsam dışıdır; ancak maskelenmemiş kişisel
    parametre taşıyan bağlantı PII sayılır.
    """
    if any(_scrub_url(url) != url for url in _URL.findall(text)):
        return True
    text, _urls = _stash_urls(text)
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
    if _ADDRESS_LABEL.search(text):
        return True
    return any(_ADDRESS_MARKER_ONLY.search(match.group()) for match in _ADDRESS.finditer(text))
