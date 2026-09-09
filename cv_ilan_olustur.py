"""Sonnet eşleştirmesi doğrulanmış bir ilan için yerel CV dosyası oluşturur.

Kullanım: python cv_ilan_olustur.py <ilan_parmak_izi>
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from cv_olustur import build
from depolama import data_file, load_json, write_json

ROOT = Path(__file__).resolve().parent
MATCH_FILE = data_file("ilan-esleme-durumu.json")
DECISIONS_FILE = data_file("arayuz-cv-secimleri.json")


def safe_part(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9ÇĞİÖŞÜçğıöşü_-]+", "-", value).strip("-")
    return value[:42] or "ilan"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_key")
    args = parser.parse_args()
    if not MATCH_FILE.exists():
        raise SystemExit("Önce Sonnet eşleştirmesi yapılmalı.")
    match = load_json(MATCH_FILE, {}).get(args.job_key)
    if not match:
        raise SystemExit("Bu ilan için Sonnet eşleştirmesi bulunamadı.")
    if match.get("karar") == "başvurma":
        raise SystemExit("Sonnet bu ilan için başvurma kararı verdi; CV oluşturulmadı.")
    job = match.get("job", {})
    language = match.get("cv_dili", "TR")
    focus = match.get("cv_tipi", "genel")
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"CV-{language}-{safe_part(job.get('company', 'sirket'))}-{safe_part(job.get('title', 'pozisyon'))}-{stamp}.docx"
    output = build(language, focus, filename)
    decisions = load_json(DECISIONS_FILE, {})
    decisions[args.job_key] = {
        **decisions.get(args.job_key, {}),
        "cv": output.stem,
        "language": language,
        "generated_file": str(output),
        "generated_at": datetime.now().isoformat(),
        "match_summary": {key: match.get(key) for key in ("karar", "uyum_puani", "cv_tipi", "gerekce")},
    }
    write_json(DECISIONS_FILE, decisions)
    print(json.dumps({"created_file": str(output), "language": language, "focus": focus}, ensure_ascii=False))


if __name__ == "__main__":
    main()
