"""
Манифест и валидатор совместимости ядра Antigravity (Раздел 3).

Предотвращает установку несовместимого ядра:
- Проверяет версию и внутреннюю структуру app.asar до внесения любых изменений;
- Проверяет наличие всех обязательных точек патчинга;
- Отклоняет неизвестные или несовместимые версии без модификации файлов;
- Обеспечивает воспроизводимый и идемпотентный in-place патчинг установленного ASAR;
- Не отключает Electron sandbox, contextIsolation или проверку сертификатов.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Список официально проверенных и поддерживаемых версий
SUPPORTED_VERSIONS = {
    "2.11.0",
}

# Обязательные точки патчинга внутри app.asar
REQUIRED_ASAR_FILES = [
    "package.json",
    "dist/languageServer.js",
    "dist/preload.js",
    "dist/menu.js",
    "dist/tray.js",
    "dist/ideInstall/wizardHtml.js",
]

# Контрольная сумма проверенного эталонного русифицированного app.asar (2.11.0)
KNOWN_PATCHED_ASAR_SHA256 = {
    "2.11.0": "24e64ac8c39b0ea4cebdeb82b96f9798e431f8b34440f1ce282ffeb9612b0e15"
}

WEB_BUNDLE_HOOK = """
        const customWebBundlePath = electron_1.app.isPackaged
            ? path_1.default.join(process.resourcesPath, 'web_bundle_ru')
            : path_1.default.join(__dirname, '..', 'resources', 'web_bundle_ru');
        if (fs.existsSync(customWebBundlePath)) {
            args.push(`--web_bundle_path=${customWebBundlePath}`);
        }
""".strip()


class CompatibilityError(Exception):
    """Исключение при несовместимости ядра или структуры приложения."""
    pass


def read_asar_header_and_data(path: Path) -> Tuple[Dict[str, Any], bytes]:
    """Читает заголовок и бинарные данные ASAR-архива."""
    with open(path, "rb") as f:
        magic = f.read(16)
        if len(magic) < 16:
            raise CompatibilityError(f"Файл {path.name} поврежден или не является ASAR-архивом.")
        u0, header_size, u2, json_len = struct.unpack("<IIII", magic)
        if u0 != 4 or json_len == 0 or header_size <= json_len:
            raise CompatibilityError(f"Некорректная геометрия заголовка ASAR в файле {path.name}.")
        raw_json = f.read(json_len)
        try:
            header = json.loads(raw_json.decode("utf-8"))
        except Exception as e:
            raise CompatibilityError(f"Не удалось разобрать JSON-заголовок {path.name}: {e}")
        data_start = 8 + header_size
        f.seek(data_start)
        data = f.read()
    return header, data


def extract_file_from_asar(header: Dict[str, Any], data: bytes, rel_path: str) -> Optional[bytes]:
    """Извлекает содержимое конкретного файла из ASAR."""
    parts = rel_path.split("/")
    curr = header
    for p in parts:
        if "files" in curr and p in curr["files"]:
            curr = curr["files"][p]
        else:
            return None
    if "offset" in curr and "size" in curr:
        offset = int(curr["offset"])
        size = int(curr["size"])
        return data[offset:offset + size]
    return None


def validate_asar_compatibility(asar_path: Path) -> Dict[str, Any]:
    """
    Проверяет установленный app.asar на совместимость с манифестом.

    Возвращает dict с метаданными:
      - compatible: bool
      - version: str
      - reason: str (при несовместимости)
      - already_patched: bool
    """
    if not asar_path.exists():
        return {
            "compatible": False,
            "version": "unknown",
            "reason": f"Файл не найден: {asar_path}",
            "already_patched": False,
        }

    try:
        header, data = read_asar_header_and_data(asar_path)
    except Exception as e:
        return {
            "compatible": False,
            "version": "corrupted",
            "reason": f"Повреждён ASAR-контейнер: {e}",
            "already_patched": False,
        }

    # 1. Проверяем наличие package.json и извлекаем версию
    pkg_bytes = extract_file_from_asar(header, data, "package.json")
    if not pkg_bytes:
        return {
            "compatible": False,
            "version": "missing_package_json",
            "reason": "В app.asar отсутствует обязательный package.json.",
            "already_patched": False,
        }

    try:
        pkg_json = json.loads(pkg_bytes.decode("utf-8"))
        version = str(pkg_json.get("version", "")).strip()
    except Exception as e:
        return {
            "compatible": False,
            "version": "invalid_package_json",
            "reason": f"Не удалось прочитать package.json в app.asar: {e}",
            "already_patched": False,
        }

    # 2. Проверяем версию по белому списку манифеста
    if version not in SUPPORTED_VERSIONS:
        return {
            "compatible": False,
            "version": version,
            "reason": (
                f"Версия Antigravity '{version}' не поддерживается манифестом совместимости. "
                f"Поддерживаемые версии: {', '.join(sorted(SUPPORTED_VERSIONS))}."
            ),
            "already_patched": False,
        }

    # 3. Проверяем обязательные файлы структуры
    for req_file in REQUIRED_ASAR_FILES:
        if extract_file_from_asar(header, data, req_file) is None:
            return {
                "compatible": False,
                "version": version,
                "reason": f"В app.asar отсутствует обязательная точка патчинга: '{req_file}'.",
                "already_patched": False,
            }

    # 4. Проверяем точку инъекции в dist/languageServer.js
    ls_bytes = extract_file_from_asar(header, data, "dist/languageServer.js")
    ls_text = ls_bytes.decode("utf-8", errors="replace") if ls_bytes else ""
    already_patched = "web_bundle_ru" in ls_text and "--web_bundle_path" in ls_text

    if not already_patched and "--enable_sidecars" not in ls_text:
        return {
            "compatible": False,
            "version": version,
            "reason": "В dist/languageServer.js не найдена якорная точка инъекции веб-бандла (--enable_sidecars).",
            "already_patched": False,
        }

    return {
        "compatible": True,
        "version": version,
        "reason": "Совместимо",
        "already_patched": already_patched,
    }


def inject_language_server_web_bundle(ls_code: str) -> str:
    """
    Идемпотентно добавляет передачу --web_bundle_path в аргументы запуска LS_BINARY.
    """
    marker = "--web_bundle_path"
    if marker in ls_code:
        return ls_code

    anchor = "'--enable_sidecars',"
    if anchor not in ls_code:
        anchor = '"--enable_sidecars",'
    if anchor not in ls_code:
        raise CompatibilityError("Не найден маркер --enable_sidecars в dist/languageServer.js.")

    replacement = f"{anchor}\n{WEB_BUNDLE_HOOK}"
    return ls_code.replace(anchor, replacement, 1)
