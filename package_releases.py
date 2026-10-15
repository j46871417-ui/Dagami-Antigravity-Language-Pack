#!/usr/bin/env python3
"""
Release Packaging Script for Dagami Antigravity Language Pack.
Packages standalone distribution archives for Windows, Linux, and macOS.
"""

import os
from pathlib import Path
import shutil
import tarfile
import zipfile

REPO_ROOT = Path(__file__).resolve().parent
DIST_DIR = REPO_ROOT / "release_dist"
DIST_DIR.mkdir(exist_ok=True)

VERSION = "v1.1.0"
BASE_NAME = f"DagamiAntigravityLanguagePack-{VERSION}"

COMMON_DIRS = ["translations", "resources", "assets"]
COMMON_FILES = [
    "dagami_ag_localizer.py",
    "dagami_translator_builder.py",
    "js_literals.py",
    "INSTRUCTIONS.md",
    "README.md",
    "LICENSE",
]

def add_to_zip(zf: zipfile.ZipFile, root_dir: Path, arc_prefix: str, files: list, dirs: list):
    for f in files:
        fp = root_dir / f
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
        if fp.exists():
            ti = tf.gettarinfo(fp, f"{arc_prefix}/{f}")
            if f.endswith(".sh"):
                ti.mode = 0o755  # executable permissions
            tf.addfile(ti, open(fp, "rb"))
    for d in dirs:
        dp = root_dir / d
        if dp.exists():
            for item in dp.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(root_dir)
                    ti = tf.gettarinfo(item, f"{arc_prefix}/{rel.as_posix()}")
                    tf.addfile(ti, open(item, "rb"))

def package_windows():
    out_zip = DIST_DIR / f"{BASE_NAME}-Windows.zip"
    files = COMMON_FILES + [
        "AntigravityLocalizer.exe",
        "dagami-ag-localizer.cmd",
        "dagami-ag-localizer.bat",
        "install.bat",
        "install.ps1",
    ]
    print(f"[*] Packaging Windows: {out_zip.name}...")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        add_to_zip(zf, REPO_ROOT, f"{BASE_NAME}-Windows", files, COMMON_DIRS)
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
        "AntigravityLocalizer.exe",
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
    print(f"  [+] Created {out_zip.name} ({out_zip.stat().st_size / (1024*1024):.2f} MB)")
    return out_zip

if __name__ == "__main__":
    w = package_windows()
    l = package_linux()
    m = package_macos()
    a = package_all()
    print("\n[+] All packages generated successfully in:", DIST_DIR)
