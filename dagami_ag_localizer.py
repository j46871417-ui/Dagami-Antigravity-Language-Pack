#!/usr/bin/env python3
"""
Dagami Antigravity Language Pack.

Multilingual localization suite for Google Antigravity Desktop & Antigravity IDE.
Supports dynamic switching to Russian (ru), Chinese (zh), Spanish (es),
Japanese (ja), German (de), French (fr), and future community language packs.

Repository: https://github.com/j46871417-ui/Antigravity-Localizer
Community Telegram: https://t.me/+8qU7020rMF84OWNi
Support & Donations: https://pay.cloudtips.ru/p/671fda86
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path

# Configure utf-8 stdout where possible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import js_literals as jsl
import dagami_translator_builder as dtb

# Base paths
if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    BUNDLE_DIR = Path(__file__).resolve().parent

TRANSLATIONS_DIR = BUNDLE_DIR / "translations"
LANGUAGES_DIR = TRANSLATIONS_DIR / "languages"
ASSETS_DIR = BUNDLE_DIR / "assets"
RU_PACK_ZIP = ASSETS_DIR / "ru_pack.zip"
NLS_RU_FILE = ASSETS_DIR / "nls.messages.ru.json"

APP_NAME = "Dagami Antigravity Language Pack"
APP_VERSION = "1.1.0"
TELEGRAM_URL = "https://t.me/+8qU7020rMF84OWNi"
DONATION_URL = "https://pay.cloudtips.ru/p/671fda86"

BACKUP_SUFFIX = ".bak.original"
ASAR_BACKUP_NAME = "app.asar.original_backup"
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
PRELOAD_MARKER = dtb.PRELOAD_MARKER


def safe_print(*args, **kwargs):
    if sys.stdout is not None:
        try:
            print(*args, **kwargs)
        except Exception:
            try:
                # Fallback for systems where console encoding is restricted
                encoding = getattr(sys.stdout, "encoding", "ascii") or "ascii"
                enc_args = [str(a).encode(encoding, errors="replace").decode(encoding) for a in args]
                print(*enc_args, **kwargs)
            except Exception:
                pass


def print_banner():
    safe_print("=" * 68)
    safe_print(f"   [+] {APP_NAME} (v{APP_VERSION})")
    safe_print("   Многоязычный пакет локализации для Google Antigravity")
    safe_print(f"   Telegram сообщество: {TELEGRAM_URL}")
    safe_print(f"   Поддержать разработку: {DONATION_URL}")
    safe_print("=" * 68)
    safe_print()


# =============================================================================
# Process Management & File Lock Handling
# =============================================================================

ANTIGRAVITY_PROCESS_NAMES = [
    "Antigravity IDE.exe",
    "Antigravity.exe",
]


def wait_for_files_unlocked(file_paths: list[Path], timeout: float = 10.0, poll_interval: float = 0.25, log_fn=safe_print) -> bool:
    start_time = time.time()
    existing_files = [p for p in file_paths if p and p.exists()]
    if not existing_files:
        return True

    log_fn(f"  Ожидание разблокировки целевых файлов (таймаут {timeout:.0f}с)...")
    while time.time() - start_time < timeout:
        all_unlocked = True
        for p in existing_files:
            try:
                with open(p, "r+b"):
                    pass
            except (IOError, PermissionError, OSError):
                all_unlocked = False
                break
        if all_unlocked:
            return True
        time.sleep(poll_interval)

    locked = []
    for p in existing_files:
        try:
            with open(p, "r+b"):
                pass
        except (IOError, PermissionError, OSError):
            locked.append(p.name)
    if locked:
        log_fn(f"  [Предупреждение] Файлы остаются заблокированы другими процессами: {', '.join(locked)}")
        return False
    return True


def is_inside_antigravity_session() -> bool:
    return bool(os.environ.get("ANTIGRAVITY_AGENT") or os.environ.get("ANTIGRAVITY_CONVERSATION_ID"))


def kill_antigravity_processes(log_fn=safe_print, force=False, no_kill=False):
    if no_kill or (not force and is_inside_antigravity_session()):
        log_fn("\n[*] Закрытие активных процессов пропущено (сессия защищена от прерывания).")
        return

    log_fn("\n[Процессы] Завершение всех активных процессов Antigravity...")
    killed_any = False
    for proc in ANTIGRAVITY_PROCESS_NAMES:
        try:
            res = subprocess.run(
                ["taskkill", "/F", "/T", "/IM", proc],
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
            )
            if res.returncode == 0:
                log_fn(f"  Принудительно закрыт процесс: {proc}")
                killed_any = True
        except Exception:
            pass

    if killed_any:
        log_fn("  Ожидание выгрузки процессов из памяти...")
        deadline = time.time() + 5.0
        while time.time() < deadline:
            try:
                chk = subprocess.run(
                    ["tasklist"],
                    capture_output=True,
                    text=True,
                    creationflags=CREATE_NO_WINDOW,
                )
                still_running = any(proc.lower() in chk.stdout.lower() for proc in ANTIGRAVITY_PROCESS_NAMES)
                if not still_running:
                    break
            except Exception:
                break
            time.sleep(0.3)
        log_fn("  Процессы Antigravity успешно выгружены.")
    else:
        log_fn("  Активных процессов не обнаружено.")


# =============================================================================
# Path Detection & Validation
# =============================================================================

def get_default_paths():
    local_app_data = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))
    prog_files = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
    user_home = Path(os.path.expanduser("~"))

    ide_candidates = [
        local_app_data / "Programs" / "Antigravity IDE",
        prog_files / "Antigravity IDE",
        local_app_data / "Programs" / "antigravity-ide",
    ]
    desktop_candidates = [
        local_app_data / "Programs" / "antigravity",
        prog_files / "antigravity",
        local_app_data / "Programs" / "Antigravity",
    ]

    detected_ide = None
    for p in ide_candidates:
        if p.exists() and validate_ide_path(p):
            detected_ide = p
            break

    detected_desktop = None
    for p in desktop_candidates:
        if p.exists() and validate_desktop_path(p):
            detected_desktop = p
            break

    ide_user_data = user_home / ".antigravity-ide"

    return {
        "ide_path": detected_ide,
        "desktop_path": detected_desktop,
        "ide_user_data": ide_user_data,
    }


def validate_ide_path(path: Path) -> bool:
    if not path or not path.exists():
        return False
    pkg = path / "resources" / "app" / "extensions" / "antigravity" / "package.json"
    exe1 = path / "Antigravity IDE.exe"
    exe2 = path / "Antigravity.exe"
    return pkg.exists() or exe1.exists() or exe2.exists()


def validate_desktop_path(path: Path) -> bool:
    if not path or not path.exists():
        return False
    asar = path / "resources" / "app.asar"
    exe = path / "Antigravity.exe"
    return asar.exists() or exe.exists()


# =============================================================================
# File Backup and Restore
# =============================================================================

def backup_file(filepath: Path, log_fn=safe_print) -> bool:
    if not filepath.exists():
        return False
    backup = filepath.with_suffix(filepath.suffix + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(filepath, backup)
        log_fn(f"[Бэкап] Создана копия: {backup.name}")
        return True
    return False


def restore_file(filepath: Path, log_fn=safe_print) -> bool:
    backup = filepath.with_suffix(filepath.suffix + BACKUP_SUFFIX)
    if backup.exists():
        try:
            shutil.copy2(backup, filepath)
            log_fn(f"[Откат] Восстановлен: {filepath.name}")
            return True
        except Exception:
            try:
                with open(backup, "rb") as src, open(filepath, "r+b") as dst:
                    dst.seek(0)
                    dst.write(src.read())
                    dst.truncate()
                    dst.flush()
                log_fn(f"[Откат] Восстановлен (in-place): {filepath.name}")
                return True
            except Exception as e:
                log_fn(f"[Откат] Ошибка восстановления {filepath.name}: {e}")
                return False
    return False


# =============================================================================
# ASAR Archive Parsing and Safe Writing
# =============================================================================

def read_asar(path: Path):
    with open(path, "rb") as f:
        magic = f.read(16)
        u0, header_size, u2, json_len = struct.unpack("<IIII", magic)
        header = json.loads(f.read(json_len).decode("utf-8"))
        data_start = 8 + header_size
        f.seek(data_start)
        data = f.read()
    return header, data


def compute_sha256_blocks(data: bytes, block_size: int = 4194304):
    blocks = []
    for i in range(0, len(data), block_size):
        block = data[i:i + block_size]
        blocks.append(hashlib.sha256(block).hexdigest())
    full_hash = hashlib.sha256(data).hexdigest()
    return {
        "algorithm": "SHA256",
        "hash": full_hash,
        "blockSize": block_size,
        "blocks": blocks,
    }


def write_asar_atomic(path: Path, header: dict, data: bytes):
    json_bytes = json.dumps(header, separators=(',', ':')).encode("utf-8")
    json_len = len(json_bytes)
    pad_len = (4 - (json_len % 4)) % 4
    padding = b"\x00" * pad_len

    u2 = json_len + 4 + pad_len
    header_size = u2 + 4
    u0 = 4

    magic = struct.pack("<IIII", u0, header_size, u2, json_len)
    expected_size = 16 + json_len + pad_len + len(data)

    temp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(temp_path, "wb") as f:
            f.write(magic)
            f.write(json_bytes)
            f.write(padding)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        actual_size = temp_path.stat().st_size
        if actual_size != expected_size:
            raise IOError(f"Несоответствие размера ASAR: ожидалось {expected_size} байт, записано {actual_size} байт")

        try:
            os.replace(temp_path, path)
        except (PermissionError, OSError):
            # When Antigravity or Electron is running, replacing the file node can trigger
            # Windows sharing restrictions. Fall back to direct in-place stream write.
            with open(path, "r+b") as target_file:
                target_file.seek(0)
                target_file.write(magic)
                target_file.write(json_bytes)
                target_file.write(padding)
                target_file.write(data)
                target_file.truncate()
                target_file.flush()
                os.fsync(target_file.fileno())
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def write_asar(path: Path, header: dict, data: bytes):
    write_asar_atomic(path, header, data)


# =============================================================================
# Injection & String Helpers
# =============================================================================

def strip_json_comments(text: str) -> str:
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return ""
        return s
    pattern = re.compile(r'//.*?$|/\*.*?\*/|"(?:\\.|[^\\"])*"', re.DOTALL | re.MULTILINE)
    return re.sub(pattern, replacer, text)


def inject_dom_translator(preload_text: str, dom_script: str) -> str:
    """
    Idempotent injection of runtime translator into preload.js.
    """
    if PRELOAD_MARKER in preload_text:
        preload_text = preload_text[:preload_text.index(PRELOAD_MARKER)]
    return preload_text.rstrip() + "\n\n" + dom_script


def replace_js_string_literals(content: str, string_map: dict[str, str], log_fn=safe_print) -> tuple[str, int]:
    return jsl.replace_js_string_literals(content, string_map, log_fn=log_fn)


# =============================================================================
# Language Pack Manager
# =============================================================================

def list_available_languages() -> list[dict]:
    languages = []
    if not LANGUAGES_DIR.exists():
        return languages

    for item in sorted(LANGUAGES_DIR.iterdir()):
        if item.is_dir():
            meta_path = item / "metadata.json"
            dict_path = item / "dict.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    term_count = 0
                    if dict_path.exists():
                        try:
                            with open(dict_path, "r", encoding="utf-8") as df:
                                d = json.load(df)
                                term_count = len(d)
                        except Exception:
                            pass
                    meta["terms"] = term_count
                    languages.append(meta)
                except Exception:
                    pass
    return languages


def print_language_list():
    langs = list_available_languages()
    safe_print("\n Доступные языковые пакеты Dagami Antigravity Language Pack:")
    safe_print("-" * 68)
    safe_print(f" {'Код':<6} | {'Флаг':<4} | {'Название':<24} | {'Терминов':<10} | {'Версия'}")
    safe_print("-" * 68)
    for l in langs:
        code = l.get("code", "")
        flag = l.get("flag", "🌐")
        name = f"{l.get('nativeName', '')} ({l.get('name', '')})"
        terms = str(l.get("terms", 0))
        ver = l.get("version", "1.0.0")
        safe_print(f" {code:<6} | {flag:<4} | {name:<24} | {terms:<10} | {ver}")
    safe_print("-" * 68)
    safe_print(f"Команда для переключения: dagami-ag-localizer --lang <код>")
    safe_print(f"Поддержать добавление новых языков: {DONATION_URL}\n")


def update_language_packs(log_fn=safe_print):
    log_fn("\n[*] Проверка и обновление языковых пакетов...")
    langs = list_available_languages()
    updated = 0
    for l in langs:
        code = l.get("code")
        # Validate that runtime script builds correctly
        try:
            js = dtb.build_runtime_translator_js(code)
            if js.startswith(PRELOAD_MARKER):
                updated += 1
                log_fn(f"  [+] Пакет '{code}' ({l.get('nativeName')}): проверен и готов к использованию.")
        except Exception as e:
            log_fn(f"  [-] Ошибка валидации пакета '{code}': {e}")
    log_fn(f"\n[+] Всего актуальных пакетов: {updated}")
    log_fn(f"[*] Для добавления других языков напишите в сообщество: {TELEGRAM_URL}")


# =============================================================================
# Core Localizer Engine
# =============================================================================

class DagamiLocalizer:
    def __init__(
        self,
        ide_path: Path = None,
        desktop_path: Path = None,
        ide_user_data: Path = None,
        log_fn=safe_print,
        force_kill: bool = False,
        no_kill: bool = False,
    ):
        self.ide_path = ide_path
        self.desktop_path = desktop_path
        self.ide_user_data = ide_user_data or (Path.home() / ".antigravity-ide")
        self.log = log_fn
        self.force_kill = force_kill
        self.no_kill = no_kill

    def get_lang_meta(self, lang_code: str) -> dict:
        return dtb.get_language_metadata(lang_code)

    def install_ide(self, lang_code: str = "ru") -> bool:
        if not self.ide_path or not validate_ide_path(self.ide_path):
            self.log("[IDE] Каталог Antigravity IDE не найден или некорректен.")
            return False

        meta = self.get_lang_meta(lang_code)
        kill_antigravity_processes(self.log, force=self.force_kill, no_kill=self.no_kill)
        self.log(f"\n--- Установка языка {meta.get('nativeName', lang_code)} для Antigravity IDE ---")

        ext_base = self.ide_path / "resources" / "app" / "extensions" / "antigravity"
        pkg_path = ext_base / "package.json"
        ext_js_path = ext_base / "dist" / "extension.js"
        argv_json_path = self.ide_user_data / "argv.json"
        jetski_path = self.ide_path / "resources" / "app" / "out" / "jetskiAgent" / "main.js"

        ide_targets = [p for p in [pkg_path, ext_js_path, argv_json_path, jetski_path] if p.exists()]
        if not wait_for_files_unlocked(ide_targets, timeout=10.0, log_fn=self.log):
            self.log("[IDE] Ошибка: целевые файлы заблокированы внешними процессами. Прерывание.")
            return False

        # 1. VS Code Language Pack (for Russian)
        if lang_code == "ru":
            ext_dir = self.ide_user_data / "extensions"
            pack_target = ext_dir / "ms-ceintl.vscode-language-pack-ru-1.106.0-universal"
            if not pack_target.exists():
                if RU_PACK_ZIP.exists():
                    self.log("[IDE] Распаковка русского языкового пакета VS Code...")
                    ext_dir.mkdir(parents=True, exist_ok=True)
                    pack_target.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(RU_PACK_ZIP, "r") as zf:
                        zf.extractall(pack_target)
                    self.log("[IDE] Языковой пакет успешно установлен.")
                else:
                    self.log("[IDE] Архив языкового пакета не найден, пропускаем.")

        # 2. argv.json -> locale: <vscodeLocale>
        target_locale = meta.get("vscodeLocale", lang_code)
        if argv_json_path.exists():
            backup_file(argv_json_path, self.log)
            try:
                with open(argv_json_path, "r", encoding="utf-8") as f:
                    argv_content = f.read()

                if '"locale"' in argv_content:
                    argv_content = re.sub(r'"locale"\s*:\s*"[^"]*"', f'"locale": "{target_locale}"', argv_content)
                else:
                    argv_content = re.sub(r'(\{)', f'\\1\n\t"locale": "{target_locale}",', argv_content, count=1)

                clean_test = strip_json_comments(argv_content)
                json.loads(clean_test)

                with open(argv_json_path, "w", encoding="utf-8") as f:
                    f.write(argv_content)

                self.log(f"[IDE] В argv.json включен язык (locale: {target_locale}).")
            except Exception as e:
                self.log(f"[IDE] Ошибка обновления argv.json: {e}. Откат к оригиналу.")
                restore_file(argv_json_path, self.log)

        # 3. Patch package.json
        ide_lang_file = LANGUAGES_DIR / lang_code / "ide.json"
        if not ide_lang_file.exists():
            ide_lang_file = TRANSLATIONS_DIR / "ide_strings.json"

        if pkg_path.exists() and ide_lang_file.exists():
            backup_file(pkg_path, self.log)
            try:
                with open(ide_lang_file, "r", encoding="utf-8") as f:
                    translations = json.load(f)
                with open(pkg_path, "r", encoding="utf-8") as f:
                    pkg = json.load(f)

                changes = 0
                contributes = pkg.get("contributes", {})

                cmd_trans = translations.get("commands", {})
                for cmd in contributes.get("commands", []):
                    cid = cmd.get("command", "")
                    if cid in cmd_trans:
                        entry = cmd_trans[cid]
                        val = entry.get(lang_code) or entry.get("ru")
                        if val:
                            cmd["title"] = val
                            changes += 1

                cfg_trans = translations.get("configuration", {})
                props = contributes.get("configuration", {}).get("properties", {})
                for prop_key, prop_val in props.items():
                    if prop_key in cfg_trans:
                        entry = cfg_trans[prop_key]
                        desc_val = entry.get(lang_code) or entry.get("ru")
                        if desc_val:
                            for field in ["description", "markdownDescription"]:
                                if field in prop_val:
                                    prop_val[field] = desc_val
                                    changes += 1

                if "configurationTitle" in translations and "configuration" in contributes:
                    ct = translations["configurationTitle"].get(lang_code) or translations["configurationTitle"].get("ru")
                    if ct:
                        contributes["configuration"]["title"] = ct
                        changes += 1

                with open(pkg_path, "w", encoding="utf-8") as f:
                    json.dump(pkg, f, ensure_ascii=False, indent=2)

                self.log(f"[IDE] Обновлено строк в package.json: {changes}")
            except Exception as e:
                self.log(f"[IDE] Ошибка патчинга package.json: {e}")
                restore_file(pkg_path, self.log)

        # 4. Patch nls.messages.json for Russian if available
        if lang_code == "ru":
            nls_path = self.ide_path / "resources" / "app" / "out" / "nls.messages.json"
            if nls_path.exists() and NLS_RU_FILE.exists():
                backup_file(nls_path, self.log)
                try:
                    shutil.copy2(NLS_RU_FILE, nls_path)
                    self.log("[IDE] Применена локализация каркаса VS Code (15 000+ строк).")
                except Exception as e:
                    self.log(f"[IDE] Ошибка обновления nls.messages.json: {e}")
                    restore_file(nls_path, self.log)

        self.log(f"[IDE] Языковой пакет '{lang_code}' для Antigravity IDE успешно установлен!")
        return True

    def install_desktop(self, lang_code: str = "ru") -> bool:
        if not self.desktop_path or not validate_desktop_path(self.desktop_path):
            self.log("[Desktop] Каталог Antigravity Desktop не найден или некорректен.")
            return False

        meta = self.get_lang_meta(lang_code)
        kill_antigravity_processes(self.log, force=self.force_kill, no_kill=self.no_kill)
        self.log(f"\n--- Установка языка {meta.get('nativeName', lang_code)} для Antigravity 2.0 Desktop ---")

        asar_path = self.desktop_path / "resources" / "app.asar"
        if not asar_path.exists():
            self.log(f"[Desktop] app.asar не найден: {asar_path}")
            return False

        if not wait_for_files_unlocked([asar_path], timeout=10.0, log_fn=self.log):
            self.log(f"[Desktop] Ошибка: {asar_path.name} заблокирован другим процессом.")
            return False

        backup_file(asar_path, self.log)

        # Permanent pristine backup for clean language switching
        permanent_backup = asar_path.with_name(ASAR_BACKUP_NAME)
        if not permanent_backup.exists():
            shutil.copy2(asar_path, permanent_backup)
            self.log(f"[Desktop] Сохранена базовая копия: {permanent_backup.name}")

        try:
            # Load desktop strings for target language
            desktop_lang_file = LANGUAGES_DIR / lang_code / "desktop.json"
            if desktop_lang_file.exists():
                with open(desktop_lang_file, "r", encoding="utf-8") as f:
                    translations = json.load(f)
            else:
                legacy_file = TRANSLATIONS_DIR / "desktop_strings.json"
                with open(legacy_file, "r", encoding="utf-8") as f:
                    translations = json.load(f)

            # Always read from permanent pristine backup to avoid accumulated patches
            source_asar = permanent_backup if permanent_backup.exists() else asar_path
            header, data = read_asar(source_asar)

            menu_map = translations.get("menu", {})
            tray_map = translations.get("tray", {})
            wizard_map = translations.get("wizard", {})

            # Targets to patch inside app.asar
            targets = {
                "dist/menu.js": menu_map,
                "dist/main.js": tray_map,
                "dist/ideInstall/wizardHtml.js": wizard_map,
            }

            # Build runtime translator script for target language
            runtime_dom_script = dtb.build_runtime_translator_js(lang_code)

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
            changes = 0

            for path_str, old_offset, old_size, entry in file_list:
                file_bytes = data[old_offset:old_offset + old_size]

                # JS String literal patching
                if path_str in targets and targets[path_str]:
                    try:
                        file_text = file_bytes.decode("utf-8")
                        file_text, sub_changes = replace_js_string_literals(file_text, targets[path_str], self.log)
                        if sub_changes > 0:
                            changes += sub_changes
                            file_bytes = file_text.encode("utf-8")
                    except UnicodeDecodeError:
                        self.log(f"[Desktop] Предупреждение: {path_str} не является UTF-8, пропуск.")

                # Preload runtime injection
                if path_str == "dist/preload.js":
                    try:
                        preload_text = file_bytes.decode("utf-8")
                        preload_text = inject_dom_translator(preload_text, runtime_dom_script)
                        file_bytes = preload_text.encode("utf-8")
                        changes += 1
                        self.log(f"[Desktop] Внедрён языковой движок Dagami ({meta.get('nativeName', lang_code)}) в dist/preload.js")
                    except Exception as e:
                        self.log(f"[Desktop] Ошибка внедрения в preload.js: {e}")

                entry["offset"] = str(current_offset)
                entry["size"] = len(file_bytes)
                if "integrity" in entry:
                    entry["integrity"] = compute_sha256_blocks(file_bytes)

                new_data_chunks.append(file_bytes)
                current_offset += len(file_bytes)

            new_data = b"".join(new_data_chunks)
            write_asar_atomic(asar_path, header, new_data)

            self.log(f"[Desktop] Заменено строк и компонентов: {changes}")
            self.log(f"[Desktop] Язык {meta.get('nativeName', lang_code)} успешно установлен в Antigravity Desktop!")
            return True
        except Exception as e:
            self.log(f"[Desktop] Ошибка патчинга app.asar: {e}. Откат к оригиналу.")
            restore_file(asar_path, self.log)
            return False

    def restore_all(self) -> bool:
        kill_antigravity_processes(self.log, force=self.force_kill, no_kill=self.no_kill)
        self.log("\n=== Восстановление оригинальной версии Google Antigravity ===")
        restored = 0

        # IDE
        if self.ide_path:
            ext_base = self.ide_path / "resources" / "app" / "extensions" / "antigravity"
            if restore_file(ext_base / "package.json", self.log):
                restored += 1
            if restore_file(ext_base / "dist" / "extension.js", self.log):
                restored += 1
            nls_path = self.ide_path / "resources" / "app" / "out" / "nls.messages.json"
            if restore_file(nls_path, self.log):
                restored += 1
            jetski_path = self.ide_path / "resources" / "app" / "out" / "jetskiAgent" / "main.js"
            if restore_file(jetski_path, self.log):
                restored += 1

        if self.ide_user_data:
            if restore_file(self.ide_user_data / "argv.json", self.log):
                restored += 1

        # Desktop
        if self.desktop_path:
            asar_path = self.desktop_path / "resources" / "app.asar"
            permanent_backup = asar_path.with_name(ASAR_BACKUP_NAME)
            if permanent_backup.exists():
                try:
                    shutil.copy2(permanent_backup, asar_path)
                    self.log(f"[Откат] Восстановлен {asar_path.name} из {ASAR_BACKUP_NAME}")
                    restored += 1
                except Exception:
                    try:
                        with open(permanent_backup, "rb") as src, open(asar_path, "r+b") as dst:
                            dst.seek(0)
                            dst.write(src.read())
                            dst.truncate()
                            dst.flush()
                        self.log(f"[Откат] Восстановлен (in-place) {asar_path.name} из {ASAR_BACKUP_NAME}")
                        restored += 1
                    except Exception as e:
                        self.log(f"[Откат] Ошибка восстановления {asar_path.name}: {e}")
            elif restore_file(asar_path, self.log):
                restored += 1

        self.log(f"Всего файлов восстановлено: {restored}")
        self.log("[+] Официальная версия Google Antigravity (English) успешно восстановлена!")
        return restored > 0


# Alias for backward compatibility
AntigravityLocalizer = DagamiLocalizer


# =============================================================================
# Interactive CLI
# =============================================================================

def run_interactive_cli(localizer: DagamiLocalizer):
    print_banner()
    while True:
        safe_print("\nМеню управления:")
        safe_print("  [1] Установить русский язык (Russian / ru)")
        safe_print("  [2] Установить китайский язык (Chinese Simplified / zh)")
        safe_print("  [3] Установить испанский язык (Spanish / es)")
        safe_print("  [4] Установить японский язык (Japanese / ja)")
        safe_print("  [5] Выбрать другой язык...")
        safe_print("  [6] Показать список всех доступных языков (--list)")
        safe_print("  [7] Обновить языковые пакеты (--update)")
        safe_print("  [8] Восстановить официальный оригинал Google (English / restore)")
        safe_print("  [9] Сообщество в Telegram")
        safe_print("  [10] Поддержать проект (Донат)")
        safe_print("  [0] Выход")
        safe_print()

        choice = input("Введите номер действия: ").strip()

        if choice == "1":
            localizer.install_desktop("ru")
            if localizer.ide_path:
                localizer.install_ide("ru")
        elif choice == "2":
            localizer.install_desktop("zh")
            if localizer.ide_path:
                localizer.install_ide("zh")
        elif choice == "3":
            localizer.install_desktop("es")
            if localizer.ide_path:
                localizer.install_ide("es")
        elif choice == "4":
            localizer.install_desktop("ja")
            if localizer.ide_path:
                localizer.install_ide("ja")
        elif choice == "5":
            print_language_list()
            custom_code = input("Введите код языка (например, de, fr): ").strip().lower()
            if custom_code:
                localizer.install_desktop(custom_code)
                if localizer.ide_path:
                    localizer.install_ide(custom_code)
        elif choice == "6":
            print_language_list()
        elif choice == "7":
            update_language_packs()
        elif choice == "8":
            localizer.restore_all()
        elif choice == "9":
            safe_print(f"\nTelegram сообщество: {TELEGRAM_URL}")
            try:
                import webbrowser
                webbrowser.open(TELEGRAM_URL)
            except Exception:
                pass
        elif choice == "10":
            safe_print(f"\nСтраница поддержки проекта: {DONATION_URL}")
            try:
                import webbrowser
                webbrowser.open(DONATION_URL)
            except Exception:
                pass
        elif choice in ("0", "q", "exit"):
            safe_print("До свидания!")
            break
        else:
            safe_print("[!] Неверный выбор. Пожалуйста, укажите цифру из списка.")


# =============================================================================
# Tkinter GUI
# =============================================================================

class DagamiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("680x600")
        self.root.minsize(620, 520)

        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox

        style = ttk.Style()
        style.theme_use("clam")

        default_paths = get_default_paths()
        self.ide_path_var = tk.StringVar(value=str(default_paths["ide_path"] or ""))
        self.desktop_path_var = tk.StringVar(value=str(default_paths["desktop_path"] or ""))
        self.opt_ide = tk.BooleanVar(value=bool(default_paths["ide_path"]))
        self.opt_desktop = tk.BooleanVar(value=bool(default_paths["desktop_path"]))

        # Language selection
        langs = list_available_languages()
        self.lang_choices = {f"{l.get('flag', '')} {l.get('nativeName', '')} ({l.get('code')})": l.get('code') for l in langs}
        default_lang_str = next(iter(self.lang_choices.keys())) if self.lang_choices else "🇷🇺 Русский (ru)"
        self.selected_lang_var = tk.StringVar(value=default_lang_str)

        self._build_ui()
        self._update_status()

    def _build_ui(self):
        main_frame = self.ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=self.tk.BOTH, expand=True)

        # Header
        header_label = self.ttk.Label(
            main_frame,
            text=f"🚀 {APP_NAME}",
            font=("Segoe UI", 14, "bold"),
        )
        header_label.pack(anchor="w", pady=(0, 2))

        sub_label = self.ttk.Label(
            main_frame,
            text="Мультиязычная локализация Google Antigravity Desktop и Antigravity IDE",
            font=("Segoe UI", 9),
            foreground="#555555",
        )
        sub_label.pack(anchor="w", pady=(0, 10))

        # Links bar
        links_box = self.ttk.Frame(main_frame)
        links_box.pack(fill=self.tk.X, pady=(0, 12))

        btn_tg = self.tk.Button(
            links_box,
            text="📢 Чат сообщества в Telegram",
            bg="#2CA5E0",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=self.tk.FLAT,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._open_telegram,
        )
        btn_tg.pack(side=self.tk.LEFT, padx=(0, 10))

        btn_donate = self.tk.Button(
            links_box,
            text="☕ Поддержать проект (Донат)",
            bg="#FF6F00",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=self.tk.FLAT,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._open_donation,
        )
        btn_donate.pack(side=self.tk.LEFT)

        # Language Selector
        lang_group = self.ttk.LabelFrame(main_frame, text=" Выбор языка ", padding="10")
        lang_group.pack(fill=self.tk.X, pady=(0, 10))

        self.ttk.Label(lang_group, text="Языковой пакет:").pack(side=self.tk.LEFT, padx=(0, 10))
        lang_combo = self.ttk.Combobox(
            lang_group,
            textvariable=self.selected_lang_var,
            values=list(self.lang_choices.keys()),
            state="readonly",
            width=35,
        )
        lang_combo.pack(side=self.tk.LEFT, fill=self.tk.X, expand=True)

        # Antigravity IDE section
        ide_group = self.ttk.LabelFrame(main_frame, text=" Antigravity IDE ", padding="10")
        ide_group.pack(fill=self.tk.X, pady=(0, 8))

        ide_top = self.ttk.Frame(ide_group)
        ide_top.pack(fill=self.tk.X)
        self.ttk.Checkbutton(ide_top, text="Локализовать Antigravity IDE", variable=self.opt_ide).pack(side=self.tk.LEFT)
        self.ide_status_label = self.ttk.Label(ide_top, text="", font=("Segoe UI", 9, "bold"))
        self.ide_status_label.pack(side=self.tk.RIGHT)

        ide_path_box = self.ttk.Frame(ide_group)
        ide_path_box.pack(fill=self.tk.X, pady=(6, 0))
        self.ttk.Entry(ide_path_box, textvariable=self.ide_path_var).pack(side=self.tk.LEFT, fill=self.tk.X, expand=True, padx=(0, 5))
        self.ttk.Button(ide_path_box, text="Обзор...", width=9, command=self._browse_ide).pack(side=self.tk.RIGHT)

        # Antigravity Desktop section
        desk_group = self.ttk.LabelFrame(main_frame, text=" Antigravity 2.0 (Desktop) ", padding="10")
        desk_group.pack(fill=self.tk.X, pady=(0, 12))

        desk_top = self.ttk.Frame(desk_group)
        desk_top.pack(fill=self.tk.X)
        self.ttk.Checkbutton(desk_top, text="Локализовать Antigravity 2.0 Desktop", variable=self.opt_desktop).pack(side=self.tk.LEFT)
        self.desk_status_label = self.ttk.Label(desk_top, text="", font=("Segoe UI", 9, "bold"))
        self.desk_status_label.pack(side=self.tk.RIGHT)

        desk_path_box = self.ttk.Frame(desk_group)
        desk_path_box.pack(fill=self.tk.X, pady=(6, 0))
        self.ttk.Entry(desk_path_box, textvariable=self.desktop_path_var).pack(side=self.tk.LEFT, fill=self.tk.X, expand=True, padx=(0, 5))
        self.ttk.Button(desk_path_box, text="Обзор...", width=9, command=self._browse_desktop).pack(side=self.tk.RIGHT)

        # Action Buttons
        btn_frame = self.ttk.Frame(main_frame)
        btn_frame.pack(fill=self.tk.X, pady=(0, 10))

        self.btn_install = self.tk.Button(
            btn_frame,
            text="Установить язык",
            bg="#1976D2",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=self.tk.FLAT,
            padx=15,
            pady=6,
            command=self._on_install,
        )
        self.btn_install.pack(side=self.tk.LEFT, padx=(0, 10))

        self.btn_restore = self.tk.Button(
            btn_frame,
            text="Восстановить оригинал (English)",
            bg="#757575",
            fg="white",
            font=("Segoe UI", 10),
            relief=self.tk.FLAT,
            padx=15,
            pady=6,
            command=self._on_restore,
        )
        self.btn_restore.pack(side=self.tk.LEFT)

        # Log
        log_frame = self.ttk.LabelFrame(main_frame, text=" Журнал выполнения ", padding="5")
        log_frame.pack(fill=self.tk.BOTH, expand=True)

        self.log_text = self.tk.Text(log_frame, wrap=self.tk.WORD, font=("Consolas", 9), height=7)
        self.log_text.pack(side=self.tk.LEFT, fill=self.tk.BOTH, expand=True)
        scrollbar = self.ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=self.tk.RIGHT, fill=self.tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _open_telegram(self):
        import webbrowser
        webbrowser.open(TELEGRAM_URL)

    def _open_donation(self):
        import webbrowser
        webbrowser.open(DONATION_URL)

    def _browse_ide(self):
        f = self.filedialog.askdirectory(title="Выберите папку Antigravity IDE")
        if f:
            self.ide_path_var.set(f)
            self._update_status()

    def _browse_desktop(self):
        f = self.filedialog.askdirectory(title="Выберите папку Antigravity Desktop")
        if f:
            self.desktop_path_var.set(f)
            self._update_status()

    def _update_status(self):
        ide_ok = validate_ide_path(Path(self.ide_path_var.get()))
        self.ide_status_label.config(
            text="✓ Обнаружено" if ide_ok else "✕ Не найдено",
            foreground="#2E7D32" if ide_ok else "#C62828"
        )
        desk_ok = validate_desktop_path(Path(self.desktop_path_var.get()))
        self.desk_status_label.config(
            text="✓ Обнаружено" if desk_ok else "✕ Не найдено",
            foreground="#2E7D32" if desk_ok else "#C62828"
        )

    def log(self, msg: str):
        self.log_text.insert(self.tk.END, msg + "\n")
        self.log_text.see(self.tk.END)

    def _on_install(self):
        self.btn_install.config(state=self.tk.DISABLED)
        self.btn_restore.config(state=self.tk.DISABLED)
        self.log_text.delete("1.0", self.tk.END)

        sel_str = self.selected_lang_var.get()
        lang_code = self.lang_choices.get(sel_str, "ru")

        def worker():
            ide_p = Path(self.ide_path_var.get()) if self.opt_ide.get() else None
            desk_p = Path(self.desktop_path_var.get()) if self.opt_desktop.get() else None

            localizer = DagamiLocalizer(
                ide_path=ide_p,
                desktop_path=desk_p,
                log_fn=self.log,
            )

            success = True
            if self.opt_ide.get():
                if not localizer.install_ide(lang_code):
                    success = False
            if self.opt_desktop.get():
                if not localizer.install_desktop(lang_code):
                    success = False

            self.root.after(0, lambda: self._on_finish("Установка завершена!" if success else "Установка завершена с предупреждениями."))

        threading.Thread(target=worker, daemon=True).start()

    def _on_restore(self):
        self.btn_install.config(state=self.tk.DISABLED)
        self.btn_restore.config(state=self.tk.DISABLED)
        self.log_text.delete("1.0", self.tk.END)

        def worker():
            ide_p = Path(self.ide_path_var.get())
            desk_p = Path(self.desktop_path_var.get())

            localizer = DagamiLocalizer(
                ide_path=ide_p,
                desktop_path=desk_p,
                log_fn=self.log,
            )
            localizer.restore_all()
            self.root.after(0, lambda: self._on_finish("Восстановление завершено!"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_finish(self, message: str):
        self.btn_install.config(state=self.tk.NORMAL)
        self.btn_restore.config(state=self.tk.NORMAL)
        self._update_status()
        self.messagebox.showinfo("Готово", message)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Dagami Antigravity Language Pack — мультиязычная локализация Google Antigravity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Сообщество: {TELEGRAM_URL}\nПоддержать проект: {DONATION_URL}",
    )
    parser.add_argument("--lang", type=str, help="Установить указанный язык (ru, zh, es, ja, de, fr...)")
    parser.add_argument("--list", action="store_true", help="Показать доступные языки")
    parser.add_argument("--update", action="store_true", help="Обновить языковые пакеты")
    parser.add_argument("--restore", action="store_true", help="Откатить к оригинальной версии (English)")
    parser.add_argument("--uninstall", action="store_true", help="Удалить локализацию и восстановить оригинал")
    parser.add_argument("--cli", action="store_true", help="Интерактивный консольный режим")
    parser.add_argument("--gui", action="store_true", help="Запустить графический интерфейс")
    parser.add_argument("--ide-path", type=str, help="Пользовательский путь к Antigravity IDE")
    parser.add_argument("--desktop-path", type=str, help="Пользовательский путь к Antigravity Desktop")
    parser.add_argument("--no-kill", action="store_true", help="Не завершать процессы Antigravity перед установкой")
    parser.add_argument("--force-kill", action="store_true", help="Принудительно завершить процессы Antigravity")

    # Compatibility flags
    parser.add_argument("--install", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    default_paths = get_default_paths()
    ide_p = Path(args.ide_path) if args.ide_path else default_paths["ide_path"]
    desk_p = Path(args.desktop_path) if args.desktop_path else default_paths["desktop_path"]

    if args.ide_path and not validate_ide_path(ide_p):
        safe_print(f"[-] Ошибка: указан неверный путь к Antigravity IDE: {args.ide_path}")
        sys.exit(1)
    if args.desktop_path and not validate_desktop_path(desk_p):
        safe_print(f"[-] Ошибка: указан неверный путь к Antigravity Desktop: {args.desktop_path}")
        sys.exit(1)

    if args.ide_path and not args.desktop_path:
        desk_p = None
    if args.desktop_path and not args.ide_path:
        ide_p = None

    localizer = DagamiLocalizer(
        ide_path=ide_p,
        desktop_path=desk_p,
        force_kill=args.force_kill,
        no_kill=args.no_kill,
    )

    if args.list:
        print_banner()
        print_language_list()
        return

    if args.update:
        print_banner()
        update_language_packs()
        return

    if args.restore or args.uninstall:
        print_banner()
        if not localizer.restore_all():
            sys.exit(1)
        return

    if args.lang:
        print_banner()
        lang_code = args.lang.strip().lower()
        if lang_code == "en":
            if not localizer.restore_all():
                sys.exit(1)
            return

        if not desk_p and not ide_p:
            safe_print("[-] Ошибка: целевые пути Antigravity не найдены. Укажите --ide-path или --desktop-path.")
            sys.exit(1)

        safe_print(f"[*] Выбран язык: {lang_code}")
        success = True
        if desk_p:
            if not localizer.install_desktop(lang_code):
                success = False
        if ide_p:
            if not localizer.install_ide(lang_code):
                success = False

        if not success:
            sys.exit(1)

        safe_print("\n" + "=" * 68)
        safe_print("  [+] Языковой пакет успешно установлен!")
        safe_print(f"  [+] Чат сообщества в Telegram: {TELEGRAM_URL}")
        safe_print(f"  [+] Поддержать проект: {DONATION_URL}")
        safe_print("=" * 68)
        return

    if args.install:
        print_banner()
        if not desk_p and not ide_p:
            safe_print("[-] Ошибка: целевые пути Antigravity не найдены. Укажите --ide-path или --desktop-path.")
            sys.exit(1)
        success = True
        if desk_p:
            if not localizer.install_desktop("ru"):
                success = False
        if ide_p:
            if not localizer.install_ide("ru"):
                success = False
        if not success:
            sys.exit(1)
        return

    # If run in terminal or --cli requested
    if args.cli or (sys.stdin and sys.stdin.isatty() and not args.gui):
        run_interactive_cli(localizer)
        return

    # Otherwise open GUI
    try:
        import tkinter as tk
        root = tk.Tk()
        app = DagamiGUI(root)
        root.mainloop()
    except Exception as e:
        # If GUI fails (headless, SSH, or no display), fallback to CLI
        safe_print(f"[!] Не удалось запустить графический интерфейс ({e}). Переключение в консольный режим.")
        run_interactive_cli(localizer)


if __name__ == "__main__":
    main()
