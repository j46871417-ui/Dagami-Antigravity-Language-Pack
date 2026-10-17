"""Active install operations shared by the native GUI and CLI."""
from __future__ import annotations
import io
import json
import plistlib
import re
import hashlib
import sys
import tempfile
import zipfile
from pathlib import Path
from localizer_state import PatchState, digest
from jsonc_utils import update_argv_locale


def api(owner):
    return sys.modules[type(owner).__module__]


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def localized(value, lang):
    return value.get(lang) if isinstance(value, dict) else value


def packed_files(app, raw):
    header, data = app.read_asar_bytes(raw)
    result = {}
    def walk(node, prefix=''):
        for name, entry in node.get('files', {}).items():
            full = prefix + name
            if 'files' in entry:
                walk(entry, full + '/')
            elif 'offset' in entry and not entry.get('unpacked'):
                offset, size = int(entry['offset']), entry['size']
                if offset < 0 or size < 0 or offset + size > len(data):
                    raise ValueError('Invalid ASAR range')
                result[full] = data[offset:offset + size]
    walk(header)
    return result


def clean_legacy_base(app, path, patched):
    current = packed_files(app, patched)
    allowed = {'dist/menu.js', 'dist/main.js', 'dist/tray.js', 'dist/ideInstall/wizardHtml.js', 'dist/preload.js'}
    if 'package.json' not in current or 'dist/preload.js' not in current:
        raise ValueError('Cannot bind a legacy backup to this app build')
    for candidate in (path.with_name('app.asar.original_backup'), path.with_suffix(path.suffix + '.bak.original')):
        if not candidate.is_file(): continue
        raw = candidate.read_bytes()
        try: files = packed_files(app, raw)
        except (ValueError, TypeError, KeyError): continue
        if app.PRELOAD_MARKER.encode() in raw or b'__ag_renderThought' in raw: continue
        # Version alone is not enough: all unchanged code must also match.
        if files.keys() == current.keys() and all(files[name] == current[name] for name in current if name not in allowed):
            return raw
    raise ValueError('No clean backup for this app build. Use a clean app copy.')


def ide_version(app, root):
    base = app.get_ide_ext_base(root).parent.parent
    values = []
    for name in ('package.json', 'product.json'):
        file = base / name
        if file.exists():
            info = load(file)
            values.append([info.get('version'), info.get('commit')])
    return hashlib.sha256(json.dumps(values).encode()).hexdigest() if values else None


def nls_by_keys(source, keys, contents):
    original = json.loads(source)
    if not isinstance(original, list) or not all(isinstance(item, str) for item in original):
        raise ValueError('Unsupported NLS shape')
    output, count = [], 0
    for module, names in keys:
        messages = contents.get(module, {})
        for key in names:
            key = key.get('key') if isinstance(key, dict) else key
            if len(output) >= len(original): raise ValueError('NLS key count mismatch')
            value = messages.get(key)
            if isinstance(value, str):
                output.append(value); count += 1
            else:
                output.append(original[len(output)])
    if len(output) != len(original): raise ValueError('NLS key count mismatch')
    return (json.dumps(output, ensure_ascii=False) + '\n').encode('utf-8'), count


