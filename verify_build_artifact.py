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

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from antigravity_localizer import verify_bundle_integrity, __version__ as PY_VERSION


def check_source_bundle(bundle_dir: Path) -> list[str]:
    """Проверяет полноту исходных файлов бандла."""
    ok, issues = verify_bundle_integrity(bundle_dir)
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
    required_symbols = [
        "class MarkdownShield",
        "class CircuitBreaker",
        "class TwoLevelCache",
        "class GlobalRequestQueue",
        "function splitTextIntoSafeChunks"
    ]
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

    # 2. Program.cs
    program_cs = REPO_ROOT / "Program.cs"
    if program_cs.exists():
        try:
            cs_content = program_cs.read_text(encoding="utf-8")
            match = re.search(r'public\s+const\s+string\s+Version\s*=\s*"([^"]+)"', cs_content)
            if match:
                cs_ver = match.group(1)
                if cs_ver != expected_version:
                    issues.append(f"Версия в Program.cs ({cs_ver}) не совпадает с Python ({expected_version})")
            else:
                issues.append("Не удалось найти AppConfig.Version в Program.cs")
        except Exception as e:
            issues.append(f"Не удалось проверить Program.cs: {e}")

    return issues


def check_executable_artifact(exe_path: Path) -> list[str]:
    """Проверяет собранный исполняемый файл .exe."""
    issues = []
    if not exe_path.exists():
        return [f"Исполняемый файл не найден: {exe_path}"]

    if exe_path.stat().st_size < 1024 * 1024:
        issues.append(f"Размер EXE подозрительно мал ({exe_path.stat().st_size} байт). Скорее всего, ресурсы не были упакованы.")

    env = os.environ.copy()
    env["ANTIGRAVITY_SKIP_KILL"] = "1"

    # Проверка --version
    try:
        proc_ver = subprocess.run(
            [str(exe_path), "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        out = (proc_ver.stdout + proc_ver.stderr).strip()
        if PY_VERSION not in out:
            issues.append(f"Вывод --version ({out}) не содержит ожидаемой версии {PY_VERSION}")
    except Exception as e:
        issues.append(f"Не удалось запустить {exe_path.name} --version: {e}")

    # Проверка --verify-bundle
    try:
        proc_bundle = subprocess.run(
            [str(exe_path), "--verify-bundle"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        if proc_bundle.returncode != 0:
            out = (proc_bundle.stdout + proc_bundle.stderr).strip()
            issues.append(f"Флаг --verify-bundle завершился с кодом {proc_bundle.returncode}: {out}")
    except Exception as e:
        issues.append(f"Не удалось запустить {exe_path.name} --verify-bundle: {e}")

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

        engine_file = bundle_dir / "resources" / "web_bundle_ru" / "i18n-ru.js"
        engine_issues = check_web_bundle_engine(engine_file)
        all_issues.extend(engine_issues)

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
