"""
Патч русификации Antigravity 2.0 (Desktop app).

Применяет переводы из translations/desktop_strings.json к app.asar:
  - dist/menu.js (меню окна)
  - dist/tray.js (меню в трее)
  - dist/ideInstall/wizardHtml.js (мастер установки)

Поддерживает:
  python patch_desktop.py --dry-run
  python patch_desktop.py
  python patch_desktop.py --restore
"""

import hashlib
import json
import os
import shutil
import struct
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TRANSLATIONS_FILE = SCRIPT_DIR / "translations" / "desktop_strings.json"

APP_BASE = Path(os.environ.get(
    "ANTIGRAVITY_APP_PATH",
    r"C:\Users\gabov\AppData\Local\Programs\antigravity"
))
ASAR_FILE = APP_BASE / "resources" / "app.asar"
BACKUP_FILE = ASAR_FILE.with_suffix(".asar.bak.original")


def load_translations() -> dict:
    with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def read_asar(path: Path):
    with open(path, "rb") as f:
        magic = f.read(16)
        u0, header_size, u2, json_len = struct.unpack("<IIII", magic)
        header = json.loads(f.read(json_len).decode("utf-8"))
        data_start = 8 + header_size
        f.seek(data_start)
        data = f.read()
    return header, data


def write_asar(path: Path, header: dict, data: bytes):
    json_bytes = json.dumps(header, separators=(',', ':')).encode("utf-8")
    json_len = len(json_bytes)
    pad_len = (4 - (json_len % 4)) % 4
    padding = b"\x00" * pad_len

    u2 = json_len + 4 + pad_len
    header_size = u2 + 4
    u0 = 4

    magic = struct.pack("<IIII", u0, header_size, u2, json_len)
    with open(path, "wb") as f:
        f.write(magic)
        f.write(json_bytes)
        f.write(padding)
        f.write(data)


def find_file_entry(header: dict, path_str: str):
    parts = path_str.split("/")
    curr = header
    for p in parts:
        if "files" in curr and p in curr["files"]:
            curr = curr["files"][p]
        else:
            return None
    return curr


def compute_integrity(data: bytes, block_size: int = 4194304):
    blocks = []
    for i in range(0, len(data), block_size):
        block = data[i:i + block_size]
        blocks.append(hashlib.sha256(block).hexdigest())
    full_hash = hashlib.sha256(data).hexdigest()
    return {
        "algorithm": "SHA256",
        "hash": full_hash,
        "blockSize": block_size,
        "blocks": blocks
    }


def patch_desktop(dry_run: bool = False) -> int:
    if not ASAR_FILE.exists():
        print(f"ASAR not found: {ASAR_FILE}")
        return 0

    trans = load_translations()
    header, data = read_asar(ASAR_FILE)
    changes = 0

    # Collect files to patch and their string replacements
    targets = {
        "dist/menu.js": trans.get("menu", {}),
        "dist/tray.js": trans.get("tray", {}),
        "dist/ideInstall/wizardHtml.js": trans.get("wizard", {})
    }

    # Reconstruct data buffer with modified files
    # Flatten all files with their current offsets
    file_list = []
    def walk(node, prefix=""):
        if "files" in node:
            for name, entry in node["files"].items():
                p = f"{prefix}/{name}" if prefix else name
                if "files" in entry:
                    walk(entry, p)
                elif "offset" in entry:
                    file_list.append((p, int(entry["offset"]), int(entry["size"]), entry))
    walk(header)
    file_list.sort(key=lambda x: x[1])

    new_data_chunks = []
    current_offset = 0

    for path_str, old_offset, old_size, entry in file_list:
        file_bytes = data[old_offset:old_offset + old_size]

        if path_str in targets and targets[path_str]:
            replacements = targets[path_str]
            file_text = file_bytes.decode("utf-8", errors="replace")
            sub_changes = 0
            for en_str, ru_str in replacements.items():
                if en_str in file_text:
                    count = file_text.count(en_str)
                    print(f"  [{path_str}] ({count}x): '{en_str}' -> '{ru_str}'")
                    file_text = file_text.replace(en_str, ru_str)
                    sub_changes += count
            if sub_changes > 0:
                changes += sub_changes
                file_bytes = file_text.encode("utf-8")

        if path_str == "dist/preload.js":
            dom_script_file = SCRIPT_DIR / "translations" / "dom_translator.js"
            if dom_script_file.exists():
                with open(dom_script_file, "r", encoding="utf-8") as f:
                    dom_script = f.read()
                preload_text = file_bytes.decode("utf-8", errors="replace")
                marker = "// Antigravity UI Runtime Localizer"
                if marker in preload_text:
                    preload_text = preload_text[:preload_text.index(marker)].rstrip()
                preload_text += "\n\n" + dom_script
                file_bytes = preload_text.encode("utf-8")
                changes += 1
                print("  [dist/preload.js]: Injected updated DOM Runtime Localizer")

        entry["offset"] = str(current_offset)
        entry["size"] = len(file_bytes)
        if "integrity" in entry:
            entry["integrity"] = compute_integrity(file_bytes)

        new_data_chunks.append(file_bytes)
        current_offset += len(file_bytes)

    print(f"\nTotal replacements: {changes}")

    if not dry_run and changes > 0:
        if not BACKUP_FILE.exists():
            shutil.copy2(ASAR_FILE, BACKUP_FILE)
            print(f"Backup created: {BACKUP_FILE}")
        new_data = b"".join(new_data_chunks)
        write_asar(ASAR_FILE, header, new_data)
        print(f"Patched ASAR written: {ASAR_FILE}")

    return changes


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    restore = "--restore" in args

    if restore:
        if BACKUP_FILE.exists():
            shutil.copy2(BACKUP_FILE, ASAR_FILE)
            print(f"Restored: {ASAR_FILE}")
        else:
            print(f"No backup found: {BACKUP_FILE}")
        return

    if dry_run:
        print("=== DRY RUN: patch_desktop.py ===")

    patch_desktop(dry_run)


if __name__ == "__main__":
    main()
