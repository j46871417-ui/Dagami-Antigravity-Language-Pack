#!/usr/bin/env python3
"""
Dagami Antigravity Language Pack.

Multilingual localization suite for Google Antigravity Desktop & Antigravity IDE.
Supports dynamic switching to Russian (ru), Chinese (zh), Spanish (es),
Japanese (ja), German (de), French (fr), and future community language packs.

Repository: https://github.com/j46871417-ui/Dagami-Antigravity-Language-Pack
Community Telegram: https://t.me/+8qU7020rMF84OWNi
Support & Donations: https://pay.cloudtips.ru/p/671fda86
"""

import io
import tempfile
import signal
from localizer_core import InstallOperations
from jsonc_utils import update_argv_locale, strip_jsonc
import argparse
import queue
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

# Attach console on Windows if launched from terminal in noconsole mode
if sys.platform == "win32":
    try:
        import ctypes
        if ctypes.windll.kernel32.AttachConsole(-1) or ctypes.windll.kernel32.GetConsoleWindow():
            if sys.stdin is None or getattr(sys.stdin, "closed", False):
                sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
            if sys.stdout is None or getattr(sys.stdout, "closed", False):
                sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            if sys.stderr is None or getattr(sys.stderr, "closed", False):
                sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configure utf-8 stdout where possible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import js_literals as jsl
import dagami_translator_builder as dtb
import app_updates
from app_info import APP_NAME, APP_VERSION

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

__version__ = APP_VERSION
TELEGRAM_URL = "https://t.me/+8qU7020rMF84OWNi"
DONATION_URL = "https://pay.cloudtips.ru/p/671fda86"

BACKUP_SUFFIX = ".bak.original"
ASAR_BACKUP_NAME = "app.asar.original_backup"
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
PRELOAD_MARKER = dtb.PRELOAD_MARKER


def verify_bundle_integrity(bundle_dir: Path = None) -> tuple[bool, list[str]]:
    """Проверяет наличие и целостность обязательных компонентов языковых пакетов."""
    target_dir = bundle_dir or BUNDLE_DIR
    issues = []
    required_files = [
        target_dir / "translations" / "structured_thoughts.js",
        target_dir / "assets" / "app-icon.ico",
        target_dir / "assets" / "app-icon.icns",
        target_dir / "assets" / "app-icon-64.png",
        target_dir / "assets" / "app-icon-256.png",
        target_dir / "translations" / "languages" / "ru" / "dict.json",
        target_dir / "translations" / "languages" / "ru" / "metadata.json",
        target_dir / "translations" / "languages" / "zh" / "dict.json",
        target_dir / "translations" / "languages" / "es" / "dict.json",
        target_dir / "assets" / "ru_pack.zip",
        target_dir / "assets" / "nls.messages.ru.json",
    ]
    for f in required_files:
        if not f.exists():
            issues.append(f"Отсутствует обязательный ресурс: {f.name} ({f})")
        elif f.stat().st_size == 0:
            issues.append(f"Файл ресурса пуст: {f.name}")
    return (len(issues) == 0, issues)


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
    if no_kill or os.environ.get("ANTIGRAVITY_SKIP_KILL") == "1" or (not force and is_inside_antigravity_session()):
        log_fn("\n[*] Закрытие активных процессов пропущено (сессия защищена от прерывания).")
        return

    log_fn("\n[Процессы] Завершение всех активных процессов Antigravity...")
    killed_any = False

    if sys.platform == "win32":
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
    else:
        # Linux & macOS process termination
        proc_patterns = [
            "antigravity",
            "Antigravity",
            "antigravity-ide",
            "Antigravity IDE",
            
        ]
        for pattern in proc_patterns:
            try:
                res = subprocess.run(["pkill", "-TERM", "-x", pattern], capture_output=True)
                if res.returncode == 0:
                    log_fn(f"  Принудительно закрыт процесс: {pattern}")
                    killed_any = True
            except Exception:
                pass

        if killed_any:
            time.sleep(0.5)
            log_fn("  Процессы Antigravity успешно выгружены.")
        else:
            log_fn("  Активных процессов не обнаружено.")


# =============================================================================
# Path Detection & Validation (Cross-Platform: Windows, Linux, macOS)
# =============================================================================

def resolve_desktop_path(path: Path) -> Path:
    if not path:
        return path
    if path.suffix == ".app" and (path / "Contents").exists():
        return path / "Contents"
    return path


def get_desktop_asar_path(desktop_path: Path) -> Path:
    dp = resolve_desktop_path(desktop_path)
    candidates = [
        dp / "resources" / "app.asar",
        dp / "Resources" / "app.asar",
    ]
    for c in candidates:
        if c.exists():
            return c
    return dp / "resources" / "app.asar"


