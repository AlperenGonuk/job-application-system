# Yayın öncesi kontrol listesi

- [x] Lisans seçildi ve `LICENSE` dosyası eklendi.
- [x] `data/`, gerçek CV'ler, profil, ekran görüntüsü ve API anahtarları Git'te izlenmiyor (`data/` gitignore'da; değişiklikler kişisel veri için tarandı).
- [x] `python -m unittest discover -s tests -v` Windows ve Linux'ta başarılı.
- [ ] `scripts\setup.bat` ve `scripts\start.bat` temiz bir Windows hesabında denendi.
- [x] `scripts/setup.sh` ve `scripts/start.sh` Linux'ta denendi (WSL Ubuntu 24.04, temiz kopya): eksik `python3-venv`/`python3-tk` uyarısı, yarım `.venv` onarımı, testler ve masaüstü arayüzünün WSLg'de açılması doğrulandı.
- [ ] macOS gerçek bir cihazda denendi. (Şimdilik yalnız statik denetim: platforma özel Tk çağrısı yok, DOCX `open` ile açılıyor.)
- [x] `job_app/migration.py`, eski Türkçe adlandırmalı veriyle denendi; dosya adları ve JSON anahtarları veri kaybı olmadan yeni şemaya taşındı.
- [x] Ön eleme en az iki farklı ajanla uçtan uca denendi (Antigravity, Codex).
- [ ] Detaylı eleme ve CV uyumu ikinci bir ajanla denendi. (Şimdilik yalnız Hermes ile uçtan uca doğrulandı.)
- [x] Yapay zeka başlangıç yönergesi örnek bir aday profiliyle Hermes'e verildi; üretilen `profile.json` ve `candidate-evidence.json` uygulamanın okuma fonksiyonlarından geçti, ardından detaylı eleme, CV üretimi, CV uyumu ve ilana özel CV uçtan uca çalıştı.
- [ ] `python scripts/build_exe.py` ile üretilen tek dosya .exe, temiz bir makinede çalıştırıldı.
- [x] README'deki kurulum adımları ve bilinen sınırlar güncel.
