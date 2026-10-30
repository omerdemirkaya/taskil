"""Taskil'i Python gerektirmeyen tek parça uygulama olarak derler ve dağıtıma hazırlar.

Kullanım (derlemek istediğin işletim sisteminde çalıştır):
    pip install pyinstaller
    python build.py                 # çıktı: dist/release/
    python build.py --arch arm64    # dosya adındaki mimari etiketini değiştirir

Çıktılar:
    Windows : Taskil-windows-x64.exe      (çift tıkla çalışır)
    macOS   : Taskil-macos-<mimari>.dmg   (Taskil.app'i Uygulamalar'a sürükle)
    Linux   : Taskil-linux-x64.tar.gz     (içindeki Taskil dosyasını çalıştır)
Dosya adlarında sürüm yok; böylece web sitesindeki "en son sürüm" linkleri hiç değişmez.
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

ROOT = Path(__file__).resolve().parent
NAME = "Taskil"
BUNDLE_ID = "app.taskil.Taskil"
DIST = ROOT / "dist"
RELEASE = DIST / "release"


def version():
    src = (ROOT / "taskil.py").read_text(encoding="utf-8")
    return re.search(r'__version__\s*=\s*"([^"]+)"', src).group(1)


def default_arch():
    m = platform.machine().lower()
    return {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(m, m)


def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


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


def build(arch):
    ver = version()
    system = platform.system()
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.rmtree(ROOT / "build", ignore_errors=True)

    sep = os.pathsep
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
           "--name", NAME, "--distpath", str(DIST), "--workpath", str(ROOT / "build"),
           "--specpath", str(ROOT / "build"),
           "--exclude-module", "PIL", "--exclude-module", "numpy"]
    for size in (32, 64, 256):
        cmd += ["--add-data", f"{ROOT / 'assets' / f'taskil-{size}.png'}{sep}assets"]

    if system == "Windows":
        cmd += ["--onefile", "--icon", str(ROOT / "assets" / "taskil.ico"),
                "--version-file", str(windows_version_file(ver))]
    elif system == "Darwin":
        cmd += ["--onedir", "--icon", str(ROOT / "assets" / "taskil.icns"),
                "--osx-bundle-identifier", BUNDLE_ID]
    else:
        cmd += ["--onefile"]
    cmd.append(str(ROOT / "taskil.py"))
    run(cmd)

    RELEASE.mkdir(parents=True, exist_ok=True)
    if system == "Windows":
        out = RELEASE / f"{NAME}-windows-{arch}.exe"
        shutil.copy2(DIST / f"{NAME}.exe", out)
    elif system == "Darwin":
        out = package_macos(ver, arch)
    else:
        out = package_linux(ver, arch)
    print(f"\nHazır: {out}  ({out.stat().st_size / 1e6:.1f} MB)")


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
    run(["hdiutil", "create", "-volname", NAME, "-srcfolder", str(stage),
         "-ov", "-format", "UDZO", str(out)])
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", default=default_arch())
    build(ap.parse_args().arch)
