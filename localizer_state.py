"""Atomic, hash linked patch state. No in-place writes or legacy backup reuse."""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.dagami-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            os.chmod(name, path.stat().st_mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class PatchState:
    def __init__(self, root, extra_roots=(), version=None):
        self.version = version
        self.root = Path(root).resolve()
        self.allowed = (self.root, *(Path(p).resolve() for p in extra_roots))
        self.folder = self.root / '.dagami-state'
        self.manifest = self.folder / 'manifest.json'
        self.journal = self.folder / 'pending.json'
        self.entries = {}

    def checked(self, path):
        path = Path(path).resolve()
        if not any(path.is_relative_to(base) for base in self.allowed) or path.is_relative_to(self.folder):
            raise ValueError('State target is outside the app folders')
        return path

    def __enter__(self):
        if self.folder.is_symlink():
            raise ValueError("Patch state must not be a link")
        self.folder.mkdir(exist_ok=True)
        self.lock = open(self.folder / 'lock', 'a+b')
        self.lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                if not self.lock.read(1):
                    self.lock.write(b'0'); self.lock.flush()
                self.lock.seek(0)
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            raise RuntimeError('Another patch task is active')
        try:
            self.entries = json.loads(self.manifest.read_text('utf-8')) if self.manifest.exists() else {}
            if self.journal.exists():
                pending = json.loads(self.journal.read_text('utf-8'))
                if self.entries != pending['next']:
                    self._rollback(pending)
                self.journal.unlink()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        self.lock.close()

    def store(self, data):
        key = digest(data)
        if key is not None:
            file = self.folder / (key + '.bin')
            if not file.exists():
                atomic(file, data)
        return key

    def read(self, key):
        if key is None:
            return None
        if not isinstance(key, str) or len(key) != 64 or any(c not in '0123456789abcdef' for c in key):
            raise ValueError('Invalid backup hash')
        data = (self.folder / (key + '.bin')).read_bytes()
        if digest(data) != key:
            raise ValueError('Backup hash mismatch')
        return data

    def original(self, path):
        path = self.checked(path)
        current = path.read_bytes() if path.exists() else None
        entry = self.entries.get(str(path))
        if entry:
            if digest(current) not in (entry['applied'], entry['original']):
                if self.version and entry.get('version') and self.version != entry['version']:
                    self.entries.pop(str(path))
                    return current
                raise ValueError(f'File changed outside Dagami: {path.name}. Restore first or use a clean app copy.')
            return self.read(entry['original'])
        return current

    def accept_updated(self, path):
        # Called only for a verified clean ASAR after an upstream app update.
        path = self.checked(path)
        self.entries.pop(str(path), None)

    def _set(self, path, data):
        if data is None:
            path.unlink(missing_ok=True)
        else:
            atomic(path, data)

    def _rollback(self, pending):
        # Validate every target and backup before rolling any file back.
        values = []
        for name, item in pending['files'].items():
            path = self.checked(name)
            current = path.read_bytes() if path.exists() else None
            if digest(current) not in (item['before'], item['after']):
                raise ValueError(f'Cannot recover an externally changed file: {path.name}')
            values.append((path, self.read(item['before'])))
        for path, data in reversed(values):
            current = path.read_bytes() if path.exists() else None
            if current != data:
                self._set(path, data)

    def apply(self, changes, restoring=False):
        before = dict(self.entries)
        after = dict(before)
        files = {}
        for path, data in changes.items():
            path = self.checked(path)
            old = path.read_bytes() if path.exists() else None
            original = self.original(path)
            files[str(path)] = {'before': self.store(old), 'after': self.store(data)}
            if restoring:
                after.pop(str(path), None)
            else:
                after[str(path)] = {'original': self.store(original), 'applied': digest(data), 'version': self.version}
        pending = {'files': files, 'next': after}
        atomic(self.journal, json.dumps(pending).encode())
        try:
            for path, data in changes.items():
                self._set(self.checked(path), data)
            atomic(self.manifest, json.dumps(after, indent=2).encode())
        except BaseException:
            self._rollback(pending)
            self.journal.unlink()
            raise
        self.entries = after
        self.journal.unlink()

    def restore(self):
        changes = {self.checked(name): self.original(name) for name in self.entries}
        if changes:
            self.apply(changes, restoring=True)
        return len(changes)
