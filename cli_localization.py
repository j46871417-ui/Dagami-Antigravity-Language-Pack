"""Conservative offline translation of reviewed Go CLI UI literals.

No instruction, pointer, string length, flag or model output modifications.
Only the reviewed Windows x64 1.4.10 build family is accepted. The caller
owns transactional backup/rollback; unsupported versions fail before writes.
"""
from __future__ import annotations

import hashlib
import json
import struct


def readonly_data(raw):
    if len(raw) < 64 or raw[:2] != b'MZ':
        raise ValueError('CLI: поддерживается Windows x64 Go PE; ELF/Mach-O пока не поддерживаются.')
    pe = struct.unpack_from('<I', raw, 60)[0]
    if pe > len(raw) - 24 or raw[pe:pe+4] != b'PE\0\0':
        raise ValueError('CLI: повреждённый PE-заголовок.')
    machine, count = struct.unpack_from('<HH', raw, pe+4)
    optional = struct.unpack_from('<H', raw, pe+20)[0]
    table = pe+24+optional
    if machine != 0x8664 or not 1 <= count <= 96 or table+40*count > len(raw):
        raise ValueError('CLI: неизвестная архитектура или таблица секций.')
    found = []
    for index in range(count):
        pos = table+index*40
        size, offset = struct.unpack_from('<II', raw, pos+16)
        flags = struct.unpack_from('<I', raw, pos+36)[0]
        if raw[pos:pos+8].rstrip(b'\0') == b'.rdata':
            if offset < table+40*count or not size or offset+size > len(raw) or flags & 0xA0000000 or not flags & 0x40000000:
                raise ValueError('CLI: секция строк должна быть read-only, без кода.')
            found.append((offset, offset+size))
    if len(found) != 1 or b'\xff Go buildinf:' not in raw:
        raise ValueError('CLI: не распознан Go executable.')
    return found[0]


def translate(raw, catalog):
    """Require an explicitly reviewed source hash, not just matching phrases."""
    if hashlib.sha256(raw).hexdigest() not in catalog.get('reviewed_sha256', []):
        raise ValueError('CLI: эта сборка ещё не проверена. Исходный файл не изменён.')
    start, end = readonly_data(raw)
    patches = []
    for source, target in catalog['strings'].items():
        old, new = source.encode('utf-8'), target.encode('utf-8')
        # Avoid generic words, format-string changes and adjacent string damage.
        if len(old) < 20 or len(new) > len(old) or not new or b'\0' in new:
            raise ValueError('CLI: недопустимая длина строки перевода.')
        if source.count('%') != target.count('%') or '%' in source:
            raise ValueError('CLI: форматные строки не поддерживаются.')
        pos = raw.find(old, start, end)
        if pos < 0 or raw.find(old, pos+1, end) >= 0:
            raise ValueError('CLI: отсутствующая или неоднозначная строка интерфейса.')
        patches.append((pos, pos+len(old), new.ljust(len(old), b' ')))
    patches.sort()
    if len(patches) < 10 or any(left[1] > right[0] for left, right in zip(patches, patches[1:])):
        raise ValueError('CLI: неполный или пересекающийся набор переводов.')
    output = bytearray(raw)
    for first, last, value in patches:
        output[first:last] = value
    assert len(output) == len(raw)
    return bytes(output), len(patches)


def load_catalog(path):
    return json.loads(path.read_text(encoding='utf-8'))
