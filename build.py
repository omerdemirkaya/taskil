"""Taskil'i Python gerektirmeyen tek parça uygulama olarak derler ve dağıtıma hazırlar.

Kullanım (derlemek istediğin işletim sisteminde çalıştır):
    pip install pyinstaller
    python build.py                 # çıktı: dist/release/
    python build.py --arch arm64    # dosya adındaki mimari etiketini değiştirir

Çıktılar:
    Windows : Taskil-windows-x64.exe                (çift tıkla çalışır)
              Taskil-microsoft-store-upload.msix    (yalnızca Microsoft Store'a yüklemek için)
    macOS   : Taskil-macos-<mimari>.dmg             (Taskil.app'i Uygulamalar'a sürükle)
    Linux   : Taskil-linux-x64.tar.gz               (içindeki Taskil dosyasını çalıştır)
Dosya adlarında sürüm yok; böylece web sitesindeki "en son sürüm" linkleri hiç değişmez.

MSIX paketi için Windows SDK gerekir (GitHub'ın Windows makinelerinde hazır gelir).
"""
import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from xml.sax.saxutils import escape

# Windows konsolu Türkçe karakterleri yazdıramayabiliyor; çıktıyı UTF-8'e zorla
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent
NAME = "Taskil"
BUNDLE_ID = "app.taskil.Taskil"
DIST = ROOT / "dist"
RELEASE = DIST / "release"

# Microsoft Store (Partner Center → Product identity) bilgileri
STORE = {
    "identity_name": "Startiux.Taskil",
    "publisher": "CN=50FDEF67-1E39-4BBB-BE9A-4A4EB54AAE09",
    "publisher_display_name": "Startiux",
    "display_name": "Taskil",
    "description": "A simple, offline, calendar-based daily task planner.",
    "languages": ["en-us", "tr-tr"],
}
MSIX_FILE = f"{NAME}-microsoft-store-upload.msix"


def version():
    src = (ROOT / "taskil.py").read_text(encoding="utf-8")
    return re.search(r'__version__\s*=\s*"([^"]+)"', src).group(1)


def default_arch():
    m = platform.machine().lower()
    return {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(m, m)


def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, cwd=ROOT)


def windows_version_file(ver):
    """Dosya özelliklerinde görünen ürün adı / sürüm bilgisi."""
    nums = (ver.split(".") + ["0", "0", "0"])[:4]
    tup = ", ".join(n if n.isdigit() else "0" for n in nums)
    path = DIST / "version_info.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers=({tup}), prodvers=({tup})),
  kids=[
    StringFileInfo([StringTable('041F04B0', [
      StringStruct('ProductName', '{NAME}'),
      StringStruct('FileDescription', '{NAME}'),
      StringStruct('FileVersion', '{ver}'),
      StringStruct('ProductVersion', '{ver}'),
      StringStruct('OriginalFilename', '{NAME}.exe'),
      StringStruct('LegalCopyright', '{NAME}')])]),
    VarFileInfo([VarStruct('Translation', [0x041F, 1200])])
  ]
)
""", encoding="utf-8")
    return path


def pyinstaller(mode, distpath, work, extra=()):
    sep = os.pathsep
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", mode,
           "--name", NAME, "--distpath", distpath, "--workpath", ROOT / "build" / work,
           "--specpath", ROOT / "build" / work,
           "--exclude-module", "PIL", "--exclude-module", "numpy", *extra]
    for size in (32, 64, 256):
        cmd += ["--add-data", f"{ROOT / 'assets' / f'taskil-{size}.png'}{sep}assets"]
    cmd.append(ROOT / "taskil.py")
    run(cmd)


def build(arch):
    ver = version()
    system = platform.system()
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    RELEASE.mkdir(parents=True, exist_ok=True)

    if system == "Windows":
        win = ["--icon", ROOT / "assets" / "taskil.ico", "--version-file", windows_version_file(ver)]
        pyinstaller("--onefile", DIST, "exe", win)
        out = RELEASE / f"{NAME}-windows-{arch}.exe"
        shutil.copy2(DIST / f"{NAME}.exe", out)
        outputs = [out]
        msix = package_msix(ver, win)
        if msix:
            outputs.append(msix)
    elif system == "Darwin":
        pyinstaller("--onedir", DIST, "app", ["--icon", ROOT / "assets" / "taskil.icns",
                                               "--osx-bundle-identifier", BUNDLE_ID])
        outputs = [package_macos(ver, arch)]
    else:
        pyinstaller("--onefile", DIST, "bin")
        outputs = [package_linux(ver, arch)]

    print()
    for out in outputs:
        print(f"Hazır: {out}  ({out.stat().st_size / 1e6:.1f} MB)")


# ------------------------------------------------------------------ macOS / Linux

def package_macos(ver, arch):
    app = DIST / f"{NAME}.app"
    plist = app / "Contents" / "Info.plist"
    for key, val in (("CFBundleShortVersionString", ver), ("CFBundleVersion", ver),
                     ("NSHighResolutionCapable", "true")):
        typ = "-bool" if val == "true" else "-string"
        subprocess.run(["defaults", "write", str(plist), key, typ, val], check=False)
    subprocess.run(["plutil", "-convert", "xml1", str(plist)], check=False)
    # imzasız uygulama: en azından geçici (ad-hoc) imza at ki Apple Silicon'da açılabilsin
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], check=False)

    stage = DIST / "dmg"
    stage.mkdir()
    shutil.copytree(app, stage / app.name, symlinks=True)
    os.symlink("/Applications", stage / "Applications")
    out = RELEASE / f"{NAME}-macos-{arch}.dmg"
    run(["hdiutil", "create", "-volname", NAME, "-srcfolder", stage,
         "-ov", "-format", "UDZO", out])
    return out


def package_linux(ver, arch):
    folder = f"{NAME}-linux-{arch}"
    stage = DIST / folder
    stage.mkdir()
    shutil.copy2(DIST / NAME, stage / NAME)
    (stage / NAME).chmod(0o755)
    shutil.copy2(ROOT / "assets" / "taskil-256.png", stage / "taskil.png")
    install = stage / "install.sh"
    install.write_text("""#!/bin/sh
