# Geliştirme durumu — İngilizceleştirme ve çoklu ajan çalışması

> Bu dosya yarım kalan çalışmayı başka bir oturumda devralmak içindir.
> **Yeni oturumda önce bu dosyayı oku.** Son güncelleme: 14 Eylül 2026.

## Durum özeti

| | |
|---|---|
| Dal | `feature/english-naming-and-multi-agent` → `main`'e birleştirildi |
| Commit | Commit'lendi ve GitHub'a gönderildi |
| Testler | 49/49 geçiyor (`python -m unittest discover -s tests`) |
| Arayüz | Açılıyor, Ayarlar penceresi dahil doğrulandı |
| Uçtan uca | Ön eleme Antigravity (`agy`) ile gerçek veriyle koştu |

## Neden bu çalışma yapıldı

Kullanıcının kararları (bu oturumda açıkça soruldu ve yanıtlandı):

1. **İngilizceleştirme kapsamı:** Her şey — dosya adları, sınıf/değişken adları, JSON anahtarları, sabit değerler ve `data/` dosya adları. Eski veriyi taşıyan otomatik migration yazılacak.
2. **Ajan entegrasyonu:** Otomatik tespit + Ayarlar'dan seçim + `{prompt}` yer tutuculu özel komut.
3. **Açılış pop-up'ı:** Kopyalanan yönerge, herhangi bir AI'ya verilince kullanıcıya sektör/rol gibi soruları sorsun; **kullanıcı CV'sini verirse ondan bilgileri çıkarsın** ve yalnız eksikleri sorsun.
4. **Dağıtım:** Düzeltilmiş `.bat` + net README, tek dosya `.exe` (PyInstaller), Linux/macOS desteği. (pip paketi istenmedi.)

Sonradan eklenen üç istek:

5. Ajan başına **önerilen modeller**, görev tipine göre (ön eleme / detaylı eleme).
6. Çalışma sırasında **konsol penceresi görünmesin** — kullanıcılar virüs sanabiliyor.
7. Özel komut desteğinin istemi uzatmadığı doğrulandı (uzatmıyor).

## Değişmeyen kural

Kullanıcının açık talimatı: **"sistemin temel mantığını bozmamaya dikkat et, çalışma şekli aynı kalsın."**

Buna uyularak:

- Dosyalar **1:1** eşlendi; modül bölme/birleştirme yapılmadı.
- **İstem (prompt) metinleri Türkçe bırakıldı**; yalnız içlerindeki şema anahtarları İngilizceye çevrildi. Böylece modelin karar davranışı ve `reason` alanının dili aynı kaldı.
- Eşik değerleri, kuyruk sırası, filtreler, kilit süreleri, kota hatası davranışı aynen korundu.
- Açıklamalar ve docstring'ler Türkçe kaldı (kullanıcı isteği).

## Dosya eşlemesi

| Eski | Yeni |
|---|---|
| `depolama.py` | `job_app/storage.py` |
| `ayarlar.py` | `job_app/settings.py` |
| `pii_temizle.py` | `job_app/privacy.py` |
| `url_dogrula.py` | `job_app/url_guard.py` |
| `ilan_tekrar_ayikla.py` | `job_app/dedupe.py` |
| `ilan_topla.py` | `job_app/collect_jobs.py` |
| `hermes_adapter.py` | `job_app/ai_runner.py` |
| `ilan_haiku_on_ele.py` | `job_app/review_initial.py` |
| `ilan_sonnet_esle.py` | `job_app/review_detailed.py` |
| `cv_uyum_incele.py` | `job_app/cv_match.py` |
| `cv_ats.py` | `job_app/ats_score.py` |
| `cv_olustur.py` | `job_app/cv_document.py` |
| `cv_ilan_olustur.py` | `job_app/cv_for_job.py` |
| `is_basvuru_arayuzu.py` | `job_app/ui_app.py` |
| `AI-ONBOARDING-SKILL.md` | `docs/AGENT-ONBOARDING.md` |
| `profil.ornek.json` | `examples/profile.example.json` |
| `aday-kanitlari.ornek.json` | `examples/candidate-evidence.example.json` |
| `ilan-kaynaklari.ornek.json` | `examples/job-sources.example.json` |
| `kurulum.bat` / `baslat.bat` | `scripts/setup.bat` / `scripts/start.bat` |

