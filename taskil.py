#!/usr/bin/env python3
"""
Taskil — günlük görev takvimi / daily task calendar.

- Ekranı kaplayarak (maximize) açılır, istenirse küçültülebilir.
- Ay ve yıl başlığına tıklayınca ay / yıl seçici açılır.
- Takvim karelerinde o günün görev ilerlemesi çubuk olarak görünür.
- Bir güne tıklayınca o günün sayfası açılır: görev ekle, sürükleyerek sırala,
  tamamlandı işaretle, çift tıkla düzenle, sil. Uzun metinlerde kutu büyür.
- Türkçe / English dil desteği (sağ üstteki TR | EN).

Veriler kullanıcıya özel uygulama klasöründe tutulur:
    Windows : %APPDATA%\\Taskil\\tasks.json
    macOS   : ~/Library/Application Support/Taskil/tasks.json
    Linux   : ~/.local/share/taskil/tasks.json
Taşınabilir mod: programın yanında tasks.json varsa (boş olsa bile) o kullanılır.

Kaynaktan çalıştırma: Python 3.8+ (tkinter dahil). Derlenmiş sürümler Python gerektirmez.
"""

__version__ = "1.0.0"

import calendar
import json
import os
import shutil
import sys
import uuid
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk

APP_NAME = "Taskil"
APP_ID = "Taskil.App.1"
DATA_FILE = "tasks.json"
LEGACY_DIRS = ("GunlukTakvim", "gunluk-takvim")    # eski sürümün veri klasörleri


