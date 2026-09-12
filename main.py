"""İş Başvuru Sistemi giriş noktası.

Argümansız çağrıldığında masaüstü arayüzünü açar. Bir görev adıyla çağrıldığında
yalnız o görevi çalıştırır; arayüz uzun süren işleri bu yolla ayrı süreçte
başlatır. Tek dosya .exe olarak paketlendiğinde uygulama kendi kendini görev
adıyla yeniden çağırabilir.

Kullanım:
    python main.py                          # masaüstü arayüzü
    python main.py collect                  # yeni ilanları topla
    python main.py initial-review --limit 5 # ön eleme
    python main.py detailed-review --mode flexible
    python main.py cv-match <ilan_parmak_izi>
    python main.py cv-for-job <ilan_parmak_izi>
    python main.py build-cv                 # temel TR/EN CV'leri üret
    python main.py migrate                  # eski Türkçe veriyi yeniden taşı
"""
from __future__ import annotations

import importlib
import os
import sys

TASKS = {
    "collect": "job_app.collect_jobs",
    "initial-review": "job_app.review_initial",
    "detailed-review": "job_app.review_detailed",
    "cv-match": "job_app.cv_match",
    "cv-for-job": "job_app.cv_for_job",
    "build-cv": "job_app.cv_document",
    "dedupe": "job_app.dedupe",
    "migrate": "job_app.migration",
}


def _ensure_streams() -> None:
    """Konsolsuz çalışmada eksik çıktı akışlarını onarır.

    Uygulama pencere göstermeden (pythonw veya paketlenmiş sürüm) açıldığında
    ``sys.stdout`` boş olabilir. Alt görevler sonuçlarını standart çıktıya
    yazdığı için önce gerçek tanıtıcıyı bağlamayı dener, olmazsa çıktıyı yutar.
    """
    for name, descriptor in (("stdout", 1), ("stderr", 2)):
        if getattr(sys, name, None) is not None:
            continue
        try:
            stream = os.fdopen(os.dup(descriptor), "w", encoding="utf-8", errors="replace")
        except OSError:
            stream = open(os.devnull, "w", encoding="utf-8")
        setattr(sys, name, stream)


def _report_crash(error: BaseException) -> None:
    """Beklenmeyen hatayı data/app.log dosyasına yazar.

    Uygulama konsol penceresi olmadan açıldığında hata mesajı hiçbir yerde
    görünmez; bu dosya tek kayıt noktasıdır.
    """
    import traceback

    from job_app.storage import DATA_DIR

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        report = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        (DATA_DIR / "app.log").write_text(report, encoding="utf-8")
    except OSError:
        pass


def main() -> None:
    _ensure_streams()
    from job_app import migration

    task = sys.argv[1] if len(sys.argv) > 1 else ""
    if task != "migrate":
        # Taşıma bir kez çalışır; "migrate" görevi zaten kendisi zorla çalıştırır.
        migration.run()
    if not task:
        from job_app.ui_app import Application

        try:
            Application().mainloop()
        except BaseException as error:  # konsolsuz açılışta hata kaybolmasın
            _report_crash(error)
            raise
        return
    if task not in TASKS:
        raise SystemExit(f"Bilinmeyen görev: {task}\nGeçerli görevler: {', '.join(TASKS)}")
    module = importlib.import_module(TASKS[task])
    sys.argv = [task, *sys.argv[2:]]
    module.main()


if __name__ == "__main__":
    main()
