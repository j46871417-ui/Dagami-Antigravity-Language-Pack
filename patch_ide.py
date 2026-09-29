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
import tempfile
from pathlib import Path

from js_literals import replace_js_string_literals

# ===== Пути =====
SCRIPT_DIR = Path(__file__).parent
TRANSLATIONS_FILE = SCRIPT_DIR / "translations" / "ide_strings.json"

# Antigravity IDE extension paths
# Путь по умолчанию выводится из LOCALAPPDATA, а не из абсолютной строки с именем
# конкретного пользователя (F-013). ANTIGRAVITY_IDE_PATH остаётся приоритетным.
IDE_BASE = Path(os.environ.get("ANTIGRAVITY_IDE_PATH") or (
    Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    / "Programs" / "Antigravity IDE"
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
        # Атомарная запись: обрыв на середине json.dump оставит IDE без манифеста,
        # а VS Code не стартует с битым package.json расширения.
        fd, tmp_name = tempfile.mkstemp(
            dir=str(PACKAGE_JSON.parent), prefix=PACKAGE_JSON.name + ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                json.dump(pkg, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, PACKAGE_JSON)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
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

    if dry_run:
        # Содержимое не меняется, но число совпадений считаем честно —
        # тем же движком, что и при реальном патче (иначе dry-run врёт).
        _, changes = replace_js_string_literals(content, ui_strings)
        return changes

    # Единая авторитетная реализация (js_literals.py): корректно экранирует
    # кавычки, обратный слэш, backtick и ${ в переводе (F-001, F-026),
    # не трогает ключи объектов ("key": value) и системные идентификаторы.
    content, changes = replace_js_string_literals(content, ui_strings, log_fn=print)

    if changes > 0:
        backup_file(EXTENSION_JS)
        # Атомарная запись: частично записанный extension.js = нерабочая IDE.
        fd, tmp_name = tempfile.mkstemp(
            dir=str(EXTENSION_JS.parent), prefix=EXTENSION_JS.name + ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, EXTENSION_JS)
        except BaseException:
            # Не оставляем мусорный .tmp рядом с рабочим расширением.
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
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
