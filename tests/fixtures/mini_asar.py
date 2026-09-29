#!/usr/bin/env python3
"""
Мини-фикстура для создания валидного asar-контейнера, воспроизводящего
настоящую геометрию resources/app.asar (F-038, F-016).

Формат asar ( Electron ). Прелюдия — 16 байт, 4 uint32 little-endian.
Поля не названы в коде Electron, поэтому подписаны по проверенному соответствию
на настоящем resources/app.asar (значения: 4, 274148, 274144, 274140):

  [0] = 4          (константа)
  [1] = json_len+8 (274148) — из неё выводится начало данных: base = 8 + [1]
  [2] = json_len+4 (274144)
  [3] = json_len   (274140) — ИСТИННАЯ длина JSON

  JSON начинается со смещения 16 и занимает ровно [3] байт.
  Между JSON и данными НЕТ выравнивающих нулей: смежные 8 байт после JSON —
  это уже начало первого файла. Проверено на реальном файле: JSON закрывается
  '}}}}' на байте 16+[3]-1 = 274155, а байты 274156..263 — '"use str', т.е.
  начало dist/preload.js.

  Отсюда тождество 8 + [1] == 16 + [3] == 274156, и именно его использует
  production-код: data_start = 8 + header_size.
  offset'ы файлов в JSON отсчитываются от этого base.

ВАЖНО (история ошибки в этой фикстуре): сначала здесь писали padding до 8 байт
И добавляли те же 8 байт в формулу базы, то есть учитывали выравнивание дважды.
Данные уезжали на 8 байт, длины совпадали, и roundtrip давал
«MISMATCH orig=N read=N» при побайтно сдвинутом содержимом. Правильно — писать
JSON без паддинга и задавать [1] = json_len + 8.

Каждый файл в JSON:
  { "size": int, "offset": str, "integrity": {...} }
  integrity: { "algorithm": "SHA256", "hash": hex, "blockSize": 4194304, "blocks": [hex] }

Настоящий resources/app.asar:
  [0]=4, [1]=274148, [2]=274144, [3]=274140, base = 274156
  dist/preload.js @ offset 154328, size 4925
  (проверяется тестом tests/test_asar_container.py против реального файла)
"""

import json
import hashlib
import struct
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def compute_integrity(data: bytes) -> Dict[str, Any]:
    """Воспроизводит compute_sha256_blocks из antigravity_localizer.py."""
    block_size = 4194304  # 4 MiB
    hasher = hashlib.sha256()
    hasher.update(data)
    full_hash = hasher.hexdigest()
    blocks = []
    for i in range(0, len(data), block_size):
        chunk = data[i:i + block_size]
        h = hashlib.sha256()
        h.update(chunk)
        blocks.append(h.hexdigest())
    return {
        "algorithm": "SHA256",
        "hash": full_hash,
        "blockSize": block_size,
        "blocks": blocks,
    }


def build_mini_asar(output_path: Path, files: Dict[str, bytes]) -> None:
    """
    Собирает мини-asar из словаря {rel_path: bytes}.
    Порядок файлов детерминирован (sorted keys) — для воспроизводимости.
    """
    # 1. Считаем размеры и offsets
    sorted_paths = sorted(files.keys())
    entries = {}
    current_offset = 0
    for rel in sorted_paths:
        data = files[rel]
        entries[rel] = {
            "size": len(data),
            "offset": str(current_offset),
            "integrity": compute_integrity(data),
        }
        current_offset += len(data)

    # 2. Строим JSON заголовок (только "files" на верхнем уровне)
    header = {"files": {}}
    # Превращаем плоский словарь в вложенную структуру с "files" на каждом уровне
    for rel, entry in entries.items():
        parts = rel.split("/")
        node = header["files"]
        for part in parts[:-1]:
            node = node.setdefault(part, {"files": {}})["files"]
        node[parts[-1]] = entry

    header_json = json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_len = len(header_json)

    # Прелюдия настоящего app.asar: u0=4, u1=274148, u2=274144, u3=274140.
    # Проверено на реальном файле: JSON заканчивается '}}}}' ровно на байте
    # 16+u3-1, то есть u3 — истинная длина JSON. Следующие 8 байт — уже НАЧАЛО
    # данных ('"use str'), а не паддинг: data_start = 16 + u3 = 8 + u1 = 274156.
    #
    # Отсюда формулы writer'а: u1 = json_len + 8, u2 = json_len + 4, u3 = json_len,
    # а между JSON и данными НЕТ выравнивающих нулей. Раньше фикстура и вставляла
    # padding, и добавляла те же 8 байт в базу — база уезжала на 8 байт.
    u0 = 4
    u1 = json_len + 8
    u2 = json_len + 4

    # 3. Записываем asar
    with open(output_path, "wb") as f:
        f.write(struct.pack("<4I", u0, u1, u2, json_len))
        f.write(header_json)
        # Данные файлов: начинаются ровно с 8 + u1 == 16 + json_len
        for rel in sorted_paths:
            f.write(files[rel])


