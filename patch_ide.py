"""
Патч русификации расширения Antigravity для IDE.

Применяет переводы из translations/ide_strings.json к:
  - package.json (команды, настройки, редакторы)
  - extension.js (UI-строки в коде)

Создает бэкапы перед изменением.

Использование:
  python patch_ide.py           # применить патч
  python patch_ide.py --restore # откатить к оригиналу
  python patch_ide.py --dry-run # показать что будет изменено
"""

import json
import shutil
import sys
import os
import re
from pathlib import Path

# ===== Пути =====
SCRIPT_DIR = Path(__file__).parent
TRANSLATIONS_FILE = SCRIPT_DIR / "translations" / "ide_strings.json"

# Antigravity IDE extension paths
IDE_BASE = Path(os.environ.get(
    "ANTIGRAVITY_IDE_PATH",
    r"C:\Users\gabov\AppData\Local\Programs\Antigravity IDE"
))
EXTENSION_DIR = IDE_BASE / "resources" / "app" / "extensions" / "antigravity"
PACKAGE_JSON = EXTENSION_DIR / "package.json"
EXTENSION_JS = EXTENSION_DIR / "dist" / "extension.js"

BACKUP_SUFFIX = ".bak.original"


def load_translations() -> dict:
    with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def backup_file(filepath: Path) -> bool:
    """Создать бэкап если его ещё нет."""
    backup = filepath.with_suffix(filepath.suffix + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(filepath, backup)
        print(f"  Backup: {backup}")
        return True
    else:
        print(f"  Backup exists: {backup}")
        return False


def restore_file(filepath: Path) -> bool:
    """Откатить файл из бэкапа."""
    backup = filepath.with_suffix(filepath.suffix + BACKUP_SUFFIX)
    if backup.exists():
        shutil.copy2(backup, filepath)
        print(f"  Restored: {filepath}")
        return True
    else:
        print(f"  No backup found: {backup}")
        return False


def patch_package_json(translations: dict, dry_run: bool = False) -> int:
    """Патч package.json — команды, настройки, редакторы."""
    print("\n=== package.json ===")

    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    changes = 0
    contributes = pkg.get("contributes", {})

    # Команды
    cmd_translations = translations.get("commands", {})
    for cmd in contributes.get("commands", []):
        cmd_id = cmd.get("command", "")
        if cmd_id in cmd_translations:
            old = cmd.get("title", "")
            new = cmd_translations[cmd_id]["ru"]
            if old != new:
                print(f"  [cmd] {cmd_id}: '{old}' -> '{new}'")
                if not dry_run:
                    cmd["title"] = new
                changes += 1

    # Настройки (description / markdownDescription)
    config_translations = translations.get("configuration", {})
    config_props = contributes.get("configuration", {}).get("properties", {})
    for prop_key, prop_val in config_props.items():
        if prop_key in config_translations:
            new_text = config_translations[prop_key]["ru"]
            for field in ["description", "markdownDescription"]:
                if field in prop_val:
                    old = prop_val[field]
                    # Сохраняем markdown-ссылки
                    links = re.findall(r'\[.*?\]\(.*?\)', old)
                    replacement = new_text
                    if links:
                        replacement = new_text + " " + " ".join(links)
                    if old != replacement:
                        print(f"  [config] {prop_key}.{field}: truncated -> '{replacement[:60]}...'")
                        if not dry_run:
                            prop_val[field] = replacement
                        changes += 1

    # Заголовок конфигурации
    config_title = translations.get("configurationTitle", {})
    if config_title and "configuration" in contributes:
        old = contributes["configuration"].get("title", "")
        new = config_title.get("ru", old)
        if old != new:
            print(f"  [config-title]: '{old}' -> '{new}'")
            if not dry_run:
                contributes["configuration"]["title"] = new
            changes += 1

    # Кастомные редакторы
    editor_translations = translations.get("customEditors", {})
    for editor in contributes.get("customEditors", []):
        editor_id = editor.get("viewType", "")
        if editor_id in editor_translations:
            old = editor.get("displayName", "")
            new = editor_translations[editor_id]["ru"]
            if old != new:
                print(f"  [editor] {editor_id}: '{old}' -> '{new}'")
                if not dry_run:
                    editor["displayName"] = new
                changes += 1

    if not dry_run and changes > 0:
        backup_file(PACKAGE_JSON)
        with open(PACKAGE_JSON, "w", encoding="utf-8") as f:
            json.dump(pkg, f, ensure_ascii=False)
        print(f"  Saved {PACKAGE_JSON}")

    return changes


def patch_extension_js(translations: dict, dry_run: bool = False) -> int:
    """Патч extension.js — замена строковых литералов в коде."""
    print("\n=== extension.js ===")

    ui_strings = translations.get("ui_strings", {})
    if not ui_strings:
        print("  No UI strings to patch")
        return 0

    with open(EXTENSION_JS, "r", encoding="utf-8") as f:
        content = f.read()

    changes = 0
    for en_text, ru_text in ui_strings.items():
        # Ищем строку в кавычках (двойных или одинарных)
        for quote in ['"', "'"]:
            pattern = f'{quote}{re.escape(en_text)}{quote}'
            replacement = f'{quote}{ru_text}{quote}'
            if pattern in content:
                count = content.count(pattern)
                print(f"  [{count}x] '{en_text}' -> '{ru_text}'")
                if not dry_run:
                    content = content.replace(pattern, replacement)
                changes += count

    if not dry_run and changes > 0:
        backup_file(EXTENSION_JS)
        with open(EXTENSION_JS, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Saved {EXTENSION_JS}")

    return changes


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    restore = "--restore" in args

    if restore:
        print("=== Restoring from backups ===")
        restore_file(PACKAGE_JSON)
        restore_file(EXTENSION_JS)
        print("\nDone. Restart Antigravity IDE to apply.")
        return

    if dry_run:
        print("=== DRY RUN (no files will be modified) ===")

    if not TRANSLATIONS_FILE.exists():
        print(f"ERROR: Translation file not found: {TRANSLATIONS_FILE}")
        sys.exit(1)

    if not EXTENSION_DIR.exists():
        print(f"ERROR: Extension directory not found: {EXTENSION_DIR}")
        sys.exit(1)

    translations = load_translations()

    total = 0
    total += patch_package_json(translations, dry_run)
    total += patch_extension_js(translations, dry_run)

    print(f"\n{'Would change' if dry_run else 'Changed'}: {total} strings")
    if not dry_run and total > 0:
        print("Restart Antigravity IDE to apply changes.")


if __name__ == "__main__":
    main()
