"""
Регрессионные тесты менеджера транзакций, версионированных бэкапов и отката (Раздел 4).
"""

import os
import shutil
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from transaction_manager import (
    SingleInstanceLock,
    ConcurrencyLockError,
    BackupManager,
    TransactionJournal,
    atomic_stage_and_replace,
    compute_file_sha256,
)

WORK_DIR = REPO_ROOT / "tests" / "_tx_tmp"


class TestTransactionRollback(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)
        WORK_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(WORK_DIR, ignore_errors=True)

    def setUp(self):
        self.test_dir = WORK_DIR / "sub"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_single_instance_lock_prevents_concurrency(self):
        """Параллельный захват блокировки вызывает ConcurrencyLockError."""
        lock1 = SingleInstanceLock(lock_dir=self.test_dir)
        lock1.acquire()
        try:
            lock2 = SingleInstanceLock(lock_dir=self.test_dir)
            with self.assertRaises(ConcurrencyLockError):
                lock2.acquire()
        finally:
            lock1.release()

    def test_versioned_backup_preserves_distinct_versions(self):
        """Бэкапы разных версий не перезаписывают друг друга."""
        target = self.test_dir / "app.asar"
        target.write_bytes(b"DATA_VERSION_1")

        bm = BackupManager()
        bak1 = bm.create_versioned_backup(target, version="2.11.0")
        self.assertTrue(bak1.exists())
        self.assertIn("v2.11.0", bak1.name)

        # Симулируем обновление приложения пользователем
        target.write_bytes(b"DATA_VERSION_2_NEW_APP")
        bak2 = bm.create_versioned_backup(target, version="2.12.0")
        self.assertTrue(bak2.exists())
        self.assertIn("v2.12.0", bak2.name)

        # Проверяем, что первый бэкап не поврежден
        self.assertEqual(bak1.read_bytes(), b"DATA_VERSION_1")
        self.assertEqual(bak2.read_bytes(), b"DATA_VERSION_2_NEW_APP")

    def test_session_journal_emergency_rollback(self):
        """При аварии в процессе установки Session Journal восстанавливает исходный файл."""
        target = self.test_dir / "extension.js"
        target.write_bytes(b"ORIGINAL_EXTENSION_CONTENT")

        # Создаем снимок перед текущей операцией
        pre_op_snapshot = self.test_dir / "extension.js.snapshot"
        shutil.copy2(target, pre_op_snapshot)

        journal = TransactionJournal(self.test_dir / "journal.json")
        journal.record_stage("REPLACE", target, backup=pre_op_snapshot)

        # Симулируем частичную запись с ошибкой
        target.write_bytes(b"CORRUPTED_MID_OPERATION_DATA")

        # Запускаем откат
        success = journal.rollback()
        self.assertTrue(success)
        self.assertEqual(target.read_bytes(), b"ORIGINAL_EXTENSION_CONTENT")
        self.assertFalse((self.test_dir / "journal.json").exists())

    def test_atomic_stage_and_replace_replaces_cleanly(self):
        """Атомарная замена гарантирует запись без промежуточных битых состояний."""
        target = self.test_dir / "test.txt"
        target.write_text("OLD", encoding="utf-8")

        new_data = b"NEW_DATA_SUCCESS"
        atomic_stage_and_replace(new_data, target, expected_size=len(new_data))
        self.assertEqual(target.read_bytes(), new_data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
