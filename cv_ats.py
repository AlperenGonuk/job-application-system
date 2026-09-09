"""Model kullanmadan, yerel CV-ilan anahtar kelime uyumu hesaplar.

Bu bir işe alım sisteminin gerçek ATS puanı değil; CV'de doğrulanmış terimlerin
ilan metnindeki teknik terimlerle örtüşmesine dayalı şeffaf bir tahmindir.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from docx import Document

from ilan_sonnet_esle import fetch_description
from depolama import data_dir, data_file, load_json, write_json

ROOT = Path(__file__).resolve().parent
CV_DIR = data_dir("CV-Sürümleri")
PROFILES_FILE = data_file("cv-ats-profilleri.json")
SCORES_FILE = data_file("cv-ats-puanlari.json")
def available_cvs() -> dict[str, dict]:
    """Kullanıcının ürettiği tüm CV-TR/EN-*.docx dosyalarını keşfeder."""
    result = {}
    for path in CV_DIR.glob("CV-*.docx"):
        language = "EN" if path.stem.upper().startswith("CV-EN-") else "TR"
        result[path.stem] = {"path": path, "language": language}
    return result

# Eş anlamlılar bilinçli olarak dar tutulur: olmayan beceriyi puana eklemez.
TERMS = {
    "python": (r"\bpython\b",), "sql": (r"\bsql\b",), "mysql": (r"\bmysql\b",),
    "postgresql": (r"\bpostgre(?:sql)?\b",), "sqlalchemy": (r"\bsqlalchemy\b",),
    "java": (r"\bjava\b",), "spring_boot": (r"\bspring\s*boot\b",),
    "git": (r"\bgit(?:hub)?\b",), "flutter": (r"\bflutter\b",), "dart": (r"\bdart\b",),
    "firebase": (r"\bfirebase\b",), "firestore": (r"\bfirestore\b",),
    "pandas": (r"\bpandas\b",), "numpy": (r"\bnumpy\b",), "xgboost": (r"\bxgboost\b",),
    "docker": (r"\bdocker\b",), "kubernetes": (r"\bkubernetes\b|\bk8s\b",),
    "aws": (r"\baws\b|amazon web services",), "kafka": (r"\bkafka\b",),
    "redis": (r"\bredis\b",), "rabbitmq": (r"\brabbitmq\b",),
    "csharp": (r"\bc#\b|\bcsharp\b|\.net",), "cpp": (r"\bc\+\+\b",),
    "opencv": (r"\bopencv\b",), "pytorch": (r"\bpytorch\b",), "react": (r"\breact\b",),
    "javascript": (r"\bjavascript\b|\btypescript\b",), "rest_api": (r"\brest(?:ful)?\b|\bapi\b",),
}


def digest(value: bytes | str) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def terms_in(text: str) -> set[str]:
    text = text.casefold()
    return {term for term, patterns in TERMS.items() if any(re.search(pattern, text, re.I) for pattern in patterns)}


PHONE_OR_CONTACT_PATTERN = re.compile(
    r"(\+?\d[\d\s\-()]{7,}\d)|"
    r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)|"
    r"(linkedin\.com[^\s]*)|(github\.com[^\s]*)",
    re.I,
)


def cv_body(path: Path) -> str:
    # Adres/iletişim bu hesap için gerekli değildir; profile de alınmaz.
    rows = []
    doc = Document(path)
    for idx, paragraph in enumerate(doc.paragraphs):
        row = paragraph.text.strip()
        if not row:
            continue
        if idx < 4 and (
            PHONE_OR_CONTACT_PATTERN.search(row)
            or any(kw in row.lower() for kw in ("türkiye", "turkey", "ilçe", "city", "country", "mah.", "cad.", "sok."))
        ):
            continue
        if PHONE_OR_CONTACT_PATTERN.search(row):
            continue
        rows.append(row)
    return "\n".join(rows)


def profiles() -> dict:
    old = load_json(PROFILES_FILE, {})
    result = {"cvs": {}}
    changed = False
    for name, spec in available_cvs().items():
        path = spec["path"]
        raw_hash = digest(path.read_bytes())
        cached = old.get("cvs", {}).get(name, {})
        if cached.get("file_hash") == raw_hash:
            result["cvs"][name] = cached
            continue
        body = cv_body(path)
        result["cvs"][name] = {"file_hash": raw_hash, "language": spec["language"], "terms": sorted(terms_in(body))}
        changed = True
    if changed or old != result:
        result["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_json(PROFILES_FILE, result)
    return result


def role_bonus(title: str, cv_terms: set[str]) -> int:
    title = title.casefold()
    if any(word in title for word in ("backend", "software", "yazılım", "developer", "engineer")) and {"python", "sql"} <= cv_terms:
        return 12
    if any(word in title for word in ("data", "veri")) and {"python", "pandas"} <= cv_terms:
        return 8
    return 0


def compute(job: dict) -> dict:
    """İlan metnini alır; erişilemezse kart bilgisiyle düşük güvenli puan üretir."""
    try:
        description = fetch_description(job["source_url"])
    except Exception:
        description = ""
    basis = "ilan metni" if len(description) >= 450 else "ilan kartı (tam metin alınamadı)"
    job_text = " ".join((job.get("title", ""), job.get("company", ""), job.get("location", ""), description))
    job_terms = terms_in(job_text)
    current_profiles = profiles()["cvs"]
    rows = []
    for name, profile in current_profiles.items():
        cv_terms = set(profile["terms"])
        matched = sorted(job_terms & cv_terms)
        missing = sorted(job_terms - cv_terms)
        # Terim yoksa unvan uyumu ile düşük güvenli bir başlangıç verir; şişirilmiş puan üretmez.
        coverage = len(matched) / len(job_terms) if job_terms else 0.0
        score = round(min(100, 20 + coverage * 63 + role_bonus(job.get("title", ""), cv_terms)))
        if basis != "ilan metni":
            score = min(score, 45)
        rows.append({"cv": name, "puan": score, "eslesen_terimler": matched, "eksik_terimler": missing, "dil": profile["language"]})
    return {"computed_at": datetime.now(timezone.utc).isoformat(), "basis": basis, "description_hash": digest(description), "rows": rows}


def get_or_compute(key: str, job: dict) -> dict:
    cache = load_json(SCORES_FILE, {})
    profile_hashes = {name: profile["file_hash"] for name, profile in profiles()["cvs"].items()}
    cached = cache.get(key)
    if cached and cached.get("profile_hashes") == profile_hashes:
        return cached
    result = compute(job)
    result["profile_hashes"] = profile_hashes
    cache[key] = result
    write_json(SCORES_FILE, cache)
    return result
