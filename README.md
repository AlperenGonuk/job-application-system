# Job Application System / İş Başvuru Sistemi

## English

A privacy-first local desktop app for collecting public job listings, tracking applications, and managing CV workflows on Windows, Linux, and macOS. Job-search data stays on the user's device and application decisions remain fully manual.

> This is the public release source. Do not add real CVs, personal job history, model sessions, API keys, or screenshots containing personal information.

### What it does

- Collects public job cards only when the user starts a scan, and removes previously seen listings.
- Creates default LinkedIn searches from saved role and location preferences; users can add their own sources later.
- Explains zero-result scans: no cards received, filtered by preferences, previously seen, or source failure.
- Filters jobs by scan date and optional initial or detailed AI-review results.
- Offers strict, flexible, and very flexible detailed-review modes for connected AI models.
- Compares verified technical terms in local CV files with a job description. This is a local estimate, not an employer ATS result.
- Tracks the selected Turkish or English CV and manual application decision for each listing.

### What it does not do

- It does not apply to jobs automatically.
- It does not monitor email or send applications.
- It does not guarantee an interview, employment, or ATS outcome.

### Quick start

1. Install Python 3.11+. LibreOffice is optional, for viewing DOCX files inside the app (otherwise the OS default handler opens them).
2. Install dependencies: `scripts\setup.bat` on Windows, `./scripts/setup.sh` on Linux/macOS (or `bash scripts/setup.sh`). On Linux the desktop UI also needs the system packages for virtual environments and Tkinter, which many distributions leave out — `setup.sh` checks both and prints the exact command, e.g. `sudo apt install python3-venv python3-tk` on Ubuntu/Debian. On macOS, the python.org installer already includes Tkinter; with Homebrew Python run `brew install python-tk`.
3. Start the app: `scripts\start.bat` on Windows, `./scripts/start.sh` on Linux/macOS, or `python main.py`.
4. **Create your profile with your own AI agent.** In the first-run window (or **How to use**), press **Copy AI onboarding instruction** and paste it into the AI agent you already use — Hermes, Claude Code, Codex, Antigravity, or a browser chat. Give it your CV if you have one; it reads that first and only asks what is missing. Agents that can write files create `data/profile.json` and `data/candidate-evidence.json` themselves (and may fill your job preferences into `data/settings.json`); a browser chat prints both files for you to save.
5. **Read both files once.** The instruction forbids invented experience, but models can still overstate — for example calling you a graduate before you graduate, or adding a tool you never named. Correct anything that is not true; the AI reviews trust these files.
6. In the app, open **Settings**: check your job preferences, choose your AI agent, and press **Test selected agent**.
7. Run **Collect new jobs → Initial review → Detailed review**. Base TR/EN CVs can be generated with `python main.py build-cv`; all CVs land in `data/cv-versions/`.

Prefer to do it by hand? Copy `examples/profile.example.json` to `data/profile.json` and `examples/candidate-evidence.example.json` to `data/candidate-evidence.json`, then fill in only truthful information. Detailed review stops with a clear message until `data/candidate-evidence.json` exists.

On the first scan the app creates a default job source from your preferences; you can add your own in `data/job-sources.json`. Data from an older Turkish-named version is migrated automatically on first launch (`python main.py migrate` runs it manually).

#### Command-line tasks

Besides the desktop UI (`python main.py`), individual steps can run standalone:

```
python main.py collect
python main.py initial-review --limit 5
python main.py detailed-review --mode flexible
python main.py cv-match <job_fingerprint>
python main.py cv-for-job <job_fingerprint>
python main.py build-cv
python main.py migrate
```

A single-file executable can be built with `python scripts/build_exe.py` (requires PyInstaller). Tests: `python -m unittest discover -s tests`.

### Project layout

