# İş Başvuru Sistemi

Windows için yerel iş ilanı ve CV takip aracı. İlan taramalarını saklar, tekrar ilanları ayıklar, isteğe bağlı model değerlendirmesi yürütür ve hangi CV'nin hangi ilana seçildiğini yerelde kaydeder.

> Bu klasör yayın hazırlığı içindir; henüz yayımlanmış bir paket değildir. Gerçek CV, kişisel ilan geçmişi veya model oturumları bu klasöre konmaz.

## Şu an yaptığı işler

- Kullanıcı tetiklediğinde açık ilan kartlarını toplar ve daha önce görülenleri ayıklar.
- Tarihe, Haiku ön elemesine ve Sonnet kararına göre ilanları arayüzde filtreler.
- Katı, esnek ve çok esnek Sonnet değerlendirme modları sunar.
- Yerel CV dosyalarındaki teknik terimleri ilan metniyle karşılaştırır. Bu puan şirket ATS sonucu değildir.
- İlanın dili için TR/EN CV seçimini ve başvuru kararını yerelde saklar.

## Yapmadığı işler

- Otomatik başvuru yapmaz.
- E-posta hesabını izlemez veya başvuru göndermez.
- İşe alınma ya da ATS geçiş garantisi vermez.

## İlk kurulum

1. Python 3.11+ ve LibreOffice (DOCX görüntülemek için) kurun.
2. Windows'ta `kurulum.bat` dosyasını bir kez, ardından `baslat.bat` dosyasını çalıştırın. İsterseniz eşdeğer komutla sanal ortam oluşturup `pip install -r requirements.txt` de kullanabilirsiniz.
3. `data` klasörü oluşturun. `profil.ornek.json` dosyasını `data/profil.json` olarak kopyalayın; yalnız gerçek ve doğrulanmış bilgilerinizi yazın.
4. `aday-kanitlari.ornek.json` dosyasını `data/aday-kanitlari.json` olarak kopyalayın; değerlendirmede kullanılabilecek doğrulanmış kanıtları ekleyin.
5. `python cv_olustur.py` ile temel TR/EN CV'leri oluşturun.
6. İlk taramada uygulama tercihlerinize göre varsayılan ilan kaynağını otomatik hazırlar. İsterseniz sonradan `data/ilan-kaynaklari.json` içinden kendi kaynaklarınızı ekleyebilirsiniz.
7. `python is_basvuru_arayuzu.py` ile uygulamayı başlatın.

### Yapay zeka özellikleri ve Hermes CLI bağımlılığı

- **Yapay zeka olmadan çekirdek:** İlan toplama, tekrar ayıklama, yerel filtreleme, anahtar kelime tabanlı yerel ATS puanı ve CV kayıt yönetimi hiçbir model veya CLI gerektirmeden tamamen yerel çalışır.
- **Yapay zeka değerlendirmesi:** Arayüzdeki "Ön eleme", "Detaylı eleme" ve "Mevcut CV'lerle uyumu incele" özellikleri `hermes` CLI üzerinden çalışır. Bu işlevleri kullanabilmek için sisteminizde `hermes` CLI aracının ve ilgili model erişiminin kurulu olması gerekir. Hermes CLI kurulu değilse arayüz bilgilendirici uyarı gösterir ve çekirdek işlevleri engellemez.

## Gizlilik

Tüm kullanıcı verisi `data/` altında tutulur ve `.gitignore` içindedir: profil, ayarlar, üretilen CV'ler, ilan geçmişi ve değerlendirme kayıtları. Kişisel kimlik (telefon, e-posta, açık adres, fotoğraf/yol) verileri yapay zeka karşılaştırmalarına gönderilmez; CV gövdesinde yalnız tanınan mesleki bölümler kullanılır. İlan URL'leri HTTPS, izinli alan adı, yönlendirme ve yanıt boyutu kontrollerinden geçer. Bir yayın öncesinde `git status` ile kişisel verilerin izlenmediği ayrıca doğrulanmalıdır.

Yayın öncesi adımlar için [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md), teknik güvenlik sınırları için [SECURITY.md](SECURITY.md) dosyalarına bakın.

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
