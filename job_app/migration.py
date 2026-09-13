"""Türkçe adlı eski yerel verileri İngilizce şemaya taşır.

Uygulama açılışında bir kez çalışır ve şunları yapar:
1. Eski sürümlerde proje kökünde duran çalışma dosyalarını ``data/`` altına alır.
2. Türkçe dosya/klasör adlarını İngilizce karşılıklarıyla yeniden adlandırır.
3. JSON içeriğindeki Türkçe anahtar ve sabit değerleri İngilizceye çevirir.

Taşıma kayıpsızdır: hedef dosya zaten varsa eski dosyaya dokunulmaz ve işlem
atlanır. Tamamlandığında ``data/.migration-done`` işaretçisi yazılır.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from job_app.storage import DATA_DIR, ROOT, load_json, write_json

MARKER_FILE = DATA_DIR / ".migration-done"

# Eski ad -> yeni ad (dosyalar)
FILE_RENAMES = {
    "ayarlar.json": "settings.json",
    "profil.json": "profile.json",
    "aday-kanitlari.json": "candidate-evidence.json",
    "ilan-kayit-defteri.json": "job-registry.json",
    "ilan-kaynaklari.json": "job-sources.json",
    "ilan-on-eleme-durumu.json": "initial-review-state.json",
    "ilan-esleme-durumu.json": "detailed-review-state.json",
    "cv-uyum-durumu.json": "cv-match-state.json",
    "arayuz-cv-secimleri.json": "cv-selections.json",
    "cv-ats-profilleri.json": "ats-profiles.json",
    "cv-ats-puanlari.json": "ats-scores.json",
}

# Eski ad -> (yeni ad, dosya adı öneki eşlemesi)
DIRECTORY_RENAMES = {
    "tarama-gecmisi": ("scan-history", ("tarama-", "scan-")),
    "on-eleme-gecmisi": ("initial-review-history", ("on-eleme-", "initial-review-")),
    "esleme-gecmisi": ("detailed-review-history", ("sonnet-", "review-")),
    "cv-uyum-gecmisi": ("cv-match-history", ("cv-uyum-", "cv-match-")),
    "CV-Sürümleri": ("cv-versions", None),
}

# JSON anahtarları
KEY_RENAMES = {
    "etiket": "label",
    "sonnet": "needs_detail",
    "karar": "decision",
    "uyum_puani": "match_score",
    "cv_tipi": "cv_focus",
    "cv_dili": "cv_language",
    "gerekce": "reason",
    "kullanilacak_kanitlar": "evidence_used",
    "eksik_anahtarlar": "missing_requirements",
    "en_uygun_cv": "best_cv",
    "sonuclar": "results",
    "guclu_eslesmeler": "strong_matches",
    "not": "note",
    "puan": "score",
    "eslesen_terimler": "matched_terms",
    "eksik_terimler": "missing_terms",
    "dil": "language",
}

# Yeni anahtar -> o anahtarın altındaki sabit değerlerin çevirisi
VALUE_RENAMES = {
    "label": {"aday": "candidate", "belirsiz": "unclear", "kapsam_dışı": "out_of_scope"},
    "needs_detail": {"evet": True, "hayır": False},
    "decision": {"başvur": "apply", "manuel_incele": "review_manually", "başvurma": "skip"},
    "cv_focus": {"genel": "general"},
    "mode": {"kati": "strict", "esnek": "flexible", "cok_esnek": "very_flexible"},
    "detailed_review_mode": {"kati": "strict", "esnek": "flexible", "cok_esnek": "very_flexible"},
    "work_arrangements": {"ofis": "onsite", "hibrit": "hybrid", "uzaktan": "remote"},
}

# profil.json içindeki CV varyant adı
CV_VARIANT_RENAMES = {"genel": "general"}


def translate(value, *, parent_key: str = ""):
    """JSON ağacındaki Türkçe anahtar ve sabit değerleri İngilizceye çevirir."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            new_key = KEY_RENAMES.get(key, key)
            result[new_key] = translate(item, parent_key=new_key)
        return result
    if isinstance(value, list):
        return [translate(item, parent_key=parent_key) for item in value]
    if isinstance(value, str):
        return VALUE_RENAMES.get(parent_key, {}).get(value, value)
    return value


def translate_profile(profile: dict) -> dict:
    """profil.json içindeki 'genel' CV varyantını 'general' adına taşır."""
    variants = profile.get("cv_profiles")
    if not isinstance(variants, dict):
        return profile
    for language, entries in variants.items():
        if isinstance(entries, dict):
            variants[language] = {CV_VARIANT_RENAMES.get(name, name): body for name, body in entries.items()}
    return profile


def _move(source: Path, destination: Path) -> bool:
    """Kayıpsız taşır.

    Hedef zaten bir dosyaysa eski dosyaya dokunulmaz. Hedef bir klasörse
    (uygulama açılışta boş klasörleri oluşturabildiği için sık görülür)
    içerik tek tek taşınır ve yalnız adı çakışmayanlar aktarılır.
    """
    if not source.exists():
        return False
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return True
    if not (source.is_dir() and destination.is_dir()):
        return False
    moved_any = False
    for item in list(source.iterdir()):
        target = destination / item.name
        if not target.exists():
            shutil.move(str(item), str(target))
            moved_any = True
    if not any(source.iterdir()):
        source.rmdir()
    return moved_any


