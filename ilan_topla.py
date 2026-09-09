"""İş Başvuru Sistemi: manuel çalıştırılan, yerel ilan toplayıcı.

Kullanım:
    python ilan_topla.py

Her kaynak herkese açık ilan kartlarını çeker, başlık/konum ön filtresi yapar,
önce aynı koşudaki sonra kalıcı kayıt defterindeki tekrarları ayıklar. Model
çağırmaz ve başvuru yapmaz.
"""
from __future__ import annotations

import html
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from ilan_tekrar_ayikla import fingerprint
from ayarlar import load_settings
from depolama import data_dir, data_file, load_json, write_json
from url_dogrula import safe_fetch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
SOURCES_FILE = data_file("ilan-kaynaklari.json")
SOURCES_TEMPLATE = ROOT / "ilan-kaynaklari.ornek.json"
REGISTRY_FILE = data_file("ilan-kayit-defteri.json")
HISTORY_DIR = data_dir("tarama-gecmisi")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def one(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.I | re.S)
    return clean(match.group(1)) if match else ""


COUNTRY_ALIASES = {
    "türkiye": ("türkiye", "turkey"), "united states": ("united states", "usa", "u.s."),
    "united kingdom": ("united kingdom", "uk", "great britain"), "south korea": ("south korea", "korea"),
    "united arab emirates": ("united arab emirates", "uae"), "czechia": ("czechia", "czech republic"),
}
COUNTRY_QUERY_NAMES = {"türkiye": "Turkey", "united states": "United States", "united kingdom": "United Kingdom"}
CITY_ALIASES = {
    "istanbul": ("istanbul", "i̇stanbul", "sarıyer", "ataşehir", "pendik", "beşiktaş", "kadıköy", "üsküdar", "şişli", "bakırköy", "eyüpsultan"),
    "ankara": ("ankara", "çankaya", "keçiören", "yenimahalle", "etlik", "gölbaşı"),
    "izmir": ("izmir", "i̇zmir", "bornova", "konak", "karşıyaka", "bayraklı"),
}
UNRESTRICTED_COUNTRIES = {"tüm dünya", "tüm ülkeler", "worldwide", "all countries"}
UNRESTRICTED_CITIES = {"tüm türkiye", "all cities", "all cities in türkiye"}


def preference_mismatches(job: dict, settings: dict) -> list[str]:
    """Kartta açıkça görünen çelişkileri döndürür; eksik kart bilgisi ilanı gizlemez."""
    title = job.get("title", "").casefold()
    location = job.get("location", "").casefold()
    roles = [value.casefold() for value in settings.get("target_roles", []) if value.strip()]
    countries = [value.casefold() for value in settings.get("target_countries", []) if value.strip()]
    cities = [value.casefold() for value in settings.get("target_cities", []) if value.strip()]
    seniority = [value.casefold() for value in settings.get("seniority", []) if value.strip()]
    work_arrangements = {value.casefold() for value in settings.get("work_arrangements", []) if value.strip()}
    is_remote = any(word in location for word in ("remote", "uzaktan", "hybrid", "hibrit"))
    is_hybrid = any(word in location for word in ("hybrid", "hibrit"))
    mismatches: list[str] = []
    ignored = {"junior", "entry", "level", "intern", "internship", "stajyer", "staj", "new", "grad", "graduate", "part", "time"}
    token_aliases = {"engineering": "engineer", "engineer": "engineer", "developer": "develop", "development": "develop", "analyst": "analys", "analytics": "analys", "accounting": "account", "accountant": "account"}
    categories = {
        "technology": {"software", "engineer", "develop", "backend", "frontend", "devops", "cloud", "cyber", "qa", "test"},
        "data": {"data", "analys", "machine", "learning"},
        "finance": {"finance", "financial", "account", "bank", "audit"},
        "business": {"business", "sales", "marketing", "customer", "product"},
        "operations": {"operation", "supply", "chain", "logistics", "project"},
        "research": {"research", "scientist"}, "legal": {"legal", "law"}, "hr": {"human", "resource", "recruit"},
    }
    def normalized_terms(value: str) -> set[str]:
        return {token_aliases.get(term, term) for term in re.findall(r"[\wçğıöşü]+", value.casefold()) if len(term) >= 3 and term not in ignored}
    def role_matches(role: str) -> bool:
        terms, title_terms = normalized_terms(role), normalized_terms(title)
        if not terms:
            return True
        if terms & title_terms or any(term in title for term in terms):
            return True
        return any(terms & members and title_terms & members for members in categories.values())
    if roles and not any(role_matches(role) for role in roles):
        mismatches.append("role")
    country_match = lambda country: any(alias in location for alias in COUNTRY_ALIASES.get(country, (country,)))
    if countries and not is_remote and not any(country in UNRESTRICTED_COUNTRIES for country in countries):
        known_country = any(alias in location for aliases in COUNTRY_ALIASES.values() for alias in aliases)
        if known_country and not any(country_match(country) for country in countries):
            mismatches.append("country")
    if cities and not is_remote and not any(city in UNRESTRICTED_CITIES for city in cities):
        city_matches = lambda city: any(alias in location for alias in CITY_ALIASES.get(city, (city,)))
        # Konumda şehir/ilçe bilgisi varsa ancak o zaman filtrele; boş/eksik kartlar korunur.
        known_city = any(alias in location for aliases in CITY_ALIASES.values() for alias in aliases)
        if known_city and not any(city_matches(city) for city in cities):
            mismatches.append("city")
    if work_arrangements:
        job_arrangement = "hibrit" if is_hybrid else "uzaktan" if is_remote else "ofis"
        if job_arrangement not in work_arrangements:
            mismatches.append("work_arrangement")
    # Kıdem bilgisi ilanda görünmüyorsa yanlış negatif üretmeyiz; yalnız açık çelişkiyi eleyiz.
    experienced = ("senior", "sr.", "lead", "manager", "director", "principal", "staff", "mid-level", "kıdemli")
    if seniority and any(word in title for word in experienced):
        if not any(level in title for level in seniority):
            mismatches.append("seniority")
    return mismatches


