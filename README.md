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
| `tools/make_icons.py` | İkonları yeniden üretmek için (isteğe bağlı) |

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
3. Yayına hazır olduğunda bir sürüm etiketi gönder:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   Derleme bittiğinde dosyalar deponun **Releases** sayfasında yayınlanır.

Yeni sürüm çıkarırken `taskil.py` içindeki `__version__ = "1.0.0"` satırını güncelleyip
yeni bir etiket (`v1.0.1` gibi) göndermen yeterli.

## Çıkan dosyalar

| Sistem | Dosya | Kullanıcı ne yapar |
|---|---|---|
| Windows | `Taskil-windows-x64.exe` | Çift tıklar, açılır |
| macOS (M1/M2/M3/M4) | `Taskil-macos-arm64.dmg` | Açar, Taskil'i Uygulamalar'a sürükler |
| macOS (Intel) | `Taskil-macos-intel.dmg` | Aynı şekilde |
| Linux | `Taskil-linux-x64.tar.gz` | Açar, `Taskil` dosyasını çalıştırır; istersen `install.sh` menüye ekler |

## Web sitesi için indirme linkleri

Dosya adlarında sürüm numarası olmadığı için şu linkler **her zaman en son sürümü** indirir
(`KULLANICI/DEPO` kısmını kendi deponla değiştir):

```
https://github.com/KULLANICI/DEPO/releases/latest/download/Taskil-windows-x64.exe
https://github.com/KULLANICI/DEPO/releases/latest/download/Taskil-macos-arm64.dmg
https://github.com/KULLANICI/DEPO/releases/latest/download/Taskil-macos-intel.dmg
https://github.com/KULLANICI/DEPO/releases/latest/download/Taskil-linux-x64.tar.gz
```

## İlk açılışta çıkan güvenlik uyarıları

Program kod imzası olmadan dağıtıldığı için işletim sistemleri ilk açılışta uyarı verir.
Bu uyarılar programın zararlı olduğu anlamına gelmez; tanınmayan yayıncı demektir.

- **Windows:** "Windows bilgisayarınızı korudu" ekranında **Ek bilgi → Yine de çalıştır**.
  Uyarıyı tamamen kaldırmak için bir kod imzalama sertifikası gerekir.
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