def _rewrite(path: Path) -> None:
    """Bir JSON dosyasının içeriğini yeni şemaya çevirir."""
    data = load_json(path, None)
    if data is None:
        return
    converted = translate(data)
    if path.name == "profile.json" and isinstance(converted, dict):
        converted = translate_profile(converted)
    if converted != data:
        write_json(path, converted)


def _normalized(path: Path | str) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _relocations() -> list[tuple[Path, Path, tuple[str, str] | None]]:
    """Taşınan klasörlerin eski konumları -> yeni konum eşlemesi.

    Klasörler hem proje kökünden hem de ``data/`` altındaki Türkçe addan
    ``data/<yeni ad>`` konumuna taşınır.
    """
    pairs = []
    for legacy_name, (new_name, prefix) in DIRECTORY_RENAMES.items():
        for old_base in (ROOT / legacy_name, DATA_DIR / legacy_name):
            pairs.append((old_base, DATA_DIR / new_name, prefix))
    return pairs


def relocated_path(stored: str) -> Path | None:
    """Eski bir klasörü gösteren kayıtlı yolun taşıma sonrası karşılığı.

    Yalnız şu koşulların hepsi sağlanırsa yeni yol döner; aksi halde None:
    - yol taşınan eski klasörlerden birinin içindedir,
    - eski dosya artık yoktur (çakışma nedeniyle yerinde kaldıysa dokunulmaz),
    - yeni yol hedef klasörün içinde kalır ve dosya gerçekten oradadır.
    """
    if not stored:
        return None
    absolute = os.path.abspath(stored)
    for old_base, new_base, prefix in _relocations():
        base = os.path.abspath(str(old_base))
        if not _normalized(absolute).startswith(_normalized(base) + os.sep):
            continue
        parts = list(Path(absolute[len(base) + 1:]).parts)
        if not parts or Path(absolute).exists():
            return None
        if prefix and len(parts) == 1 and parts[0].startswith(prefix[0]):
            parts[0] = prefix[1] + parts[0][len(prefix[0]):]
        candidate = new_base.joinpath(*parts)
        if not _normalized(candidate).startswith(_normalized(new_base) + os.sep):
            return None
        return candidate if candidate.is_file() else None
    return None


def update_path_references() -> int:
    """cv-selections.json içindeki üretilmiş CV yollarını yeni konuma çevirir."""
    path = DATA_DIR / "cv-selections.json"
    data = load_json(path, None)
    if not isinstance(data, dict):
        return 0
    updated = 0
    for entry in data.values():
        if not isinstance(entry, dict) or not isinstance(entry.get("generated_file"), str):
            continue
        new_path = relocated_path(entry["generated_file"])
        if new_path is not None:
            entry["generated_file"] = str(new_path)
            updated += 1
    if updated:
        write_json(path, data)
    return updated


def run(*, force: bool = False) -> dict:
    """Taşımayı yürütür ve neyin taşındığını özetler."""
    if MARKER_FILE.exists() and not force:
        # Önceki bir taşıma CV'leri taşıyıp kayıtlı yolları eski konumda
        # bırakmış olabilir. Tam taşıma yeniden çalışmaz; yalnız bu yollar
        # onarılır. İşlem idempotenttir: onarılacak kayıt yoksa dosya yazılmaz.
        return {"skipped": True, "path_references": update_path_references()}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    moved_files, moved_dirs = [], []

    # 1) Eski sürümlerde kökte kalmış çalışma dosyaları data/ altına alınır.
    for legacy_name in (*FILE_RENAMES, *DIRECTORY_RENAMES):
        if _move(ROOT / legacy_name, DATA_DIR / legacy_name):
            moved_files.append(legacy_name)

    # 2) Dosya adları İngilizceye çevrilir.
    for legacy_name, new_name in FILE_RENAMES.items():
        if _move(DATA_DIR / legacy_name, DATA_DIR / new_name):
            moved_files.append(f"{legacy_name} -> {new_name}")

    # 3) Klasör adları ve içindeki dosya adları çevrilir.
    for legacy_name, (new_name, prefix) in DIRECTORY_RENAMES.items():
        if _move(DATA_DIR / legacy_name, DATA_DIR / new_name):
            moved_dirs.append(f"{legacy_name} -> {new_name}")
        target = DATA_DIR / new_name
        if prefix and target.is_dir():
            old_prefix, new_prefix = prefix
            for item in target.glob(f"{old_prefix}*"):
                _move(item, target / (new_prefix + item.name[len(old_prefix):]))

    # 4) JSON içerikleri yeni şemaya çevrilir.
    rewritten = 0
    for path in DATA_DIR.rglob("*.json"):
        if path.name.startswith("."):
            continue
        _rewrite(path)
        rewritten += 1

    # 5) Kayıtlı dosya yolları taşınan klasörlerin yeni konumuna çevrilir.
    path_references = update_path_references()

    MARKER_FILE.write_text(json.dumps({"files": moved_files, "directories": moved_dirs}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"skipped": False, "files": moved_files, "directories": moved_dirs, "rewritten": rewritten, "path_references": path_references}


def main() -> None:
    """Taşımayı zorla yeniden çalıştırır ve özetini yazar."""
    print(json.dumps(run(force=True), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
