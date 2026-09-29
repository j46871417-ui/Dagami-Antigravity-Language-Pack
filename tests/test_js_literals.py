"""
Тесты экранирования и контекстной замены JS-литералов.

Покрывают находки F-001 (re.escape вместо литерала + неэкранированный перевод),
F-026 (backslash, backtick, ${) и регрессии контекстного фильтра.

Запуск:  python -m unittest discover -s tests -v
Зависимостей нет: только стандартная библиотека.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from js_literals import (  # noqa: E402
    escape_js_string,
    is_system_identifier,
    build_literal_pattern,
    replace_js_string_literals,
)


class TestEscapeJsString(unittest.TestCase):
    """escape_js_string — базис, на котором стоит вся безопасность замены."""

    def test_plain_text_unchanged(self):
        self.assertEqual(escape_js_string("Сохранить", '"'), "Сохранить")

    def test_double_quote_escaped_for_double_quote_literal(self):
        self.assertEqual(escape_js_string('Файл "имя"', '"'), 'Файл \\"имя\\"')

    def test_double_quote_not_escaped_for_single_quote_literal(self):
        # В одинарном литерале двойная кавычка безопасна — экранировать не нужно.
        self.assertEqual(escape_js_string('Файл "имя"', "'"), 'Файл "имя"')

    def test_single_quote_escaped(self):
        self.assertEqual(escape_js_string("it's", "'"), "it\\'s")

    def test_backslash_escaped(self):
        # Ключевая регрессия F-026: путь C:\Users ломал литерал.
        self.assertEqual(escape_js_string(r"C:\Users", '"'), r"C:\\Users")

    def test_backslash_escaped_before_quote(self):
        # Порядок замен: слэш первым, иначе получим \\\" вместо \\\".
        self.assertEqual(escape_js_string('a\\"b', '"'), 'a\\\\\\"b')

    def test_backtick_escaped_in_template_literal(self):
        self.assertEqual(escape_js_string("a`b", "`"), "a\\`b")

    def test_template_substitution_neutralised(self):
        # ${...} в переводе исполнялся бы как код — это инъекция из словаря.
        self.assertEqual(escape_js_string("${alert(1)}", "`"), "\\${alert(1)}")

    def test_dollar_without_brace_untouched(self):
        self.assertEqual(escape_js_string("Цена $5", "`"), "Цена $5")

    def test_newlines_become_escapes(self):
        self.assertEqual(escape_js_string("a\nb", '"'), "a\\nb")
        self.assertEqual(escape_js_string("a\r\nb", '"'), "a\\nb")

    def test_rejects_unknown_quote(self):
        with self.assertRaises(ValueError):
            escape_js_string("x", "#")


class TestBuildLiteralPattern(unittest.TestCase):
    """Шаблон должен находить литералы и НЕ трогать ключи объектов."""

    def test_matches_double_quoted_literal(self):
        p = build_literal_pattern("Open File")
        self.assertIsNotNone(p.search('x = "Open File";'))

    def test_matches_single_quoted_literal(self):
        p = build_literal_pattern("Open File")
        self.assertIsNotNone(p.search("x = 'Open File';"))

    def test_matches_backtick_literal(self):
        p = build_literal_pattern("Open File")
        self.assertIsNotNone(p.search("x = `Open File`;"))

    def test_does_not_match_object_key(self):
        # "Open File": value — это ключ, переводить его нельзя.
        p = build_literal_pattern("Open File")
        self.assertIsNone(p.search('{"Open File": 1}'))

    def test_does_not_match_inside_longer_identifier(self):
        p = build_literal_pattern("Open")
        self.assertIsNone(p.search('myOpen = "OpenFile"'))

    def test_regex_metacharacters_treated_literally(self):
        # F-001: строка с () должна искаться как текст, а не как регэксп.
        p = build_literal_pattern("Save (all)")
        self.assertIsNotNone(p.search('x = "Save (all)";'))
        self.assertIsNone(p.search('x = "Save all";'))


class TestSystemIdentifierFilter(unittest.TestCase):

    def test_skips_module_path(self):
        self.assertTrue(is_system_identifier("vscode.extensions"))

    def test_keeps_ui_text_with_space(self):
        # "Open in Browser" содержит слэш-подобных символов нет, но проверяем
        # что наличие пробела снимает фильтр даже при точке.
        self.assertFalse(is_system_identifier("Open in http://x"))

    def test_keeps_sentence_like_text(self):
        self.assertFalse(is_system_identifier("Save as .txt"))

    def test_keeps_plain_ui_word(self):
        self.assertFalse(is_system_identifier("Settings"))


class TestReplaceJsStringLiterals(unittest.TestCase):
    """Поведение замены на реальных сценариях словаря переводов."""

    def test_simple_replacement(self):
        out, n = replace_js_string_literals(
            'const a = "Save";', {"Save": "Сохранить"}
        )
        self.assertEqual(n, 1)
        self.assertEqual(out, 'const a = "Сохранить";')

    def test_replacement_preserves_single_quotes(self):
        out, n = replace_js_string_literals(
            "const a = 'Save';", {"Save": "Сохранить"}
        )
        self.assertEqual(n, 1)
        self.assertEqual(out, "const a = 'Сохранить';")

    def test_replacement_preserves_backticks(self):
        out, n = replace_js_string_literals(
            "const a = `Save`;", {"Save": "Сохранить"}
        )
        self.assertEqual(n, 1)
        self.assertEqual(out, "const a = `Сохранить`;")

    def test_translation_with_quote_stays_valid_js(self):
        # F-001: перевод с двойной кавычкой ломал код.
        out, n = replace_js_string_literals(
            'const a = "Open";', {"Open": 'Открыть "файл"'}
        )
        self.assertEqual(n, 1)
        self.assertEqual(out, 'const a = "Открыть \\"файл\\"";')
        # Проверяем, что литерал действительно закрыт корректно.
        self.assertEqual(out.count('\\"'), 2)

    def test_translation_with_backslash_in_backtick(self):
        # F-026 на реальном кейсе: путь внутри template literal.
        out, n = replace_js_string_literals(
            "const a = `Path`;", {"Path": r"C:\Users\me"}
        )
        self.assertEqual(n, 1)
        self.assertEqual(out, "const a = `C:\\\\Users\\\\me`;")

    def test_template_substitution_not_executed(self):
        out, n = replace_js_string_literals(
            "const a = `Label`;", {"Label": "${process.exit()}"}
        )
        self.assertEqual(n, 1)
        self.assertIn("\\${process.exit()}", out)

    def test_multiple_occurrences_counted(self):
        out, n = replace_js_string_literals(
            'a="Save";b="Save";', {"Save": "Сохранить"}
        )
        self.assertEqual(n, 2)
        self.assertEqual(out, 'a="Сохранить";b="Сохранить";')

    def test_object_key_not_translated(self):
        out, n = replace_js_string_literals(
            '{"Save": 1, x: "Save"}', {"Save": "Сохранить"}
        )
        self.assertEqual(n, 1)
        self.assertEqual(out, '{"Save": 1, x: "Сохранить"}')

    def test_identical_translation_is_noop(self):
        out, n = replace_js_string_literals('a="Save";', {"Save": "Save"})
        self.assertEqual(n, 0)
        self.assertEqual(out, 'a="Save";')

    def test_empty_source_key_skipped(self):
        out, n = replace_js_string_literals('a="x";', {"": "y"})
        self.assertEqual(n, 0)

    def test_non_string_translation_skipped_not_crash(self):
        logs = []
        out, n = replace_js_string_literals(
            'a="Save";', {"Save": 123}, log_fn=logs.append
        )
        self.assertEqual(n, 0)
        self.assertTrue(any("Нестроковый" in m for m in logs))

    def test_does_not_mutate_input_map(self):
        m = {"Save": "Сохранить"}
        replace_js_string_literals('a="Save";', m)
        self.assertEqual(m, {"Save": "Сохранить"})

    def test_system_identifier_skipped(self):
        logs = []
        out, n = replace_js_string_literals(
            'import "vscode.extensions";',
            {"vscode.extensions": "рус"},
            log_fn=logs.append,
        )
        self.assertEqual(n, 0)
        self.assertTrue(any("системн" in m.lower() for m in logs))

    def test_idempotent_second_pass(self):
        src = 'const a = "Save"; const b = `Path`;'
        m = {"Save": "Сохранить", "Path": r"C:\x"}
        once, n1 = replace_js_string_literals(src, m)
        twice, n2 = replace_js_string_literals(once, m)
        self.assertEqual(n2, 0, "повторный прогон не должен находить замен")
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main(verbosity=2)