def resolve_ide_path(path: Path) -> Path:
    if not path:
        return path
    if path.suffix == ".app" and (path / "Contents").exists():
        return path / "Contents"
    return path


def get_ide_ext_base(ide_path: Path) -> Path:
    ip = resolve_ide_path(ide_path)
    candidates = [
        ip / "resources" / "app" / "extensions" / "antigravity",
        ip / "Resources" / "app" / "extensions" / "antigravity",
    ]
    for c in candidates:
        if c.exists():
            return c
    return ip / "resources" / "app" / "extensions" / "antigravity"


def get_ide_out_dir(ide_path: Path) -> Path:
    ip = resolve_ide_path(ide_path)
    candidates = [
        ip / "resources" / "app" / "out",
        ip / "Resources" / "app" / "out",
    ]
    for c in candidates:
        if c.exists():
            return c
    return ip / "resources" / "app" / "out"


def validate_ide_path(path: Path) -> bool:
    if not path or not path.exists():
        return False
    pkg = get_ide_ext_base(path) / "package.json"
    return pkg.is_file()


def validate_desktop_path(path: Path) -> bool:
    return bool(path and get_desktop_asar_path(path).is_file())


def get_default_paths():
    user_home = Path.home()
    ide_candidates = []
    desktop_candidates = []
    ide_user_data = user_home / ".antigravity-ide"

    if sys.platform == "win32":
        local_app_data = Path(os.environ.get("LOCALAPPDATA", user_home / "AppData" / "Local"))
        prog_files = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
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
    elif sys.platform == "darwin":  # macOS
        desktop_candidates = [
            Path("/Applications/Google Antigravity.app/Contents"),
            Path("/Applications/Antigravity.app/Contents"),
            user_home / "Applications" / "Google Antigravity.app" / "Contents",
            user_home / "Applications" / "Antigravity.app" / "Contents",
            Path("/Applications/Google Antigravity.app"),
            Path("/Applications/Antigravity.app"),
        ]
        ide_candidates = [
            Path("/Applications/Google Antigravity IDE.app/Contents"),
            Path("/Applications/Antigravity IDE.app/Contents"),
            user_home / "Applications" / "Google Antigravity IDE.app" / "Contents",
            user_home / "Applications" / "Antigravity IDE.app" / "Contents",
            Path("/Applications/Google Antigravity IDE.app"),
            Path("/Applications/Antigravity IDE.app"),
        ]
        mac_support_dir = user_home / "Library" / "Application Support" / "Antigravity IDE"
        ide_user_data = mac_support_dir
    else:  # Linux
        desktop_candidates = [
            Path("/opt/Google/Antigravity"),
            Path("/opt/antigravity"),
            Path("/opt/Google/antigravity"),
            Path("/usr/lib/antigravity"),
            Path("/usr/share/antigravity"),
            user_home / ".local" / "share" / "Google" / "Antigravity",
            user_home / ".local" / "share" / "antigravity",
            user_home / ".local" / "share" / "programs" / "antigravity",
        ]
        ide_candidates = [
            Path("/opt/Google/Antigravity IDE"),
            Path("/opt/antigravity-ide"),
            Path("/usr/lib/antigravity-ide"),
            Path("/usr/share/antigravity-ide"),
            user_home / ".local" / "share" / "antigravity-ide",
            user_home / ".local" / "share" / "programs" / "antigravity-ide",
        ]
        linux_config_dir = Path(os.environ.get("XDG_CONFIG_HOME", user_home / ".config")) / "Antigravity IDE"
        ide_user_data = linux_config_dir

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

    return {
        "ide_path": detected_ide,
        "desktop_path": detected_desktop,
        "ide_user_data": ide_user_data,
    }


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
    from localizer_state import atomic
    backup = filepath.with_suffix(filepath.suffix + BACKUP_SUFFIX)
    if not backup.is_file():
        return False
    try:
        atomic(filepath, backup.read_bytes())
        return True
    except OSError as error:
        log_fn(f"[Откат] Сбой: {error}")
        return False


# =============================================================================
# ASAR Archive Parsing and Safe Writing
# =============================================================================

def read_asar(path: Path):
    return read_asar_bytes(Path(path).read_bytes())


