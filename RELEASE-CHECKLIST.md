# Yayın öncesi kontrol listesi

- [x] Lisans seçildi ve `LICENSE` dosyası eklendi.
- [x] `data/`, gerçek CV'ler, profil, ekran görüntüsü ve API anahtarları Git'te izlenmiyor (`data/` gitignore'da; değişiklikler kişisel veri için tarandı).
- [x] `python -m unittest discover -s tests -v` başarılı.
- [x] Yapay zeka başlangıç yönergesi gerçek bir kullanıcı verisiyle Hermes'e verildi; üretilen `profile.json` ve `candidate-evidence.json` uygulamanın okuma fonksiyonlarından geçti, ardından detaylı eleme, CV üretimi, CV uyumu ve ilana özel CV uçtan uca çalıştı.
- [ ] `scripts\setup.bat` ve `scripts\start.bat` temiz bir Windows hesabında denendi.
- [x] `scripts/setup.sh` ve `scripts/start.sh` Linux'ta denendi (WSL Ubuntu 24.04, GitHub'dan temiz klon): eksik `python3-venv`/`python3-tk` uyarısı, yarım `.venv` onarımı, testler ve masaüstü arayüzünün WSLg'de açılması doğrulandı.
- [ ] macOS'ta gerçek cihazda denenmedi; yalnız statik denetim yapıldı (platforma özel Tk çağrısı yok, DOCX `open` ile açılıyor).
- [ ] `job_app/migration.py`, eski Türkçe adlandırmalı gerçek veriyle denendi; dosya adları ve JSON anahtarları veri kaybı olmadan yeni şemaya taşınıyor.
- [ ] Yapay zeka düğmeleri (ön eleme, detaylı eleme, CV uyumu) en az iki farklı ajanla denendi (ör. Claude Code ve bir başka desteklenen CLI).
- [ ] `python scripts/build_exe.py` ile üretilen tek dosya .exe, temiz bir makinede çalıştırıldı.
- [ ] README'deki kurulum ve sınırlamalar güncel.
- [ ] GitHub/LinkedIn duyurusu için metin, ayrı onayla hazırlanacak; bu kontrol listesi paylaşım yapmaz.
