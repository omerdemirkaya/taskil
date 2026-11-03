# Taskil

Günlük görevlerini takvim üzerinde planladığın, sade ve şık bir masaüstü uygulaması.
Windows, macOS ve Linux'ta çalışır; derlenmiş sürümler için Python kurmaya gerek yoktur.

## Klasör yapısı

| Dosya | Ne işe yarar |
|---|---|
| `taskil.py` | Uygulamanın kendisi (tek dosya) |
| `assets/` | Uygulama ikonları (`.ico` Windows, `.icns` macOS, `.png`) |
| `build.py` | Uygulamayı tek parça programa çeviren derleme betiği |
| `.github/workflows/build.yml` | GitHub'da üç işletim sistemi için otomatik derleme |
| `assets/msix/` | Microsoft Store paketinin görselleri |
| `tools/make_icons.py`, `tools/make_store_assets.py` | İkonları ve Store görsellerini yeniden üretmek için (isteğe bağlı) |

## Neden GitHub ile derliyoruz?

Her işletim sisteminin programı **kendi sisteminde** derlenmek zorunda: Windows `.exe`'si
Windows'ta, macOS uygulaması Mac'te üretilir. GitHub Actions bunu ücretsiz olarak
üç sistemde aynı anda yapar, senin üç bilgisayarın olmasına gerek kalmaz.

## Derleme adımları (GitHub)

1. GitHub'da yeni bir depo (repository) oluştur ve bu klasörün içeriğini oraya yükle.
   `.github` klasörünün de yüklendiğinden emin ol (gizli klasördür).
2. Deponun **Actions** sekmesine gir → **Build Taskil** → **Run workflow**.
   Yaklaşık 5–10 dakika sonra çalışmanın sayfasında **Artifacts** bölümünden
   dosyaları indirip deneyebilirsin.
3. Yayına hazır olduğunda deponun **Releases → Create a new release** sayfasına git:
   **Tag** kutusuna `v1.0.1` gibi yeni bir sürüm yazıp **Create new tag** de, bir başlık ver ve
   **Publish release**'e bas. Derleme otomatik başlar; yaklaşık 10 dakika sonra
   dosyalar o sürümün altına eklenir.

Yeni sürüm çıkarırken önce `taskil.py` içindeki `__version__ = "..."` satırını güncelle.
Microsoft Store her güncellemede sürüm numarasının artmasını şart koşar.

## Çıkan dosyalar

| Sistem | Dosya | Kullanıcı ne yapar |
|---|---|---|
| Windows | `Taskil-windows-x64.exe` | Çift tıklar, açılır |
| macOS (M1/M2/M3/M4) | `Taskil-macos-arm64.dmg` | Açar, Taskil'i Uygulamalar'a sürükler |
| macOS (Intel) | `Taskil-macos-intel.dmg` | Aynı şekilde |
| Linux | `Taskil-linux-x64.tar.gz` | Açar, `Taskil` dosyasını çalıştırır; istersen `install.sh` menüye ekler |
| Microsoft Store | `Taskil-microsoft-store-upload.msix` | **Kullanıcılar için değil**; sadece Partner Center'a yüklenir |

## Microsoft Store'a yükleme

Windows derlemesi, `.exe`'nin yanında Store'a yüklenecek `Taskil-microsoft-store-upload.msix`
dosyasını da üretir. Paket kimlik bilgileri (`Startiux.Taskil`, yayıncı kodu) `build.py`
içindeki `STORE` bölümündedir. Paket imzasızdır; Microsoft Store onaydan sonra kendisi imzalar,
bu yüzden Store'dan kuranlar hiçbir güvenlik uyarısı görmez.

1. Partner Center'da Taskil uygulamasında yeni bir gönderim (submission) başlat.
2. **Packages** bölümüne `.msix` dosyasını yükle.
3. Mağaza bilgilerini (açıklama, ekran görüntüleri) Türkçe ve İngilizce doldur ve gönder.

## Web sitesi için indirme linkleri

Dosya adlarında sürüm numarası olmadığı için şu linkler **her zaman en son sürümü** indirir:

```
https://github.com/omerdemirkaya/taskil/releases/latest/download/Taskil-windows-x64.exe
https://github.com/omerdemirkaya/taskil/releases/latest/download/Taskil-macos-arm64.dmg
https://github.com/omerdemirkaya/taskil/releases/latest/download/Taskil-macos-intel.dmg
https://github.com/omerdemirkaya/taskil/releases/latest/download/Taskil-linux-x64.tar.gz
```

## İlk açılışta çıkan güvenlik uyarıları

Program kod imzası olmadan dağıtıldığı için işletim sistemleri ilk açılışta uyarı verir.
Bu uyarılar programın zararlı olduğu anlamına gelmez; tanınmayan yayıncı demektir.

- **Windows:** "Windows bilgisayarınızı korudu" ekranında **Ek bilgi → Yine de çalıştır**.
  Microsoft Store'dan kurulan sürümde bu uyarı çıkmaz.
- **macOS:** İlk açılışta engellenirse **Sistem Ayarları → Gizlilik ve Güvenlik** altında
  **Yine de Aç**'a basılır. Uyarısız açılması için Apple Developer hesabı
  (yıllık ücretli) ile imzalama ve notarize işlemi gerekir.
- **Linux:** Uyarı yoktur; dosyanın çalıştırılabilir olması yeterli.

Bu notları web sitendeki indirme sayfasına kısa bir "Nasıl kurulur?" bölümü olarak eklemeni öneririm.

## Kendi bilgisayarında derlemek (isteğe bağlı)

```bash
pip install pyinstaller
python build.py          # çıktı: dist/release/
```

## Veriler nerede tutulur?

Her kullanıcının görevleri kendi bilgisayarında, kullanıcıya özel klasörde saklanır:

- Windows: `%APPDATA%\Taskil\tasks.json`
- macOS: `~/Library/Application Support/Taskil/tasks.json`
- Linux: `~/.local/share/taskil/tasks.json`

Önceki "Günlük Takvim" sürümünü kullandıysan verilerin ilk açılışta otomatik olarak taşınır.


## Privacy policy

Taskil does not collect, store or transmit any personal data. It never connects to the
internet: all tasks are stored only in a local file on the user's own computer, and no
information is sent to the developer or to any third party.

Taskil hiçbir kişisel veri toplamaz, saklamaz veya iletmez. İnternete bağlanmaz; tüm görevler
yalnızca kullanıcının kendi bilgisayarındaki bir dosyada tutulur ve geliştiriciye ya da
üçüncü taraflara hiçbir bilgi gönderilmez.
