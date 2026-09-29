"""
Регрессионные тесты идемпотентности внедрения движка русификации в preload.js.

Проверяют F-002: без маркера в начале translations/dom_translator.js каждая
установка добавляла в dist/preload.js ещё одну полную копию движка.

Запуск: python -m unittest discover -s tests -v
"""

import ast  # noqa: E402
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import antigravity_localizer as al  # noqa: E402
from js_literals import replace_js_string_literals  # noqa: E402

DOM_TRANSLATOR = REPO_ROOT / "translations" / "dom_translator.js"
IDE_STRINGS = REPO_ROOT / "translations" / "ide_strings.json"

PRELOAD_FIXTURE = """\
const { contextBridge } = require('electron');
contextBridge.exposeInMainWorld('ag', { version: '2.0' });
"""


class TestMarkerContract(unittest.TestCase):
    """Маркер — это контракт между dom_translator.js и инжекторами."""

    def test_dom_translator_starts_with_marker(self):
        text = DOM_TRANSLATOR.read_text(encoding="utf-8")
        self.assertTrue(
            text.startswith(al.PRELOAD_MARKER),
            "translations/dom_translator.js должен начинаться с маркера "
            f"{al.PRELOAD_MARKER!r}, иначе повторная установка не идемпотентна (F-002)",
        )

    def test_marker_is_on_its_own_first_line(self):
        # Если маркер склеится с кодом, truncation срежет часть первой строки.
        first_line = DOM_TRANSLATOR.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(first_line.strip(), al.PRELOAD_MARKER)

    def test_marker_constant_matches_patch_desktop(self):
        # Оба инжектора обязаны знать одну и ту же строку.
        source = (REPO_ROOT / "patch_desktop.py").read_text(encoding="utf-8")
        self.assertIn(
            al.PRELOAD_MARKER,
            source,
            "patch_desktop.py использует другой маркер, чем antigravity_localizer.py",
        )


class TestInjectDomTranslator(unittest.TestCase):

    def setUp(self):
        self.script = DOM_TRANSLATOR.read_text(encoding="utf-8")

    def test_injects_marker_and_body(self):
        out = al.inject_dom_translator(PRELOAD_FIXTURE, self.script)
        self.assertIn(al.PRELOAD_MARKER, out)
        self.assertIn("contextBridge.exposeInMainWorld", out)
        self.assertTrue(out.endswith(self.script))

    def test_second_injection_is_byte_identical(self):
        once = al.inject_dom_translator(PRELOAD_FIXTURE, self.script)
        twice = al.inject_dom_translator(once, self.script)
        third = al.inject_dom_translator(twice, self.script)
        self.assertEqual(once, twice, "повторное внедрение изменило preload.js (F-002)")
        self.assertEqual(twice, third)

    def test_first_install_equals_all_later_installs(self):
        # Регрессия: rstrip должен применяться и к чистому preload. Иначе первая
        # установка даёт '\n\n\n' вместо '\n\n' и отличается по размеру от всех
        # последующих — то есть результат зависит от числа запусков.
        once = al.inject_dom_translator(PRELOAD_FIXTURE, self.script)
        twice = al.inject_dom_translator(once, self.script)
        self.assertEqual(len(once), len(twice), "первая установка отличается по размеру")
        self.assertNotIn("\n\n\n" + al.PRELOAD_MARKER, once)

    def test_no_growth_across_repeated_installs(self):
        # Ключевая метрика дефекта: размер не должен расти с числом установок.
        text = PRELOAD_FIXTURE
        sizes = []
        for _ in range(5):
            text = al.inject_dom_translator(text, self.script)
            sizes.append(len(text))
        self.assertEqual(
            len(set(sizes)),
            1,
            f"размер preload.js растёт с каждой установкой: {sizes}",
        )

    def test_script_body_appears_exactly_once(self):
        text = PRELOAD_FIXTURE
        for _ in range(3):
            text = al.inject_dom_translator(text, self.script)
        self.assertEqual(text.count(al.PRELOAD_MARKER), 1)
        # Уникальный маркер тела движка, а не общая фраза из шапки.
        self.assertEqual(text.count("'use strict';"), self.script.count("'use strict';"))

    def test_preserves_original_preload_content(self):
        out = al.inject_dom_translator(PRELOAD_FIXTURE, self.script)
        self.assertIn("const { contextBridge } = require('electron');", out)
        self.assertLess(out.index("contextBridge"), out.index(al.PRELOAD_MARKER))

    def test_user_edit_before_marker_survives_reinstall(self):
        # Пользователь дописал что-то в начало preload.js — повторная установка
        # не должна затирать его правку.
        edited = PRELOAD_FIXTURE + "\n// моя правка\n"
        once = al.inject_dom_translator(edited, self.script)
        twice = al.inject_dom_translator(once, self.script)
        self.assertIn("// моя правка", twice)

    def test_legacy_preload_without_marker_does_not_crash(self):
        # Совместимость: старый preload, пропатченный до появления маркера.
        legacy = PRELOAD_FIXTURE + "\n\n" + self.script
        out = al.inject_dom_translator(legacy, self.script)
        self.assertIn(al.PRELOAD_MARKER, out)

    def test_empty_preload(self):
        # Пустой preload — вырожденный случай: канонический разделитель "\n\n"
        # вставляется всегда, поэтому результат начинается с пустой строки.
        # Важно не это, а то, что движок на месте и повторный вызов стабилен.
        out = al.inject_dom_translator("", self.script)
        self.assertIn(al.PRELOAD_MARKER, out)
        self.assertTrue(out.endswith(self.script))
        self.assertEqual(out, "\n\n" + self.script)
        self.assertEqual(al.inject_dom_translator(out, self.script), out)

    def test_marker_only_text_collapses_to_script(self):
        out = al.inject_dom_translator(al.PRELOAD_MARKER, self.script)
        self.assertEqual(out.count(al.PRELOAD_MARKER), 1)
        self.assertTrue(out.endswith(self.script))


