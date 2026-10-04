"""
Google Antigravity Localizer (Русификатор).

Графическое и консольное приложение для автоматической русификации:
- Antigravity IDE (каркас VS Code + расширение ядра Antigravity)
- Antigravity 2.0 (Desktop Electron App)

Поддерживает автоматическое обнаружение путей, ручной выбор,
создание резервных копий и полный откат к оригиналу.
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
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Единая авторитетная реализация замены JS-литералов (F-001/F-026).
# Импорт обязателен явно: PyInstaller не находит его по анализу вызовов,
# если обращаться через локальную обёртку.
import js_literals as jsl
from jsonc_utils import strip_jsonc, parse_jsonc, update_argv_locale
from step_status import StepStatus, StepResult
from compatibility import (
    validate_asar_compatibility,
    inject_language_server_web_bundle,
    CompatibilityError,
    SUPPORTED_VERSIONS,
)
from transaction_manager import (
    SingleInstanceLock,
    BackupManager,
    TransactionJournal,
    atomic_stage_and_replace,
    LockError,
)

__version__ = "1.0.1"

# Пути к встроенным ресурсам (совместимо с PyInstaller _MEIPASS)
if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    BUNDLE_DIR = Path(__file__).parent

IDE_TRANSLATIONS_FILE = BUNDLE_DIR / "translations" / "ide_strings.json"
DESKTOP_TRANSLATIONS_FILE = BUNDLE_DIR / "translations" / "desktop_strings.json"
CHAT_TRANSLATIONS_FILE = BUNDLE_DIR / "translations" / "chat_strings.json"
DOM_TRANSLATOR_FILE = BUNDLE_DIR / "translations" / "dom_translator.js"
RU_PACK_ZIP = BUNDLE_DIR / "assets" / "ru_pack.zip"
NLS_RU_FILE = BUNDLE_DIR / "assets" / "nls.messages.ru.json"
WEB_BUNDLE_RU_SOURCE = BUNDLE_DIR / "resources" / "web_bundle_ru"

BACKUP_SUFFIX = ".bak.original"
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def verify_bundle_integrity(bundle_dir: Path = None) -> tuple[bool, list[str]]:
    """
    Проверяет наличие и целостность всех обязательных компонентов установщика.
    Возвращает (success: bool, issues: list[str]).
    """
    target_dir = bundle_dir or BUNDLE_DIR
    issues = []

    required_files = [
        target_dir / "translations" / "ide_strings.json",
        target_dir / "translations" / "desktop_strings.json",
        target_dir / "translations" / "chat_strings.json",
        target_dir / "translations" / "dom_translator.js",
        target_dir / "assets" / "ru_pack.zip",
        target_dir / "assets" / "nls.messages.ru.json",
        target_dir / "resources" / "web_bundle_ru" / "main.js",
        target_dir / "resources" / "web_bundle_ru" / "i18n-ru.js",
    ]

    for f in required_files:
        if not f.exists():
            issues.append(f"Отсутствует обязательный ресурс: {f.name}")
        elif f.stat().st_size == 0:
            issues.append(f"Обязательный ресурс пуст: {f.name}")

    web_bundle_engine = target_dir / "resources" / "web_bundle_ru" / "i18n-ru.js"
    if web_bundle_engine.exists():
        try:
            content = web_bundle_engine.read_text(encoding="utf-8")
            required_symbols = ["MarkdownShield", "CircuitBreaker", "TwoLevelCache", "splitTextIntoSafeChunks"]
            for sym in required_symbols:
                if sym not in content:
                    issues.append(f"В i18n-ru.js отсутствует критический компонент движка: {sym}")
        except Exception as e:
            issues.append(f"Не удалось прочитать i18n-ru.js: {e}")

    return (len(issues) == 0, issues)


def safe_print(*args, **kwargs):
    if sys.stdout is not None:
        try:
            print(*args, **kwargs)
        except Exception:
            pass


# =============================================================================
# Принудительное закрытие процессов Antigravity
# =============================================================================

ANTIGRAVITY_PROCESS_NAMES = [
    "Antigravity IDE.exe",
    "Antigravity.exe",
]


def wait_for_files_unlocked(file_paths: list[Path], timeout: float = 10.0, poll_interval: float = 0.25, log_fn=safe_print) -> bool:
    """
    Опрашивает доступность списка файлов на запись (polling).
    Возвращает True, как только все файлы разблокированы, либо False по истечении таймаута.
    """
    start_time = time.time()
    existing_files = [p for p in file_paths if p and p.exists()]
    if not existing_files:
        return True

    log_fn(f"  Ожидание разблокировки целевых файлов (таймаут {timeout:.0f}с)...")
    while time.time() - start_time < timeout:
        all_unlocked = True
        for p in existing_files:
            try:
                # Пытаемся открыть файл на эксклюзивный доступ для чтения и записи
                with open(p, "r+b"):
                    pass
            except (IOError, PermissionError, OSError):
                all_unlocked = False
                break
        if all_unlocked:
            return True
        time.sleep(poll_interval)

    # Финальная проверка заблокированных файлов
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


def kill_antigravity_processes(log_fn=safe_print):
    """
    Завершает активные процессы Antigravity и опрашивает систему до фактического выхода процессов.
    """
    if "unittest" in sys.modules or os.environ.get("ANTIGRAVITY_SKIP_KILL", "").lower() in ("1", "true", "yes"):
        log_fn("[Процессы] Пропуск завершения процессов (тестовая среда / ANTIGRAVITY_SKIP_KILL).")
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
        log_fn("  Команды завершения отправлены. Ожидание выгрузки процессов из памяти...")
        # Polling процессов tasklist до 5 секунд
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
# Поиск путей по умолчанию
# =============================================================================

def get_default_paths():
    local_app_data = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))
    user_home = Path(os.path.expanduser("~"))

    ide_path = local_app_data / "Programs" / "Antigravity IDE"
    desktop_path = local_app_data / "Programs" / "antigravity"
    ide_user_data = user_home / ".antigravity-ide"

    return {
        "ide_path": ide_path if ide_path.exists() else None,
        "desktop_path": desktop_path if desktop_path.exists() else None,
        "ide_user_data": ide_user_data,
    }


def validate_ide_path(path: Path) -> bool:
    if not path or not path.exists():
        return False
    pkg = path / "resources" / "app" / "extensions" / "antigravity" / "package.json"
    exe = path / "Antigravity IDE.exe"
    return pkg.exists() or exe.exists()


def validate_desktop_path(path: Path) -> bool:
    if not path or not path.exists():
        return False
    asar = path / "resources" / "app.asar"
    exe = path / "Antigravity.exe"
    return asar.exists() or exe.exists()


# =============================================================================
# Утилиты бэкапа и отката
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
        shutil.copy2(backup, filepath)
        log_fn(f"[Откат] Восстановлен: {filepath.name}")
        return True
    return False


# =============================================================================
# ASAR парсер и патчер
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


def write_asar_atomic(path: Path, header: dict, data: bytes):
    """
    Атомарная запись ASAR-архива по паттерну 'write-to-temp + atomic-rename'.
    Временный файл создается рядом с оригиналом на том же томе, после проверки размера
    выполняется os.replace. При любых сбоях временный файл удаляется.
    """
    json_bytes = json.dumps(header, separators=(',', ':')).encode("utf-8")
    json_len = len(json_bytes)
    pad_len = (4 - (json_len % 4)) % 4
    padding = b"\x00" * pad_len

    u2 = json_len + 4 + pad_len
    header_size = u2 + 4
    u0 = 4

    magic = struct.pack("<IIII", u0, header_size, u2, json_len)
    expected_size = 16 + json_len + pad_len + len(data)

    # Временный файл строго в том же каталоге, чтобы os.replace был атомарным
    temp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(temp_path, "wb") as f:
            f.write(magic)
            f.write(json_bytes)
            f.write(padding)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        # Валидация размера созданного файла
        actual_size = temp_path.stat().st_size
        if actual_size != expected_size:
            raise IOError(f"Несоответствие размера ASAR: ожидалось {expected_size} байт, записано {actual_size} байт")

        # Атомарная замена целевого файла
        os.replace(temp_path, path)
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def write_asar(path: Path, header: dict, data: bytes):
    # Псевдоним для сохранения обратной совместимости вызовов
    write_asar_atomic(path, header, data)


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


# =============================================================================
# Ядро локализации
# =============================================================================


def strip_json_comments(text: str) -> str:
    """
    Удаляет однострочные (//) и многострочные (/* */) комментарии и завершающие
    запятые из JSONC, сохраняя строковые литералы без повреждений.
    """
    return strip_jsonc(text)


PRELOAD_MARKER = "// Antigravity UI Runtime Localizer"


def inject_dom_translator(preload_text: str, dom_script: str) -> str:
    """
    Идемпотентно внедряет движок русификации в конец preload.js.

    Контракт идемпотентности (F-002): повторный вызов на уже пропатченном тексте
    даёт байт-в-байт тот же результат. Достигается тем, что
    translations/dom_translator.js начинается с PRELOAD_MARKER, и мы отрезаем
    всё начиная с этого маркера перед повторной вставкой. Без маркера в исходнике
    каждая установка добавляла бы ещё одну полную копию движка, а app.asar
    раздувался бы на ~60 КБ за запуск.

    Если маркера нет ни в preload, ни в dom_script — внедрение всё равно
    происходит (совместимость со старым dom_translator.js), но идемпотентность
    не гарантируется; это осознанный компромисс, а не недосмотр.
    """
    if PRELOAD_MARKER in preload_text:
        preload_text = preload_text[:preload_text.index(PRELOAD_MARKER)]
    # rstrip делается ВСЕГДА, а не только на ветке с маркером: иначе первая
    # установка на preload.js, заканчивающийся переводом строки, даёт лишний
    # '\n' (три подряд вместо двух), и первая установка отличается по размеру
    # от всех последующих. Это тот же класс дефекта, что и F-002.
    return preload_text.rstrip() + "\n\n" + dom_script


def replace_js_string_literals(content: str, string_map: dict[str, str], log_fn=safe_print) -> tuple[str, int]:
    """
    Контекстно-зависимая замена строковых литералов в JS-коде.

    Делегирует в js_literals.py — единую авторитетную реализацию, которую
    использует и patch_ide.py. Раньше здесь была вторая, расходящаяся копия
    логики: она не экранировала обратный слэш и ${ в backtick-литералах (F-026).
    Публичное имя и сигнатура сохранены для обратной совместимости.
    """
    return jsl.replace_js_string_literals(content, string_map, log_fn=log_fn)


class AntigravityLocalizer:
    def __init__(self, ide_path: Path = None, desktop_path: Path = None, ide_user_data: Path = None, log_fn=safe_print, auto_kill: bool = True):
        self.ide_path = ide_path
        self.desktop_path = desktop_path
        self.ide_user_data = ide_user_data or (Path.home() / ".antigravity-ide")
        self.log = log_fn
        self.auto_kill = auto_kill

    def install_ide(self) -> bool:
        if not self.ide_path or not validate_ide_path(self.ide_path):
            self.log("[IDE] Путь к Antigravity IDE не найден или некорректен.")
            return False

        if self.auto_kill:
            kill_antigravity_processes(self.log)
        self.log("\n--- Русификация Antigravity IDE ---")

        ext_base = self.ide_path / "resources" / "app" / "extensions" / "antigravity"
        pkg_path = ext_base / "package.json"
        ext_js_path = ext_base / "dist" / "extension.js"
        argv_json_path = self.ide_user_data / "argv.json"
        jetski_path = self.ide_path / "resources" / "app" / "out" / "jetskiAgent" / "main.js"

        # Polling: ожидание освобождения дескрипторов файлов процессами
        ide_targets = [p for p in [pkg_path, ext_js_path, argv_json_path, jetski_path] if p.exists()]
        if not wait_for_files_unlocked(ide_targets, timeout=10.0, log_fn=self.log):
            self.log("[IDE] Ошибка: целевые файлы заблокированы внешними процессами. Прерывание.")
            return False

        steps: list[StepResult] = []

        # 1. Языковой пакет VS Code
        ext_dir = self.ide_user_data / "extensions"
        pack_target = ext_dir / "ms-ceintl.vscode-language-pack-ru-1.106.0-universal"
        if not pack_target.exists():
            if RU_PACK_ZIP.exists():
                try:
                    self.log("[IDE] Распаковка русского языкового пакета VS Code...")
                    ext_dir.mkdir(parents=True, exist_ok=True)
                    pack_target.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(RU_PACK_ZIP, "r") as zf:
                        zf.extractall(pack_target)
                    self.log("[IDE] Языковой пакет успешно установлен.")
                    steps.append(StepResult("vscode_language_pack", StepStatus.SUCCESS, "Установлен"))
                except Exception as e:
                    self.log(f"[IDE] Ошибка распаковки языкового пакета: {e}")
                    steps.append(StepResult("vscode_language_pack", StepStatus.FAILED, str(e), is_mandatory=False))
            else:
                self.log("[IDE] Архив языкового пакета не найден, пропускаем.")
                steps.append(StepResult("vscode_language_pack", StepStatus.SKIPPED, "Архив не найден", is_mandatory=False))
        else:
            self.log("[IDE] Языковой пакет VS Code уже установлен.")
            steps.append(StepResult("vscode_language_pack", StepStatus.ALREADY_DONE, "Уже установлен"))

        # 2. argv.json -> locale: ru (с сохранением JSONC и валидацией)
        if argv_json_path:
            if argv_json_path.exists():
                backup_file(argv_json_path, self.log)
            if not update_argv_locale(argv_json_path, target_locale="ru", log_fn=self.log):
                self.log("[IDE] Ошибка обновления/валидации argv.json. Откат к оригиналу.")
                restore_file(argv_json_path, self.log)
                steps.append(StepResult("argv_locale", StepStatus.FAILED, "Не удалось обновить argv.json", is_mandatory=False))
            else:
                steps.append(StepResult("argv_locale", StepStatus.SUCCESS, "locale: ru установлен"))

        # 3. Патч package.json расширения antigravity (через json.load/dump с валидацией)
        if pkg_path.exists() and IDE_TRANSLATIONS_FILE.exists():
            backup_file(pkg_path, self.log)
            try:
                with open(IDE_TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                    translations = json.load(f)
                with open(pkg_path, "r", encoding="utf-8") as f:
                    pkg = json.load(f)

                changes = 0
                contributes = pkg.get("contributes", {})

                # Команды
                cmd_trans = translations.get("commands", {})
                for cmd in contributes.get("commands", []):
                    cid = cmd.get("command", "")
                    if cid in cmd_trans:
                        cmd["title"] = cmd_trans[cid]["ru"]
                        changes += 1

                # Настройки
                cfg_trans = translations.get("configuration", {})
                props = contributes.get("configuration", {}).get("properties", {})
                for prop_key, prop_val in props.items():
                    if prop_key in cfg_trans:
                        ru_desc = cfg_trans[prop_key]["ru"]
                        for field in ["description", "markdownDescription"]:
                            if field in prop_val:
                                prop_val[field] = ru_desc
                                changes += 1

                # Заголовок конфигурации
                if "configurationTitle" in translations and "configuration" in contributes:
                    contributes["configuration"]["title"] = translations["configurationTitle"]["ru"]
                    changes += 1

                # Кастомные редакторы
                ed_trans = translations.get("customEditors", {})
                for ed in contributes.get("customEditors", []):
                    eid = ed.get("viewType", "")
                    if eid in ed_trans:
                        ed["displayName"] = ed_trans[eid]["ru"]
                        changes += 1

                with open(pkg_path, "w", encoding="utf-8") as f:
                    json.dump(pkg, f, ensure_ascii=False, indent=2)

                # Пост-валидация записанного package.json
                with open(pkg_path, "r", encoding="utf-8") as f:
                    json.load(f)

                self.log(f"[IDE] Обновлено строк в package.json: {changes}")
                steps.append(StepResult("package_json", StepStatus.SUCCESS, f"Обновлено {changes} строк", is_mandatory=True))
            except Exception as e:
                self.log(f"[IDE] Ошибка патчинга/валидации package.json: {e}. Откат к оригиналу.")
                restore_file(pkg_path, self.log)
                steps.append(StepResult("package_json", StepStatus.FAILED, str(e), is_mandatory=True))
        elif pkg_path.exists():
            steps.append(StepResult("package_json", StepStatus.FAILED, "Файл переводов ide_strings.json не найден", is_mandatory=True))
        else:
            steps.append(StepResult("package_json", StepStatus.SKIPPED, "package.json не найден", is_mandatory=False))

        # 4. Патч extension.js (контекстно-зависимая замена строковых литералов)
        if ext_js_path.exists() and IDE_TRANSLATIONS_FILE.exists():
            backup_file(ext_js_path, self.log)
            try:
                with open(IDE_TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                    translations = json.load(f)
                ui_strings = translations.get("ui_strings", {})
                with open(ext_js_path, "r", encoding="utf-8") as f:
                    content = f.read()

                content, changes = replace_js_string_literals(content, ui_strings, self.log)
                if changes > 0:
                    with open(ext_js_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.log(f"[IDE] Заменено строковых литералов в extension.js: {changes}")
                steps.append(StepResult("extension_js", StepStatus.SUCCESS, f"Заменено {changes} литералов", is_mandatory=True))
            except Exception as e:
                self.log(f"[IDE] Ошибка патчинга extension.js: {e}. Откат к оригиналу.")
                restore_file(ext_js_path, self.log)
                steps.append(StepResult("extension_js", StepStatus.FAILED, str(e), is_mandatory=True))

        # 5. Патч nls.messages.json (полная русификация каркаса VS Code: меню, окна, настройки)
        nls_path = self.ide_path / "resources" / "app" / "out" / "nls.messages.json"
        if nls_path.exists() and NLS_RU_FILE.exists():
            backup_file(nls_path, self.log)
            try:
                shutil.copy2(NLS_RU_FILE, nls_path)
                self.log("[IDE] Применена русская локализация меню и каркаса VS Code (15 180 строк).")
                steps.append(StepResult("nls_messages", StepStatus.SUCCESS, "Применена русификация меню", is_mandatory=False))
            except Exception as e:
                self.log(f"[IDE] Ошибка обновления nls.messages.json: {e}. Откат к оригиналу.")
                restore_file(nls_path, self.log)
                steps.append(StepResult("nls_messages", StepStatus.FAILED, str(e), is_mandatory=False))

        # 6. Патч jetskiAgent/main.js (интерфейс чата и панели агента Antigravity)
        if jetski_path.exists() and CHAT_TRANSLATIONS_FILE.exists():
            backup_file(jetski_path, self.log)
            try:
                with open(CHAT_TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                    chat_trans = json.load(f)
                with open(jetski_path, "r", encoding="utf-8") as f:
                    jetski_content = f.read()

                jetski_content, chat_changes = replace_js_string_literals(jetski_content, chat_trans, self.log)
                if chat_changes > 0:
                    with open(jetski_path, "w", encoding="utf-8") as f:
                        f.write(jetski_content)
                    self.log(f"[IDE] Обновлено строк в интерфейсе агента Antigravity: {chat_changes}")
                steps.append(StepResult("jetski_agent", StepStatus.SUCCESS, f"Обновлено {chat_changes} строк", is_mandatory=False))
            except Exception as e:
                self.log(f"[IDE] Ошибка патчинга jetskiAgent: {e}. Откат к оригиналу.")
                restore_file(jetski_path, self.log)
                steps.append(StepResult("jetski_agent", StepStatus.FAILED, str(e), is_mandatory=False))

        # Проверка обязательных шагов
        failed_mandatory = [s for s in steps if not s.is_success() and s.is_mandatory]
        if failed_mandatory:
            self.log("\n[IDE] Русификация завершилась с ошибкой обязательных компонентов:")
            for s in failed_mandatory:
                self.log(f"  [-] {s.step_name}: {s.message}")
            return False

        # Проверка запущенных процессов
        try:
            p = subprocess.run(
                ["tasklist", "/fi", "imagename eq Antigravity IDE.exe"],
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
            )
            if "Antigravity IDE.exe" in p.stdout:
                self.log("\n[ВНИМАНИЕ] Antigravity IDE сейчас запущен!")
                self.log("Перезапустите редактор, чтобы изменения вступили в силу.")
        except Exception:
            pass

        self.log("[IDE] Русификация IDE успешно завершена!")
        return True

    def install_desktop(self) -> bool:
        if not self.desktop_path or not validate_desktop_path(self.desktop_path):
            self.log("[Desktop] Путь к Antigravity Desktop не найден или некорректен.")
            return False

        if self.auto_kill:
            kill_antigravity_processes(self.log)
        self.log("\n--- Русификация Antigravity 2.0 Desktop ---")
        res_dir = self.desktop_path / "resources"
        asar_path = res_dir / "app.asar"
        if not asar_path.exists():
            self.log(f"[Desktop] app.asar не найден: {asar_path}")
            return False

        # 1. Защита от параллельного запуска через файловый мьютекс
        lock_file = res_dir / ".localizer.lock"
        try:
            lock = SingleInstanceLock(lock_file)
            lock.acquire()
        except LockError as e:
            self.log(f"[Desktop] Ошибка блокировки: {e}")
            return False

        try:
            # 2. Валидация совместимости ядра через манифест до изменения файлов
            compat = validate_asar_compatibility(asar_path)
            if not compat.get("compatible", False):
                self.log(f"[Desktop] Отказ совместимости: {compat.get('reason', 'Несовместимая версия ядра')}")
                return False

            # Polling: ожидание разблокировки app.asar процессами перед записью
            if not wait_for_files_unlocked([asar_path], timeout=10.0, log_fn=self.log):
                self.log(f"[Desktop] Ошибка: {asar_path.name} заблокирован другим процессом. Прерывание.")
                return False

            # 3. Создание бэкапа с привязкой к версии и SHA256 хешу
            backup_mgr = BackupManager(res_dir)
            backup_path = backup_mgr.create_backup(asar_path, version=compat.get("version", "2.11.0"))
            self.log(f"[Desktop] Создана резервная копия ядра ({compat.get('version')}): {backup_path.name}")
            backup_file(asar_path, self.log)  # Обратная совместимость с .bak.original

            # 4. Инициализация журнала транзакции для гарантированного отката
            journal = TransactionJournal(res_dir)
            journal.record_modified(asar_path, backup_path)

            with open(DESKTOP_TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                translations = json.load(f)

            header, data = read_asar(asar_path)
            targets = {
                "dist/menu.js": translations.get("menu", {}),
                "dist/tray.js": translations.get("tray", {}),
                "dist/ideInstall/wizardHtml.js": translations.get("wizard", {}),
            }

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

                # Патч languageServer.js: подключение изолированного веб-бандла
                if path_str == "dist/languageServer.js":
                    try:
                        ls_text = file_bytes.decode("utf-8")
                        new_ls_text = inject_language_server_web_bundle(ls_text)
                        if new_ls_text != ls_text:
                            file_bytes = new_ls_text.encode("utf-8")
                            changes += 1
                            self.log("[Desktop] Внедрён хук веб-бандла в dist/languageServer.js (--web_bundle_path)")
                    except Exception as e:
                        self.log(f"[Desktop] Ошибка патчинга languageServer.js: {e}")

                if path_str in targets and targets[path_str]:
                    try:
                        file_text = file_bytes.decode("utf-8")
                        file_text, sub_changes = replace_js_string_literals(file_text, targets[path_str], self.log)
                        if sub_changes > 0:
                            changes += sub_changes
                            file_bytes = file_text.encode("utf-8")
                    except UnicodeDecodeError:
                        self.log(f"[Desktop] Предупреждение: {path_str} не является валидным UTF-8, модификация пропущена.")

                if path_str == "dist/preload.js" and DOM_TRANSLATOR_FILE.exists():
                    try:
                        with open(DOM_TRANSLATOR_FILE, "r", encoding="utf-8") as f:
                            dom_script = f.read()
                        preload_text = file_bytes.decode("utf-8")
                        preload_text = inject_dom_translator(preload_text, dom_script)
                        file_bytes = preload_text.encode("utf-8")
                        changes += 1
                        self.log("[Desktop] Внедрён движок динамической русификации интерфейса в dist/preload.js")
                    except UnicodeDecodeError:
                        self.log("[Desktop] Предупреждение: dist/preload.js не декодируется в UTF-8, пропуск.")
                    except Exception as e:
                        self.log(f"[Desktop] Ошибка внедрения в preload.js: {e}")

                entry["offset"] = str(current_offset)
                entry["size"] = len(file_bytes)
                if "integrity" in entry:
                    entry["integrity"] = compute_sha256_blocks(file_bytes)

                new_data_chunks.append(file_bytes)
                current_offset += len(file_bytes)

            new_data = b"".join(new_data_chunks)
            # Атомарная запись через временный файл и os.replace
            write_asar_atomic(asar_path, header, new_data)

            # 5. Размещение веб-бандла (web_bundle_ru)
            target_bundle = res_dir / "web_bundle_ru"
            if not WEB_BUNDLE_RU_SOURCE.exists() or not (WEB_BUNDLE_RU_SOURCE / "i18n-ru.js").exists():
                raise FileNotFoundError(
                    f"Критический языковой ресурс не найден: {WEB_BUNDLE_RU_SOURCE}. "
                    "Убедитесь, что установщик собран со всеми необходимыми ресурсами (resources/web_bundle_ru)."
                )
            self.log("[Desktop] Размещение веб-бандла (resources/web_bundle_ru)...")
            target_bundle.mkdir(parents=True, exist_ok=True)
            for root, dirs, files in os.walk(WEB_BUNDLE_RU_SOURCE):
                rel_dir = Path(root).relative_to(WEB_BUNDLE_RU_SOURCE)
                dest_dir = target_bundle / rel_dir
                dest_dir.mkdir(parents=True, exist_ok=True)
                for f in files:
                    src_f = Path(root) / f
                    dst_f = dest_dir / f
                    if not dst_f.exists():
                        journal.record_created(dst_f)
                    else:
                        journal.record_modified(dst_f, dst_f)
                    shutil.copy2(src_f, dst_f)
            self.log("[Desktop] Языковой веб-бандл успешно размещён.")

            # Успешная фиксация транзакции
            journal.commit()
            self.log(f"[Desktop] Заменено строк и точек внедрения в app.asar: {changes}")
            self.log("[Desktop] Русификация Desktop успешно завершена!")
            return True
        except Exception as e:
            self.log(f"[Desktop] Ошибка установки Desktop: {e}. Выполняется откат...")
            try:
                journal.rollback(log_fn=self.log)
            except Exception as rb_err:
                self.log(f"[Desktop] Ошибка отката журнала: {rb_err}")
                restore_file(asar_path, self.log)
            return False
        finally:
            try:
                lock.release()
            except Exception:
                pass

    def restore_all(self) -> bool:
        if self.auto_kill:
            kill_antigravity_processes(self.log)
        self.log("\n=== Откат к оригинальным файлам ===")
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

        # argv.json
        if self.ide_user_data:
            if restore_file(self.ide_user_data / "argv.json", self.log):
                restored += 1

        # Desktop
        if self.desktop_path:
            res_dir = self.desktop_path / "resources"
            asar_path = res_dir / "app.asar"
            backup_mgr = BackupManager(res_dir)
            latest_bak = backup_mgr.find_latest_backup(asar_path)
            legacy_bak = asar_path.with_suffix(asar_path.suffix + BACKUP_SUFFIX)

            asar_restored = False
            if latest_bak and latest_bak.exists():
                if backup_mgr.restore_backup(latest_bak, asar_path):
                    self.log(f"[Desktop] Восстановлен оригинальный app.asar из {latest_bak.name}")
                    restored += 1
                    asar_restored = True
            elif legacy_bak.exists():
                if restore_file(asar_path, self.log):
                    restored += 1
                    asar_restored = True
            else:
                self.log("[Desktop] Предупреждение: резервная копия app.asar не найдена!")

            # web_bundle_ru удаляется ТОЛЬКО если оригинальный app.asar успешно восстановлен
            web_bundle = res_dir / "web_bundle_ru"
            if web_bundle.exists():
                if asar_restored:
                    try:
                        shutil.rmtree(web_bundle)
                        self.log("[Desktop] Каталог web_bundle_ru успешно удалён.")
                    except Exception as e:
                        self.log(f"[Desktop] Ошибка удаления web_bundle_ru: {e}")
                else:
                    self.log("[Desktop] ВНИМАНИЕ: web_bundle_ru сохранён, так как app.asar не был восстановлен из бэкапа. Это предотвращает поломку приложения.")

        self.log(f"Всего файлов восстановлено: {restored}")
        return restored > 0


# =============================================================================
# Графический интерфейс (Tkinter)
# =============================================================================

class LocalizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Google Antigravity — Русификатор v{__version__}")
        self.root.geometry("640x540")
        self.root.minsize(580, 480)

        # Стиль
        style = ttk.Style()
        style.theme_use("clam")

        default_paths = get_default_paths()
        self.ide_path_var = tk.StringVar(value=str(default_paths["ide_path"] or ""))
        self.desktop_path_var = tk.StringVar(value=str(default_paths["desktop_path"] or ""))
        self.opt_ide = tk.BooleanVar(value=bool(default_paths["ide_path"]))
        self.opt_desktop = tk.BooleanVar(value=bool(default_paths["desktop_path"]))

        self._build_ui()
        self._update_status()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        header_label = ttk.Label(
            main_frame,
            text="Русификатор Google Antigravity",
            font=("Segoe UI", 14, "bold"),
        )
        header_label.pack(anchor="w", pady=(0, 4))

        sub_label = ttk.Label(
            main_frame,
            text="Автоматическая установка перевода интерфейса и откат к оригиналу",
            font=("Segoe UI", 9),
            foreground="#555555",
        )
        sub_label.pack(anchor="w", pady=(0, 15))

        # Секция: Antigravity IDE
        ide_group = ttk.LabelFrame(main_frame, text=" Antigravity IDE (Редактор) ", padding="10")
        ide_group.pack(fill=tk.X, pady=(0, 10))

        ide_top = ttk.Frame(ide_group)
        ide_top.pack(fill=tk.X)
        ttk.Checkbutton(ide_top, text="Русифицировать Antigravity IDE", variable=self.opt_ide).pack(side=tk.LEFT)
        self.ide_status_label = ttk.Label(ide_top, text="", font=("Segoe UI", 9, "bold"))
        self.ide_status_label.pack(side=tk.RIGHT)

        ide_path_box = ttk.Frame(ide_group)
        ide_path_box.pack(fill=tk.X, pady=(8, 0))
        ttk.Entry(ide_path_box, textvariable=self.ide_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(ide_path_box, text="Обзор...", width=10, command=self._browse_ide).pack(side=tk.RIGHT)

        # Секция: Antigravity Desktop
        desk_group = ttk.LabelFrame(main_frame, text=" Antigravity 2.0 (Desktop) ", padding="10")
        desk_group.pack(fill=tk.X, pady=(0, 15))

        desk_top = ttk.Frame(desk_group)
        desk_top.pack(fill=tk.X)
        ttk.Checkbutton(desk_top, text="Русифицировать Antigravity 2.0 Desktop", variable=self.opt_desktop).pack(side=tk.LEFT)
        self.desk_status_label = ttk.Label(desk_top, text="", font=("Segoe UI", 9, "bold"))
        self.desk_status_label.pack(side=tk.RIGHT)

        desk_path_box = ttk.Frame(desk_group)
        desk_path_box.pack(fill=tk.X, pady=(8, 0))
        ttk.Entry(desk_path_box, textvariable=self.desktop_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(desk_path_box, text="Обзор...", width=10, command=self._browse_desktop).pack(side=tk.RIGHT)

        # Кнопки действий
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.btn_install = tk.Button(
            btn_frame,
            text="Установить русификацию",
            bg="#1976D2",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=self._on_install,
        )
        self.btn_install.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_restore = tk.Button(
            btn_frame,
            text="Откатить к оригиналу",
            bg="#757575",
            fg="white",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=self._on_restore,
        )
        self.btn_restore.pack(side=tk.LEFT)

        # Лог
        log_frame = ttk.LabelFrame(main_frame, text=" Журнал выполнения ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=("Consolas", 9), height=8)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _browse_ide(self):
        f = filedialog.askdirectory(title="Выберите папку установки Antigravity IDE")
        if f:
            self.ide_path_var.set(f)
            self._update_status()

    def _browse_desktop(self):
        f = filedialog.askdirectory(title="Выберите папку установки Antigravity Desktop")
        if f:
            self.desktop_path_var.set(f)
            self._update_status()

    def _update_status(self):
        ide_ok = validate_ide_path(Path(self.ide_path_var.get()))
        if ide_ok:
            self.ide_status_label.config(text="✓ Обнаружено", foreground="#2E7D32")
        else:
            self.ide_status_label.config(text="✕ Не найдено", foreground="#C62828")

        desk_ok = validate_desktop_path(Path(self.desktop_path_var.get()))
        if desk_ok:
            self.desk_status_label.config(text="✓ Обнаружено", foreground="#2E7D32")
        else:
            self.desk_status_label.config(text="✕ Не найдено", foreground="#C62828")

    def log(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _set_buttons_state(self, enabled: bool):
        st = tk.NORMAL if enabled else tk.DISABLED
        self.btn_install.config(state=st)
        self.btn_restore.config(state=st)

    def _on_install(self):
        self._set_buttons_state(False)
        self.log_text.delete("1.0", tk.END)

        def worker():
            try:
                ide_p = Path(self.ide_path_var.get()) if self.opt_ide.get() else None
                desk_p = Path(self.desktop_path_var.get()) if self.opt_desktop.get() else None

                localizer = AntigravityLocalizer(
                    ide_path=ide_p,
                    desktop_path=desk_p,
                    log_fn=self.log,
                )

                success = True
                if self.opt_ide.get():
                    if not ide_p or not localizer.install_ide():
                        success = False
                if self.opt_desktop.get():
                    if not desk_p or not localizer.install_desktop():
                        success = False

                msg = "Установка завершена успешно!" if success else "Установка завершилась с ошибками. Проверьте лог."
                self.root.after(0, lambda: self._on_finish(msg, is_error=not success))
            except Exception as ex:
                self.log(f"\n[-] Критическая ошибка установки: {ex}")
                self.root.after(0, lambda: self._on_finish(f"Критическая ошибка: {ex}", is_error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _on_restore(self):
        self._set_buttons_state(False)
        self.log_text.delete("1.0", tk.END)

        def worker():
            try:
                ide_p = Path(self.ide_path_var.get()) if self.ide_path_var.get() else None
                desk_p = Path(self.desktop_path_var.get()) if self.desktop_path_var.get() else None

                localizer = AntigravityLocalizer(
                    ide_path=ide_p,
                    desktop_path=desk_p,
                    log_fn=self.log,
                )
                success = localizer.restore_all()
                msg = "Откат к оригинальным файлам завершён успешно!" if success else "Откат не выполнен или не найдены бэкапы."
                self.root.after(0, lambda: self._on_finish(msg, is_error=not success))
            except Exception as ex:
                self.log(f"\n[-] Ошибка отката: {ex}")
                self.root.after(0, lambda: self._on_finish(f"Ошибка отката: {ex}", is_error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _on_finish(self, message: str, is_error: bool = False):
        self._set_buttons_state(True)
        self._update_status()
        if is_error:
            messagebox.showerror("Ошибка", message)
        else:
            messagebox.showinfo("Готово", message)


# =============================================================================
# CLI точка входа
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Русификатор Google Antigravity")
    parser.add_argument("--version", action="version", version=f"Antigravity Localizer v{__version__}")
    parser.add_argument("--verify-bundle", action="store_true", help="Проверить целостность встроенных ресурсов")
    parser.add_argument("--cli", action="store_true", help="Запуск в консольном режиме без GUI")
    parser.add_argument("--install", action="store_true", help="Установить русификацию")
    parser.add_argument("--restore", action="store_true", help="Откатить к оригиналу")
    parser.add_argument("--ide-path", type=str, help="Путь к Antigravity IDE")
    parser.add_argument("--desktop-path", type=str, help="Путь к Antigravity Desktop")

    args = parser.parse_args()

    if args.verify_bundle:
        ok, issues = verify_bundle_integrity()
        if ok:
            safe_print(f"[+] Все ресурсы и веб-бандл Antigravity Localizer v{__version__} успешно верифицированы.")
            sys.exit(0)
        else:
            safe_print(f"[-] Ошибки верификации ресурсов Antigravity Localizer v{__version__}:")
            for iss in issues:
                safe_print(f"    - {iss}")
            sys.exit(1)

    default_paths = get_default_paths()
    ide_p = Path(args.ide_path) if args.ide_path else default_paths["ide_path"]
    desk_p = Path(args.desktop_path) if args.desktop_path else default_paths["desktop_path"]

    if args.cli or args.install or args.restore:
        has_error = False

        if args.ide_path and not validate_ide_path(ide_p):
            safe_print(f"[-] Ошибка: указан неверный путь к Antigravity IDE: {args.ide_path}")
            sys.exit(1)
        if args.desktop_path and not validate_desktop_path(desk_p):
            safe_print(f"[-] Ошибка: указан неверный путь к Antigravity Desktop: {args.desktop_path}")
            sys.exit(1)

        if not ide_p and not desk_p:
            safe_print("[-] Ошибка: целевые пути Antigravity не найдены. Укажите --ide-path или --desktop-path.")
            sys.exit(1)

        localizer = AntigravityLocalizer(ide_path=ide_p, desktop_path=desk_p)
        if args.restore:
            if not localizer.restore_all():
                has_error = True
        elif args.install:
            if ide_p:
                if not localizer.install_ide():
                    has_error = True
            if desk_p:
                if not localizer.install_desktop():
                    has_error = True
        else:
            safe_print("Укажите --install или --restore для CLI режима.")
            sys.exit(1)

        if has_error:
            sys.exit(1)
        sys.exit(0)

    # Запуск графического интерфейса
    root = tk.Tk()
    app = LocalizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