Yeni dosyalar: `main.py`, `job_app/__init__.py`, `job_app/ai_agents.py`, `job_app/migration.py`, `job_app/process.py`, `scripts/setup.sh`, `scripts/start.sh`, `scripts/start-console.bat`, `scripts/build_exe.py`.

## Şema değişiklikleri

JSON anahtarları: `etiket→label`, `sonnet→needs_detail` (artık **boolean**), `karar→decision`, `uyum_puani→match_score`, `cv_tipi→cv_focus`, `cv_dili→cv_language`, `gerekce→reason`, `kullanilacak_kanitlar→evidence_used`, `eksik_anahtarlar→missing_requirements`, `en_uygun_cv→best_cv`, `sonuclar→results`, `guclu_eslesmeler→strong_matches`, `not→note`, `puan→score`, `eslesen_terimler→matched_terms`, `eksik_terimler→missing_terms`, `dil→language`.

Sabit değerler: `aday→candidate`, `belirsiz→unclear`, `kapsam_dışı→out_of_scope`, `başvur→apply`, `manuel_incele→review_manually`, `başvurma→skip`, `kati→strict`, `esnek→flexible`, `cok_esnek→very_flexible`, `ofis→onsite`, `hibrit→hybrid`, `uzaktan→remote`, `genel→general`.

`data/` dosya adları: `settings.json`, `profile.json`, `candidate-evidence.json`, `job-registry.json`, `job-sources.json`, `initial-review-state.json`, `detailed-review-state.json`, `cv-match-state.json`, `cv-selections.json`, `ats-profiles.json`, `ats-scores.json`, `scan-history/`, `initial-review-history/`, `detailed-review-history/`, `cv-match-history/`, `cv-versions/`.

Taşıma `job_app/migration.py` ile uygulama açılışında bir kez otomatik çalışır, `data/.migration-done` işaretçisi bırakır. Kullanıcının gerçek verisiyle denendi: 8 ilan ve tüm tarama geçmişi kayıpsız taşındı.

## Çoklu ajan katmanı

- `job_app/ai_agents.py` — ajan profilleri (`hermes`, `claude`, `codex`, `agy`, `gemini`, `pi`, `cursor-agent`), PATH tespiti, komut kurma, önerilen modeller.
- `job_app/ai_runner.py` — kilit, PII temizliği, zaman aşımı, boş yanıt hatası. Eski `hermes_run` yerine `run_agent(prompt, task="fast"|"deep", model_override=..., settings=...)`.
- İstem her ajan için **aynıdır**; fark yalnız komut satırındadır. `prompt_mode` `"arg"` veya `"stdin"`.
- Ayarlar > Yapay zeka: ajan seçimi, iki model alanı (fast/deep), "Önerilen modelleri uygula", "Seçili ajanı test et", `{prompt}` yer tutuculu özel komut alanı.

Önerilen modeller (`RECOMMENDED_MODELS`) — yalnız öneridir, alanlar boşsa ajanın kendi varsayılanı gider:

| Ajan | fast | deep |
|---|---|---|
| Hermes | `claude-haiku-4-5-20251001` | `claude-sonnet-4-6` |
| Claude Code | `haiku` | `sonnet` |
| Codex CLI | `gpt-5.6-luna` | `gpt-5.5` |
| Antigravity | `gemini-3.8-flash-medium` | `gemini-3.1-pro-high` |

Gemini CLI, Pi ve Cursor için doğrulanmış ad **bilinçli olarak yazılmadı** (uydurma model adı yazılmayacak). Arayüz o ajanlarda genel kuralı ve `pi --list-models` gibi listeleme komutunu gösterir.

## Yol boyunca çözülen üç tuzak

