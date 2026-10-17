"""
Менеджер транзакций, версионированных бэкапов и безопасного отката (Разделы 3 и 4).

Гарантии:
- Привязка резервных копий к версии и хешу исходных файлов (не затирает бэкапы при обновлении);
- Журналирование сессии (Session Journal) для аварийного отката текущей операции;
- Атомарное размещение файлов через временные файлы на том же томе (os.replace);
- Однопоточная блокировка (Single-Instance Lock / Mutex) против параллельного запуска;
- Защита от удаления ресурсов при поврежденном/отсутствующем бэкапе ASAR;
- Сохранение пользовательских конфигураций и настроек обновления.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


class TransactionError(Exception):
    pass


class ConcurrencyLockError(TransactionError):
    pass


LockError = ConcurrencyLockError


class SingleInstanceLock:
    """Файловая блокировка для предотвращения параллельных операций установки/отката."""

    def __init__(self, lock_dir: Optional[Path] = None):
        if lock_dir is None:
            self.lock_file = Path(tempfile.gettempdir()) / "antigravity_localizer.lock"
        elif lock_dir.suffix == ".lock":
            self.lock_file = lock_dir
        else:
            self.lock_file = lock_dir / "antigravity_localizer.lock"
        self._acquired = False

    def acquire(self) -> None:
        if self.lock_file.exists():
            try:
                content = self.lock_file.read_text(encoding="utf-8").strip()
                pid_str, ts_str = content.split(":", 1)
                pid = int(pid_str)
                # Проверяем активность процесса на Windows
                if self._is_pid_alive(pid):
                    raise ConcurrencyLockError(
                        f"Другая операция русификатора уже выполняется (PID {pid}). "
                        "Дождитесь её завершения."
                    )
            except (ValueError, ConcurrencyLockError) as e:
                if isinstance(e, ConcurrencyLockError):
                    raise
                # Если файл поврежден, удаляем его
                try:
                    self.lock_file.unlink()
                except OSError:
                    pass

        try:
            self.lock_file.write_text(f"{os.getpid()}:{time.time()}", encoding="utf-8")
            self._acquired = True
        except Exception as e:
            raise TransactionError(f"Не удалось захватить блокировку процесса: {e}")

    def release(self) -> None:
        if self._acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except OSError:
                pass
            self._acquired = False

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        if pid == os.getpid():
            return True
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def compute_file_sha256(path: Path) -> str:
    """Вычисляет полный SHA-256 хеш файла."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class TransactionJournal:
    """
    Журнал операции для отслеживания и аварийного отката текущей попытки (Session Rollback).
    """

    def __init__(self, journal_path: Path):
        if journal_path.is_dir() or not journal_path.suffix:
            self.journal_path = journal_path / ".transaction_journal.json"
        else:
            self.journal_path = journal_path
        self.entries: List[Dict[str, Any]] = []

    def record_stage(self, action: str, target: Path, backup: Optional[Path] = None, meta: Optional[Dict] = None) -> None:
        entry = {
            "action": action,
            "target": str(target),
            "backup": str(backup) if backup else None,
            "meta": meta or {},
            "timestamp": time.time(),
        }
        self.entries.append(entry)
        self._flush()

    def record_modified(self, target: Path, backup: Optional[Path] = None) -> None:
        self.record_stage("REPLACE", target, backup)

    def record_created(self, target: Path) -> None:
        self.record_stage("CREATE", target)

    def commit(self) -> None:
        self.cleanup()

    def _flush(self) -> None:
        try:
            self.journal_path.parent.mkdir(parents=True, exist_ok=True)
            self.journal_path.write_text(json.dumps(self.entries, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def rollback(self, log_fn: Callable[[str], None] = lambda m: None) -> bool:
        """Откатывает изменения текущей сессии в обратном порядке."""
        success = True
        for entry in reversed(self.entries):
            action = entry.get("action")
            target = Path(entry["target"])
            backup_str = entry.get("backup")
            backup = Path(backup_str) if backup_str else None

            try:
                if action == "REPLACE" and backup and backup.exists():
                    shutil.copy2(backup, target)
                    log_fn(f"  [Аварийный откат] Восстановлен из снимка сессии: {target.name}")
                elif action == "CREATE" and target.exists():
                    if target.is_dir():
                        shutil.rmtree(target, ignore_errors=True)
                    else:
                        target.unlink()
                    log_fn(f"  [Аварийный откат] Удален созданный файл: {target.name}")
            except Exception as e:
                log_fn(f"  [Аварийный откат] Ошибка при откате {target.name}: {e}")
                success = False

        self.cleanup()
        return success

    def cleanup(self) -> None:
        try:
            if self.journal_path.exists():
                self.journal_path.unlink()
        except OSError:
            pass


class BackupManager:
    """
    Управление версионированными и хеш-привязанными резервными копиями.
    """

    def __init__(self, target_dir_or_log_fn: Any = None, log_fn: Optional[Callable[[str], None]] = None):
        if callable(target_dir_or_log_fn):
            self.log = target_dir_or_log_fn
            self.base_dir = None
        else:
            self.base_dir = Path(target_dir_or_log_fn) if target_dir_or_log_fn else None
            self.log = log_fn or (lambda m: None)

    def create_versioned_backup(self, target_file: Path, version: str = "unknown") -> Path:
        """
        Создает резервную копию, привязанную к версии и SHA-256 хешу исходного файла.
        Не перезаписывает бэкап старой версии при обновлении приложения.
        """
        if not target_file.exists():
            raise TransactionError(f"Целевой файл для бэкапа не существует: {target_file}")

        # Защита от перезаписи: если для этой версии уже есть резервная копия,
        # не создаем новую (файл мог быть уже частично или полностью пропатчен)
        existing = self.find_latest_valid_backup(target_file, expected_version=version)
        if existing and existing.exists():
            self.log(f"[Бэкап] Резервная копия для версии {version} уже сохранена: {existing.name}")
            return existing

        file_hash = compute_file_sha256(target_file)
        short_hash = file_hash[:10]

        # Имя бэкапа: app.asar.bak.v2.11.0.24e64ac8c3
        backup_name = f"{target_file.name}.bak.v{version}.{short_hash}"
        backup_path = target_file.with_name(backup_name)

        # Сохраняем файл бэкапа
        if not backup_path.exists():
            shutil.copy2(target_file, backup_path)
            self.log(f"[Бэкап] Создана постоянная резервная копия: {backup_path.name}")
        else:
            self.log(f"[Бэкап] Резервная копия для версии {version} (хеш {short_hash}) уже существует.")

        # Метаданные бэкапа
        meta_path = backup_path.with_suffix(".json")
        if not meta_path.exists():
            meta = {
                "target": str(target_file.resolve()),
                "version": version,
                "sha256": file_hash,
                "timestamp": time.time(),
            }
            try:
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            except OSError:
                pass

        # Также поддерживаем канонический app.asar.original_backup для обратной совместимости
        canonical_backup = target_file.with_name(f"{target_file.name}.original_backup")
        if not canonical_backup.exists():
            try:
                shutil.copy2(target_file, canonical_backup)
            except OSError:
                pass

        return backup_path

    def find_latest_valid_backup(self, target_file: Path, expected_version: Optional[str] = None) -> Optional[Path]:
        """
        Находит самую свежую валидную резервную копию для целевого файла.
        """
        parent = target_file.parent
        prefix = f"{target_file.name}.bak.v"
        candidates = []

        if parent.exists():
            for f in parent.glob(f"{prefix}*"):
                if f.name.endswith(".json"):
                    continue
                candidates.append(f)

        if expected_version:
            matching = [c for c in candidates if f"v{expected_version}" in c.name]
            if matching:
                candidates = matching
            else:
                return None

        if candidates:
            # Сортируем по времени модификации (самый свежий первый)
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for c in candidates:
                if c.stat().st_size > 0:
                    return c

        # Запасной вариант — канонический original_backup
        canonical = target_file.with_name(f"{target_file.name}.original_backup")
        if canonical.exists() and canonical.stat().st_size > 0:
            return canonical

        legacy_bak = target_file.with_name(f"{target_file.name}.bak.original")
        if legacy_bak.exists() and legacy_bak.stat().st_size > 0:
            return legacy_bak

        return None

    def list_backups(self, filename: str) -> List[Dict[str, Any]]:
        parent = self.base_dir if self.base_dir else Path.cwd()
        backups = []
        prefix = f"{filename}.bak.v"
        for f in parent.glob(f"{prefix}*"):
            if f.name.endswith(".json"):
                continue
            meta_f = f.with_suffix(".json")
            version = "unknown"
            if meta_f.exists():
                try:
                    meta = json.loads(meta_f.read_text(encoding="utf-8"))
                    version = meta.get("version", "unknown")
                except Exception:
                    pass
            else:
                parts = f.name.split(".bak.v")
                if len(parts) > 1:
                    version = parts[1].split(".")[0]
            backups.append({
                "path": str(f.resolve()),
                "name": f.name,
                "version": version,
                "mtime": f.stat().st_mtime,
            })
        backups.sort(key=lambda x: x["mtime"], reverse=True)
        return backups

    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        if not backup_path.exists():
            return False
        try:
            shutil.copy2(backup_path, target_path)
            self.log(f"[Откат] Восстановлен из бэкапа: {target_path.name}")
            return True
        except Exception as e:
            self.log(f"[Откат] Ошибка восстановления: {e}")
            return False

    create_backup = create_versioned_backup
    find_latest_backup = find_latest_valid_backup


def atomic_stage_and_replace(
    staging_content: bytes,
    target_path: Path,
    expected_size: Optional[int] = None,
) -> None:
    """
    Атомарно записывает данные во временный файл в том же каталоге,
    проверяет размер и выполняет os.replace.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_name(f"{target_path.name}.{os.getpid()}.stage.tmp")
    try:
        with open(temp_path, "wb") as f:
            f.write(staging_content)
            f.flush()
            os.fsync(f.fileno())

        actual_size = temp_path.stat().st_size
        if expected_size is not None and actual_size != expected_size:
            raise TransactionError(
                f"Ошибка валидации размера: ожидалось {expected_size} байт, записано {actual_size}"
            )

        os.replace(temp_path, target_path)
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise
