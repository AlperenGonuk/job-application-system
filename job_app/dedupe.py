"""İş Başvuru Sistemi için yerel tekrar ilan ayıklama aracıdır.

Kullanım:
python ilan_tekrar_ayikla.py yeni-ilanlar.json ilan-kayit-defteri.json
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gh_src", "trk",
    "position", "pagenum", "refid", "trackingid", "currentjobid",
}


def text_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")


def canonical_url(value: str | None) -> str:
    if not value:
        return ""
    parts = urlsplit(value)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_KEYS]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(sorted(query)), ""))


def fingerprint(job: dict) -> str:
    url = canonical_url(job.get("source_url"))
    if url:
        return f"url:{url}"
    return "fallback:" + "|".join(text_key(job.get(k)) for k in ("company", "title", "location"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("registry", type=Path)
    args = parser.parse_args()

    incoming = json.loads(args.input.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8")) if args.registry.exists() else {}
    batch_keys: set[str] = set()
    new_jobs, repeated_in_batch, seen_before = [], [], []
    now = datetime.now(timezone.utc).isoformat()

    for job in incoming:
        key = fingerprint(job)
        if key in batch_keys:
            repeated_in_batch.append(job["id"])
            continue
        batch_keys.add(key)
        if key in registry:
            registry[key]["last_seen"] = now
            seen_before.append(job["id"])
            continue
        registry[key] = {"first_seen": now, "last_seen": now, "company": job.get("company"), "title": job.get("title")}
        new_jobs.append(job)

    args.registry.parent.mkdir(parents=True, exist_ok=True)
    args.registry.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"raw": len(incoming), "unique_in_batch": len(batch_keys), "new": len(new_jobs), "duplicate_in_batch": len(repeated_in_batch), "previously_seen": len(seen_before), "new_jobs": new_jobs}, ensure_ascii=False))


if __name__ == "__main__":
    main()