1. **Toplu yeniden adlandırma kendi tablosunu bozdu.** `job_app/*.py` üzerinde çalışan toplu dosya-adı çevirisi, `migration.py`'nin kendi eşleme tablosunu da çevirdi (`"ilan-kayit-defteri.json"` → `"job-registry.json"`), tablo kendi kendini gösterir hale geldi ve migration hiçbir şey taşımadı. Elle düzeltildi. **Benzer bir toplu değişiklik yapılacaksa `migration.py` hariç tutulmalı.**
2. **Kodlama ajanları başsız modda boş dönüyor.** `agy`, istemdeki ilan bağlantısını görünce araç çağırmaya kalktı, izin isteyemediği için boş çıktı verdi. Çözüm: `ai_runner.NO_TOOL_PREAMBLE` — her ajana aynı biçimde "araç kullanma, yalnız metne bak" diyen ~200 karakterlik ön ek. Ayrıca boş yanıt hatası artık ajanın `stderr` çıktısını da gösteriyor.
3. **PII temizleyici ilan URL'sini bozuyordu (eski, gizli hata).** LinkedIn ilan numarası 10 hanelidir; telefon deseni bunu yakalayıp `[TELEFON GİZLİ]` yapıyordu. Model doğru yanıt verse bile dönen `id` hiçbir ilanla eşleşmiyor, ön eleme **her zaman** şema hatası veriyordu. Bu hata refactor'dan önce de vardı. `privacy.py` artık bağlantıları geçici işaretçiyle koruyor; `has_pii` de aynı mantığı kullanıyor.

## Konsol penceresi gizleme

- `job_app/process.py` → `hidden_process_options()`; Windows'ta `CREATE_NO_WINDOW` + `SW_HIDE`. `ai_runner` ve `ui_app` (görev çalıştırma, CV açma) kullanıyor.
- `scripts/start.bat` artık `pythonw.exe` ile açıyor, konsol hiç görünmüyor.
- `scripts/start-console.bat` sorun giderme için konsollu başlatır.
- `main.py` içinde `_ensure_streams()` (konsolsuz modda çıktı akışı onarımı) ve `_report_crash()` (`data/app.log`).

## Yapılmayanlar / sıradaki adımlar

1. **Detaylı eleme kanıt dosyası olmadan erken durur.** `data/candidate-evidence.json` yoksa hiçbir ilan indirilmeden ve kaydedilmeden tek hatayla çıkar (önceden her ilan için ayrı hata veriyor, kısa metinli ilanları kanıtsız kaydedebiliyordu).
2. **`.exe` derlemesi denenmedi** — PyInstaller kurulu değil. `pip install pyinstaller && python scripts/build_exe.py`. Paketlenmiş sürümde alt görevler exe'yi kendi adıyla yeniden çağırır (`task_command()` içinde `sys.frozen` dalı); bu yol **henüz gerçek bir exe ile test edilmedi**.
3. **Detaylı eleme uçtan uca denenmedi** — `data/candidate-evidence.json` yok. Kullanıcı önce onboarding yönergesiyle profilini oluşturmalı.
4. **Linux/macOS script'leri denenmedi** (bu makine Windows).
5. `codex` 13 Eylül'de Codex masaüstü uygulamasının içindeki `codex.exe` ile canlı doğrulandı (ön eleme şeması, `gpt-5.6-luna` / `gpt-5.5`); ancak masaüstü uygulaması PATH'e eklemediği için otomatik tespit edilmiyor. `cursor-agent` kurulu değil; profili canlı doğrulanmadı. `gemini` kurulu ama hesabı uygun değil (`IneligibleTierError`), `pi` eklenti hatası veriyor. Canlı doğrulananlar: **hermes, claude, agy**.
6. `SECURITY.md` gözden geçirildi, değişiklik gerekmedi.

## Gerçek kullanıcı verisiyle uçtan uca test (14 Eylül 2026)

Başlangıç yönergesi, kullanıcının kariyer notlarının kopyasıyla Hermes'e (`--provider anthropic -m claude-sonnet-4-6`, `chat --query-file --oneshot`) verildi. Kaynak vault'a yazılmadı (değiştirilme zamanlarıyla doğrulandı).