def read_mini_asar(path: Path) -> Dict[str, bytes]:
    """Обратная операция: читает asar и возвращает {rel_path: bytes}."""
    with open(path, "rb") as f:
        raw = f.read()

    _u0, u1, _u2, json_len = struct.unpack("<4I", raw[:16])
    header_json = raw[16:16 + json_len].decode("utf-8")
    header = json.loads(header_json)

    # Ровно та же формула, что в production-коде (patch_desktop.read_asar,
    # antigravity_localizer.read_asar): data_start = 8 + u1.
    # На реальном app.asar 8 + u1 == 16 + u3 == 274156.
    base = 8 + u1
    assert base == 16 + json_len, (base, 16 + json_len)
    result = {}

    def walk(node: dict, prefix: str = "") -> None:
        for name, entry in node.get("files", {}).items():
            full = prefix + name
            if "offset" in entry and "size" in entry:
                offset = int(entry["offset"])
                size = int(entry["size"])
                result[full] = raw[base + offset: base + offset + size]
            else:
                walk(entry, full + "/")

    walk(header)
    return result


def verify_roundtrip(tmp_path: Path) -> bool:
    """Создаёт, читает, сравнивает побайтово."""
    import random
    random.seed(42)
    files = {
        "dist/preload.js": b"const { contextBridge } = require('electron');\ncontextBridge.exposeInMainWorld('ag', { version: '2.0' });\n",
        "dist/menu.js": bytes([random.randint(0, 255) for _ in range(1234)]),
        "dist/tray.js": b"module.exports = { tray: 'menu' };\n",
        "dist/ideInstall/wizardHtml.js": b"<html>wizard</html>",
        "icon.png": b"PNG\x00" + bytes([0] * 100),
    }
    asar_path = tmp_path / "test.asar"
    build_mini_asar(asar_path, files)
    read_back = read_mini_asar(asar_path)
    ok = all(files[k] == read_back.get(k, b"") for k in files)
    if not ok:
        for k in files:
            if files[k] != read_back.get(k, b""):
                print(f"MISMATCH {k}: orig={len(files[k])} read={len(read_back.get(k, b''))}")
    return ok


if __name__ == "__main__":
    import shutil
    # Песочница харнесса запрещает запись в ЛЮБОЙ каталог, созданный через tempfile
    # (проверено: os.makedirs + запись в рабочем пространстве проходит, а
    # tempfile.mkdtemp(dir=<workspace>) — падает с PermissionError). Поэтому для
    # фикстуры используем обычный подкаталог, а не tempfile. Это же ограничение
    # было причиной, по которой pytest не удалось установить, и почему тесты
    # написаны на stdlib unittest.
    work_dir = Path(__file__).resolve().parent / "_asar_work"
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True)
    try:
        ok = verify_roundtrip(work_dir)
        print("ROUNDTRIP OK" if ok else "ROUNDTRIP FAILED")
        # Ненулевой код возврата при провале: иначе вызывающая сторона
        # (CI, hook, ручной запуск) видит успех при сломанном roundtrip.
        sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)