```
main.py                    # entry point: desktop UI or a single task
job_app/
  storage.py                # local data read/write layer
  settings.py                # app settings
  privacy.py                  # strips PII before AI calls
  url_guard.py                 # job URL validation
  dedupe.py                     # removes previously seen listings
  collect_jobs.py                # public job-card collection
  ai_agents.py                    # AI CLI agent registry & detection
  ai_runner.py                     # sends prompts to the selected agent
  review_initial.py                 # initial AI review
  review_detailed.py                 # detailed AI review
  cv_match.py                         # CV-to-job comparison
  ats_score.py                         # local keyword-based ATS estimate
  cv_document.py                        # base TR/EN CV generation
  cv_for_job.py                          # per-job CV generation
  ui_app.py                               # desktop UI
  migration.py                             # one-time legacy data migration
scripts/                    # setup.bat/.sh, start.bat/.sh, build_exe.py
examples/                   # *.example.json templates
docs/AGENT-ONBOARDING.md    # AI onboarding instruction
data/                       # user data, gitignored
```

### AI agents

- **Core features without AI:** Job collection, deduplication, local filtering, local keyword-based ATS estimation, and CV tracking work without any model or CLI.
- **AI-assisted features:** Initial review, detailed review, and CV-to-job comparison use a connected AI CLI agent. The app scans PATH for Hermes, Claude Code (`claude`), Codex CLI (`codex`), Antigravity (`agy`), Gemini CLI (`gemini`), Pi (`pi`), and Cursor Agent (`cursor-agent`). Pick one under Settings > AI agent, optionally override its model names, and verify it with **Test selected agent** — or write a custom command with a `{prompt}` placeholder (e.g. `myagent run --text {prompt}`). If none is installed, AI buttons show a warning but the non-AI core is never blocked.
- **Hermes and providers:** The app calls Hermes with `--provider anthropic` and Claude models by default, regardless of Hermes' own default provider. If your Hermes uses another provider (Gemini, OpenRouter, …), set `"ai_provider"` in `data/settings.json` and put matching model names in Settings.
- **Codex desktop app:** The Codex desktop app ships its own `codex.exe` but does not add it to PATH, so it is not detected automatically. Install Codex CLI, or use a custom command pointing at that `codex.exe` with `exec {prompt}`.

Verified agent/model pairs are listed in `docs/AGENT-ONBOARDING.md`. Leaving model fields empty is always safe: the agent's own default model is used.

### Privacy and security

All user data lives under `data/` and is excluded by `.gitignore`: profile, settings, generated CVs, job history, and review results. Known identity fields (name, phone, email, address, photo, ID number) are removed from AI inputs, only recognized career sections of a CV are used, and free text plus URL parameters are scrubbed with pattern-based masking for phone numbers, emails, ID numbers, street addresses, photos, and local paths. Pattern-based masking is best effort and can miss unusually formatted personal data, so keep personal details out of free-text fields. Job URLs are checked for HTTPS, allowed host, redirects, private-network destinations, and response-size limits.

See [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md) for release checks and [SECURITY.md](SECURITY.md) for technical security boundaries. Released under the [MIT License](LICENSE).

---

## Türkçe

Windows, Linux ve macOS için yerel iş ilanı ve CV takip aracı. Açık ilanları toplar, tekrar eden ilanları ayıklar, isteğe bağlı yapay zeka değerlendirmesi yürütür ve hangi CV'nin hangi ilana seçildiğini yerelde kaydeder. İş arama verisi bilgisayarında kalır, başvuru kararları tamamen sende.

> Bu depo herkese açık yayın kaynağıdır. Gerçek CV, kişisel ilan geçmişi, model oturumları, API anahtarı veya kişisel bilgi içeren ekran görüntüsü eklenmez.

### Şu an yaptığı işler

- Kullanıcı tetiklediğinde açık ilan kartlarını toplar ve daha önce görülenleri ayıklar.
- Kayıtlı rol ve konum tercihlerinden varsayılan LinkedIn aramalarını oluşturur; sonradan kendi kaynaklarını ekleyebilirsin.
- İlanları tarama tarihine, ön eleme ve detaylı eleme sonuçlarına göre filtreler.
- Detaylı eleme için katı, esnek ve çok esnek değerlendirme modları sunar.
- Yerel CV dosyalarındaki teknik terimleri ilan metniyle karşılaştırır. Bu puan şirket ATS sonucu değildir.
- Her ilan için seçilen TR/EN CV'yi ve başvuru kararını yerelde saklar.

### Yapmadığı işler

- Otomatik başvuru yapmaz.
- E-posta hesabını izlemez veya başvuru göndermez.
- İşe alınma ya da ATS geçiş garantisi vermez.

