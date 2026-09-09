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

1. Install Python 3.11+ and LibreOffice if you want to view DOCX files in the app.
2. On Windows, run `kurulum.bat` once, then run `baslat.bat`.
3. The app creates the `data` folder locally. Copy `profil.ornek.json` to `data/profil.json` and add only truthful, verified information.
4. Copy `aday-kanitlari.ornek.json` to `data/aday-kanitlari.json` and add evidence for CV and job-review workflows.
5. Run `python cv_olustur.py` to create base Turkish and English CVs.
6. On the first scan, the app creates a default source from saved preferences. You can later add your own sources in `data/ilan-kaynaklari.json`.
7. Run `python is_basvuru_arayuzu.py` to start the desktop app.

### AI features and Hermes CLI

- **Core features without AI:** Job collection, deduplication, local filtering, local keyword-based ATS estimation, and CV tracking work without a model or CLI.
- **AI-assisted features:** Initial review, detailed review, and current-CV comparison use the `hermes` CLI. Install Hermes and configure a supported model account to use them. If Hermes is unavailable, the app explains this without blocking non-AI features.

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

1. Python 3.11+ ve LibreOffice (DOCX görüntülemek için) kurun.
2. Windows'ta `kurulum.bat` dosyasını bir kez, ardından `baslat.bat` dosyasını çalıştırın. İsterseniz eşdeğer komutla sanal ortam oluşturup `pip install -r requirements.txt` de kullanabilirsiniz.
3. `data` klasörü oluşturun. `profil.ornek.json` dosyasını `data/profil.json` olarak kopyalayın; yalnız gerçek ve doğrulanmış bilgilerinizi yazın.
4. `aday-kanitlari.ornek.json` dosyasını `data/aday-kanitlari.json` olarak kopyalayın; değerlendirmede kullanılabilecek doğrulanmış kanıtları ekleyin.
5. `python cv_olustur.py` ile temel TR/EN CV'leri oluşturun.
6. İlk taramada uygulama tercihlerinize göre varsayılan ilan kaynağını otomatik hazırlar. İsterseniz sonradan `data/ilan-kaynaklari.json` içinden kendi kaynaklarınızı ekleyebilirsiniz.
7. `python is_basvuru_arayuzu.py` ile uygulamayı başlatın.

#### Yapay zeka özellikleri ve Hermes CLI bağımlılığı

- **Yapay zeka olmadan çekirdek:** İlan toplama, tekrar ayıklama, yerel filtreleme, anahtar kelime tabanlı yerel ATS puanı ve CV kayıt yönetimi hiçbir model veya CLI gerektirmeden tamamen yerel çalışır.
- **Yapay zeka değerlendirmesi:** Arayüzdeki "Ön eleme", "Detaylı eleme" ve "Mevcut CV'lerle uyumu incele" özellikleri `hermes` CLI üzerinden çalışır. Bu işlevleri kullanabilmek için sisteminizde `hermes` CLI aracının ve ilgili model erişiminin kurulu olması gerekir. Hermes CLI kurulu değilse arayüz bilgilendirici uyarı gösterir ve çekirdek işlevleri engellemez.

### Gizlilik

Tüm kullanıcı verisi `data/` altında tutulur ve `.gitignore` içindedir: profil, ayarlar, üretilen CV'ler, ilan geçmişi ve değerlendirme kayıtları. Kişisel kimlik (telefon, e-posta, açık adres, fotoğraf/yol) verileri yapay zeka karşılaştırmalarına gönderilmez; CV gövdesinde yalnız tanınan mesleki bölümler kullanılır. İlan URL'leri HTTPS, izinli alan adı, yönlendirme ve yanıt boyutu kontrollerinden geçer. Bir yayın öncesinde `git status` ile kişisel verilerin izlenmediği ayrıca doğrulanmalıdır.

Yayın öncesi adımlar için [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md), teknik güvenlik sınırları için [SECURITY.md](SECURITY.md) dosyalarına bakın.

### Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
