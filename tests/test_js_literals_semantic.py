"""
Регрессионные тесты семантической безопасности замены JS-литералов (Раздел 8).
Воспроизводят ошибки аудита:
- labels["Retry"] не должно заменяться на labels["Повторить"] (изменение логики с 1 на undefined);
- вычисляемые свойства {[prop]: val};
- обращение к свойствам через точку и опциональные цепочки obj?.["prop"];
- строковые литералы в импортах (import ... from "...") и require("...");
- комментарии // и /* */;
- строковые литералы в JSX/UI-контекстах vs служебные ключи.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from js_literals import replace_js_string_literals


class TestJsLiteralsSemanticSafety(unittest.TestCase):

    def test_bracket_property_access_not_translated(self):
        """labels["Retry"] не должно становиться labels["Повторить"]."""
        code = 'const labels = {"Retry": 1};\nconst val = labels["Retry"];'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 0)
        self.assertEqual(res, code)

    def test_optional_chaining_bracket_access_not_translated(self):
        code = 'const val = labels?.["Retry"];'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 0)
        self.assertEqual(res, code)

    def test_computed_property_key_not_translated(self):
        code = 'const obj = { ["Retry"]: 1 };'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 0)
        self.assertEqual(res, code)

    def test_import_specifier_not_translated(self):
        code = 'import { x } from "Retry";'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 0)
        self.assertEqual(res, code)

    def test_require_specifier_not_translated(self):
        code = 'const x = require("Retry");'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 0)
        self.assertEqual(res, code)

    def test_single_line_comment_not_translated(self):
        code = '// "Retry"\nconst a = "Retry";'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 1)
        self.assertEqual(res, '// "Retry"\nconst a = "Повторить";')

    def test_multi_line_comment_not_translated(self):
        code = '/* "Retry" */\nconst a = "Retry";'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 1)
        self.assertEqual(res, '/* "Retry" */\nconst a = "Повторить";')

    def test_valid_ui_string_replaced_in_function_args(self):
        code = 'showDialog("Retry", true);'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 1)
        self.assertEqual(res, 'showDialog("Повторить", true);')

    def test_valid_ui_string_replaced_in_object_value(self):
        code = 'const config = { label: "Retry", key: 123 };'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 1)
        self.assertEqual(res, 'const config = { label: "Повторить", key: 123 };')

    def test_node_execution_guarantees_value_preservation(self):
        """Проверяем реальным движком Node.js, что значение свойства сохраняется как 1."""
        code = 'const labels = {"Retry": 1};\nif (labels["Retry"] !== 1) process.exit(1);'
        res, count = replace_js_string_literals(code, {"Retry": "Повторить"})
        self.assertEqual(count, 0)
        self.assertEqual(res, code)
        import subprocess
        proc = subprocess.run(["node", "-e", res], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
