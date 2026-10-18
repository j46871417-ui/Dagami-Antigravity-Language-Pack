#!/usr/bin/env python3
"""
Release Packaging Script for Dagami Antigravity Language Pack.
Packages standalone distribution archives for Windows, Linux, and macOS.
"""

import os
import argparse
import hashlib
import json
from app_info import APP_VERSION
from pathlib import Path
import shutil
import tarfile
import zipfile

REPO_ROOT = Path(__file__).resolve().parent
WINDOWS_ROOT = REPO_ROOT
DIST_DIR = REPO_ROOT / "release_dist"
DIST_DIR.mkdir(exist_ok=True)

VERSION = "v" + APP_VERSION
BASE_NAME = f"DagamiAntigravityLanguagePack-{VERSION}"

COMMON_DIRS = ["translations", "assets"]
COMMON_FILES = [
    "language_pack.py",
    "app_info.py",
    "app_updates.py",
    "update_ui.py", "native_design.py", "platform_support.py", "launch.py",
    "build_release.py", "package_native.py", "install_desktop.py", "PORTS.md",
    "dagami_ag_localizer.py",
    "dagami_translator_builder.py",
    "js_literals.py", "jsonc_utils.py", "localizer_core.py", "localizer_state.py",
    "INSTRUCTIONS.md",
    "CHANGES_1.2.0.md",
    "README.md",
    "LICENSE", "ASSET_SOURCES.json",
]

def add_to_zip(zf: zipfile.ZipFile, root_dir: Path, arc_prefix: str, files: list, dirs: list):
    for f in files:
        fp = root_dir / f
        if not fp.is_file():
            raise FileNotFoundError(fp)
        if fp.exists():
            zf.write(fp, f"{arc_prefix}/{f}")
    for d in dirs:
        dp = root_dir / d
        if dp.exists():
            for item in dp.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(root_dir)
                    zf.write(item, f"{arc_prefix}/{rel.as_posix()}")

def add_to_tar(tf: tarfile.TarFile, root_dir: Path, arc_prefix: str, files: list, dirs: list):
    for f in files:
        fp = root_dir / f
        if not fp.is_file():
            raise FileNotFoundError(fp)
        if fp.exists():
            ti = tf.gettarinfo(fp, f"{arc_prefix}/{f}")
            if f.endswith(".sh"):
                ti.mode = 0o755  # executable permissions
            with open(fp, "rb") as stream:
                tf.addfile(ti, stream)
    for d in dirs:
        dp = root_dir / d
        if dp.exists():
            for item in dp.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(root_dir)
                    ti = tf.gettarinfo(item, f"{arc_prefix}/{rel.as_posix()}")
                    with open(item, "rb") as stream:
                        tf.addfile(ti, stream)

def add_windows_runtime(zf, prefix):
    exe = WINDOWS_ROOT / "AntigravityLocalizer.exe"
    zf.write(exe, prefix + "/" + exe.name)
    if WINDOWS_ROOT != REPO_ROOT:
        for item in WINDOWS_ROOT.rglob("*"):
            if item.is_file() and item != exe:
                zf.write(item, prefix + "/" + item.relative_to(WINDOWS_ROOT).as_posix())


def package_windows():
    out_zip = DIST_DIR / f"{BASE_NAME}-Windows.zip"
    # The standalone EXE already holds its runtime, dictionaries and assets.
    files = ["INSTRUCTIONS.md", "CHANGES_1.2.0.md", "README.md", "LICENSE", "ASSET_SOURCES.json",
    ]
    print(f"[*] Packaging Windows: {out_zip.name}...")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        add_to_zip(zf, REPO_ROOT, f"{BASE_NAME}-Windows", files, [])
        add_windows_runtime(zf, f"{BASE_NAME}-Windows")
    print(f"  [+] Created {out_zip.name} ({out_zip.stat().st_size / (1024*1024):.2f} MB)")
    return out_zip

def package_linux():
    out_tar = DIST_DIR / f"{BASE_NAME}-Linux.tar.gz"
    files = COMMON_FILES + [
        "install.sh",
        "dagami-ag-localizer.sh",
    ]
    print(f"[*] Packaging Linux: {out_tar.name}...")
    with tarfile.open(out_tar, "w:gz") as tf:
        add_to_tar(tf, REPO_ROOT, f"{BASE_NAME}-Linux", files, COMMON_DIRS)
    print(f"  [+] Created {out_tar.name} ({out_tar.stat().st_size / (1024*1024):.2f} MB)")
    return out_tar

def package_macos():
    out_zip = DIST_DIR / f"{BASE_NAME}-macOS.zip"
    files = COMMON_FILES + [
        "install.sh",
        "dagami-ag-localizer.sh",
    ]
    print(f"[*] Packaging macOS: {out_zip.name}...")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        add_to_zip(zf, REPO_ROOT, f"{BASE_NAME}-macOS", files, COMMON_DIRS)
    print(f"  [+] Created {out_zip.name} ({out_zip.stat().st_size / (1024*1024):.2f} MB)")
    return out_zip

def package_all():
    out_zip = DIST_DIR / f"{BASE_NAME}-AllPlatforms.zip"
    files = COMMON_FILES + [
        "dagami-ag-localizer.cmd",
        "dagami-ag-localizer.bat",
        "install.bat",
        "install.ps1",
        "install.sh",
        "dagami-ag-localizer.sh",
    ]
    print(f"[*] Packaging AllPlatforms: {out_zip.name}...")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        add_to_zip(zf, REPO_ROOT, f"{BASE_NAME}-AllPlatforms", files, COMMON_DIRS)
        add_windows_runtime(zf, f"{BASE_NAME}-AllPlatforms")
    print(f"  [+] Created {out_zip.name} ({out_zip.stat().st_size / (1024*1024):.2f} MB)")
    return out_zip

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows-dir", type=Path, default=REPO_ROOT)
    WINDOWS_ROOT = parser.parse_args().windows_dir.resolve()
    from app_updates import validate_exe, file_hash
    validate_exe(WINDOWS_ROOT / "AntigravityLocalizer.exe", APP_VERSION)
    w = package_windows()
    l = package_linux()
    m = package_macos()
    a = package_all()
    expected = file_hash(WINDOWS_ROOT / "AntigravityLocalizer.exe")
    for archive in (w, a):
        with zipfile.ZipFile(archive) as check:
            entry = next(n for n in check.namelist() if n.endswith("/AntigravityLocalizer.exe"))
            if hashlib.sha256(check.read(entry)).hexdigest() != expected:
                raise ValueError("ZIP EXE differs from the standalone EXE")
    sums = {path.name: file_hash(path) for path in [WINDOWS_ROOT / "AntigravityLocalizer.exe", w, l, m, a]}
    (DIST_DIR / "SHA256SUMS.txt").write_text("".join(digest + "  " + name + "\n" for name, digest in sums.items()), encoding="ascii")
    print("\n[+] All packages use the same verified Windows EXE:", DIST_DIR)
