"""
Регрессионные тесты для JSONC-парсера и установки locale в argv.json (Раздел 9).
Воспроизводят подтверждённые проблемы аудита:
- Для `{}` вставка locale создаёт недопустимую завершающую запятую;
- Закомментированный `"locale"` принимается за действующий;
- Отсутствующий файл не создаётся;
- Фактическое значение locale проверяется после записи.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antigravity_localizer import update_argv_locale, strip_json_comments


class TestJsoncLocaleUpdate(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.argv_path = Path(self.temp_dir) / "argv.json"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_object_does_not_create_trailing_comma(self):
        """Для {} вставка locale не должна создавать завершающую запятую, ломающую json.loads."""
        self.argv_path.write_text("{}", encoding="utf-8")
        success = update_argv_locale(self.argv_path)
        self.assertTrue(success)

        content = self.argv_path.read_text(encoding="utf-8")
        clean = strip_json_comments(content)
        data = json.loads(clean)
        self.assertEqual(data.get("locale"), "ru")

    def test_commented_locale_not_treated_as_active(self):
        """Закомментированный 'locale' не должен считаться действующим."""
        initial_text = '// "locale": "en-US"\n{\n\t// configure editor\n}'
        self.argv_path.write_text(initial_text, encoding="utf-8")
        success = update_argv_locale(self.argv_path)
        self.assertTrue(success)

        content = self.argv_path.read_text(encoding="utf-8")
        # Комментарий в начале должен сохраниться
        self.assertIn('// "locale": "en-US"', content)
        # Внутри объекта должен появиться активный locale
        clean = strip_json_comments(content)
        data = json.loads(clean)
        self.assertEqual(data.get("locale"), "ru")

    def test_existing_active_locale_updated(self):
        """Существующий активный locale заменяется на 'ru'."""
        initial_text = '{\n\t"locale": "en-US",\n\t"disable-hardware-acceleration": true\n}'
        self.argv_path.write_text(initial_text, encoding="utf-8")
        success = update_argv_locale(self.argv_path)
        self.assertTrue(success)

        content = self.argv_path.read_text(encoding="utf-8")
        clean = strip_json_comments(content)
        data = json.loads(clean)
        self.assertEqual(data.get("locale"), "ru")
        self.assertEqual(data.get("disable-hardware-acceleration"), True)

    def test_missing_argv_json_created_with_locale(self):
        """Если argv.json отсутствует, он должен быть создан с валидным содержимым."""
        self.assertFalse(self.argv_path.exists())
        success = update_argv_locale(self.argv_path)
        self.assertTrue(success)
        self.assertTrue(self.argv_path.exists())

        content = self.argv_path.read_text(encoding="utf-8")
        data = json.loads(strip_json_comments(content))
        self.assertEqual(data.get("locale"), "ru")

    def test_trailing_comma_in_jsonc_tolerated(self):
        """JSONC с допустимой завершающей запятой должен корректно обновляться."""
        initial_text = '{\n\t"enable-crash-reporter": false,\n}'
        self.argv_path.write_text(initial_text, encoding="utf-8")
        success = update_argv_locale(self.argv_path)
        self.assertTrue(success)

        content = self.argv_path.read_text(encoding="utf-8")
        clean = strip_json_comments(content)
        # После очистки трейлинг запятых должен быть валидный json
        # (или update_argv_locale нормализует до валидного JSON)
        data = json.loads(clean)
        self.assertEqual(data.get("locale"), "ru")


if __name__ == "__main__":
    unittest.main(verbosity=2)