def read_asar_bytes(raw: bytes):
    if len(raw) < 16:
        raise ValueError("Truncated ASAR")
    u0, header_size, u2, json_len = struct.unpack("<IIII", raw[:16])
    start = 8 + header_size
    if u0 != 4 or header_size != u2 + 4 or json_len > u2 - 4 or start > len(raw) or start < 16:
        raise ValueError("Invalid ASAR header")
    header = json.loads(raw[16:16 + json_len].decode("utf-8"))
    if not isinstance(header, dict) or not isinstance(header.get("files"), dict):
        raise ValueError("Invalid ASAR file list")
    return header, raw[start:]


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

        os.replace(temp_path, path)
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
    return strip_jsonc(text)


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

class DagamiLocalizer(InstallOperations):
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
        self.ide_user_data = ide_user_data or get_default_paths()["ide_user_data"]
        self.log = log_fn
        self.force_kill = force_kill
        self.no_kill = no_kill

    def get_lang_meta(self, lang_code: str) -> dict:
        return dtb.get_language_metadata(lang_code)



# Alias for backward compatibility
AntigravityLocalizer = DagamiLocalizer


# =============================================================================
# Interactive CLI
# =============================================================================

def run_interactive_cli(localizer: DagamiLocalizer):
    if sys.stdin is None or getattr(sys.stdin, "closed", False) or not sys.stdin.isatty():
        safe_print("Нет ввода с консоли. Запустите --gui или задайте --lang.")
        return 1
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
        self.root.geometry("720x640")
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

        # Russian is the explicit default, independent of directory order.
        langs = sorted(list_available_languages(), key=lambda item: (item.get("code") != "ru", item.get("code", "")))
        self.lang_choices = {f"{item.get('nativeName', item['code'])} · {item['code'].upper()}": item['code'] for item in langs}
        self.lang_names = {label: next(item.get('nativeName', code) for item in langs if item['code'] == code) for label, code in self.lang_choices.items()}
        default_lang_str = next((label for label, code in self.lang_choices.items() if code == 'ru'), '')
        self.selected_lang_var = tk.StringVar(value=default_lang_str)
        self.bundle_dir = BUNDLE_DIR
        self.version = APP_VERSION

        self._busy = False
        self._update_busy = False
        self._log_queue = queue.Queue()
        self._build_ui()
        self.selected_lang_var.trace_add("write", self._sync_language)
        self._sync_language()
        self._update_status()
        self.root.after(100, self._drain_log)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        from native_design import build_interface
        build_interface(self)

    def _sync_language(self, *_):
        label = self.selected_lang_var.get()
        valid = label in self.lang_choices
        name = self.lang_names.get(label, '')
        self.language_hint.configure(
            text=f"Выбрано: {name}. Пакет будет применён к отмеченным приложениям." if valid else "Выберите язык из списка, чтобы продолжить.",
            foreground="#5b6574" if valid else "#b3261e")
        self.btn_install.configure(text=f"Установить: {name}" if valid else "Выберите язык",
                                   state='normal' if valid and not self._busy and not self._update_busy else 'disabled')

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
        ide_ok = bool(self.ide_path_var.get().strip()) and validate_ide_path(Path(self.ide_path_var.get()))
        self.ide_status_label.config(
            text="Найдено" if ide_ok else "Укажите папку",
            foreground="#146c43" if ide_ok else "#5b6574"
        )
        desk_ok = bool(self.desktop_path_var.get().strip()) and validate_desktop_path(Path(self.desktop_path_var.get()))
        self.desk_status_label.config(
            text="Найдено" if desk_ok else "Укажите папку",
            foreground="#146c43" if desk_ok else "#5b6574"
        )

    def log(self, msg: str):
        self._log_queue.put(msg)

    def _drain_log(self):
        try:
            while True:
                self.log_text.insert(self.tk.END, self._log_queue.get_nowait() + "\n")
                self.log_text.see(self.tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log)

    def _set_actions(self, enabled):
        self.btn_restore.configure(state='normal' if enabled else 'disabled')
        for widget in self._language_controls + self._input_controls:
            widget.configure(state='normal' if enabled else 'disabled')
        self._sync_language()
        if self._busy or self._update_busy:
            self.progress.grid()
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.grid_remove()

    def _on_close(self):
        if self._busy or self._update_busy:
            self.messagebox.showinfo("Занято", "Дождитесь конца операции.")
            return
        self.close()

    def close(self):
        self.updates.closed = True
        timers = self.root.tk.call("after", "info")
        if isinstance(timers, str):
            timers = self.root.tk.splitlist(timers)
        for timer in timers:
            self.root.after_cancel(timer)
        self.root.destroy()

    def _run_localizer(self, restoring=False):
        if self._busy or self._update_busy:
            return
        lang_code = self.lang_choices.get(self.selected_lang_var.get())
        if not restoring and not lang_code:
            self._sync_language()
            if self._language_controls:
                self._language_controls[0].focus_set()
            self.messagebox.showerror("Язык", "Выберите язык из списка, чтобы продолжить.")
            return
        if not self.opt_ide.get() and not self.opt_desktop.get():
            self.messagebox.showinfo("Выбор", "Выберите приложение.")
            return
        self._busy = True
        self.operation_status.set("Возврат исходных файлов…" if restoring else "Установка: " + self.lang_names[self.selected_lang_var.get()] + "…")
        self._set_actions(False)
        self.updates.refresh()
        self.log_text.delete("1.0", self.tk.END)
        # Snapshot Tk variables here; worker threads never read or write widgets.
        ide_enabled, desktop_enabled = self.opt_ide.get(), self.opt_desktop.get()
        ide_text, desk_text = self.ide_path_var.get().strip(), self.desktop_path_var.get().strip()
        if (ide_enabled and not ide_text) or (desktop_enabled and not desk_text):
            self._busy = False
            self.operation_status.set("Укажите папку выбранного приложения и повторите запуск.")
            self._set_actions(True)
            self.messagebox.showerror("Путь", "Укажите путь к выбранному приложению.")
            return
        ide_p = Path(ide_text) if ide_enabled else None
        desk_p = Path(desk_text) if desktop_enabled else None
        def worker():
            try:
                localizer = DagamiLocalizer(ide_path=ide_p, desktop_path=desk_p, log_fn=self.log)
                if restoring:
                    success = localizer.restore_all()
                    message = "Исходный вид возвращён." if success else "Не всё удалось. См. журнал."
                else:
                    success = True
                    if ide_enabled and not localizer.install_ide(lang_code): success = False
                    if desktop_enabled and not localizer.install_desktop(lang_code): success = False
                    message = "Язык установлен." if success else "Не всё удалось. См. журнал."
            except Exception:
                self.log("Сбой операции. См. пути и права записи.")
                message = "Сбой операции. См. журнал."
            self.updates.events.put(lambda message=message: self._on_finish(message))
        threading.Thread(target=worker, daemon=True).start()

    def _on_install(self):
        self._run_localizer()

    def _on_restore(self):
        self._run_localizer(restoring=True)

    def _on_finish(self, message: str):
        self._busy = False
        self.operation_status.set(message)
        self._set_actions(not self._update_busy)
        self._update_status()
        self.updates.refresh()
        self.messagebox.showinfo("Готово", message)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--apply-update":
        return app_updates.run_helper(sys.argv[2])
    parser = argparse.ArgumentParser(
        description="Dagami Antigravity Language Pack — мультиязычная локализация Google Antigravity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Сообщество: {TELEGRAM_URL}\nПоддержать проект: {DONATION_URL}",
    )
    parser.add_argument("--version", "-v", action="version", version=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument("--verify-bundle", action="store_true", help="Проверить целостность бандла ресурсов")
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

    parser.add_argument("--check-update", action="store_true", help="Проверить новую версию на GitHub")
    parser.add_argument("--download-update", action="store_true", help="Скачать новую версию без установки")
    args = parser.parse_args()

    if args.check_update or args.download_update:
        try:
            release = app_updates.check()
            safe_print("Установлено: " + APP_VERSION + "; GitHub: " + (release["tag"] if release else "нет пакета"))
            if args.download_update and app_updates.newer(release):
                safe_print("Файл скачан и проверен: " + str(app_updates.download(release)))
            return 0
        except Exception:
            safe_print("Нет связи с GitHub или файл не прошёл проверку. Проверьте сеть и прокси.")
            return 1

    if args.verify_bundle:
        ok, issues = verify_bundle_integrity()
        if ok:
            safe_print("[+] Целостность бандла ресурсов подтверждена.")
            sys.exit(0)
        else:
            safe_print("[-] Обнаружены проблемы целостности:")
            for issue in issues:
                safe_print(f"  - {issue}")
            sys.exit(1)

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
        ide_user_data=default_paths["ide_user_data"],
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
        return run_interactive_cli(localizer)

    # Otherwise open GUI
    try:
        from native_design import enable_dpi_awareness
        enable_dpi_awareness()
        import tkinter as tk
        root = tk.Tk(className="DagamiLanguagePack")
        app = DagamiGUI(root)
        root.mainloop()
    except Exception as e:
        # If GUI fails (headless, SSH, or no display), fallback to CLI
        safe_print(f"[!] Не удалось запустить графический интерфейс ({e}). Переключение в консольный режим.")
        return run_interactive_cli(localizer)


if __name__ == "__main__":
    sys.exit(main())