### İlk kurulum

1. Python 3.11+ kur. LibreOffice isteğe bağlıdır; DOCX dosyalarını uygulama içinden görmek için gerekir (yoksa işletim sisteminin varsayılan programı açar).
2. Bağımlılıkları kur: Windows'ta `scripts\setup.bat`, Linux/macOS'ta `./scripts/setup.sh` (ya da `bash scripts/setup.sh`). Linux'ta masaüstü arayüzü için sanal ortam ve Tkinter sistem paketleri de gerekir; birçok dağıtım bunları kurmaz. `setup.sh` ikisini de kontrol eder ve gereken komutu yazar, örneğin Ubuntu/Debian'da `sudo apt install python3-venv python3-tk`. macOS'ta python.org yükleyicisi Tkinter'i içerir; Homebrew Python kullanıyorsan `brew install python-tk` çalıştır.
3. Uygulamayı başlat: Windows'ta `scripts\start.bat`, Linux/macOS'ta `./scripts/start.sh` ya da doğrudan `python main.py`.
4. **Profilini kendi yapay zeka ajanınla oluştur.** İlk açılış penceresinde (veya **Nasıl kullanılır?** bölümünde) **Yapay zeka başlangıç yönergesini kopyala** düğmesine bas ve metni zaten kullandığın ajana yapıştır — Hermes, Claude Code, Codex, Antigravity ya da tarayıcıdaki bir sohbet. CV'n varsa ver; önce onu okur, yalnız eksikleri sorar. Dosya yazabilen ajanlar `data/profile.json` ve `data/candidate-evidence.json` dosyalarını kendisi oluşturur (iş tercihlerini `data/settings.json` içine de işleyebilir); tarayıcı sohbeti iki dosyayı ekrana yazar, sen kaydedersin.
5. **İki dosyayı bir kez oku.** Yönerge olmayan deneyimi yazmayı yasaklar ama modeller yine de abartabilir — örneğin mezun olmadan "mezun" yazmak ya da hiç söylemediğin bir aracı eklemek. Doğru olmayan her şeyi düzelt; yapay zeka değerlendirmeleri bu dosyalara güvenir.
6. Uygulamada **Ayarlar**'ı aç: iş tercihlerini kontrol et, yapay zeka ajanını seç ve **Seçili ajanı test et** düğmesine bas.
7. **Yeni ilanları topla → Ön eleme → Detaylı eleme** sırasıyla çalıştır. Temel TR/EN CV'ler `python main.py build-cv` ile üretilir; tüm CV'ler `data/cv-versions/` klasörüne düşer.

Elle yapmak istersen `examples/profile.example.json` dosyasını `data/profile.json`, `examples/candidate-evidence.example.json` dosyasını `data/candidate-evidence.json` olarak kopyala ve yalnız doğru bilgileri yaz. `data/candidate-evidence.json` oluşana kadar detaylı eleme net bir uyarıyla durur.

İlk taramada uygulama tercihlerine göre varsayılan ilan kaynağını hazırlar; kendi kaynaklarını `data/job-sources.json` içine ekleyebilirsin. Eski Türkçe adlandırmalı bir sürümden kalan veri ilk açılışta otomatik taşınır (`python main.py migrate` ile elle de çalışır).

#### Komut satırı görevleri

Masaüstü arayüzü (`python main.py`) dışında adımlar tek başına da çalıştırılabilir:

```
python main.py collect
python main.py initial-review --limit 5
python main.py detailed-review --mode flexible
python main.py cv-match <ilan_parmak_izi>
python main.py cv-for-job <ilan_parmak_izi>
python main.py build-cv
python main.py migrate
```

Tek dosya .exe için `python scripts/build_exe.py` (PyInstaller gerekir). Testler: `python -m unittest discover -s tests`.

### Proje yapısı

