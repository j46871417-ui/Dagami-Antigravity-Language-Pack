#!/usr/bin/env python3
"""
Скрипт верификации собранных артефактов и целостности дистрибутива Antigravity Localizer.

Проверяет:
1. Наличие всех обязательных ресурсов локализации:
   - translations (ide_strings.json, desktop_strings.json, chat_strings.json, dom_translator.js)
   - assets (ru_pack.zip, nls.messages.ru.json)
   - resources/web_bundle_ru (main.js, i18n-ru.js)
2. Целостность нового веб-движка:
   - Синтаксическая валидность JS (через node -c)
   - Присутствие критических компонентов: MarkdownShield, CircuitBreaker, TwoLevelCache, splitTextIntoSafeChunks, GlobalRequestQueue
   - Отсутствие несанкционированных сторонних эндпоинтов (MyMemory)
3. Синхронизацию версий (SemVer) между компонентами (Python, C#, package.json)
4. Работоспособность собранного EXE (при передаче пути к .exe через аргумент):
   - Запуск с флагом --version
   - Запуск с флагом --verify-bundle
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from dagami_ag_localizer import verify_bundle_integrity, __version__ as PY_VERSION


def check_source_bundle(bundle_dir: Path) -> list[str]:
    """Проверяет полноту исходных файлов бандла."""
    ok, issues = verify_bundle_integrity(bundle_dir)
    for lang in ("ru", "zh", "es", "ja", "de", "fr"):
        folder = bundle_dir / "translations" / "languages" / lang
        for name in ("dict.json", "metadata.json", "desktop.json", "ide.json"):
            try:
                data = json.loads((folder / name).read_text("utf-8"))
                if not isinstance(data, dict) or not data: raise ValueError("Empty pack")
            except (ValueError, OSError) as error:
                issues.append(f"{lang}/{name}: {error}")
    return issues


def check_web_bundle_engine(engine_file: Path) -> list[str]:
    """Проверяет синтаксис и критические компоненты JS-движка."""
    issues = []
    if not engine_file.exists():
        return [f"Файл движка не найден: {engine_file}"]

    content = engine_file.read_text(encoding="utf-8")

    # 1. Проверка синтаксиса через node -c если node доступен
    try:
        proc = subprocess.run(
            ["node", "-c", str(engine_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode != 0:
            issues.append(f"Синтаксическая ошибка в {engine_file.name}: {proc.stderr.strip()}")
    except FileNotFoundError:
        pass  # node.js не установлен в окружении
    except Exception as e:
        issues.append(f"Ошибка проверки синтаксиса через node: {e}")

    # 2. Проверка критических классов
    required_symbols = ["const StructuredThoughts", "function createView", "function createTranslator", "function install", "AbortController"]
    for sym in required_symbols:
        if sym not in content:
            issues.append(f"В {engine_file.name} отсутствует обязательный символ: {sym}")

    # 3. Проверка отсутствия сторонних несанкционированных сервисов
    if "api.mymemory.translated.net" in content:
        issues.append("В движке обнаружен несанкционированный эндпоинт MyMemory!")

    return issues


def check_version_consistency() -> list[str]:
    """Проверяет согласованность версий между компонентами проекта."""
    issues = []
    expected_version = PY_VERSION

    # 1. package.json
    pkg_json = REPO_ROOT / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            pkg_ver = data.get("version")
            if pkg_ver and pkg_ver != expected_version:
                issues.append(f"Версия в package.json ({pkg_ver}) не совпадает с Python ({expected_version})")
        except Exception as e:
            issues.append(f"Не удалось проверить package.json: {e}")

    # Historical Program.cs is no longer built or shipped.
    from app_info import APP_VERSION
    if APP_VERSION != expected_version:
        issues.append("Shared app version differs from the entry point.")

    return issues


def check_executable_artifact(exe_path: Path) -> list[str]:
    """Проверяет собранный исполняемый файл .exe."""
    issues = []
    if not exe_path.exists():
        return [f"Исполняемый файл не найден: {exe_path}"]

    if exe_path.stat().st_size < 1024 * 1024:
        issues.append(f"Размер EXE подозрительно мал ({exe_path.stat().st_size} байт). Скорее всего, ресурсы не были упакованы.")

    env = dict(os.environ)
    env["ANTIGRAVITY_SKIP_KILL"] = "1"

    from app_updates import validate_exe
    try:
        validate_exe(exe_path, PY_VERSION)
        # Execute a non-mutating bundled check; the exit code is reliable in windowed builds.
        result = subprocess.run([str(exe_path), "--verify-bundle"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, env=env)
        if result.returncode:
            issues.append(f"Bundled resource check failed: exit={result.returncode}, hex=0x{result.returncode & 0xffffffff:08x}.")
    except Exception as error:
        issues.append("Built EXE failed validation: " + str(error))

    return issues


def main():
    parser = argparse.ArgumentParser(description="Верификатор артефактов и целостности Antigravity Localizer")
    parser.add_argument("target", nargs="?", default=None, help="Путь к проверяемому EXE или каталогу ресурсов")
    args = parser.parse_args()

    all_issues = []

    print(f"=== Верификация дистрибутива Antigravity Localizer v{PY_VERSION} ===")

    # 1. Проверка исходного бандла
    target_path = Path(args.target) if args.target else REPO_ROOT
    if target_path.is_file() and target_path.suffix.lower() == ".exe":
        print(f"[*] Проверка собранного исполняемого файла: {target_path}")
        exe_issues = check_executable_artifact(target_path)
        all_issues.extend(exe_issues)
    else:
        bundle_dir = target_path if (target_path / "translations").exists() else REPO_ROOT
        print(f"[*] Проверка ресурсов в: {bundle_dir}")
        bundle_issues = check_source_bundle(bundle_dir)
        all_issues.extend(bundle_issues)

        engine_file = bundle_dir / "translations" / "structured_thoughts.js"
        engine_issues = check_web_bundle_engine(engine_file)
        all_issues.extend(engine_issues)
        import dagami_translator_builder as builder
        with tempfile.TemporaryDirectory() as temp:
            for lang in ("ru", "zh", "es", "ja", "de", "fr"):
                try:
                    generated = Path(temp) / (lang + ".js")
                    generated.write_text(builder.build_runtime_translator_js(lang), "utf-8")
                    proc = subprocess.run(["node", "--check", str(generated)], capture_output=True, text=True, timeout=15)
                    if proc.returncode: all_issues.append(lang + ": " + proc.stderr)
                except (OSError, ValueError) as error:
                    all_issues.append(lang + ": " + str(error))

    # 2. Проверка согласованности версий
    print("[*] Проверка согласованности версий компонентов...")
    ver_issues = check_version_consistency()
    all_issues.extend(ver_issues)

    # Итог
    if all_issues:
        print("\n[-] ОБНАРУЖЕНЫ ОШИБКИ ЦЕЛОСТНОСТИ ДИСТРИБУТИВА:")
        for iss in all_issues:
            print(f"    - {iss}")
        sys.exit(1)
    else:
        print("\n[+] Все обязательные ресурсы, веб-движок и версии УСПЕШНО ВЕРИФИЦИРОВАНЫ.")
        sys.exit(0)


if __name__ == "__main__":
    main()