class TestModuleStructure(unittest.TestCase):
    """
    Структурная защита от повреждения модуля при рефакторинге.

    Поводом послужил реальный дефект, внесённый в ходе правок F-026: строка
    `class AntigravityLocalizer:` была случайно съедена заменой, и её методы
    оказались определены внутри replace_js_string_literals. ast.parse при этом
    НЕ падает — модуль остаётся синтаксически корректным, класс просто исчезает.
    Ловится только явной проверкой дерева.
    """

    @staticmethod
    def _tree(relpath):
        src = (REPO_ROOT / relpath).read_text(encoding="utf-8")
        return ast.parse(src)

    def test_classes_and_methods_survive(self):
        tree = self._tree("antigravity_localizer.py")
        classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
        for name in ("AntigravityLocalizer", "LocalizerGUI"):
            self.assertIn(name, classes, f"класс {name} исчез из модуля")
        methods = {
            m.name for m in classes["AntigravityLocalizer"].body
            if isinstance(m, ast.FunctionDef)
        }
        self.assertEqual(
            methods, {"__init__", "install_ide", "install_desktop", "restore_all"},
            "набор методов AntigravityLocalizer изменился",
        )

    def test_no_duplicate_top_level_definitions(self):
        # Вторая копия функции молча перекрывает первую — именно так правка F-026
        # оказалась мёртвым кодом под старой версией replace_js_string_literals.
        for relpath in ("antigravity_localizer.py", "patch_ide.py",
                        "patch_desktop.py", "js_literals.py"):
            tree = self._tree(relpath)
            seen, dups = {}, []
            for n in tree.body:
                if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                    if n.name in seen:
                        dups.append(f"{n.name} (строки {seen[n.name]} и {n.lineno})")
                    seen[n.name] = n.lineno
            self.assertEqual(dups, [], f"{relpath}: дублирующиеся определения {dups}")

    def test_replace_js_string_literals_delegates(self):
        src = (REPO_ROOT / "antigravity_localizer.py").read_text(encoding="utf-8")
        self.assertIn("jsl.replace_js_string_literals", src)
        # Старая копия экранировала кавычку, но не backslash и не ${ (F-026).
        self.assertNotIn("escaped_ru = ru_s.replace", src)


class TestExtensionJsEscaping(unittest.TestCase):
    """F-001: реальные переводы из ide_strings.json не должны ломать extension.js."""

    def test_all_real_translations_produce_parseable_output(self):
        import json

        ui_strings = json.loads(IDE_STRINGS.read_text(encoding="utf-8")).get("ui_strings", {})
        self.assertTrue(ui_strings, "ui_strings пуст — тест ничего не проверяет")

        # Синтетический extension.js: каждое значение как литерал в двойных кавычках.
        source = "\n".join(
            f'const s{i} = "{(v if isinstance(v, str) else str(v))}";'
            for i, v in enumerate(ui_strings)
        )
        out, changes = replace_js_string_literals(source, ui_strings)

        # Главное: результат — валидный JS. Баланс незаэкранированных кавычек
        # ломается ровно в тот момент, когда перевод вставили как есть (F-001).
        for i, line in enumerate(out.splitlines()):
            stripped = line.strip()
            if not stripped.startswith("const s"):
                continue
            body = stripped[len("const s"):].split(" = ", 1)[1].rstrip(";")
            self.assertTrue(body.startswith('"') and body.endswith('"'), line)
            inner = body[1:-1]
            # Считаем неэкранированные кавычки внутри: должно быть ноль.
            unescaped = 0
            j = 0
            while j < len(inner):
                if inner[j] == "\\":
                    j += 2
                    continue
                if inner[j] == '"':
                    unescaped += 1
                j += 1
            self.assertEqual(unescaped, 0, f"незаэкранированная кавычка в строке {i}: {line}")

        self.assertGreater(changes, 0)

    def test_translation_with_quotes_is_escaped(self):
        src = 'const a = "Open File";'
        out, n = replace_js_string_literals(src, {"Open File": 'Открыть "файл"'})
        self.assertEqual(n, 1)
        self.assertEqual(out, 'const a = "Открыть \\"файл\\"";')

    def test_translation_with_backslash_is_escaped(self):
        src = 'const a = "Open File";'
        out, n = replace_js_string_literals(src, {"Open File": r"Путь C:\Users"})
        self.assertEqual(n, 1)
        self.assertEqual(out, 'const a = "Путь C:\\\\Users";')


if __name__ == "__main__":
    unittest.main(verbosity=2)
