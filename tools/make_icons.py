"""Taskil uygulama ikonlarını üretir: assets/ altına PNG, .ico (Windows) ve .icns (macOS).

Kullanım:  pip install pillow  &&  python tools/make_icons.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
S = 2048  # büyük çizip küçülterek pürüzsüz kenar elde ediyoruz


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def gradient(size, c1, c2):
    """Sol üstten sağ alta çapraz renk geçişi."""
    a, b = hex2rgb(c1), hex2rgb(c2)
    small = Image.new("RGB", (256, 256))
    px = small.load()
    for y in range(256):
        for x in range(256):
            t = (x + y) / 510
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return small.resize((size, size), Image.BICUBIC)


def draw_master():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # turkuaz geçişli yuvarlak kare zemin
    mask = Image.new("L", (S, S), 0)
    m = 96
    ImageDraw.Draw(mask).rounded_rectangle((m, m, S - m, S - m), radius=440, fill=255)
    img.paste(gradient(S, "#4ED2C7", "#0B8489"), (0, 0), mask)

    d = ImageDraw.Draw(img)
    # beyaz takvim kartı (hafif gölgeli)
    x1, y1, x2, y2 = 430, 560, S - 430, S - 400
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((x1, y1 + 40, x2, y2 + 40), radius=170,
                                             fill=(10, 70, 75, 70))
    img.alpha_composite(shadow)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x1, y1, x2, y2), radius=170, fill="#FFFFFF")
    # kartın üst bandı
    band = Image.new("L", (S, S), 0)
    ImageDraw.Draw(band).rounded_rectangle((x1, y1, x2, y2), radius=170, fill=255)
    top = Image.new("L", (S, S), 0)
    ImageDraw.Draw(top).rectangle((x1, y1, x2, y1 + 250), fill=255)
    from PIL import ImageChops
    img.paste(Image.new("RGBA", (S, S), hex2rgb("#CDF3EF") + (255,)), (0, 0),
              ImageChops.multiply(band, top))
    d = ImageDraw.Draw(img)
    # halkalar
    for cx in (x1 + 300, x2 - 300):
        d.rounded_rectangle((cx - 55, y1 - 120, cx + 55, y1 + 130), radius=55, fill="#14384F")
    # onay işareti
    pts = [(760, 1210), (940, 1390), (1300, 1010)]
    d.line(pts, fill="#0EA5A0", width=150, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse((p[0] - 75, p[1] - 75, p[0] + 75, p[1] + 75), fill="#0EA5A0")
    return img


def main():
    OUT.mkdir(exist_ok=True)
    master = draw_master()
    sizes = [16, 24, 32, 48, 64, 128, 256, 512, 1024]
    imgs = {s: master.resize((s, s), Image.LANCZOS) for s in sizes}
    for s in (32, 64, 256, 512, 1024):
        imgs[s].save(OUT / f"taskil-{s}.png")
    imgs[256].save(OUT / "taskil.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    imgs[1024].save(OUT / "taskil.icns")
    print("ikonlar üretildi:", OUT)


if __name__ == "__main__":
    main()
