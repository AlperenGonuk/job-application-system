"""Detaylı elemeden geçmiş bir ilan için yerel CV dosyası oluşturur.

Kullanım: python main.py cv-for-job <ilan_parmak_izi>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from job_app.cv_document import build_cv
from job_app.storage import data_file, load_json, write_json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

MATCH_FILE = data_file("detailed-review-state.json")
DECISIONS_FILE = data_file("cv-selections.json")


def safe_part(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9ÇĞİÖŞÜçğıöşü_-]+", "-", value).strip("-")
    return value[:42] or "job"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_key")
    args = parser.parse_args()
    if not MATCH_FILE.exists():
        raise SystemExit("Önce detaylı eleme yapılmalı.")
    match = load_json(MATCH_FILE, {}).get(args.job_key)
    if not match:
        raise SystemExit("Bu ilan için detaylı eleme sonucu bulunamadı.")
    if match.get("decision") == "skip":
        raise SystemExit("Detaylı eleme bu ilan için başvurma kararı verdi; CV oluşturulmadı.")
    job = match.get("job", {})
    language = match.get("cv_language", "TR")
    focus = match.get("cv_focus", "general")
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"CV-{language}-{safe_part(job.get('company', 'company'))}-{safe_part(job.get('title', 'position'))}-{stamp}.docx"
    output = build_cv(language, focus, filename)
    decisions = load_json(DECISIONS_FILE, {})
    decisions[args.job_key] = {
        **decisions.get(args.job_key, {}),
        "cv": output.stem,
        "language": language,
        "generated_file": str(output),
        "generated_at": datetime.now().isoformat(),
        "match_summary": {key: match.get(key) for key in ("decision", "match_score", "cv_focus", "reason")},
    }
    write_json(DECISIONS_FILE, decisions)
    print(json.dumps({"created_file": str(output), "language": language, "focus": focus}, ensure_ascii=False))


if __name__ == "__main__":
    main()