def resource_path(rel):
    """Paketlenmiş (PyInstaller) ya da kaynak halinde, yanındaki dosyanın yolu."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / rel

# ------------------------------------------------------------------- dil desteği

STRINGS = {
    "tr": {
        "app_title": "Taskil",
        "months": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
                   "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
        "weekdays": ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"],
        "weekdays_long": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma",
                          "Cumartesi", "Pazar"],
        "date_fmt": "{d} {month} {y}",
        "today": "Bugün",
        "today_is": "Bugün: {date}, {weekday}",
        "stat_total": "Toplam görev",
        "stat_done": "Tamamlanan",
        "stat_open": "Bekleyen",
        "stat_month": "Bu ay",
        "back": "‹  Takvim",
        "placeholder": "Yeni görev yaz ve Enter'a bas…",
        "add": "+ Ekle",
        "progress": "{d}/{n} görev tamamlandı",
        "no_tasks_yet": "Henüz görev yok",
        "pct": "%{p}",
        "tasks_header": "Görevler",
        "months_short": ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl",
                         "Eki", "Kas", "Ara"],
        "short_dt": "{d} {m} {hm}",
        "created": "Eklendi {t}",
        "done_at": "Tamamlandı {t}",
        "added_toast": "✓  Görev eklendi",
        "moved_toast": "✓  Taşındı",
        "tip_top": "En üste taşı",
        "tip_bottom": "En alta taşı",
        "tip_delete": "Sil",
        "empty_title": "Bu gün henüz boş",
        "empty_sub": "Yukarıdaki kutuya ilk görevini yazıp Enter'a bas.",
        "hint": "Sürükleyerek sırala  ·  Çift tıkla: düzenle  ·  Shift+Enter: alt satır  ·  Esc: takvime dön",
        "pick_month": "Bir ay seç",
        "pick_year": "Bir yıl seç",
        "data": "Veriler: {path}",
        "load_err": "Veri dosyası okunamadı ({err}).\nBoş bir takvimle başlatıldı.",
        "backup": "Eski dosyanın yedeği:\n{path}",
    },
    "en": {
        "app_title": "Taskil",
        "months": ["January", "February", "March", "April", "May", "June", "July",
                   "August", "September", "October", "November", "December"],
        "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "weekdays_long": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                          "Saturday", "Sunday"],
        "date_fmt": "{month} {d}, {y}",
        "today": "Today",
        "today_is": "Today: {weekday}, {date}",
        "stat_total": "Total tasks",
        "stat_done": "Completed",
        "stat_open": "Pending",
        "stat_month": "This month",
        "back": "‹  Calendar",
        "placeholder": "Type a new task and press Enter…",
        "add": "+ Add",
        "progress": "{d}/{n} tasks completed",
        "no_tasks_yet": "No tasks yet",
        "pct": "{p}%",
        "tasks_header": "Tasks",
        "months_short": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                         "Oct", "Nov", "Dec"],
        "short_dt": "{m} {d}, {hm}",
        "created": "Added {t}",
        "done_at": "Completed {t}",
        "added_toast": "✓  Task added",
        "moved_toast": "✓  Moved",
        "tip_top": "Move to top",
        "tip_bottom": "Move to bottom",
        "tip_delete": "Delete",
        "empty_title": "Nothing planned yet",
        "empty_sub": "Type your first task in the box above and press Enter.",
        "hint": "Drag to reorder  ·  Double-click: edit  ·  Shift+Enter: new line  ·  Esc: back to calendar",
        "pick_month": "Pick a month",
        "pick_year": "Pick a year",
        "data": "Data: {path}",
        "load_err": "Could not read the data file ({err}).\nStarted with an empty calendar.",
        "backup": "Backup of the old file:\n{path}",
    },
}


def detect_lang():
    try:
        if sys.platform.startswith("win"):
            import ctypes
            # 0x1F = Türkçe birincil dil kimliği
            return "tr" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x1F else "en"
        import locale
        for v in (os.environ.get("LANG", ""), locale.getlocale()[0] or ""):
            if v.lower().startswith(("tr", "turkish")):
                return "tr"
    except Exception:
        pass
    return "en"


# ------------------------------------------------------------------ renk paleti
# Açık turkuaz → koyu petrol mavisi

P = {
    "ice": "#CDF3EF", "frost": "#A8EAE3", "sky": "#7EDFD6", "aqua": "#4ED2C7",
    "cyan": "#20C1B5", "ocean": "#0EA5A0", "deep": "#0B8489", "royal": "#17607A",
    "navy": "#14384F",
}

C = {
    "bg": "#F1FAF9",           # sayfa zemini — çok açık turkuaz
    "surface": "#FFFFFF",
    "surface_alt": "#F8FDFC",
    "border": "#D5EFEC",
    "border_strong": "#B9E5E0",
    "text": P["navy"],
    "muted": "#5A7F86",
    "faint": "#A3C4C4",
    "accent": P["ocean"],
    "accent_dark": P["deep"],
    "soft": "#E2F6F3",         # ikincil buton / çip zemini
    "soft_hover": "#CFEFEB",
    "weekend": "#0E9A96",
    "danger": "#E0607A",
    "danger_soft": "#FDECEF",
    "drag": "#ECFAF8",
    "shadow": "#E1F1EF",
}

TILE_PAL = {
    "normal": dict(bg="#FFFFFF", hover="#F2FBFA", border="#DCF1EE", track="#E3F5F2",
                   fill=P["cyan"], full=P["ocean"], title=C["text"], muted=C["muted"]),
    "today": dict(bg=P["ice"], hover="#BFEFE9", border=P["sky"], track="#E6F8F5",
                  fill=P["deep"], full=P["deep"], title=P["navy"], muted=P["royal"]),
    "other": dict(bg="#F7FCFB", hover="#F2FBFA", border="#E5F3F1", track="#EDF7F6",
                  fill=P["frost"], full=P["sky"], title="#B3CFCF", muted="#B3CFCF"),
}


# ------------------------------------------------------------------ veri katmanı

def _data_base() -> Path:
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def default_data_dir() -> Path:
    name = APP_NAME if sys.platform.startswith("win") or sys.platform == "darwin" else "taskil"
    return _data_base() / name


def resolve_data_path() -> Path:
    if getattr(sys, "frozen", False):          # PyInstaller ile paketlenmişse
        here = Path(sys.executable).resolve().parent
    else:
        here = Path(__file__).resolve().parent
    local = here / DATA_FILE
    if local.exists():
        return local
    path = default_data_dir() / DATA_FILE
    if not path.exists():                      # eski sürümden kalan veriyi taşı
        for old in LEGACY_DIRS:
            src = _data_base() / old / DATA_FILE
            if src.exists():
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, path)
                except OSError:
                    pass
                break
    return path


class TaskStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = {"version": 1, "settings": {}, "tasks": {}}
        self.load_error = None
        self.load()

    def load(self):
        if not self.path.exists() or self.path.stat().st_size == 0:
            self.save()
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict) or not isinstance(d.get("tasks"), dict):
                raise ValueError("unexpected file format")
            d.setdefault("settings", {})
            self.data = d
        except (json.JSONDecodeError, ValueError, OSError) as e:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = self.path.with_name(f"{self.path.stem}.broken-{stamp}.json")
            try:
                shutil.copy2(self.path, backup)
            except OSError:
                backup = None
            self.load_error = (e, backup)
            self.data = {"version": 1, "settings": {}, "tasks": {}}
            self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)       # yarım yazılmış dosya kalmasın

    # -- ayarlar
    def get_setting(self, key, default=None):
        return self.data.get("settings", {}).get(key, default)

    def set_setting(self, key, value):
        self.data.setdefault("settings", {})[key] = value
        self.save()

    # -- görevler
    @staticmethod
    def key(d: date) -> str:
        return d.isoformat()

    def tasks_for(self, d: date):
        return self.data["tasks"].get(self.key(d), [])

    def _find(self, d, tid):
        return next((t for t in self.tasks_for(d) if t["id"] == tid), None)

    def add(self, d: date, title: str):
        t = {"id": uuid.uuid4().hex, "title": title, "done": False,
             "created_at": datetime.now().isoformat(timespec="seconds"), "done_at": None}
        self.data["tasks"].setdefault(self.key(d), []).append(t)
        self.save()
        return t

    def toggle(self, d, tid):
        t = self._find(d, tid)
        if t:
            t["done"] = not t["done"]
            t["done_at"] = datetime.now().isoformat(timespec="seconds") if t["done"] else None
            self.save()

    def rename(self, d, tid, title):
        t = self._find(d, tid)
        if t and title and title != t["title"]:
            t["title"] = title
            t["updated_at"] = datetime.now().isoformat(timespec="seconds")
            self.save()

    def delete(self, d, tid):
        k = self.key(d)
        lst = [t for t in self.data["tasks"].get(k, []) if t["id"] != tid]
        if lst:
            self.data["tasks"][k] = lst
        else:
            self.data["tasks"].pop(k, None)
        self.save()

    def reorder(self, d, ids):
        """Görevleri verilen id sırasına göre dizer."""
        k = self.key(d)
        lst = self.data["tasks"].get(k, [])
        by_id = {t["id"]: t for t in lst}
        new = [by_id[i] for i in ids if i in by_id]
        new += [t for t in lst if t["id"] not in ids]     # güvenlik: kaybolan olmasın
        if [t["id"] for t in new] != [t["id"] for t in lst]:
            self.data["tasks"][k] = new
            self.save()

    def _count(self, prefix=""):
        total = done = 0
        for k, lst in self.data["tasks"].items():
            if k.startswith(prefix):
                total += len(lst)
                done += sum(1 for t in lst if t["done"])
        return total, done

    def stats(self):
        return self._count()

    def month_stats(self, y, m):
        return self._count(f"{y:04d}-{m:02d}-")

    def year_stats(self, y):
        return self._count(f"{y:04d}-")


# ----------------------------------------------------------- çizim yardımcıları

def pick_font_family(root):
    available = set(tkfont.families(root))
    for fam in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter", "Ubuntu",
                "Cantarell", "Noto Sans", "DejaVu Sans", "Arial", "Helvetica"):
        if fam in available:
            return fam
    return tkfont.nametofont("TkDefaultFont").actual()["family"]


def rounded_rect(cv, x1, y1, x2, y2, r, fill="", outline="", width=1, tags=()):
    """Kenarları pürüzsüz yuvarlak köşeli dikdörtgen (yay + çizgi ile)."""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    r = int(max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2)))
    d = 2 * r
    corners = ((x1, y1, 90), (x2 - d, y1, 0), (x1, y2 - d, 180), (x2 - d, y2 - d, 270))
    if fill:
        cv.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags=tags)
        cv.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags=tags)
        if r:
            for ax, ay, st in corners:
                cv.create_arc(ax, ay, ax + d, ay + d, start=st, extent=90,
                              style="pieslice", fill=fill, outline="", tags=tags)
    if outline:
        if r:
            for ax, ay, st in corners:
                cv.create_arc(ax, ay, ax + d, ay + d, start=st, extent=90,
                              style="arc", outline=outline, width=width, tags=tags)
        cv.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=width, tags=tags)
        cv.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=width, tags=tags)
        cv.create_line(x1, y1 + r, x1, y2 - r, fill=outline, width=width, tags=tags)
        cv.create_line(x2, y1 + r, x2, y2 - r, fill=outline, width=width, tags=tags)


def mix(c1, c2, t):
    """İki hex rengi karıştırır (t=0 → c1, t=1 → c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def hex_to_colorref(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r | (g << 8) | (b << 16)


def style_windows_titlebar(win):
    """Windows 11'de başlık çubuğunu uygulamanın renklerine boyar (Win10'da zararsızca yok sayılır)."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())

        def dwm(attr, value):
            v = ctypes.c_int(value)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))

        dwm(20, 0)                                    # açık tema
        dwm(34, hex_to_colorref(C["border_strong"]))  # pencere kenarı
        dwm(35, hex_to_colorref(C["bg"]))             # başlık çubuğu arka planı
        dwm(36, hex_to_colorref(C["text"]))           # başlık yazısı
    except Exception:
        pass


def make_icon(root):
    """Python tüyü yerine küçük bir takvim ikonu çizer."""
    img = tk.PhotoImage(master=root, width=64, height=64)

    def box(color, x1, y1, x2, y2):
        img.put(color, to=(x1, y1, x2, y2))

    box(P["deep"], 6, 10, 58, 24)
    box("#ffffff", 6, 24, 58, 58)
    box(P["deep"], 6, 24, 8, 58)
    box(P["deep"], 56, 24, 58, 58)
    box(P["deep"], 6, 56, 58, 58)
    box(P["ice"], 18, 5, 23, 16)
    box(P["ice"], 41, 5, 46, 16)
    for r in range(3):
        for c in range(4):
            x, y = 13 + c * 10, 29 + r * 9
            box(P["cyan"] if (r, c) == (1, 2) else P["ice"], x, y, x + 7, y + 6)
    return img


# --------------------------------------------------------------- arayüz parçaları

class RoundButton(tk.Canvas):
    """Yuvarlak köşeli, her platformda aynı görünen buton."""

    def __init__(self, master, text, command, font, bg=None, fg=None, hover_bg=None,
                 padx=12, pady=6, radius=10, parent_bg=None):
        super().__init__(master, highlightthickness=0, bd=0, cursor="hand2",
                         bg=parent_bg or C["bg"])
        self.text, self.command, self.font = text, command, font
        self._bg, self._fg = bg or C["soft"], fg or C["text"]
        self._hover_bg = hover_bg or C["soft_hover"]
        self.padx, self.pady, self.radius = padx, pady, radius
        self.hover = self.pressed = False
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._click)
        self._draw()

    def _press(self, _e):
        self.pressed = True
        self._draw()

    def _set_hover(self, v):
        self.hover = v
        self._draw()

    def set_bg(self, bg):
        self._bg = bg
        self._draw()

    def set_text(self, text):
        self.text = text
        self._draw()

    def _draw(self):
        w = self.font.measure(self.text) + 2 * self.padx
        h = self.font.metrics("linespace") + 2 * self.pady
        self.config(width=w, height=h)
        self.delete("all")
        if self.pressed:          # basılıyken koyulaşır ve hafifçe içeri çöker
            rounded_rect(self, 1, 1, w - 2, h - 2, self.radius,
                         fill=mix(self._hover_bg, "#000000", 0.18))
            self.create_text(w / 2, h / 2 + 1, text=self.text, font=self.font, fill=self._fg)
            return
        rounded_rect(self, 0, 0, w - 1, h - 1, self.radius,
                     fill=self._hover_bg if self.hover else self._bg)
        self.create_text(w / 2, h / 2, text=self.text, font=self.font, fill=self._fg)

    def _click(self, e):
        self.pressed = False
        self._draw()
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            self.command()


def primary_button(master, text, command, font, **kw):
    return RoundButton(master, text, command, font, bg=C["accent"], fg="white",
                       hover_bg=C["accent_dark"], **kw)


class Pill(tk.Canvas):
    """Küçük yuvarlak etiket (sayı rozeti, 'Bugün' etiketi vb.)."""

    def __init__(self, master, font, bg, fg, parent_bg=None, padx=9, pady=2):
        super().__init__(master, highlightthickness=0, bd=0, bg=parent_bg or C["bg"])
        self.font, self._bg, self._fg, self.padx, self.pady = font, bg, fg, padx, pady

    def set(self, text):
        w = self.font.measure(text) + 2 * self.padx
        h = self.font.metrics("linespace") + 2 * self.pady
        self.config(width=w, height=h)
        self.delete("all")
        rounded_rect(self, 0, 0, w - 1, h - 1, h // 2, fill=self._bg)
        self.create_text(w / 2, h / 2, text=text, font=self.font, fill=self._fg)
        return self


class GrowText(tk.Text):
    """İçeriğe göre yüksekliği büyüyen çok satırlı metin kutusu."""

    def __init__(self, master, font, min_lines=1, max_lines=6, placeholder=None, **kw):
        super().__init__(master, height=min_lines, width=1, wrap="word", font=font,
                         undo=True, relief="flat", bd=0, **kw)
        self.min_lines, self.max_lines = min_lines, max_lines
        self.ph = None
        if placeholder:
            self.ph = tk.Label(self, text=placeholder, font=font, bg=self.cget("bg"),
                               fg=C["faint"], cursor="xterm", bd=0, padx=0, pady=0)
            self.ph.bind("<Button-1>", lambda e: self.focus_set())
        for seq in ("<KeyRelease>", "<Configure>", "<<Paste>>", "<FocusIn>"):
            self.bind(seq, lambda e: self.after_idle(self.fit), add="+")
        self.after_idle(self.fit)

    def value(self):
        return self.get("1.0", "end-1c")

    def set_value(self, s):
        self.delete("1.0", "end")
        self.insert("1.0", s)
        self.fit()

    def fit(self):
        if not self.winfo_exists():
            return
        try:
            n = self.count("1.0", "end", "displaylines")
        except tk.TclError:
            n = None
        if isinstance(n, tuple):
            n = n[0]
        lines = max(self.min_lines, min(self.max_lines, n or 1))
        if int(self.cget("height")) != lines:
            self.config(height=lines)
        if self.ph is not None:
            if self.value():
                self.ph.place_forget()
            else:
                self.ph.place(x=0, y=0)     # Text iç boşluğu (padx/pady) zaten uygulanıyor


class RoundedInput(tk.Canvas):
    """Yuvarlak köşeli çerçeve içinde büyüyen metin kutusu."""

    PADX, PADY = 16, 12

    def __init__(self, master, app, placeholder, max_lines=6):
        super().__init__(master, bg=C["bg"], highlightthickness=0, bd=0, height=46)
        self.focused = False
        self.text = GrowText(self, app.f_body, max_lines=max_lines, placeholder=placeholder,
                             bg=C["surface"], fg=C["text"], insertbackground=C["text"],
                             padx=0, pady=0, highlightthickness=0,
                             selectbackground=P["frost"], selectforeground=C["text"])
        self.win = self.create_window(self.PADX, self.PADY, anchor="nw", window=self.text)
        self.bind("<Configure>", lambda e: self._layout())
        self.bind("<Button-1>", lambda e: self.text.focus_set())
        self.text.bind("<Configure>", lambda e: self._layout(), add="+")
        self.text.bind("<FocusIn>", lambda e: self._set_focus(True), add="+")
        self.text.bind("<FocusOut>", lambda e: self._set_focus(False), add="+")

    def _set_focus(self, v):
        self.focused = v
        self._layout()

    def flash_error(self):
        """Boş ekleme denemesinde çerçeve kısa süre kırmızımsı yanar."""
        self.error = True
        self._layout()
        self.text.focus_set()
        self.after(900, lambda: (setattr(self, "error", False), self._layout()))

    def _layout(self):
        w = self.winfo_width()
        h = self.text.winfo_reqheight() + 2 * self.PADY
        if int(self.cget("height")) != h:
            self.config(height=h)
        self.itemconfigure(self.win, width=max(w - 2 * self.PADX, 10))
        self.delete("frame")
        if getattr(self, "error", False):
            rounded_rect(self, 0, 0, w - 1, h - 1, 14, fill=C["danger_soft"], tags="frame")
            rounded_rect(self, 2, 2, w - 3, h - 3, 12, fill=C["surface"],
                         outline=C["danger"], tags="frame")
        elif self.focused:    # odakta hafif turkuaz hale
            rounded_rect(self, 0, 0, w - 1, h - 1, 14, fill=P["ice"], tags="frame")
            rounded_rect(self, 2, 2, w - 3, h - 3, 12, fill=C["surface"],
                         outline=P["aqua"], tags="frame")
        else:
            rounded_rect(self, 1, 1, w - 2, h - 2, 13, fill=C["surface"],
                         outline=C["border_strong"], tags="frame")
        self.tag_lower("frame")


class Tile(tk.Canvas):
    """Yuvarlak köşeli kare: takvim günü, ay veya yıl + görev ilerleme çubuğu."""

    def __init__(self, master, app, on_click, title_font, radius=12):
        super().__init__(master, highlightthickness=0, bd=0, cursor="hand2",
                         width=40, height=40, bg=C["bg"])
        self.app, self.on_click, self.title_font, self.radius = app, on_click, title_font, radius
        self.cfg, self.key, self.hover = None, None, False
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", lambda e: self.cfg and self.on_click(self.key))

    def _set_hover(self, v):
        self.hover = v
        self.redraw()

    def set(self, key, title, kind="normal", total=0, done=0, title_fg=None,
            selected=False, bold=False):
        self.key = key
        self.cfg = dict(title=title, kind=kind, total=total, done=done,
                        title_fg=title_fg, selected=selected, bold=bold)
        self.redraw()

    def redraw(self):
        if not self.cfg:
            return
        c, a = self.cfg, self.app
        pal = TILE_PAL[c["kind"]]
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            return
        sel = c["selected"]
        rounded_rect(self, 1, 1, w - 2, h - 2, self.radius,
                     fill=pal["hover"] if self.hover else pal["bg"],
                     outline=C["accent"] if sel else (P["sky"] if self.hover else pal["border"]),
                     width=2 if sel else 1)
        pad = 14
        fnt = self.title_font[1] if c["bold"] else self.title_font[0]
        self.create_text(pad, 11, anchor="nw", text=c["title"], font=fnt,
                         fill=c["title_fg"] or pal["title"])

        n, d = c["total"], c["done"]
        if not n:
            return
        all_done = d == n
        bh = 6
        y2 = h - pad
        y1 = y2 - bh
        rounded_rect(self, pad, y1, w - pad, y2, 3, fill=pal["track"])
        if d:
            fw = max((w - 2 * pad) * d / n, bh)
            rounded_rect(self, pad, y1, pad + fw, y2, 3,
                         fill=pal["full"] if all_done else pal["fill"])
        if h >= 64:
            p = round(100 * d / n)
            self.create_text(pad, y1 - 6, anchor="sw", text=f"{d}/{n}",
                             font=a.f_small, fill=pal["muted"])
            self.create_text(w - pad, y1 - 6, anchor="se",
                             text=("✓ " if all_done else "") + a.t("pct", p=p),
                             font=a.f_small_bold,
                             fill=pal["full"] if all_done else pal["muted"])


class StatCard(tk.Canvas):
    """Sağ üstteki yuvarlak köşeli istatistik kartı."""

    def __init__(self, master, app, caption, color):
        super().__init__(master, highlightthickness=0, bd=0, bg=C["bg"], height=66, width=100)
        self.app, self.caption, self.color, self.value = app, caption, color, "0"

    def set(self, value):
        self.value = str(value)
        a = self.app
        w = max(a.f_stat.measure(self.value), a.f_small.measure(self.caption) + 14) + 34
        h = 66
        self.config(width=w)
        self.delete("all")
        rounded_rect(self, 1, 1, w - 2, h - 2, 12, fill=C["surface"], outline=C["border"])
        self.create_text(17, 10, anchor="nw", text=self.value, font=a.f_stat, fill=C["text"])
        self.create_oval(17, 45, 24, 52, fill=self.color, outline="")
        self.create_text(30, 48, anchor="w", text=self.caption, font=a.f_small, fill=C["muted"])


class ProgressCard(tk.Canvas):
    """Gün sayfasının üstündeki ilerleme kartı."""

    def __init__(self, master, app):
        super().__init__(master, highlightthickness=0, bd=0, bg=C["bg"], height=88)
        self.app, self.done, self.total = app, 0, 0
        self.bind("<Configure>", lambda e: self.redraw())

    def set(self, done, total):
        self.done, self.total = done, total
        self.redraw()

    def redraw(self):
        a, w, h = self.app, self.winfo_width(), 88
        if w < 40:
            return
        self.delete("all")
        rounded_rect(self, 1, 4, w - 2, h - 1, 16, fill=C["shadow"])
        rounded_rect(self, 1, 1, w - 2, h - 4, 16, fill=C["surface"], outline=C["border"])
        n, d = self.total, self.done
        txt = a.t("progress", d=d, n=n) if n else a.t("no_tasks_yet")
        self.create_text(22, 28, anchor="w", text=txt, font=a.f_body, fill=C["text"])
        if n:
            all_done = d == n
            self.create_text(w - 22, 28, anchor="e", font=a.f_section,
                             text=("✓ " if all_done else "") + a.t("pct", p=round(100 * d / n)),
                             fill=C["accent"] if d else C["muted"])
        rounded_rect(self, 22, 52, w - 22, 62, 5, fill="#E3F5F2")
        if n and d:
            rounded_rect(self, 22, 52, 22 + max((w - 44) * d / n, 10), 62, 5,
                         fill=P["ocean"] if d == n else P["cyan"])


# ------------------------------------------------------------------- uygulama

class App(tk.Tk):
    def __init__(self, store: TaskStore):
        super().__init__()
        self.withdraw()                         # kurulum bitene kadar gizle
        self.store = store
        self.lang = store.get_setting("lang") or detect_lang()
        if self.lang not in STRINGS:
            self.lang = "en"

        self.today = date.today()
        self.year, self.month = self.today.year, self.today.month
        self.view = "calendar"       # calendar | day
        self.mode = "days"           # days | months | years
        self.day = None
        self.year_page = self.year - 4
        self.day_view = None

        self.configure(bg=C["bg"])
        self._init_fonts()
        self._icons = []
        for size in (256, 64, 32):             # paketteki ikon; yoksa çizilen yedek ikon
            p = resource_path(f"assets/taskil-{size}.png")
            if p.exists():
                try:
                    self._icons.append(tk.PhotoImage(master=self, file=str(p)))
                except tk.TclError:
                    pass
        if not self._icons:
            self._icons = [make_icon(self)]
        self.iconphoto(True, *self._icons)
        self._init_style()

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1180, sw - 80), min(800, sh - 120)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max((sh - h) // 2 - 20, 0)}")
        self.minsize(900, 640)

        self.build_ui()
        self.bind("<Escape>", self._on_escape)
        self.bind_all("<ButtonPress-1>", self._global_press, add="+")
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind(seq, self._on_wheel)

        self.deiconify()
        self._maximize()
        self.after(30, lambda: style_windows_titlebar(self))
        self.after(60_000, self._check_day_change)

        if store.load_error:
            err, backup = store.load_error
            msg = self.t("load_err", err=err)
            if backup:
                msg += "\n\n" + self.t("backup", path=backup)
            self.after(400, lambda: messagebox.showwarning(self.t("app_title"), msg))

    # -- temel
    def t(self, key, **kw):
        s = STRINGS[self.lang][key]
        return s.format(**kw) if kw else s

    def fmt_date(self, d):
        return self.t("date_fmt", d=d.day, month=self.t("months")[d.month - 1], y=d.year)

    def _init_fonts(self):
        fam = pick_font_family(self)

        def F(size, weight="normal", **kw):
            return tkfont.Font(self, family=fam, size=size, weight=weight, **kw)

        self.f_title = F(22, "bold")
        self.f_sub = F(10)
        self.f_head = F(10, "bold")
        self.f_daynum = (F(12), F(12, "bold"))
        self.f_tile_big = (F(15), F(15, "bold"))
        self.f_small = F(9)
        self.f_small_bold = F(9, "bold")
        self.f_body = F(11)
        self.f_body_strike = F(11, overstrike=1)
        self.f_btn = F(10, "bold")
        self.f_arrow = F(14, "bold")
        self.f_stat = F(17, "bold")
        self.f_section = F(13, "bold")
        self.f_empty_icon = F(26, "bold")

    def _init_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Vertical.TScrollbar", background=P["frost"], troughcolor=C["bg"],
                        bordercolor=C["bg"], lightcolor=P["frost"], darkcolor=P["frost"],
                        arrowcolor=C["muted"], gripcount=0, width=8)
        style.map("Vertical.TScrollbar", background=[("active", P["sky"])],
                  lightcolor=[("active", P["sky"])], darkcolor=[("active", P["sky"])])
        try:                                     # okları olmayan ince kaydırma çubuğu
            style.layout("Vertical.TScrollbar", [("Vertical.Scrollbar.trough", {
                "sticky": "ns", "children": [("Vertical.Scrollbar.thumb",
                                               {"expand": "1", "sticky": "nswe"})]})])
        except tk.TclError:
            pass

    def _maximize(self):
        if sys.platform.startswith("win") or sys.platform == "darwin":
            try:
                self.state("zoomed")
                return
            except tk.TclError:
                pass
        try:
            self.attributes("-zoomed", True)
        except tk.TclError:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

    # -- iskelet
    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self.title(self.t("app_title"))

        # üstte paletin tonlarından ince bir şerit
        strip = tk.Frame(self, height=4, bg=C["bg"])
        strip.pack(fill="x")
        for col in (P["ice"], P["frost"], P["sky"], P["aqua"], P["cyan"], P["ocean"],
                    P["deep"], P["royal"], P["navy"]):
            tk.Frame(strip, bg=col, height=4).pack(side="left", fill="x", expand=True)

        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", padx=24, pady=(16, 12))
        self.head_left = tk.Frame(top, bg=C["bg"])
        self.head_left.pack(side="left", fill="y")
        right = tk.Frame(top, bg=C["bg"])
        right.pack(side="right", anchor="n")
        self._build_lang_toggle(right)
        self.st_month = self._stat(right, self.t("stat_month"), P["royal"])
        self.st_open = self._stat(right, self.t("stat_open"), P["aqua"])
        self.st_done = self._stat(right, self.t("stat_done"), P["ocean"])
        self.st_total = self._stat(right, self.t("stat_total"), P["navy"])

        tk.Label(self, text=f"Taskil v{__version__}   ·   " + self.t("data", path=self.store.path),
                 font=self.f_small,
                 bg=C["bg"], fg=C["faint"], anchor="w"
                 ).pack(side="bottom", fill="x", padx=26, pady=(0, 8))
        self.body = tk.Frame(self, bg=C["bg"])
        self.body.pack(fill="both", expand=True)

        if self.view == "day" and self.day:
            self.show_day(self.day)
        else:
            self.show_calendar()

    def _build_lang_toggle(self, parent):
        f = tk.Frame(parent, bg=C["bg"])
        f.pack(side="right", padx=(14, 0), anchor="center")
        for code in ("tr", "en"):
            active = code == self.lang
            RoundButton(f, code.upper(), lambda c=code: self.set_lang(c), self.f_btn,
                        bg=C["accent"] if active else C["soft"],
                        fg="white" if active else C["muted"],
                        hover_bg=C["accent_dark"] if active else C["soft_hover"],
                        padx=11, pady=5, radius=9).pack(side="left", padx=2)

    def _stat(self, parent, caption, color):
        card = StatCard(parent, self, caption, color)
        card.pack(side="right", padx=(8, 0))
        return card

    def set_lang(self, code):
        if code == self.lang:
            return
        self.lang = code
        self.store.set_setting("lang", code)
        self.build_ui()

    def update_stats(self):
        total, done = self.store.stats()
        m_total, m_done = self.store.month_stats(self.year, self.month)
        self.st_total.set(total)
        self.st_done.set(done)
        self.st_open.set(total - done)
        self.st_month.set(f"{m_done}/{m_total}")

    def _clear(self, *frames):
        for fr in frames:
            for w in fr.winfo_children():
                w.destroy()

    # ------------------------------------------------------------ takvim görünümü
    def show_calendar(self):
        self.view, self.day_view = "calendar", None
        self._clear(self.head_left, self.body)

        nav = tk.Frame(self.head_left, bg=C["bg"])
        nav.pack(anchor="w")
        self.month_btn = RoundButton(nav, " ", lambda: self.toggle_mode("months"),
                                     self.f_title, bg=C["bg"], padx=10, pady=2)
        self.month_btn.pack(side="left")
        self.year_btn = RoundButton(nav, " ", lambda: self.toggle_mode("years"),
                                    self.f_title, bg=C["bg"], padx=10, pady=2)
        self.year_btn.pack(side="left", padx=(2, 0))
        primary_button(nav, self.t("today"), self.go_today, self.f_btn,
                       padx=16, pady=7).pack(side="left", padx=(16, 0))
        t = self.today
        tk.Label(self.head_left, font=self.f_sub, bg=C["bg"], fg=C["muted"],
                 text=self.t("today_is", date=self.fmt_date(t),
                             weekday=self.t("weekdays_long")[t.weekday()])
                 ).pack(anchor="w", padx=10, pady=(6, 0))

        self.cal_wrap = tk.Frame(self.body, bg=C["bg"])
        self.cal_wrap.pack(fill="both", expand=True, padx=21, pady=(0, 6))
        self.render_calendar()

    def render_calendar(self):
        months = self.t("months")
        self.month_btn.set_text(f"{months[self.month - 1]} ▾")
        self.year_btn.set_text(f"{self.year} ▾")
        self.month_btn.set_bg(C["soft"] if self.mode == "months" else C["bg"])
        self.year_btn.set_bg(C["soft"] if self.mode == "years" else C["bg"])

        wrap = self.cal_wrap
        self._clear(wrap)
        for i in range(8):
            wrap.columnconfigure(i, weight=0, uniform="")
            wrap.rowconfigure(i, weight=0, uniform="")
        {"days": self._render_days, "months": self._render_months,
         "years": self._render_years}[self.mode](wrap)
        self.update_stats()

    def _render_days(self, wrap):
        wd = self.t("weekdays")
        for c in range(7):
            wrap.columnconfigure(c, weight=1, uniform="col")
            tk.Label(wrap, text=wd[c].upper(), font=self.f_small_bold, bg=C["bg"],
                     fg=C["weekend"] if c >= 5 else C["muted"]
                     ).grid(row=0, column=c, pady=(0, 6))
        for r in range(1, 7):
            wrap.rowconfigure(r, weight=1, uniform="row")

        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(self.year, self.month)
        days = [d for w in weeks for d in w]
        while len(days) < 42:                      # her zaman 6 satır
            days.append(days[-1] + timedelta(days=1))
        for i, d in enumerate(days):
            tasks = self.store.tasks_for(d)
            in_month = d.month == self.month
            kind = "today" if d == self.today else ("normal" if in_month else "other")
            fg = C["weekend"] if (kind == "normal" and d.weekday() >= 5) else None
            tile = Tile(wrap, self, self.show_day, self.f_daynum)
            tile.grid(row=i // 7 + 1, column=i % 7, sticky="nsew", padx=3, pady=3)
            tile.set(d, str(d.day), kind, len(tasks), sum(1 for t in tasks if t["done"]),
                     title_fg=fg, bold=d == self.today)

    def _picker_title(self, wrap, text, paging=False):
        bar = tk.Frame(wrap, bg=C["bg"])
        bar.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8), padx=3)
        tk.Label(bar, text=text, font=self.f_section, bg=C["bg"],
                 fg=C["text"]).pack(side="left")
        if paging:
            RoundButton(bar, "›", lambda: self._page_years(12), self.f_arrow,
                        padx=11, pady=1).pack(side="right")
            RoundButton(bar, "‹", lambda: self._page_years(-12), self.f_arrow,
                        padx=11, pady=1).pack(side="right", padx=(0, 4))

    def _grid_4x3(self, wrap):
        for c in range(4):
            wrap.columnconfigure(c, weight=1, uniform="col")
        for r in range(1, 4):
            wrap.rowconfigure(r, weight=1, uniform="row")

    def _render_months(self, wrap):
        self._picker_title(wrap, self.t("pick_month"))
        self._grid_4x3(wrap)
        months = self.t("months")
        for m in range(1, 13):
            total, done = self.store.month_stats(self.year, m)
            is_now = (self.year, m) == (self.today.year, self.today.month)
            tile = Tile(wrap, self, self._pick_month, self.f_tile_big, radius=16)
            tile.grid(row=(m - 1) // 4 + 1, column=(m - 1) % 4, sticky="nsew", padx=4, pady=4)
            tile.set(m, months[m - 1], "today" if is_now else "normal", total, done,
                     selected=m == self.month, bold=is_now)

    def _render_years(self, wrap):
        start = self.year_page
        self._picker_title(wrap, f"{self.t('pick_year')}  ·  {start} – {start + 11}", paging=True)
        self._grid_4x3(wrap)
        for i in range(12):
            y = start + i
            total, done = self.store.year_stats(y)
            is_now = y == self.today.year
            tile = Tile(wrap, self, self._pick_year, self.f_tile_big, radius=16)
            tile.grid(row=i // 4 + 1, column=i % 4, sticky="nsew", padx=4, pady=4)
            tile.set(y, str(y), "today" if is_now else "normal", total, done,
                     selected=y == self.year, bold=is_now)

    def toggle_mode(self, mode):
        self.mode = "days" if self.mode == mode else mode
        if self.mode == "years":
            self.year_page = self.year - 4
        self.render_calendar()

    def _pick_month(self, m):
        self.month, self.mode = m, "days"
        self.render_calendar()

    def _pick_year(self, y):
        self.year, self.mode = y, "days"
        self.render_calendar()

    def _page_years(self, delta):
        self.year_page += delta
        self.render_calendar()

    def go_today(self):
        self.year, self.month, self.mode = self.today.year, self.today.month, "days"
        self.render_calendar()

    # -------------------------------------------------------------- gün görünümü
    def show_day(self, d: date):
        self.view, self.day = "day", d
        self.year, self.month, self.mode = d.year, d.month, "days"
        self._clear(self.head_left, self.body)

        row = tk.Frame(self.head_left, bg=C["bg"])
        row.pack(anchor="w")
        RoundButton(row, self.t("back"), self.show_calendar, self.f_btn,
                    padx=14, pady=7).pack(side="left", padx=(0, 16))
        RoundButton(row, "‹", lambda: self.show_day(d - timedelta(days=1)), self.f_arrow,
                    padx=11, pady=1).pack(side="left")
        RoundButton(row, "›", lambda: self.show_day(d + timedelta(days=1)), self.f_arrow,
                    padx=11, pady=1).pack(side="left", padx=(4, 0))
        tk.Label(row, text=self.fmt_date(d), font=self.f_title, bg=C["bg"],
                 fg=C["text"]).pack(side="left", padx=(14, 0))
        sub = tk.Frame(self.head_left, bg=C["bg"])
        sub.pack(anchor="w", pady=(6, 0))
        tk.Label(sub, text=self.t("weekdays_long")[d.weekday()], font=self.f_sub,
                 bg=C["bg"], fg=C["muted"]).pack(side="left")
        if d == self.today:
            Pill(sub, self.f_small_bold, P["ice"], P["deep"]).set(self.t("today")
                                                                  ).pack(side="left", padx=(8, 0))

        self.day_view = DayView(self.body, self, d)
        self.day_view.pack(fill="both", expand=True)
        self.update_stats()

    # ------------------------------------------------------------ olaylar
    def _on_escape(self, _e):
        if self.view == "day":
            self.show_calendar()
        elif self.mode != "days":
            self.mode = "days"
            self.render_calendar()

    def _global_press(self, e):
        """Görev düzenlenirken kutunun dışında herhangi bir yere tıklanırsa kaydet."""
        dv = self.day_view
        if not dv or not dv.winfo_exists() or dv.list.editor is None:
            return
        w = e.widget
        if w is dv.list or w is dv.list.editor:      # liste kendi tıklamasını yönetiyor
            return
        if isinstance(w, tk.Misc) and str(w).startswith(str(dv.list.editor)):
            return
        dv.list.commit_current()

    def _on_wheel(self, e):
        if self.view == "day" and self.day_view:
            self.day_view.wheel(e)

    def _check_day_change(self):
        if date.today() != self.today:
            self.today = date.today()
            if self.view == "calendar":
                self.show_calendar()
        self.after(60_000, self._check_day_change)


# ------------------------------------------------------------ görev kart listesi

class TaskList(tk.Canvas):
    """Görevleri tek bir tuval üzerinde yuvarlak köşeli kartlar olarak çizer.
    Sürükle-bırak sırasında kartlar akıcı biçimde yer değiştirir."""

    X0, GAP, TOP, R, MIN_H = 4, 10, 6, 14, 60
    EDGE = 40            # sürüklerken otomatik kaydırma bölgesi (px)
    SUB_H = 19           # tarih satırı yüksekliği

    def __init__(self, master, view):
        super().__init__(master, bg=C["bg"], highlightthickness=0, bd=0, yscrollincrement=12)
        self.view, self.app = view, view.app
        self.tasks, self.order, self.geo = {}, [], {}
        self.hover = (None, None)
        self.press = self.drag = None
        self.editing = self.editor = None
        self._ed_h = 0
        self._animating = False
        self._settle_cb = None
        self.flash = {}          # tid -> 1.0 … 0.0 (yeni eklenen / taşınan kart vurgusu)
        self.total_h = 0
        self.bind("<Configure>", lambda e: self.drag or self.redraw())
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self.drag or self._set_hover(None, None))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_double)

    # -- veri
    def set_tasks(self, tasks):
        self.tasks = {t["id"]: t for t in tasks}
        self.order = [t["id"] for t in tasks]
        self.redraw()

    # -- geometri
    def _xs(self):
        w = self.winfo_width()
        x1, x2 = self.X0, w - self.X0 - 2
        return x1, x2, x1 + 78, x2 - 124     # kart sol/sağ, metin sol/sağ

    def _icon_x(self):
        x2 = self._xs()[1]
        return {"delete": x2 - 26, "bottom": x2 - 60, "top": x2 - 92}

    def _fmt_time(self, iso):
        try:
            dt = datetime.fromisoformat(iso)
        except (TypeError, ValueError):
            return None
        hm = dt.strftime("%H:%M")
        if dt.date() == self.view.day:
            return hm
        return self.app.t("short_dt", d=dt.day, m=self.app.t("months_short")[dt.month - 1], hm=hm)

    def _subline(self, t):
        parts = []
        c = self._fmt_time(t.get("created_at"))
        if c:
            parts.append(self.app.t("created", t=c))
        if t["done"]:
            d = self._fmt_time(t.get("done_at"))
            if d:
                parts.append(self.app.t("done_at", t=d))
        return "  ·  ".join(parts)

    def _measure(self, t, text_w):
        if self.editing == t["id"] and self.editor is not None:
            th = self.editor.winfo_reqheight()
            return th, max(self.MIN_H, th + 22)
        item = self.create_text(0, -5000, text=t["title"], anchor="nw", width=text_w,
                                font=self.app.f_body_strike if t["done"] else self.app.f_body)
        bb = self.bbox(item)
        self.delete(item)
        th = (bb[3] - bb[1]) if bb else 20
        content = th + (self.SUB_H if self._subline(t) else 0)
        return th, max(self.MIN_H, content + 30)

    def redraw(self):
        self.delete("all")
        w, vh = self.winfo_width(), self.winfo_height()
        if w < 200:
            return
        if not self.order:
            self._draw_empty(w)
            self.configure(scrollregion=(0, 0, w, vh))
            return
        x1, x2, tx1, tx2 = self._xs()
        y = self.TOP
        self.geo = {}
        for tid in self.order:
            th, h = self._measure(self.tasks[tid], tx2 - tx1)
            self.geo[tid] = {"y": y, "h": h, "th": th, "target": y}
            y += h + self.GAP
        self.total_h = y
        for tid in self.order:
            self._draw_card(tid)
        self.configure(scrollregion=(0, 0, w, max(y, vh)))

    def _draw_empty(self, w):
        a, cx = self.app, w / 2
        self.create_oval(cx - 34, 30, cx + 34, 98, fill=P["ice"], outline="")
        self.create_oval(cx - 24, 40, cx + 24, 88, fill=C["surface"], outline="")
        self.create_text(cx, 64, text="✓", font=a.f_empty_icon, fill=P["aqua"])
        self.create_text(cx, 122, text=a.t("empty_title"), font=a.f_section, fill=C["text"])
        self.create_text(cx, 148, text=a.t("empty_sub"), font=a.f_sub, fill=C["muted"],
                         width=min(420, w - 40), justify="center")

    def _move_icon(self, x, cy, up, color, tag):
        """Çubuklu ok: en üste (⤒) / en alta (⤓)."""
        kw = dict(fill=color, width=2, capstyle="round", joinstyle="round", tags=tag)
        by = cy - 7 if up else cy + 7
        self.create_line(x - 6, by, x + 6, by, **kw)
        self.create_line(x, cy + 7 if up else cy - 7, x, cy - 3 if up else cy + 3, **kw)
        if up:
            self.create_line(x - 4, cy + 1, x, cy - 3, x + 4, cy + 1, **kw)
        else:
            self.create_line(x - 4, cy - 1, x, cy + 3, x + 4, cy - 1, **kw)

    def _draw_card(self, tid):
        a, t, g = self.app, self.tasks[tid], self.geo[tid]
        tag = f"c{tid}"
        self.delete(tag)
        x1, x2, tx1, tx2 = self._xs()
        y, h, th = g["y"], g["h"], g["th"]
        hov_id, zone = self.hover
        dragging = bool(self.drag and self.drag["id"] == tid)
        hovered = hov_id == tid and not self.drag
        done = t["done"]
        fl = self.flash.get(tid, 0)

        # gölge + kart
        if dragging:
            fill, border, shadow, soff = C["drag"], P["aqua"], "#CBE9E5", 7
        elif hovered:
            fill, border, shadow, soff = "#FCFEFE", P["frost"], "#D8EEEB", 4
        else:
            fill = C["surface_alt"] if done else C["surface"]
            border, shadow, soff = C["border"], C["shadow"], 2
        if fl:                       # yeni eklenen kart turkuaz parlayıp söner
            fill = mix(fill, P["ice"], fl)
            border = mix(border, P["aqua"], fl)
        rounded_rect(self, x1, y + soff, x2, y + h + soff, self.R, fill=shadow, tags=tag)
        rounded_rect(self, x1, y, x2, y + h, self.R, fill=fill, outline=border,
                     width=2 if fl > 0.3 else 1, tags=tag)
        if done:      # tamamlanan kartlarda solda ince turkuaz şerit
            rounded_rect(self, x1 + 1, y + 12, x1 + 5, y + h - 12, 2, fill=P["sky"], tags=tag)

        cy = y + h / 2
        # sürükleme tutamacı (6 nokta)
        dot = P["aqua"] if (dragging or (hovered and zone == "handle")) else \
            (P["frost"] if hovered else "#D6ECEA")
        for i in range(3):
            for j in range(2):
                px, py = x1 + 19 + j * 6, cy - 6 + i * 6
                self.create_oval(px - 1.7, py - 1.7, px + 1.7, py + 1.7, fill=dot,
                                 outline="", tags=tag)

        # yuvarlak onay kutusu
        cx, r = x1 + 52, 11
        if done:
            self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=P["ocean"], outline="", tags=tag)
            self.create_line(cx - 5, cy, cx - 1.5, cy + 4, cx + 5.5, cy - 4, fill="white",
                             width=2.2, capstyle="round", joinstyle="round", tags=tag)
        else:
            on = hovered and zone == "check"
            self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=P["ice"] if on else C["surface"],
                             outline=P["aqua"] if on else "#9BD6D0", width=2, tags=tag)
            if on:
                self.create_line(cx - 5, cy, cx - 1.5, cy + 4, cx + 5.5, cy - 4, fill=P["ocean"],
                                 width=2, capstyle="round", joinstyle="round", tags=tag)

        # metin + tarih satırı
        if self.editing == tid and self.editor is not None:
            self.create_window(tx1 - 9, y + (h - th) / 2, anchor="nw", window=self.editor,
                               width=tx2 - tx1 + 18, tags=tag)
        else:
            sub = self._subline(t)
            content = th + (self.SUB_H if sub else 0)
            ty = y + (h - content) / 2
            self.create_text(tx1, ty, anchor="nw", text=t["title"], width=tx2 - tx1,
                             font=a.f_body_strike if done else a.f_body,
                             fill=C["faint"] if done else C["text"], tags=tag)
            if sub:
                self.create_text(tx1, ty + th + 4, anchor="nw", text=sub, font=a.f_small,
                                 fill="#4FB3AB" if done else "#8AAAAE", tags=tag)

        # sağdaki eylem ikonları: en üste, en alta, sil
        ix = self._icon_x()
        idx = self.order.index(tid)
        enabled = {"top": idx > 0, "bottom": idx < len(self.order) - 1, "delete": True}
        for name in ("top", "bottom", "delete"):
            x = ix[name]
            active = hovered and zone == name and enabled[name]
            if active:
                self.create_oval(x - 15, cy - 15, x + 15, cy + 15, tags=tag, outline="",
                                 fill=C["danger_soft"] if name == "delete" else C["soft"])
            if not enabled[name]:
                col = "#E4EFEF"
            elif active:
                col = C["danger"] if name == "delete" else P["deep"]
            else:
                col = C["muted"] if hovered else "#C2DADA"
            if name == "delete":
                self.create_text(x, cy, text="✕", font=a.f_body, fill=col, tags=tag)
            else:
                self._move_icon(x, cy, name == "top", col, tag)
        if hovered and zone in ix and enabled[zone]:
            self._tooltip(ix[zone], y, h, a.t("tip_" + zone), tag)

    def _tooltip(self, x, y, h, text, tag):
        a = self.app
        tw = a.f_small_bold.measure(text) + 18
        th = a.f_small_bold.metrics("linespace") + 8
        x2 = self._xs()[1]
        left = min(x - tw / 2, x2 - tw)
        if y - th - 6 >= self.canvasy(0):       # üstte yer varsa üstte, yoksa altta
            top = y - th - 6
        else:
            top = y + h + 6
        rounded_rect(self, left, top, left + tw, top + th, 7, fill=P["navy"], tags=(tag, "tip"))
        self.create_text(left + tw / 2, top + th / 2, text=text, font=a.f_small_bold,
                         fill="white", tags=(tag, "tip"))
        self.tag_raise("tip")

    # -- vurgu animasyonu
    def flash_card(self, tid):
        self.flash[tid] = 1.0
        self._flash_step()

    def _flash_step(self):
        if getattr(self, "_flash_job", None):
            return
        def step():
            self._flash_job = None
            for tid in list(self.flash):
                self.flash[tid] = max(0.0, self.flash[tid] - 0.06)
                if tid in self.geo and not self.drag:
                    self._draw_card(tid)
                if self.flash[tid] <= 0:
                    del self.flash[tid]
            if self.flash:
                self._flash_job = self.after(35, step)
        self._flash_job = self.after(250, step)      # önce kısa süre tam parlak kalsın

    def ensure_visible(self, tid):
        g = self.geo.get(tid)
        if not g:
            return
        sr = self.cget("scrollregion").split()
        total = float(sr[3]) if len(sr) == 4 else 0
        vh = self.winfo_height()
        if total <= vh:
            return
        top = self.canvasy(0)
        if g["y"] < top:
            self.yview_moveto(max(g["y"] - 8, 0) / total)
        elif g["y"] + g["h"] > top + vh:
            self.yview_moveto((g["y"] + g["h"] - vh + 12) / total)

    # -- isabet testi
    def _hit(self, ex, ey):
        y = self.canvasy(ey)
        x1, x2, _, _ = self._xs()
        for tid in self.order:
            g = self.geo.get(tid)
            if g and g["y"] <= y <= g["y"] + g["h"] and x1 <= ex <= x2:
                cy = g["y"] + g["h"] / 2
                if (ex - (x1 + 52)) ** 2 + (y - cy) ** 2 <= 16 ** 2:
                    return tid, "check"
                for name, ix in self._icon_x().items():
                    if abs(ex - ix) <= 15 and abs(y - cy) <= 16:
                        return tid, name
                if ex < x1 + 36:
                    return tid, "handle"
                return tid, "body"
        return None, None

    def _set_hover(self, tid, zone):
        old = self.hover
        if old == (tid, zone):
            return
        self.hover = (tid, zone)
        for i in {old[0], tid}:
            if i in self.geo:
                self._draw_card(i)
        if tid in self.geo:
            self.tag_raise(f"c{tid}")      # ipucu balonu komşu kartın altında kalmasın
        cursor = "hand2" if zone in ("check", "delete", "top", "bottom") else \
            ("fleur" if zone == "handle" else "")
        self.config(cursor=cursor)

    def refresh_hover(self):
        if self.drag:
            return
        px, py = self.winfo_pointerxy()
        self._set_hover(*self._hit(px - self.winfo_rootx(), py - self.winfo_rooty()))

    # -- fare olayları
    def _on_motion(self, e):
        if not self.drag:
            self._set_hover(*self._hit(e.x, e.y))

    def _on_press(self, e):
        if self.editor is not None:          # düzenleme açıkken dışarı tıklamak kaydeder
            if self.winfo_containing(e.x_root, e.y_root) is not self.editor:
                self.commit_current()
            self.press = None
            return
        tid, zone = self._hit(e.x, e.y)
        self.press = {"id": tid, "zone": zone, "y": e.y, "y_root": e.y_root} if tid else None

    def _on_double(self, e):
        tid, zone = self._hit(e.x, e.y)
        if tid and zone in ("body", "handle") and self.editor is None:
            self.start_edit(tid)

    def _on_drag(self, e):
        p = self.press
        if not p:
            return
        if not self.drag:
            if p["zone"] not in ("body", "handle") or self.editing:
                return
            if abs(e.y_root - p["y_root"]) < 5:
                return
            g = self.geo[p["id"]]
            self.drag = {"id": p["id"], "grab": self.canvasy(p["y"]) - g["y"],
                         "y_root": e.y_root, "order0": list(self.order)}
            self.hover = (None, None)
            for tid in self.order:
                self._draw_card(tid)
            self.tag_raise(f"c{p['id']}")
            self.config(cursor="fleur")
            self._start_anim()
            self._autoscroll()
        self.drag["y_root"] = e.y_root
        self._follow()

    def _follow(self):
        d = self.drag
        tid = d["id"]
        g = self.geo[tid]
        py = self.canvasy(d["y_root"] - self.winfo_rooty())
        ny = max(0, min(py - d["grab"], self.total_h - g["h"] - self.GAP + 6))
        self.move(f"c{tid}", 0, ny - g["y"])
        g["y"] = ny
        center = ny + g["h"] / 2
        others = [o for o in self.order if o != tid]
        new_idx = sum(1 for o in others
                      if self.geo[o]["target"] + self.geo[o]["h"] / 2 < center)
        if new_idx != self.order.index(tid):
            self.order = others[:new_idx] + [tid] + others[new_idx:]
            self._retarget()

    def _retarget(self):
        y = self.TOP
        for o in self.order:
            self.geo[o]["target"] = y
            y += self.geo[o]["h"] + self.GAP

    def _start_anim(self):
        if not self._animating:
            self._animating = True
            self._animate()

    def _animate(self):
        moving = False
        drag_id = self.drag["id"] if self.drag else None
        for tid in self.order:
            if tid == drag_id or tid not in self.geo:
                continue
            g = self.geo[tid]
            diff = g["target"] - g["y"]
            if abs(diff) > 0.5:
                step = diff * 0.3 if abs(diff) > 3 else diff
                self.move(f"c{tid}", 0, step)
                g["y"] += step
                moving = True
        if self.drag or moving:
            self.after(15, self._animate)
        else:
            self._animating = False
            if self._settle_cb:
                cb, self._settle_cb = self._settle_cb, None
                cb()

    def _autoscroll(self):
        """Kenara yaklaşınca sabit hızla, yalnızca liste taşıyorsa kaydırır."""
        d = self.drag
        if not d:
            return
        cy = d["y_root"] - self.winfo_rooty()
        h = self.winfo_height()
        lo, hi = self.yview()
        step = 0
        if cy < self.EDGE and lo > 0:
            step = -1
        elif cy > h - self.EDGE and hi < 1:
            step = 1
        if step:
            self.yview_scroll(step, "units")
            self._follow()
        self.after(40, self._autoscroll)

    def _on_release(self, e):
        p, self.press = self.press, None
        if self.drag:
            d, self.drag = self.drag, None
            self.config(cursor="")
            order = list(self.order)
            self._settle_cb = lambda: self.view.reorder(order, changed=order != d["order0"])
            self._draw_card(d["id"])            # kaldırılmış görünümü geri al
            self._start_anim()                  # son kart yerine kayarak otursun
            return
        if p:
            tid, zone = self._hit(e.x, e.y)
            if tid == p["id"] and zone == p["zone"]:
                if zone == "check":
                    self.view.toggle(tid)
                elif zone == "delete":
                    self.view.delete(tid)
                elif zone in ("top", "bottom"):
                    self.view.move_to(tid, zone)

    # -- satır içi düzenleme
    def start_edit(self, tid):
        self.commit_current()
        self.editing = tid
        ed = GrowText(self, self.app.f_body, max_lines=12, bg="#F6FCFB", fg=C["text"],
                      insertbackground=C["text"], padx=8, pady=6, highlightthickness=1,
                      highlightbackground=P["aqua"], highlightcolor=P["aqua"],
                      selectbackground=P["frost"], selectforeground=C["text"])
        ed.set_value(self.tasks[tid]["title"])
        ed.bind("<Return>", lambda e: self._commit_edit(tid))
        ed.bind("<Shift-Return>", lambda e: None)
        ed.bind("<Escape>", lambda e: self._cancel_edit())
        ed.bind("<FocusOut>", lambda e: self._commit_edit(tid), add="+")
        ed.bind("<Configure>", self._editor_resized, add="+")
        self.editor, self._ed_h = ed, 0
        self.redraw()
        self.after_idle(lambda: ed.winfo_exists() and (ed.focus_set(), ed.tag_add("sel", "1.0", "end-1c")))

    def _editor_resized(self, e):
        if e.height != self._ed_h:
            self._ed_h = e.height
            self.after_idle(self.redraw)

    def _close_editor(self):
        self.editing = None
        if self.editor is not None:
            ed, self.editor = self.editor, None
            ed.destroy()

    def commit_current(self):
        if self.editing is not None:
            self._commit_edit(self.editing)

    def _commit_edit(self, tid):
        if self.editing != tid or self.editor is None:
            return "break"
        text = self.editor.value().strip()
        self._close_editor()
        self.view.rename(tid, text)          # veriye hemen yaz, ekranı sonra yenile
        return "break"

    def _cancel_edit(self):
        self._close_editor()
        self.after_idle(self.redraw)
        return "break"           # takvime dönüş (Esc) tetiklenmesin


# ------------------------------------------------------------------ gün sayfası

class DayView(tk.Frame):
    MAX_WIDTH = 860

    def __init__(self, master, app: App, d: date):
        super().__init__(master, bg=C["bg"])
        self.app, self.store, self.day = app, app.store, d
        self._toast_job = None
        self._build()
        self.after_idle(self.refresh)
        self.after_idle(self.entry.focus_set)

    def _build(self):
        a = self.app
        col = tk.Frame(self, bg=C["bg"])
        col.pack(fill="both", expand=True, padx=24, pady=(4, 6))
        self.bind("<Configure>", lambda e: col.pack_configure(
            padx=max(24, (e.width - self.MAX_WIDTH) // 2)))

        self.prog_card = ProgressCard(col, a)
        self.prog_card.pack(fill="x")

        # ekleme alanı — uzun metinde büyüyen kutu
        add = tk.Frame(col, bg=C["bg"])
        add.pack(fill="x", pady=(14, 18))
        primary_button(add, a.t("add"), self.add, a.f_btn, padx=20, pady=13, radius=13
                       ).pack(side="right", anchor="n")
        self.input = RoundedInput(add, a, a.t("placeholder"))
        self.input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry = self.input.text
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)      # yeni satır

        # liste başlığı
        head = tk.Frame(col, bg=C["bg"])
        head.pack(fill="x", padx=6, pady=(0, 8))
        tk.Label(head, text=a.t("tasks_header"), font=a.f_section, bg=C["bg"],
                 fg=C["text"]).pack(side="left")
        self.count_pill = Pill(head, a.f_small_bold, C["soft"], P["deep"])
        self.count_pill.pack(side="left", padx=(8, 0))
        self.toast = Pill(head, a.f_small_bold, P["ocean"], "white", padx=12, pady=4)
        self.top_div = tk.Frame(col, bg=C["bg"], height=1)
        self.top_div.pack(fill="x")

        tk.Label(col, text=a.t("hint"), font=a.f_small, bg=C["bg"],
                 fg=C["faint"]).pack(side="bottom", pady=(8, 0))
        self.bot_div = tk.Frame(col, bg=C["bg"], height=1)
        self.bot_div.pack(side="bottom", fill="x")

        # kart listesi
        lst = tk.Frame(col, bg=C["bg"])
        lst.pack(fill="both", expand=True, pady=(6, 4))
        self.list = TaskList(lst, self)
        self.sb = ttk.Scrollbar(lst, orient="vertical", command=self.list.yview)
        self.list.configure(yscrollcommand=self._sb_set)
        self.list.pack(side="left", fill="both", expand=True)

    def _sb_set(self, lo, hi):
        lo, hi = float(lo), float(hi)
        if hi - lo >= 0.999:
            self.sb.pack_forget()
        elif not self.sb.winfo_ismapped():
            self.sb.pack(side="right", fill="y", padx=(8, 0))
        self.sb.set(lo, hi)
        # kaydırıldığında üstte/altta ince ayraç çizgisi belirir
        self.top_div.config(bg=C["border_strong"] if lo > 0.001 else C["bg"])
        self.bot_div.config(bg=C["border_strong"] if hi < 0.999 else C["bg"])

    def wheel(self, e):
        lo, hi = self.list.yview()
        if hi - lo >= 0.999:
            return
        if e.num == 4:
            step = -1
        elif e.num == 5:
            step = 1
        elif abs(e.delta) >= 120:
            step = -int(e.delta / 120)
        else:
            step = -1 if e.delta > 0 else 1
        self.list.yview_scroll(step * 4, "units")
        self.list.refresh_hover()

    def show_toast(self, text):
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self.toast.set(text).pack(side="right")
        self._toast_job = self.after(1600, self._hide_toast)

    def _hide_toast(self):
        self._toast_job = None
        if self.toast.winfo_exists():
            self.toast.pack_forget()

    def refresh(self, scroll_end=False):
        if not self.winfo_exists():
            return
        tasks = self.store.tasks_for(self.day)
        top = self.list.yview()[0]
        self.list.set_tasks(tasks)
        self.list.yview_moveto(1.0 if scroll_end else top)
        n, done = len(tasks), sum(1 for t in tasks if t["done"])
        self.prog_card.set(done, n)
        self.count_pill.set(str(n))

    # -- işlemler
    def _changed(self, **kw):
        if not self.winfo_exists():
            return
        self.refresh(**kw)
        self.app.update_stats()

    def _on_enter(self, _e):
        self.add()
        return "break"

    def add(self):
        title = self.entry.value().strip()
        if not title:
            self.input.flash_error()
            return
        t = self.store.add(self.day, title)
        self.entry.set_value("")
        self._changed(scroll_end=True)
        self.list.flash_card(t["id"])
        self.show_toast(self.app.t("added_toast"))
        self.entry.focus_set()

    def toggle(self, tid):
        self.store.toggle(self.day, tid)
        self._changed()

    def delete(self, tid):
        self.store.delete(self.day, tid)
        self._changed()

    def rename(self, tid, text):
        self.store.rename(self.day, tid, text)
        self.after_idle(self._changed)

    def reorder(self, ids, changed=True):
        if changed:
            self.store.reorder(self.day, ids)
        self._changed()

    def move_to(self, tid, where):
        ids = [i for i in self.list.order if i != tid]
        ids = [tid] + ids if where == "top" else ids + [tid]
        self.store.reorder(self.day, ids)
        self._changed()
        self.list.ensure_visible(tid)
        self.list.flash_card(tid)
        self.show_toast(self.app.t("moved_toast"))


def main():
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)                     # net yazılar
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)  # görev çubuğu ikonu
        except Exception:
            pass
    App(TaskStore(resolve_data_path())).mainloop()


if __name__ == "__main__":
    main()