def matches_preferences(job: dict, settings: dict) -> bool:
    """Geriye uyumlu kısa yol: kartta açık bir tercih çelişkisi yoksa True."""
    return not preference_mismatches(job, settings)


def linkedin_cards(source: dict) -> list[dict]:
    document = safe_fetch(source["url"])
    blocks = re.findall(r'<div class="[^">]*base-search-card[^">]*".*?</li>', document, flags=re.I | re.S)
    cards = []
    for block in blocks:
        title = one(r'base-search-card__title[^>]*>(.*?)</h3>', block)
        company = one(r'base-search-card__subtitle[^>]*>.*?<a[^>]*>(.*?)</a>', block)
        location = one(r'job-search-card__location[^>]*>(.*?)</span>', block)
        url = one(r'base-card__full-link[^>]*href="([^"]+)"', block).replace("&amp;", "&")
        posted = one(r'<time[^>]*datetime="([^"]+)"', block)
        if not title or not company or not url:
            continue
        cards.append({"company": company, "title": title, "location": location, "source_url": url, "published_at": posted, "source": source["name"]})
    return cards


def load_source_config() -> dict:
    """İlk kullanımda örnek kaynak ayarını üretir, sonraki çalışmalarda yalnız yerel dosyayı okur."""
    if not SOURCES_FILE.exists():
        if not SOURCES_TEMPLATE.exists():
            raise SystemExit("İlan kaynak şablonu bulunamadı. Uygulamayı yeniden kurmayı deneyin.")
        template = load_json(SOURCES_TEMPLATE, None)
        if not isinstance(template, dict) or not isinstance(template.get("sources"), list):
            raise SystemExit("İlan kaynak şablonu geçersiz. Uygulamayı yeniden kurmayı deneyin.")
        write_json(SOURCES_FILE, template)
    config = load_json(SOURCES_FILE, None)
    if not isinstance(config, dict) or not isinstance(config.get("sources"), list):
        raise SystemExit("İlan kaynak ayarı geçersiz. data/ilan-kaynaklari.json dosyasını kontrol edin.")
    return config


def is_legacy_example_source(source: dict) -> bool:
    """Eski ilk-kurulum örneğini, kullanıcı dosyasını değiştirmeden dinamikleştirir."""
    return source.get("name") == "LinkedIn örnek arama" and "Junior%20Backend%20Developer" in source.get("url", "")


