"""
Регрессионные тесты манифеста и валидатора совместимости ядра Antigravity (Раздел 3).
"""

import json
import os
import shutil
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tests" / "fixtures"))

import mini_asar
from compatibility import (
    validate_asar_compatibility,
    inject_language_server_web_bundle,
    CompatibilityError,
    SUPPORTED_VERSIONS,
)

WORK_DIR = REPO_ROOT / "tests" / "_compat_tmp"


class TestCompatibilityManifest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)
        WORK_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)

    def _create_mock_asar(self, name: str, version: str = "2.11.0", has_anchor: bool = True, missing_file: str = None) -> Path:
        files = {
            "package.json": json.dumps({"name": "antigravity", "version": version}).encode("utf-8"),
            "dist/languageServer.js": (
                b"const args = ['--enable_sidecars',]; console.log(args);"
                if has_anchor else b"const args = [];"
            ),
            "dist/preload.js": b"console.log('preload');",
            "dist/menu.js": b"const menu = 'File';",
            "dist/tray.js": b"const tray = 'Open';",
            "dist/ideInstall/wizardHtml.js": b"const wizard = 'Install';",
        }
        if missing_file and missing_file in files:
            del files[missing_file]

        target = WORK_DIR / name
        mini_asar.build_mini_asar(target, files)
        return target

    def test_compatible_version_accepted(self):
        """Поддерживаемая версия 2.11.0 со всеми точками патчинга признается совместимой."""
        path = self._create_mock_asar("valid_2_11_0.asar", version="2.11.0")
        res = validate_asar_compatibility(path)
        self.assertTrue(res["compatible"])
        self.assertEqual(res["version"], "2.11.0")

    def test_unsupported_version_rejected(self):
        """Неизвестная версия (3.0.0) отклоняется без изменений."""
        path = self._create_mock_asar("invalid_3_0_0.asar", version="3.0.0")
        res = validate_asar_compatibility(path)
        self.assertFalse(res["compatible"])
        self.assertEqual(res["version"], "3.0.0")
        self.assertIn("не поддерживается манифестом совместимости", res["reason"])

    def test_missing_patch_point_rejected(self):
        """Отсутствие обязательного файла (dist/languageServer.js) отклоняется."""
        path = self._create_mock_asar("missing_ls.asar", missing_file="dist/languageServer.js")
        res = validate_asar_compatibility(path)
        self.assertFalse(res["compatible"])
        self.assertIn("отсутствует обязательная точка патчинга", res["reason"])

    def test_missing_hook_anchor_rejected(self):
        """Отсутствие якорной точки --enable_sidecars отклоняется."""
        path = self._create_mock_asar("no_anchor.asar", has_anchor=False)
        res = validate_asar_compatibility(path)
        self.assertFalse(res["compatible"])
        self.assertIn("не найдена якорная точка", res["reason"])

    def test_nonexistent_file_rejected(self):
        """Несуществующий файл возвращает compatible=False."""
        res = validate_asar_compatibility(WORK_DIR / "non_existent.asar")
        self.assertFalse(res["compatible"])

    def test_language_server_injection_is_idempotent(self):
        """Инъекция --web_bundle_path в languageServer.js идемпотентна."""
        code = "const args = ['--enable_sidecars',];"
        once = inject_language_server_web_bundle(code)
        self.assertIn("--web_bundle_path", once)
        twice = inject_language_server_web_bundle(once)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main(verbosity=2)
