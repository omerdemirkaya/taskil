"""Microsoft Store (MSIX) paketi için görselleri üretir: assets/msix/

Kullanım:  pip install pillow  &&  python tools/make_store_assets.py
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_icons import draw_master  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "msix"


def fit(master, size, scale):
    """İkonu şeffaf bir kareye, kenarın 'scale' oranı kadar büyüklükte ortalar."""
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = max(1, round(size * scale))
    icon = master.resize((inner, inner), Image.LANCZOS)
    off = (size - inner) // 2
    canvas.alpha_composite(icon, (off, off))
    return canvas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    m = draw_master()

    # Mağaza logosu (Store sayfası ve uygulama listesi)
    fit(m, 50, 1.0).save(OUT / "StoreLogo.png")
    for s in (125, 150, 200, 400):
        fit(m, 50 * s // 100, 1.0).save(OUT / f"StoreLogo.scale-{s}.png")

    # Başlat menüsü kutucuğu: ikon ortada, çevresi boş
    fit(m, 150, 0.66).save(OUT / "Square150x150Logo.png")
    for s in (125, 150, 200, 400):
        fit(m, 150 * s // 100, 0.66).save(OUT / f"Square150x150Logo.scale-{s}.png")

    # Uygulama listesi / görev çubuğu ikonu
    fit(m, 44, 0.92).save(OUT / "Square44x44Logo.png")
    for s in (125, 150, 200, 400):
        fit(m, round(44 * s / 100), 0.92).save(OUT / f"Square44x44Logo.scale-{s}.png")
    for t in (16, 24, 32, 48, 256):
        img = fit(m, t, 1.0 if t <= 32 else 0.94)
        img.save(OUT / f"Square44x44Logo.targetsize-{t}.png")
        img.save(OUT / f"Square44x44Logo.targetsize-{t}_altform-unplated.png")
        img.save(OUT / f"Square44x44Logo.targetsize-{t}_altform-lightunplated.png")

    print("Store görselleri üretildi:", OUT, len(list(OUT.glob("*.png"))), "dosya")


if __name__ == "__main__":
    main()
