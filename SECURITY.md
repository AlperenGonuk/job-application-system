# Security Notes / Güvenlik Notları

## English

This tool is designed for local use. It does not apply to jobs automatically, read email, or log in to external accounts.

### Data boundaries

- User profiles, CVs, scan history, and AI results are stored only under `data/`; Git ignores this folder.
- Known identity fields (name, phone, email, address, photo, ID number) are removed from AI-review inputs. Free text and URL query/fragment parameters are masked for phone numbers, email addresses, ID numbers, street addresses, photos, and local file paths. This masking is pattern-based and best effort; it is not a guarantee that unusually formatted personal data is caught.
- Prompts are never passed through a shell. On Windows, a prompt that would have to go through a `.cmd`/`.bat` file as an argument is sent to the underlying program of a standard npm shim instead; if that cannot be resolved, the call is refused rather than truncated.
- Job descriptions are fetched only from allowed HTTPS sources with redirect and response-size limits.

### Safe use

- Never add the `data/` folder, `.env` files, or real CVs to a repository.
- Treat AI-generated decisions as suggestions. Review the job post and CV yourself before applying.
- Instructions embedded in job descriptions are untrusted data; the application never executes them as commands.

### Reporting a security issue

Do not post screenshots, CVs, or keys containing sensitive information in public issues. Until a private reporting channel is configured, contact the repository owner privately through their GitHub profile.

---

## Türkçe

Bu araç yerel kullanıma yöneliktir. Otomatik başvuru, e-posta okuma veya hesaplara giriş yapmaz.

### Veri sınırları

- Kullanıcı profili, CV'ler, tarama geçmişi ve yapay zekâ sonuçları yalnız `data/` altında tutulur; Git bu klasörü yok sayar.
- Bilinen kimlik alanları (ad, telefon, e-posta, adres, fotoğraf, kimlik no) yapay zekâ değerlendirme girdilerinden çıkarılır. Serbest metin ve bağlantı sorgu/parça parametrelerinde telefon, e-posta, kimlik numarası, açık adres, fotoğraf ve yerel dosya yolu maskelenir. Bu maskeleme desen tabanlıdır ve en iyi çaba ilkesiyle çalışır; alışılmadık biçimde yazılmış kişisel verinin yakalanacağını garanti etmez.
- İstemler hiçbir zaman kabuk üzerinden geçirilmez. Windows'ta `.cmd`/`.bat` dosyasına argüman olarak gitmesi gereken istem, standart npm kısayolunun çağırdığı gerçek programa gönderilir; bu çözülemezse istem kırpılmak yerine çağrı reddedilir.
- İş ilanı metni yalnız HTTPS kullanan izinli kaynaklardan, yönlendirme ve yanıt boyutu sınırlarıyla alınır.

### Güvenli kullanım

- `data/` klasörünü, `.env` dosyalarını veya gerçek CV'leri bir depoya eklemeyin.
- Yapay zekâ modelinin ürettiği kararları öneri kabul edin; başvurmadan önce ilanı ve CV'yi kendiniz kontrol edin.
- İlan metnindeki talimatlar güvenilmeyen veri kabul edilir; uygulama onları komut olarak çalıştırmaz.

### Güvenlik bildirimi

Hassas bilgi içeren ekran görüntüsü, CV veya anahtarları herkese açık issue alanına koymayın. Özel bildirim kanalı yapılandırılana kadar depo sahibiyle GitHub profili üzerinden özel olarak iletişime geçin.
