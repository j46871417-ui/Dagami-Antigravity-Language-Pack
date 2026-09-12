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

BACKUP_SUFFIX = ".bak.original"
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


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
    Удаляет однострочные (//) и многострочные (/* */) комментарии из JSONC (JSON with Comments),
    сохраняя строковые литералы без повреждений для последующего парсинга json.loads.
    """
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return ""
        return s
    pattern = re.compile(r'//.*?$|/\*.*?\*/|"(?:\\.|[^\\"])*"', re.DOTALL | re.MULTILINE)
    return re.sub(pattern, replacer, text)


def replace_js_string_literals(content: str, string_map: dict[str, str], log_fn=safe_print) -> tuple[str, int]:
    """
    Контекстно-зависимая замена строковых литералов в JS-коде.
    Заменяет исключительно литералы в одинарных, двойных или обратных кавычках,
    не затрагивая имена переменных, ключи объектов (key: value), пути импортов и директивы.
    """
    changes = 0
    # Черный список: служебные идентификаторы, протоколы, расширения и системные пути
    blacklist_patterns = (
        "vscode.", "antigravity.", "http://", "https://", "file://",
        ".js", ".json", ".ts", ".node", "/", "\\"
    )

    for en_s, ru_s in string_map.items():
        if not en_s or not isinstance(en_s, str) or en_s == ru_s:
            continue

        # Пропуск системных идентификаторов
        if any(bp in en_s for bp in blacklist_patterns) and not (" " in en_s or en_s.endswith(":") or en_s.endswith(".")):
            log_fn(f"  [Контекстный фильтр] Пропуск потенциального системного идентификатора: '{en_s}'")
            continue

        # Поиск строкового литерала в кавычках с проверкой, что это не ключ объекта (без ':' сразу после кавычки)
        escaped_en = re.escape(en_s)
        # Шаблон: кавычка, текст, кавычка, и после кавычки нет двоеточия (что исключает "prop": val)
        pattern = re.compile(r'(?<![a-zA-Z0-9_\$\.\:])(["\'`])' + escaped_en + r'\1(?!\s*:)')

        def make_repl(quote_match):
            q = quote_match.group(1)
            # Экранируем кавычку того же типа внутри русского перевода, если она там есть
            escaped_ru = ru_s.replace(q, f"\\{q}") if q != '`' else ru_s
            return f"{q}{escaped_ru}{q}"

        new_content, count = pattern.subn(make_repl, content)
        if count > 0:
            content = new_content
            changes += count
        elif en_s in content:
            # Найдено в тексте, но не в виде чистого литерала (например ключ или часть составного идентификатора)
            log_fn(f"  [Контекстный фильтр] Строка '{en_s}' пропущена: используется как ключ объекта или имя свойства.")

    return content, changes

class AntigravityLocalizer:
    def __init__(self, ide_path: Path = None, desktop_path: Path = None, ide_user_data: Path = None, log_fn=safe_print):
        self.ide_path = ide_path
        self.desktop_path = desktop_path
        self.ide_user_data = ide_user_data or (Path.home() / ".antigravity-ide")
        self.log = log_fn

    def install_ide(self) -> bool:
        if not self.ide_path or not validate_ide_path(self.ide_path):
            self.log("[IDE] Путь к Antigravity IDE не найден или некорректен.")
            return False

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

        # 1. Языковой пакет VS Code
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
        else:
            self.log("[IDE] Языковой пакет VS Code уже установлен.")

        # 2. argv.json -> locale: ru (с сохранением JSONC и валидацией)
        if argv_json_path.exists():
            backup_file(argv_json_path, self.log)
            try:
                with open(argv_json_path, "r", encoding="utf-8") as f:
                    argv_content = f.read()

                import re
                if '"locale"' in argv_content:
                    argv_content = re.sub(r'"locale"\s*:\s*"[^"]*"', '"locale": "ru"', argv_content)
                else:
                    argv_content = re.sub(r'(\{)', r'\1\n\t"locale": "ru",', argv_content, count=1)

                # Предварительная валидация очищенного от комментариев JSON
                clean_test = strip_json_comments(argv_content)
                json.loads(clean_test)

                with open(argv_json_path, "w", encoding="utf-8") as f:
                    f.write(argv_content)

                # Пост-валидация записанного на диск файла
                with open(argv_json_path, "r", encoding="utf-8") as f:
                    post_test = strip_json_comments(f.read())
                    json.loads(post_test)

                self.log("[IDE] В argv.json включен русский язык (locale: ru).")
            except Exception as e:
                self.log(f"[IDE] Ошибка обновления/валидации argv.json: {e}. Откат к оригиналу.")
                restore_file(argv_json_path, self.log)

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
            except Exception as e:
                self.log(f"[IDE] Ошибка патчинга/валидации package.json: {e}. Откат к оригиналу.")
                restore_file(pkg_path, self.log)

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
            except Exception as e:
                self.log(f"[IDE] Ошибка патчинга extension.js: {e}. Откат к оригиналу.")
                restore_file(ext_js_path, self.log)

        # 5. Патч nls.messages.json (полная русификация каркаса VS Code: меню, окна, настройки)
        nls_path = self.ide_path / "resources" / "app" / "out" / "nls.messages.json"
        if nls_path.exists() and NLS_RU_FILE.exists():
            backup_file(nls_path, self.log)
            try:
                shutil.copy2(NLS_RU_FILE, nls_path)
                self.log("[IDE] Применена русская локализация меню и каркаса VS Code (15 180 строк).")
            except Exception as e:
                self.log(f"[IDE] Ошибка обновления nls.messages.json: {e}. Откат к оригиналу.")
                restore_file(nls_path, self.log)

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
            except Exception as e:
                self.log(f"[IDE] Ошибка патчинга jetskiAgent: {e}. Откат к оригиналу.")
                restore_file(jetski_path, self.log)

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

        kill_antigravity_processes(self.log)
        self.log("\n--- Русификация Antigravity 2.0 Desktop ---")
        asar_path = self.desktop_path / "resources" / "app.asar"
        if not asar_path.exists():
            self.log(f"[Desktop] app.asar не найден: {asar_path}")
            return False

        # Polling: ожидание разблокировки app.asar процессами перед записью
        if not wait_for_files_unlocked([asar_path], timeout=10.0, log_fn=self.log):
            self.log(f"[Desktop] Ошибка: {asar_path.name} заблокирован другим процессом. Прерывание.")
            return False

        backup_file(asar_path, self.log)

        try:
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

                if path_str in targets and targets[path_str]:
                    try:
                        # Проверка валидности UTF-8 перед модификацией
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
                        marker = "// Antigravity UI Runtime Localizer"
                        if marker in preload_text:
                            preload_text = preload_text[:preload_text.index(marker)].rstrip()
                        preload_text += "\n\n" + dom_script
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
            self.log(f"[Desktop] Заменено строк в app.asar: {changes}")
            self.log("[Desktop] Русификация Desktop успешно завершена!")
            return True
        except Exception as e:
            self.log(f"[Desktop] Ошибка патчинга app.asar: {e}. Откат к оригиналу.")
            restore_file(asar_path, self.log)
            return False

    def restore_all(self) -> bool:
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
            asar_path = self.desktop_path / "resources" / "app.asar"
            if restore_file(asar_path, self.log):
                restored += 1

        self.log(f"Всего файлов восстановлено: {restored}")
        return restored > 0


# =============================================================================
# Графический интерфейс (Tkinter)
# =============================================================================

class LocalizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Antigravity — Русификатор")
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
            ide_p = Path(self.ide_path_var.get()) if self.opt_ide.get() else None
            desk_p = Path(self.desktop_path_var.get()) if self.opt_desktop.get() else None

            localizer = AntigravityLocalizer(
                ide_path=ide_p,
                desktop_path=desk_p,
                log_fn=self.log,
            )

            success = True
            if self.opt_ide.get():
                if not localizer.install_ide():
                    success = False
            if self.opt_desktop.get():
                if not localizer.install_desktop():
                    success = False

            self.root.after(0, lambda: self._on_finish("Установка завершена!" if success else "Установка завершена с предупреждениями."))

        threading.Thread(target=worker, daemon=True).start()

    def _on_restore(self):
        self._set_buttons_state(False)
        self.log_text.delete("1.0", tk.END)

        def worker():
            ide_p = Path(self.ide_path_var.get())
            desk_p = Path(self.desktop_path_var.get())

            localizer = AntigravityLocalizer(
                ide_path=ide_p,
                desktop_path=desk_p,
                log_fn=self.log,
            )
            localizer.restore_all()
            self.root.after(0, lambda: self._on_finish("Откат к оригинальным файлам завершён!"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_finish(self, message: str):
        self._set_buttons_state(True)
        self._update_status()
        messagebox.showinfo("Готово", message)


# =============================================================================
# CLI точка входа
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Русификатор Google Antigravity")
    parser.add_argument("--cli", action="store_true", help="Запуск в консольном режиме без GUI")
    parser.add_argument("--install", action="store_true", help="Установить русификацию")
    parser.add_argument("--restore", action="store_true", help="Откатить к оригиналу")
    parser.add_argument("--ide-path", type=str, help="Путь к Antigravity IDE")
    parser.add_argument("--desktop-path", type=str, help="Путь к Antigravity Desktop")

    args = parser.parse_args()

    default_paths = get_default_paths()
    ide_p = Path(args.ide_path) if args.ide_path else default_paths["ide_path"]
    desk_p = Path(args.desktop_path) if args.desktop_path else default_paths["desktop_path"]

    if args.cli or args.install or args.restore:
        localizer = AntigravityLocalizer(ide_path=ide_p, desktop_path=desk_p)
        if args.restore:
            localizer.restore_all()
        elif args.install:
            if ide_p:
                localizer.install_ide()
            if desk_p:
                localizer.install_desktop()
        else:
            print("Укажите --install или --restore для CLI режима.")
        return

    # Запуск графического интерфейса
    root = tk.Tk()
    app = LocalizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