def preference_sources(config: dict, settings: dict) -> list[dict]:
    """Uygulama tarafından yönetilen kaynakları kaydedilmiş tercihlere göre üretir.

    Kullanıcının kendi URL'si asla değiştirilmez; yalnız örnek/managed kaynaklar üretilir.
    """
    sources = config.get("sources", [])
    managed = [source for source in sources if isinstance(source, dict) and (source.get("mode") == "preferences" or is_legacy_example_source(source))]
    manual = [source for source in sources if isinstance(source, dict) and source not in managed]
    if not managed:
        return manual
    roles = [value for value in settings.get("target_roles", []) if isinstance(value, str) and value.strip()]
    query_roles = roles[:8] or ["Internship OR Junior OR Entry Level"]
    countries = [value for value in settings.get("target_countries", []) if isinstance(value, str) and value.casefold() not in UNRESTRICTED_COUNTRIES]
    cities = [value for value in settings.get("target_cities", []) if isinstance(value, str) and value.casefold() not in UNRESTRICTED_CITIES]
    place = cities[0] if cities else countries[0] if countries else ""
    if countries and cities:
        place = f"{cities[0]}, {COUNTRY_QUERY_NAMES.get(countries[0].casefold(), countries[0])}"
    generated = []
    for role in query_roles:
        params = "keywords=" + quote(role, safe="")
        if place:
            params += "&location=" + quote(place, safe="")
        generated.append({"name": f"LinkedIn: {role}" + (f" — {place}" if place else ""), "url": f"https://www.linkedin.com/jobs/search?{params}", "managed": True})
    return generated + manual


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild-from-history", action="store_true", help="Geçmiş tarama dosyalarından kayıt defterini doğru URL anahtarlarıyla yeniden kurar")
    args = parser.parse_args()
    if args.rebuild_from_history:
        rebuilt = {}
        for history_file in sorted(HISTORY_DIR.glob("tarama-*.json")):
            history = load_json(history_file, {})
            for job in history.get("new_jobs", []):
                key = fingerprint(job)
                old = rebuilt.get(key, {})
                rebuilt[key] = {
                    "first_seen": old.get("first_seen", history.get("ran_at")),
                    "last_seen": history.get("ran_at"),
                    "company": job.get("company"),
                    "title": job.get("title"),
                }
        write_json(REGISTRY_FILE, rebuilt)
        print(json.dumps({"rebuilt_registry_entries": len(rebuilt)}, ensure_ascii=False))
        return

    config = load_source_config()
    max_raw = int(config.get("max_raw_cards", 150))
    settings = load_settings()
    fetched, failures, source_stats, mismatch_counts = [], [], [], {}
    resolved_sources = preference_sources(config, settings)
    if not resolved_sources:
        failures.append({"source": "İlan kaynak ayarı", "error": "Etkin kaynak yok. Ayarlardaki ilan-kaynaklari.json dosyasına en az bir kaynak ekleyin."})
    for source in resolved_sources:
        try:
            cards = linkedin_cards(source)
            accepted = []
            for job in cards:
                mismatches = preference_mismatches(job, settings)
                if not mismatches:
                    accepted.append(job)
                else:
                    for reason in mismatches:
                        mismatch_counts[reason] = mismatch_counts.get(reason, 0) + 1
            fetched.extend(accepted)
            source_stats.append({"source": source.get("name", "Bilinmeyen kaynak"), "downloaded_cards": len(cards), "preference_matched": len(accepted), "filtered_out": len(cards) - len(accepted)})
        except Exception as error:  # kaynak hatası diğer kaynakları durdurmamalı
            failures.append({"source": source.get("name", "Bilinmeyen kaynak"), "error": str(error)})
    fetched = fetched[:max_raw]

    registry = load_json(REGISTRY_FILE, {})
    batch_keys: set[str] = set()
    new_jobs, duplicate_in_batch, previously_seen = [], 0, 0
    timestamp = datetime.now(timezone.utc).isoformat()
    for job in fetched:
        # Kimlik zaman damgasına değil, ilanın değişmeyen parmak izine bağlıdır.
        job["id"] = fingerprint(job)
        key = fingerprint(job)
        if key in batch_keys:
            duplicate_in_batch += 1
            continue
        batch_keys.add(key)
        if key in registry:
            registry[key]["last_seen"] = timestamp
            previously_seen += 1
            continue
        registry[key] = {"first_seen": timestamp, "last_seen": timestamp, "company": job["company"], "title": job["title"]}
        new_jobs.append(job)

    write_json(REGISTRY_FILE, registry)
    history_file = HISTORY_DIR / f"tarama-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    downloaded_cards = sum(item["downloaded_cards"] for item in source_stats)
    result = {"ran_at": timestamp, "scan_date": datetime.now().astimezone().date().isoformat(), "downloaded_cards": downloaded_cards, "preference_matched": len(fetched), "filtered_out": downloaded_cards - len(fetched), "filter_reasons": mismatch_counts, "source_stats": source_stats, "unique_in_batch": len(batch_keys), "new_jobs": new_jobs, "duplicate_in_batch": duplicate_in_batch, "previously_seen": previously_seen, "source_failures": failures}
    write_json(history_file, result)
    print(json.dumps({**{key: result[key] for key in ("downloaded_cards", "preference_matched", "filtered_out", "filter_reasons", "unique_in_batch", "duplicate_in_batch", "previously_seen", "source_failures")}, "new": len(new_jobs), "history_file": str(history_file)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
