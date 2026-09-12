# Job Application System / İş Başvuru Sistemi

## English

A privacy-first local desktop app for collecting public job listings, tracking applications, and managing CV workflows on Windows. Job-search data stays on the user's device and application decisions remain fully manual.

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

1. Install Python 3.11+ and LibreOffice if you want to view DOCX files in the app. Linux and macOS are also supported: DOCX files open with LibreOffice when installed, or the OS default handler otherwise.
2. Set up a virtual environment and install dependencies: on Windows run `scripts\setup.bat`, on Linux/macOS run `./scripts/setup.sh`.
3. Start the app: `scripts\start.bat` (Windows) or `./scripts/start.sh` (Linux/macOS), or run `python main.py` directly.
4. The app creates the `data` folder locally. Copy `examples/profile.example.json` to `data/profile.json` and add only truthful, verified information.
5. Copy `examples/candidate-evidence.example.json` to `data/candidate-evidence.json` and add evidence for CV and job-review workflows.
6. Run `python main.py build-cv` to create base Turkish and English CVs.
7. On the first scan, the app creates a default source from saved preferences. You can later add your own sources in `data/job-sources.json`.
8. If you have data from an older Turkish-named version, it is migrated automatically on first launch (`job_app/migration.py`): file names and JSON keys move to the new schema with no data loss. You can also run it manually with `python main.py migrate`.

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
docs/AGENT-ONBOARDING.md    # AI onboarding instructions
data/                       # user data, gitignored
```

### AI agents

- **Core features without AI:** Job collection, deduplication, local filtering, local keyword-based ATS estimation, and CV tracking work without any model or CLI.
- **AI-assisted features:** Initial review, detailed review, and CV-to-job comparison use a connected AI CLI agent. The app scans PATH for supported agents — Hermes, Claude Code (`claude`), Codex CLI (`codex`), Antigravity (`agy`), Gemini CLI (`gemini`), Pi (`pi`), and Cursor Agent (`cursor-agent`) — and lists the ones it finds. Pick one under Settings > AI agent, optionally override its model names, and verify it with "Test selected agent"; or write a custom command with a `{prompt}` placeholder (e.g. `myagent run --text {prompt}`). If none is installed, AI buttons show a warning but the non-AI core is never blocked.
- **Guided profile setup:** The first-run popup's "Copy AI onboarding instructions" button copies `docs/AGENT-ONBOARDING.md` to the clipboard. Paste it into any AI agent (a CLI or a browser chat); it asks about target role, sector, and city, extracts details from an existing CV if you provide one, asks only about what's missing, and produces `data/profile.json` and `data/candidate-evidence.json`.

### Privacy and security

All user data lives under `data/` and is excluded by `.gitignore`: profile, settings, generated CVs, job history, and review results. Phone numbers, emails, addresses, photos, and local paths are excluded from AI comparison inputs. Job URLs are checked for HTTPS, allowed host, redirects, private-network destinations, and response-size limits.

See [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md) for release checks and [SECURITY.md](SECURITY.md) for technical security boundaries. Released under the [MIT License](LICENSE).

---

## Türkçe

Windows için yerel iş ilanı ve CV takip aracı. İlan taramalarını saklar, tekrar ilanları ayıklar, isteğe bağlı model değerlendirmesi yürütür ve hangi CV'nin hangi ilana seçildiğini yerelde kaydeder.

> Bu klasör yayın hazırlığı içindir; henüz yayımlanmış bir paket değildir. Gerçek CV, kişisel ilan geçmişi veya model oturumları bu klasöre konmaz.

### Şu an yaptığı işler

- Kullanıcı tetiklediğinde açık ilan kartlarını toplar ve daha önce görülenleri ayıklar.
- Tarihe, Haiku ön elemesine ve Sonnet kararına göre ilanları arayüzde filtreler.
- Katı, esnek ve çok esnek Sonnet değerlendirme modları sunar.
- Yerel CV dosyalarındaki teknik terimleri ilan metniyle karşılaştırır. Bu puan şirket ATS sonucu değildir.
- İlanın dili için TR/EN CV seçimini ve başvuru kararını yerelde saklar.

### Yapmadığı işler

- Otomatik başvuru yapmaz.
- E-posta hesabını izlemez veya başvuru göndermez.
- İşe alınma ya da ATS geçiş garantisi vermez.

### İlk kurulum

1. Python 3.11+ ve LibreOffice (DOCX görüntülemek için) kurun. Linux ve macOS da desteklenir: DOCX dosyaları kuruluysa LibreOffice, değilse işletim sisteminin varsayılan programıyla açılır.
2. Sanal ortamı kurup bağımlılıkları yüklemek için Windows'ta `scripts\setup.bat`, Linux/macOS'ta `./scripts/setup.sh` çalıştırın.
3. Uygulamayı başlatmak için Windows'ta `scripts\start.bat`, Linux/macOS'ta `./scripts/start.sh` çalıştırın; ya da doğrudan `python main.py` komutunu kullanın.
4. Uygulama `data` klasörünü yerelde oluşturur. `examples/profile.example.json` dosyasını `data/profile.json` olarak kopyalayın; yalnız gerçek ve doğrulanmış bilgilerinizi yazın.
5. `examples/candidate-evidence.example.json` dosyasını `data/candidate-evidence.json` olarak kopyalayın; değerlendirmede kullanılabilecek doğrulanmış kanıtları ekleyin.
6. `python main.py build-cv` ile temel TR/EN CV'leri oluşturun.
7. İlk taramada uygulama tercihlerinize göre varsayılan ilan kaynağını otomatik hazırlar. İsterseniz sonradan `data/job-sources.json` içinden kendi kaynaklarınızı ekleyebilirsiniz.
8. Eski Türkçe adlandırmalı bir sürümden veriniz varsa ilk açılışta otomatik taşınır (`job_app/migration.py`): dosya adları ve JSON anahtarları veri kaybı olmadan yeni şemaya geçer. İsterseniz `python main.py migrate` ile elle de çalıştırabilirsiniz.

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

#### Yapay zeka ajanları

- **Yapay zeka olmadan çekirdek:** İlan toplama, tekrar ayıklama, yerel filtreleme, anahtar kelime tabanlı yerel ATS puanı ve CV kayıt yönetimi hiçbir model veya CLI gerektirmeden tamamen yerel çalışır.
- **Yapay zeka destekli özellikler:** Ön eleme, detaylı eleme ve CV-ilan karşılaştırması bağlı bir yapay zeka CLI ajanı üzerinden çalışır. Uygulama PATH'i tarayıp desteklenen ajanları bulur — Hermes, Claude Code (`claude`), Codex CLI (`codex`), Antigravity (`agy`), Gemini CLI (`gemini`), Pi (`pi`) ve Cursor Agent (`cursor-agent`) — ve bulduklarını listeler. Ayarlar > Yapay zeka bölümünden birini seçin, isterseniz model adlarını geçersiz kılın ve "Seçili ajanı test et" ile doğrulayın; ya da `{prompt}` yer tutuculu kendi özel komutunuzu yazın (ör. `myagent run --text {prompt}`). Hiçbiri kurulu değilse yapay zeka düğmeleri uyarı gösterir ama çekirdek işlevler engellenmez.
- **Yönlendirmeli profil kurulumu:** İlk açılış pop-up'ındaki "Yapay zeka başlangıç yönergesini kopyala" düğmesi `docs/AGENT-ONBOARDING.md` içeriğini panoya kopyalar. Bunu herhangi bir yapay zeka ajanına (CLI veya tarayıcı sohbeti) yapıştırın; ajan hedef rol, sektör ve şehir gibi soruları sorar, mevcut bir CV verirseniz ondan bilgi çıkarır, yalnız eksikleri sorar ve sonunda `data/profile.json` ile `data/candidate-evidence.json` dosyalarını üretir.

### Gizlilik

Tüm kullanıcı verisi `data/` altında tutulur ve `.gitignore` içindedir: profil, ayarlar, üretilen CV'ler, ilan geçmişi ve değerlendirme kayıtları. Kişisel kimlik (telefon, e-posta, açık adres, fotoğraf/yol) verileri yapay zeka karşılaştırmalarına gönderilmez; CV gövdesinde yalnız tanınan mesleki bölümler kullanılır. İlan URL'leri HTTPS, izinli alan adı, yönlendirme ve yanıt boyutu kontrollerinden geçer. Bir yayın öncesinde `git status` ile kişisel verilerin izlenmediği ayrıca doğrulanmalıdır.

Yayın öncesi adımlar için [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md), teknik güvenlik sınırları için [SECURITY.md](SECURITY.md) dosyalarına bakın.

### Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