- Hermes `profile.json`, `candidate-evidence.json` yazdı ve `settings.json` içinde yalnız hedef alanlarını güncelledi; dosyalar `candidate_facts()`, `cv_focus_options()` ve `cv_document` okumasından geçti.
- Sonra sırasıyla çalıştı: detaylı eleme (4 ilan, 0 hata, 66 sn), `build-cv`, `cv-match` (20 sn), `cv-for-job`.
- **İçerik abartısı görüldü:** mezun olmamış kişiye "graduate", kaynakta olmayan "Git" ve "Firebase authentication", "171 testi yazdı" gibi sahiplik varsayımı, kullanıcının gereksiz dediği `data_analyst` varyantı. Yönergenin 0.3 kuralı bu dört örnekle sıkılaştırıldı; arayüz ve README artık "iki dosyayı bir kez oku" diyor.
- **Hermes sağlayıcı tuzağı:** Hermes'in kendi varsayılanı Gemini'ydi (anahtar geçersiz) ve yönerge doğrudan `hermes` ile verilince hemen düştü. Uygulama her çağrıda `--provider anthropic` gönderdiği için uygulama içinden sorun yok; ancak Anthropic dışı sağlayıcı kullanan Hermes kullanıcısı `data/settings.json` içinde `ai_provider` ayarlamalı. Arayüzde bu alan yok (README'de belgelendi).
- **Konsol kodlaması:** `cv_document.py` ve `cv_for_job.py` stdout'u UTF-8'e çevirmiyordu; arayüz çıktıyı UTF-8 okuduğu için Türkçe karakterli klasörde "CV oluşturuldu" mesajındaki yol bozuk görünüyordu. Diğer modüllerle aynı `reconfigure` bloğu eklendi.

## Linux/macOS denetimi (14 Eylül 2026)

WSL Ubuntu 24.04 üzerinde, çalışma ağacının temiz bir kopyasıyla denendi. Stok Ubuntu'da `python3-venv` ve `python3-tk` yoktu ve `sudo` şifre istediği için Tkinter'li taşınabilir Python (uv, yalnız test klasörüne) kullanıldı.

- **Eski `setup.sh` iki sorun çıkarıyordu:** `venv` eksikken yarım bir `.venv` bırakıyordu ve yeniden çalıştırıldığında bunu onarmıyordu (`pip` yok); Tkinter eksikliğini hiç söylemiyor, uygulama açılışta `ModuleNotFoundError: tkinter` ile çöküyordu. Yeni betik Python ≥ 3.11, `venv/ensurepip` ve `tkinter` kontrol ediyor, eksikte apt/dnf/pacman/Homebrew komutunu yazıyor, pip'siz `.venv`'yi yeniden kuruyor; `PYTHON=` ile başka yorumlayıcı seçilebiliyor.
- **Özel komut ayrıştırma:** `shlex.split(posix=False)` Linux/macOS'ta tek tırnaklı yolu bozuyordu (`FileNotFoundError`). Windows dışında artık `posix=True`; Windows davranışı aynı. İki platform için test eklendi.
- Linux'ta testler, `migrate`, `start.sh` ve masaüstü arayüzü (WSLg, 1180×720) çalıştı. Windows'a özel `.cmd` kısayol testinde eksik olan platform koşulu eklendi.
- **macOS gerçek cihazda denenmedi.** Statik denetim: arayüzde platforma özel Tk çağrısı yok, DOCX `open` ile açılıyor, konsol gizleme Windows dışında devre dışı.

## Devam ederken çalıştırılacaklar

```bash
cd "D:\İş Başvuru Sistemi - Açık Kaynak"
git status
.venv/Scripts/python -m unittest discover -s tests   # 49 test geçmeli
.venv/Scripts/python main.py                   # arayüz
.venv/Scripts/python main.py collect           # ilan topla (AI'sız)
.venv/Scripts/python main.py initial-review --limit 3
```

Yedek: taşıma öncesi `data/` kopyası geçici oturum klasöründeydi, kalıcı değildir. Yeni bir taşıma denemesi yapılacaksa **önce `data/` elle yedeklenmeli**.