```
main.py                    # giriş noktası: masaüstü arayüzü ya da tek bir görev
job_app/
  storage.py                # yerel veri okuma/yazma katmanı
  settings.py                # uygulama ayarları
  privacy.py                  # yapay zekaya gitmeden önce PII temizler
  url_guard.py                 # ilan URL doğrulaması
  dedupe.py                     # daha önce görülen ilanları ayıklar
  collect_jobs.py                # açık ilan kartı toplama
  ai_agents.py                    # yapay zeka CLI ajan kaydı ve tespiti
  ai_runner.py                     # istemi seçili ajana gönderir
  review_initial.py                 # ön eleme (yapay zeka)
  review_detailed.py                 # detaylı eleme (yapay zeka)
  cv_match.py                         # CV-ilan karşılaştırması
  ats_score.py                         # anahtar kelime tabanlı yerel ATS puanı
  cv_document.py                        # temel TR/EN CV üretimi
  cv_for_job.py                          # ilana özel CV üretimi
  ui_app.py                               # masaüstü arayüzü
  migration.py                             # eski veriyi tek seferlik taşıma
scripts/                    # setup.bat/.sh, start.bat/.sh, build_exe.py
examples/                   # *.example.json şablonları
docs/AGENT-ONBOARDING.md    # yapay zeka başlangıç yönergesi
data/                       # kullanıcı verisi, gitignore'da
```

### Yapay zeka ajanları

- **Yapay zeka olmadan çekirdek:** İlan toplama, tekrar ayıklama, yerel filtreleme, anahtar kelime tabanlı yerel ATS puanı ve CV kayıt yönetimi hiçbir model veya CLI gerektirmeden çalışır.
- **Yapay zeka destekli özellikler:** Ön eleme, detaylı eleme ve CV-ilan karşılaştırması bağlı bir yapay zeka CLI ajanı kullanır. Uygulama PATH'te Hermes, Claude Code (`claude`), Codex CLI (`codex`), Antigravity (`agy`), Gemini CLI (`gemini`), Pi (`pi`) ve Cursor Agent (`cursor-agent`) arar. Ayarlar > Yapay zeka bölümünden birini seç, istersen model adlarını değiştir ve **Seçili ajanı test et** ile doğrula — ya da `{prompt}` yer tutuculu kendi komutunu yaz (ör. `myagent run --text {prompt}`). Hiçbiri kurulu değilse yapay zeka düğmeleri uyarı gösterir ama çekirdek işlevler engellenmez.
- **Hermes ve sağlayıcılar:** Uygulama Hermes'i, Hermes'in kendi varsayılan sağlayıcısından bağımsız olarak `--provider anthropic` ve Claude modelleriyle çağırır. Hermes'in başka bir sağlayıcı kullanıyorsa (Gemini, OpenRouter, …) `data/settings.json` içinde `"ai_provider"` alanını ayarla ve Ayarlar'a o sağlayıcının model adlarını yaz.
- **Codex masaüstü uygulaması:** Codex masaüstü uygulaması kendi `codex.exe` dosyasıyla gelir ama PATH'e eklemez, bu yüzden otomatik bulunmaz. Codex CLI kur ya da o `codex.exe` yolunu `exec {prompt}` ile özel komut olarak yaz.

Doğrulanmış ajan/model eşleşmeleri `docs/AGENT-ONBOARDING.md` içinde. Model alanlarını boş bırakmak her zaman güvenlidir: ajanın kendi varsayılan modeli kullanılır.

### Gizlilik

Tüm kullanıcı verisi `data/` altında tutulur ve `.gitignore` içindedir: profil, ayarlar, üretilen CV'ler, ilan geçmişi ve değerlendirme kayıtları. Bilinen kimlik alanları (ad, telefon, e-posta, adres, fotoğraf, kimlik no) yapay zeka girdilerinden çıkarılır; CV gövdesinde yalnız tanınan mesleki bölümler kullanılır. Serbest metin ve bağlantı parametrelerindeki telefon, e-posta, kimlik numarası, açık adres, fotoğraf ve yerel yol desenleri maskelenir. Desen tabanlı maskeleme en iyi çaba ilkesiyle çalışır ve alışılmadık biçimde yazılmış kişisel bilgiyi kaçırabilir; serbest metin alanlarına kişisel bilgi yazma. İlan URL'leri HTTPS, izinli alan adı, yönlendirme, özel ağ hedefi ve yanıt boyutu kontrollerinden geçer.

Yayın öncesi adımlar için [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md), teknik güvenlik sınırları için [SECURITY.md](SECURITY.md) dosyalarına bak.

### Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