# Taskil'i kullanıcı menüsüne ekler (yönetici izni gerekmez).
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons"
cp "$DIR/Taskil" "$HOME/.local/bin/taskil"
cp "$DIR/taskil.png" "$HOME/.local/share/icons/taskil.png"
cat > "$HOME/.local/share/applications/taskil.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Taskil
Comment=Daily task calendar
Exec=$HOME/.local/bin/taskil
Icon=$HOME/.local/share/icons/taskil.png
Categories=Office;Calendar;
Terminal=false
EOF
echo "Taskil kuruldu. Uygulama menüsünden açabilirsiniz."
""", encoding="utf-8")
    install.chmod(0o755)
    out = RELEASE / f"{folder}.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        tar.add(stage, arcname=folder)
    return out


# ------------------------------------------------------------- Microsoft Store

def msix_version(ver):
    """MSIX sürümü dört parçalı olmalı; Store'da son parça 0 olmak zorunda."""
    nums = [int(n) if n.isdigit() else 0 for n in re.split(r"[.\-+]", ver)[:3]]
    nums += [0] * (3 - len(nums))
    return ".".join(map(str, nums)) + ".0"


def appx_manifest(ver):
    s = {k: escape(v) if isinstance(v, str) else v for k, v in STORE.items()}
    langs = "\n".join(f'    <Resource Language="{lang}" />' for lang in STORE["languages"])
    return f"""<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  IgnorableNamespaces="uap rescap">
  <Identity Name="{s['identity_name']}" Publisher="{s['publisher']}"
            Version="{msix_version(ver)}" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>{s['display_name']}</DisplayName>
    <PublisherDisplayName>{s['publisher_display_name']}</PublisherDisplayName>
    <Description>{s['description']}</Description>
    <Logo>Assets\\StoreLogo.png</Logo>
  </Properties>
  <Resources>
{langs}
  </Resources>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.26100.0" />
  </Dependencies>
  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
  <Applications>
    <Application Id="Taskil" Executable="{NAME}.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="{s['display_name']}" Description="{s['description']}"
        BackgroundColor="transparent"
        Square150x150Logo="Assets\\Square150x150Logo.png"
        Square44x44Logo="Assets\\Square44x44Logo.png" />
    </Application>
  </Applications>
</Package>
"""


def sdk_tool(name):
    """Windows SDK içindeki en yeni makeappx.exe / makepri.exe'yi bulur."""
    base = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin"
    found = []
    for p in base.glob(f"10.*/x64/{name}"):
        try:
            found.append((tuple(int(x) for x in p.parent.parent.name.split(".")), p))
        except ValueError:
            continue
    if found:
        return max(found)[1]
    w = shutil.which(name)
    return Path(w) if w else None


def stage_msix(ver, win_args):
    """PyInstaller klasör çıktısı + görseller + manifest: paketlenecek klasörü hazırlar."""
    pyinstaller("--onedir", DIST / "msix-app", "msix", win_args)
    stage = DIST / "msix"
    shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(DIST / "msix-app" / NAME, stage)
    shutil.copytree(ROOT / "assets" / "msix", stage / "Assets")
    (stage / "AppxManifest.xml").write_text(appx_manifest(ver), encoding="utf-8")
    return stage


def build_pri(makepri, stage):
    """Görsellerin ölçek/tema varyantları için resources.pri üretir (yalnızca Assets dizinini indeksler)."""
    work = DIST / "pri"
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(stage / "Assets", work / "Assets")
    shutil.copy2(stage / "AppxManifest.xml", work / "AppxManifest.xml")
    cfg = DIST / "priconfig.xml"
    run([makepri, "createconfig", "/cf", cfg, "/dq", "en-US", "/pv", "10.0.0", "/o"])
    run([makepri, "new", "/pr", work, "/cf", cfg, "/mn", work / "AppxManifest.xml",
         "/of", stage / "resources.pri", "/o"])


def package_msix(ver, win_args):
    makeappx = sdk_tool("makeappx.exe")
    if not makeappx:
        msg = "makeappx.exe bulunamadı (Windows SDK yüklü değil); MSIX paketi atlandı."
        if os.environ.get("GITHUB_ACTIONS") == "true":
            raise SystemExit(msg)
        print("UYARI:", msg)
        return None

    stage = stage_msix(ver, win_args)
    makepri = sdk_tool("makepri.exe")
    if makepri:
        try:
            build_pri(makepri, stage)
        except subprocess.CalledProcessError as e:
            print("UYARI: resources.pri üretilemedi, varsayılan görsellerle devam ediliyor:", e)
            (stage / "resources.pri").unlink(missing_ok=True)

    out = RELEASE / MSIX_FILE
    run([makeappx, "pack", "/d", stage, "/p", out, "/o"])
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", default=default_arch())
    build(ap.parse_args().arch)
