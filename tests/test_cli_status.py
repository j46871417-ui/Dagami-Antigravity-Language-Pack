"""
Регрессионные тесты для CLI и кодов возврата (Раздел 9).
Воспроизводят подтверждённые проблемы аудита:
- CLI возвращает код 0 для несуществующего пути приложения;
- Ошибки обязательных шагов должны приводить к общему неуспеху;
- Результаты шагов должны разделяться (SUCCESS, SKIPPED, ALREADY_DONE, FAILED).
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antigravity_localizer import AntigravityLocalizer, StepResult, StepStatus


class TestCliAndStatusIntegrity(unittest.TestCase):

    def test_cli_returns_nonzero_on_invalid_ide_path(self):
        """CLI должен возвращать ненулевой код при указании несуществующего пути."""
        cmd = [
            sys.executable,
            "antigravity_localizer.py",
            "--cli",
            "--install",
            "--ide-path",
            "C:\\NonExistent\\Path\\To\\Antigravity_IDE_Fake",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0, f"Expected non-zero exit code, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}")

    def test_cli_returns_nonzero_on_invalid_desktop_path(self):
        """CLI должен возвращать ненулевой код при указании несуществующего пути desktop."""
        cmd = [
            sys.executable,
            "antigravity_localizer.py",
            "--cli",
            "--install",
            "--desktop-path",
            "C:\\NonExistent\\Path\\To\\Antigravity_Desktop_Fake",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0, f"Expected non-zero exit code, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}")

    def test_step_result_model(self):
        """Проверяем структуру StepResult."""
        res_ok = StepResult("test_step", StepStatus.SUCCESS, "All good")
        self.assertTrue(res_ok.is_success())
        self.assertEqual(res_ok.status, StepStatus.SUCCESS)

        res_fail = StepResult("test_step", StepStatus.FAILED, "Critical error", is_mandatory=True)
        self.assertFalse(res_fail.is_success())
        self.assertEqual(res_fail.status, StepStatus.FAILED)

        res_skip = StepResult("test_step", StepStatus.SKIPPED, "Not needed")
        self.assertTrue(res_skip.is_success())


if __name__ == "__main__":
    unittest.main(verbosity=2)
