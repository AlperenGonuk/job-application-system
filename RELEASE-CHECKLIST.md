# Yayın öncesi kontrol listesi

- [x] Lisans seçildi ve `LICENSE` dosyası eklendi.
- [ ] `data/`, gerçek CV'ler, profil, ekran görüntüsü ve API anahtarları kaynak klasöründe yok.
- [ ] `python -m unittest discover -s tests -v` başarılı.
- [ ] `scripts\setup.bat` ve `scripts\start.bat` temiz bir Windows hesabında denendi.
- [ ] `scripts/setup.sh` ve `scripts/start.sh` Linux/macOS üzerinde denendi.
- [ ] `job_app/migration.py`, eski Türkçe adlandırmalı gerçek veriyle denendi; dosya adları ve JSON anahtarları veri kaybı olmadan yeni şemaya taşınıyor.
- [ ] Yapay zeka düğmeleri (ön eleme, detaylı eleme, CV uyumu) en az iki farklı ajanla denendi (ör. Claude Code ve bir başka desteklenen CLI).
- [ ] `python scripts/build_exe.py` ile üretilen tek dosya .exe, temiz bir makinede çalıştırıldı.
- [ ] README'deki kurulum ve sınırlamalar güncel.
- [ ] GitHub/LinkedIn duyurusu için metin, ayrı onayla hazırlanacak; bu kontrol listesi paylaşım yapmaz.
