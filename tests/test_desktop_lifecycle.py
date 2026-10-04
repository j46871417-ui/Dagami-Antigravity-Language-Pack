"""
Регрессионные тесты полного жизненного цикла Desktop (Разделы 2, 3 и 4).
Проверяет:
- Валидацию манифеста совместимости перед установкой;
- Отказ при неизвестной/неподдерживаемой версии ядра;
- Создание версионированного бэкапа и транзакционное применение in-place патчей;
- Размещение языкового бандла web_bundle_ru;
- Безопасный откат и сохранение web_bundle_ru при отсутствии бэкапа.
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
from antigravity_localizer import AntigravityLocalizer, read_asar
from compatibility import SUPPORTED_VERSIONS
from transaction_manager import BackupManager

LIFECYCLE_DIR = REPO_ROOT / "tests" / "_lifecycle_tmp"


class TestDesktopLifecycle(unittest.TestCase):

    def setUp(self):
        shutil.rmtree(LIFECYCLE_DIR, ignore_errors=True)
        LIFECYCLE_DIR.mkdir(parents=True, exist_ok=True)

        self.desktop_dir = LIFECYCLE_DIR / "antigravity_desktop"
        self.res_dir = self.desktop_dir / "resources"
        self.res_dir.mkdir(parents=True, exist_ok=True)

        # Создаем dummy Antigravity.exe для валидации пути
        (self.desktop_dir / "Antigravity.exe").write_bytes(b"MZ_DUMMY_EXE")

        os.environ["ANTIGRAVITY_SKIP_KILL"] = "1"
        self.logs = []
        self.localizer = AntigravityLocalizer(
            desktop_path=self.desktop_dir,
            log_fn=lambda m: self.logs.append(m),
            auto_kill=False
        )

    def tearDown(self):
        shutil.rmtree(LIFECYCLE_DIR, ignore_errors=True)

    def _create_mock_asar(self, version: str = "2.11.0", has_anchor: bool = True) -> Path:
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
        target = self.res_dir / "app.asar"
        mini_asar.build_mini_asar(target, files)
        return target

    def test_unsupported_version_refused_without_modification(self):
        """Неподдерживаемая версия (например, 2.12.0) отклоняется без изменения файлов."""
        asar_path = self._create_mock_asar(version="2.12.0")
        original_bytes = asar_path.read_bytes()

        res = self.localizer.install_desktop()
        self.assertFalse(res)
        self.assertEqual(asar_path.read_bytes(), original_bytes, "Файл не должен модифицироваться")

        # Проверяем, что каталог web_bundle_ru не был создан
        self.assertFalse((self.res_dir / "web_bundle_ru").exists())
        # Проверяем лог отказа
        self.assertTrue(any("Отказ совместимости" in msg for msg in self.logs))

    def test_corrupted_asar_refused(self):
        """Поврежденный файл app.asar отклоняется без падения и создания мусора."""
        asar_path = self.res_dir / "app.asar"
        asar_path.write_bytes(b"CORRUPTED_NON_ASAR_DATA_12345")

        res = self.localizer.install_desktop()
        self.assertFalse(res)
        self.assertTrue(any("Отказ совместимости" in msg for msg in self.logs))

    def test_successful_installation_and_bundle_placement(self):
        """Успешная установка: версионированный бэкап, in-place патч и размещение web_bundle_ru."""
        asar_path = self._create_mock_asar(version="2.11.0")
        original_bytes = asar_path.read_bytes()

        res = self.localizer.install_desktop()
        self.assertTrue(res)

        # 1. Проверяем наличие версионированного бэкапа
        backup_mgr = BackupManager(self.res_dir)
        backups = backup_mgr.list_backups("app.asar")
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0]["version"], "2.11.0")
        self.assertTrue(Path(backups[0]["path"]).exists())

        # 2. Проверяем, что app.asar пропатчен
        header, data = read_asar(asar_path)
        self.assertIn("languageServer.js", str(header))

        # Извлекаем languageServer.js
        ls_entry = header["files"]["dist"]["files"]["languageServer.js"]
        ls_content = data[int(ls_entry["offset"]):int(ls_entry["offset"]) + int(ls_entry["size"])].decode("utf-8")
        self.assertIn("--web_bundle_path", ls_content)
        self.assertIn("web_bundle_ru", ls_content)

        # 3. Проверяем размещение web_bundle_ru
        web_bundle_dir = self.res_dir / "web_bundle_ru"
        self.assertTrue(web_bundle_dir.exists())
        self.assertTrue((web_bundle_dir / "i18n-ru.js").exists())

    def test_restore_all_with_backup_cleans_bundle(self):
        """Откат при наличии бэкапа восстанавливает оригинальный ASAR и удаляет web_bundle_ru."""
        asar_path = self._create_mock_asar(version="2.11.0")
        original_bytes = asar_path.read_bytes()

        # Установка
        self.localizer.install_desktop()
        self.assertTrue((self.res_dir / "web_bundle_ru").exists())

        # Откат
        self.logs.clear()
        restored = self.localizer.restore_all()
        self.assertTrue(restored)

        # app.asar должен вернуться к оригинальному содержимому
        self.assertEqual(asar_path.read_bytes(), original_bytes)
        # web_bundle_ru должен быть удален
        self.assertFalse((self.res_dir / "web_bundle_ru").exists())

    def test_restore_all_without_backup_preserves_bundle(self):
        """Если бэкап отсутствует/поврежден, web_bundle_ru НЕ удаляется, предотвращая сбой ядра."""
        asar_path = self._create_mock_asar(version="2.11.0")
        self.localizer.install_desktop()

        # Имитируем удаление всех бэкапов
        for p in self.res_dir.glob("app.asar*bak*"):
            p.unlink()
        for p in self.res_dir.glob("app.asar*.original*"):
            p.unlink()
        for p in self.res_dir.glob("*.json"):
            p.unlink()

        # Попытка отката
        self.logs.clear()
        restored = self.localizer.restore_all()

        # web_bundle_ru ДОЛЖЕН БЫТЬ СОХРАНЕН!
        self.assertTrue((self.res_dir / "web_bundle_ru").exists())
        self.assertTrue(any("web_bundle_ru сохранён" in msg for msg in self.logs))

    def test_repeat_install_idempotent(self):
        """Повторный запуск установки не повреждает ASAR и сохраняет исходный бэкап."""
        asar_path = self._create_mock_asar(version="2.11.0")
        original_bytes = asar_path.read_bytes()

        res1 = self.localizer.install_desktop()
        self.assertTrue(res1)
        patched_bytes1 = asar_path.read_bytes()

        res2 = self.localizer.install_desktop()
        self.assertTrue(res2)
        patched_bytes2 = asar_path.read_bytes()

        # Содержимое после 1-й и 2-й установки должно быть идентичным
        self.assertEqual(patched_bytes1, patched_bytes2)

        # Откат должен вернуть исходный оригинал
        self.localizer.restore_all()
        self.assertEqual(asar_path.read_bytes(), original_bytes)


if __name__ == "__main__":
    unittest.main()
