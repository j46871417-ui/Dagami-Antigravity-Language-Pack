"""Тесты контейнера asar: геометрия прелюдии, чтение/запись (F-016, F-038).

Зачем этот файл. Ошибка в геометрии asar невидима «на глаз»: если база данных
уезжает на 8 байт, длины файлов остаются верными, а содержимое оказывается
побайтно сдвинутым. Именно так и проявился баг в tests/fixtures/mini_asar.py —
`MISMATCH orig=106 read=106`, одинаковые числа при разных байтах. Поэтому здесь
проверяется ПОБАЙТОВОЕ равенство и тождество базы, а не только длины.

Контейнер (проверено на настоящем resources/app.asar, 4 500 501 байт):
    [0] = 4, [1] = 274148, [2] = 274144, [3] = 274140
    JSON со смещения 16, ровно [3] байт, без выравнивающих нулей после него
    data_start = 8 + [1] == 16 + [3] == 274156
"""

import hashlib
import json
import shutil
import struct
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

sys.path.insert(0, str(REPO_ROOT / "tests" / "fixtures"))

import patch_desktop  # noqa: E402
import mini_asar  # noqa: E402

REAL_ASAR = REPO_ROOT / "resources" / "app.asar"
# Песочница запрещает запись в каталоги, созданные tempfile (см. tests/fixtures/
# mini_asar.py), поэтому используем обычный подкаталог и убираем его в tearDown.
WORK_DIR = REPO_ROOT / "tests" / "_asar_tmp"


class TestMiniAsarGeometry(unittest.TestCase):
    """Мини-фикстура обязана воспроизводить геометрию настоящего контейнера."""

    @classmethod
    def setUpClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)
        WORK_DIR.mkdir(parents=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)

    def _build(self, name="t.asar"):
        files = {
            "dist/preload.js": b"AAAA_PRELOAD",
            "dist/menu.js": b"BBBB_MENU",
        }
        path = WORK_DIR / name
        mini_asar.build_mini_asar(path, files)
        return path, files

    def test_prelude_identity_holds(self):
        """8 + [1] == 16 + [3] — тождество, на которое опирается production-код."""
        path, _ = self._build()
        raw = path.read_bytes()
        _u0, u1, u2, u3 = struct.unpack("<4I", raw[:16])
        self.assertEqual(8 + u1, 16 + u3)
        # u2 == u1 - 4 — вторая связь прелюдии.
        self.assertEqual(u2, u1 - 4)

    def test_no_padding_between_json_and_data(self):
        path, files = self._build()
        raw = path.read_bytes()
        _u0, u1, _u2, json_len = struct.unpack("<4I", raw[:16])
        header = json.loads(raw[16:16 + json_len].decode("utf-8"))
        # JSON должен парситься ровно на своей длине...
        self.assertEqual(raw[16 + json_len - 1:16 + json_len], b"}")
        # ...и сразу за ним идут данные без нулей-выравнивания.
        # Файлы пишутся в порядке sorted(keys), поэтому первый в потоке —
        # dist/menu.js, а не preload.js. Сверяемся с offset из JSON.
        node = header["files"]["dist"]["files"]["menu.js"]
        self.assertEqual(int(node["offset"]), 0)
        self.assertEqual(raw[8 + u1:8 + u1 + int(node["size"])], files["dist/menu.js"])

    def test_roundtrip_is_byte_exact(self):
        """Побайтовое равенство, а не только совпадение длин."""
        path, files = self._build("rt.asar")
        read_back = mini_asar.read_mini_asar(path)
        self.assertEqual(set(read_back), set(files))
        for rel, data in files.items():
            self.assertEqual(read_back[rel], data, f"{rel}: содержимое сдвинуто")


class TestRealAsarContainer(unittest.TestCase):
    """Проверки против настоящего resources/app.asar (пропускаются, если его нет)."""

    @classmethod
    def setUpClass(cls):
        # Класс сам создаёт каталог: порядок выполнения классов в unittest не
        # гарантирован, и полагаться на setUpClass соседнего класса нельзя.
        WORK_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)

    def setUp(self):
        if not REAL_ASAR.exists():
            self.skipTest("resources/app.asar отсутствует")

    def test_prelude_values(self):
        raw = REAL_ASAR.read_bytes()
        u0, u1, u2, u3 = struct.unpack("<4I", raw[:16])
        self.assertEqual(u0, 4)
        self.assertEqual(u1, 274148)
        self.assertEqual(u2, 274144)
        self.assertEqual(u3, 274140)
        self.assertEqual(8 + u1, 274156)
        self.assertEqual(16 + u3, 274156)
        self.assertEqual(len(raw), 4500501)

    def test_json_ends_exactly_at_u3(self):
        raw = REAL_ASAR.read_bytes()
        _u0, _u1, _u2, u3 = struct.unpack("<4I", raw[:16])
        self.assertEqual(raw[16 + u3 - 1:16 + u3], b"}")
        json.loads(raw[16:16 + u3].decode("utf-8"))

    def test_read_asar_matches_integrity_hashes(self):
        """Хеши из integrity должны совпасть с содержимым — прямая проверка базы."""
        header, _data = patch_desktop.read_asar(REAL_ASAR)
        raw = REAL_ASAR.read_bytes()
        node = header["files"]["dist"]["files"]["preload.js"]
        offset, size = int(node["offset"]), int(node["size"])
        self.assertEqual((offset, size), (154328, 4925))
        chunk = raw[274156 + offset:274156 + offset + size]
        self.assertEqual(hashlib.sha256(chunk).hexdigest(), node["integrity"]["hash"])
        self.assertTrue(chunk.startswith(b'"use strict";'))

    def test_noop_rewrite_is_byte_identical(self):
        """read_asar -> write_asar без изменений обязан вернуть исходные байты.

        Это единственная проверка, доказывающая, что reader и writer согласованы
        по базе данных: при рассинхроне размер совпадёт, а байты — нет.
        """
        out = WORK_DIR / "noop.asar"
        header, data = patch_desktop.read_asar(REAL_ASAR)
        patch_desktop.write_asar(out, header, data)
        self.assertEqual(out.read_bytes(), REAL_ASAR.read_bytes())
        header2, data2 = patch_desktop.read_asar(out)
        self.assertEqual(header2, header)
        self.assertEqual(data2, data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
