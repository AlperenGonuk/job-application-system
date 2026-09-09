# Güvenlik notları

Bu araç yerel kullanıma yöneliktir. Otomatik başvuru, e-posta okuma veya hesaplara giriş yapmaz.

## Veri sınırları

- Kullanıcı profili, CV'ler, tarama geçmişi ve yapay zeka sonuçları yalnız `data/` altında tutulur; bu klasör Git tarafından yok sayılır.
- Yapay zeka değerlendirmelerine telefon, e-posta, açık adres, fotoğraf ve yerel dosya yolu gönderilmez.
- İş ilanı metni yalnız HTTPS kullanan izinli kaynaklardan, yönlendirme ve boyut sınırlarıyla alınır.

## Güvenli kullanım

- `data/` klasörünü, `.env` dosyalarını veya gerçek CV'leri bir depoya eklemeyin.
- Yapay zeka modelinin ürettiği kararları öneri kabul edin; başvurmadan önce ilanı ve CV'yi kendiniz kontrol edin.
- İlan metnindeki talimatlar güvenilmeyen veri kabul edilir; uygulama onları komut olarak çalıştırmaz.

## Güvenlik bildirimi

Hassas bilgi içeren ekran görüntüsü, CV veya anahtarları herkese açık issue alanına koymayın. Yayın sahibi, depo açıldığında özel bir bildirim kanalı tanımlamalıdır.