class InstallOperations:
    def _prepare(self, root):
        app = api(self)
        # Modifying an integrity checked signed bundle invalidates its signature.
        # Keep it intact until there is a supported re-signing workflow.
        contents = app.resolve_desktop_path(root)
        if contents.name != 'Contents':
            contents = app.resolve_ide_path(root)
        plist = contents / 'Info.plist'
        if plist.exists():
            info = plistlib.loads(plist.read_bytes())
            if info.get('ElectronAsarIntegrity') or (contents / '_CodeSignature').exists():
                raise ValueError('Signed macOS app: use an unsigned copy. No files were changed.')
        app.kill_antigravity_processes(self.log, force=self.force_kill, no_kill=self.no_kill)

    def install_ide(self, lang_code='ru'):
        app = api(self)
        try:
            if not self.ide_path or not app.validate_ide_path(self.ide_path):
                raise ValueError('IDE package.json is missing')
            self._prepare(self.ide_path)
            ext, out = app.get_ide_ext_base(self.ide_path), app.get_ide_out_dir(self.ide_path)
            if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)?', lang_code):
                raise ValueError('Invalid language code')
            language = app.LANGUAGES_DIR / lang_code
            translations, meta = load(language / 'ide.json'), load(language / 'metadata.json')
            with PatchState(app.resolve_ide_path(self.ide_path), [self.ide_user_data], version=ide_version(app, self.ide_path)) as state:
                changes = {}
                pkg_path = ext / 'package.json'
                pkg = json.loads(state.original(pkg_path))
                contributes = pkg.get('contributes', {})
                count = 0
                for section, identity, field in [('commands', 'command', 'title'), ('customEditors', 'viewType', 'displayName')]:
                    for item in contributes.get(section, []):
                        value = localized(translations.get(section, {}).get(item.get(identity), {}), lang_code)
                        if value:
                            item[field] = value; count += 1
                configs = contributes.get('configuration', {})
                for config in configs if isinstance(configs, list) else [configs]:
                    title = localized(translations.get('configurationTitle', {}), lang_code)
                    if title:
                        config['title'] = title; count += 1
                    for key, item in config.get('properties', {}).items():
                        value = localized(translations.get('configuration', {}).get(key, {}), lang_code)
                        if value:
                            for field in ['description', 'markdownDescription']:
                                if field in item:
                                    item[field] = value; count += 1
                changes[pkg_path] = (json.dumps(pkg, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
                ui = {k: localized(v, lang_code) for k, v in translations.get('ui_strings', {}).items()}
                ui = {k: v for k, v in ui.items() if v}
                chat = load(app.TRANSLATIONS_DIR / 'chat_strings.json') if lang_code == 'ru' else load(language / 'dict.json')
                for path, mapping in [(ext / 'dist' / 'extension.js', ui), (out / 'jetskiAgent' / 'main.js', chat)]:
                    source = state.original(path)
                    if source is not None:
                        text, changed = app.replace_js_string_literals(source.decode('utf-8'), mapping, self.log)
                        changes[path] = text.encode('utf-8'); count += changed
                argv = self.ide_user_data / 'argv.json'
                source = state.original(argv)
                # Work on a staged copy; the helper never touches the live file.
                with tempfile.TemporaryDirectory() as temp:
                    staged = Path(temp) / 'argv.json'
                    if source is not None:
                        staged.write_bytes(source)
                    if not update_argv_locale(staged, meta.get('vscodeLocale', lang_code), self.log):
                        raise ValueError('argv.json update failed')
                    changes[argv] = staged.read_bytes()
                nls = out / 'nls.messages.json'
                source = state.original(nls)
                if source is not None:
                    changes[nls] = source  # Remove any previous locale first.
                    if lang_code == 'ru' and app.RU_PACK_ZIP.exists():
                        keys = out / 'nls.keys.json'
                        if keys.exists():
                            try:
                                with zipfile.ZipFile(app.RU_PACK_ZIP) as archive:
                                    contents = json.loads(archive.read('translations/main.i18n.json'))['contents']
                                changes[nls], nls_count = nls_by_keys(source, load(keys), contents)
                                count += nls_count
                            except (ValueError, KeyError, TypeError):
                                self.log('[IDE] NLS: ключи не совпали. Каркас сохранён.')
                        else:
                            self.log('[IDE] NLS: нет файла ключей. Каркас сохранён.')
                if lang_code == 'ru' and app.RU_PACK_ZIP.exists():
                    pack = self.ide_user_data / 'extensions' / 'ms-ceintl.vscode-language-pack-ru-1.106.0-universal'
                    with zipfile.ZipFile(app.RU_PACK_ZIP) as archive:
                        for item in archive.infolist():
                            name = Path(item.filename)
                            if name.is_absolute() or '..' in name.parts or '\\' in item.filename or ':' in item.filename:
                                raise ValueError('Unsafe language pack entry')
                            if not item.is_dir():
                                path = pack / name
                                state.original(path)
                                changes[path] = archive.read(item)
                state.apply(changes)
                self.log(f'[IDE] Готово. Строк: {count}. Язык: {lang_code}.')
            return True
        except Exception as error:
            self.log(f'[IDE] Сбой: {error}')
            return False

    def install_desktop(self, lang_code='ru'):
        app = api(self)
        try:
            if not self.desktop_path or not app.validate_desktop_path(self.desktop_path):
                raise ValueError('app.asar is missing')
            self._prepare(self.desktop_path)
            path = app.get_desktop_asar_path(self.desktop_path)
            root = app.resolve_desktop_path(self.desktop_path)
            if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)?', lang_code):
                raise ValueError('Invalid language code')
            translations = load(app.LANGUAGES_DIR / lang_code / 'desktop.json')
            runtime = app.dtb.build_runtime_translator_js(lang_code)
            with PatchState(root) as state:
                try:
                    original = state.original(path)
                except ValueError:
                    # A new clean upstream archive must never use the old backup.
                    _, current = app.read_asar(path)
                    if app.PRELOAD_MARKER.encode() in current or b'__ag_renderThought' in current:
                        raise
                    state.accept_updated(path)
                    original = state.original(path)
                header, data = app.read_asar_bytes(original)
                if app.PRELOAD_MARKER.encode() in data or b'__ag_renderThought' in data:
                    base = clean_legacy_base(app, path, original)
                    state.entries[str(path.resolve())] = {'original': state.store(base), 'applied': digest(original), 'version': None}
                    original = base
                    header, data = app.read_asar_bytes(original)
                    self.log('[Desktop] Найдена чистая копия той же сборки.')
                targets = {'dist/menu.js': translations.get('menu', {}),
                           'dist/main.js': translations.get('tray', {}),
                           'dist/tray.js': translations.get('tray', {}),
                           'dist/ideInstall/wizardHtml.js': translations.get('wizard', {})}
                entries = []
                def walk(node, prefix=''):
                    for name, entry in node.get('files', {}).items():
                        full = prefix + name
                        if 'files' in entry:
                            walk(entry, full + '/')
                        elif 'offset' in entry and not entry.get('unpacked'):
                            entries.append((int(entry['offset']), full, entry))
                walk(header)
                chunks, offset, injected, count = [], 0, False, 0
                for old_offset, name, entry in sorted(entries, key=lambda row: row[0]):
                    size = entry['size']
                    if old_offset < 0 or size < 0 or old_offset + size > len(data):
                        raise ValueError('Invalid ASAR file range')
                    content = data[old_offset:old_offset + size]
                    if name in targets:
                        text, changed = app.replace_js_string_literals(content.decode('utf-8'), targets[name], self.log)
                        content = text.encode('utf-8'); count += changed
                    if name == 'dist/preload.js':
                        content = app.inject_dom_translator(content.decode('utf-8'), runtime).encode('utf-8')
                        injected = True
                    entry['offset'], entry['size'] = str(offset), len(content)
                    if 'integrity' in entry:
                        block_size = entry['integrity'].get('blockSize', 4194304)
                        if not isinstance(block_size, int) or block_size <= 0:
                            raise ValueError('Invalid ASAR integrity block size')
                        entry['integrity'] = app.compute_sha256_blocks(content, block_size)
                    chunks.append(content); offset += len(content)
                if not injected:
                    raise ValueError('Unsupported ASAR: dist/preload.js is missing')
                # Serialize and parse the staged archive before committing it.
                with tempfile.TemporaryDirectory() as temp:
                    staged = Path(temp) / 'app.asar'
                    app.write_asar_atomic(staged, header, b''.join(chunks))
                    app.read_asar(staged)
                    state.apply({path: staged.read_bytes()})
                self.log(f'[Desktop] Готово. Строк: {count}. Язык: {lang_code}.')
            return True
        except Exception as error:
            self.log(f'[Desktop] Сбой: {error}')
            return False

    def restore_all(self):
        app = api(self)
        count, ok = 0, True
        for root, extra in [(self.ide_path, [self.ide_user_data]), (self.desktop_path, [])]:
            if not root:
                continue
            try:
                self._prepare(root)
                resolved = app.resolve_ide_path(root) if extra else app.resolve_desktop_path(root)
                with PatchState(resolved, extra) as state:
                    created = [Path(name) for name, entry in state.entries.items() if entry['original'] is None]
                    count += state.restore()
                    # Only remove empty folders of the known pack we created.
                    pack = self.ide_user_data / 'extensions' / 'ms-ceintl.vscode-language-pack-ru-1.106.0-universal'
                    for file in created:
                        parent = file.parent
                        while parent.is_relative_to(pack) and parent != pack.parent:
                            try: parent.rmdir()
                            except OSError: break
                            parent = parent.parent
            except Exception as error:
                self.log(f'[Откат] Сбой: {error}'); ok = False
        self.log(f'[Откат] Число файлов: {count}.')
        return ok and count > 0
