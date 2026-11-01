"""Current layouts, exact rollback and fail-closed native CLI translation."""
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import cli_localization as cli
import dagami_ag_localizer as app


def native_fixture():
    strings = {f'Reviewed CLI service description number {i:02d}.': f'Строка {i}' for i in range(12)}
    data = b'\0'.join(key.encode() for key in strings)
    raw = bytearray(512+len(data))
    raw[:2] = b'MZ'
    struct.pack_into('<I', raw, 60, 128)
    raw[128:132] = b'PE\0\0'
    struct.pack_into('<HH', raw, 132, 0x8664, 1)
    struct.pack_into('<H', raw, 148, 0)
    raw[152:160] = b'.rdata\0\0'
    struct.pack_into('<II', raw, 168, len(data), 512)
    struct.pack_into('<I', raw, 188, 0x40000040)
    raw[256:270] = b'\xff Go buildinf:'
    raw[512:] = data
    raw = bytes(raw)
    return raw, {'strings': strings, 'reviewed_sha256': [hashlib.sha256(raw).hexdigest()]}


class CliSafety(unittest.TestCase):
    def test_unchanged_code_layout_and_valid_utf8(self):
        raw, catalog = native_fixture()
        result, count = cli.translate(raw, catalog)
        self.assertEqual(count, 12)
        self.assertEqual(len(raw), len(result))
        self.assertEqual(raw[:512], result[:512])
        self.assertIn('Строка 11', result[512:].decode('utf-8'))

    def test_unknown_build_rejected_even_when_strings_match(self):
        raw, catalog = native_fixture()
        with self.assertRaisesRegex(ValueError, 'сборка'):
            cli.translate(raw+b'new-build', catalog)

    def test_executable_section_is_never_translated(self):
        raw, catalog = native_fixture()
        raw = bytearray(raw)
        struct.pack_into('<I', raw, 188, 0x60000020)
        catalog['reviewed_sha256'] = [hashlib.sha256(raw).hexdigest()]
        with self.assertRaises(ValueError): cli.translate(bytes(raw), catalog)

    def test_long_translation_rejected(self):
        raw, catalog = native_fixture()
        catalog['strings'][next(iter(catalog['strings']))] = 'Я'*100
        with self.assertRaises(ValueError): cli.translate(raw, catalog)

    def test_duplicate_or_overlapping_strings_rejected(self):
        raw, catalog = native_fixture()
        catalog['strings']['Reviewed CLI service description number '] = 'Строка'
        with self.assertRaises(ValueError): cli.translate(raw, catalog)

    def test_install_repeat_and_exact_rollback_including_foreign_patch(self):
        raw, catalog = native_fixture()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'agy.exe'; path.write_bytes(raw)
            localizer = app.DagamiLocalizer(cli_path=path, no_kill=True, log_fn=lambda *_: None)
            with patch.object(cli, 'load_catalog', return_value=catalog):
                self.assertTrue(localizer.install_cli())
                translated = path.read_bytes()
                self.assertTrue(localizer.install_cli())
                self.assertEqual(translated, path.read_bytes())
            self.assertTrue(localizer.restore_all())
            self.assertEqual(raw, path.read_bytes())

    def test_modified_binary_and_other_languages_do_not_get_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'agy.exe'; path.write_bytes(b'unknown')
            localizer = app.DagamiLocalizer(cli_path=path, no_kill=True, log_fn=lambda *_: None)
            self.assertFalse(localizer.install_cli())
            self.assertFalse(localizer.install_cli('fr'))
            self.assertEqual(path.read_bytes(), b'unknown')

    def test_menu_installs_cli_without_calling_unselected_desktop(self):
        localizer = app.DagamiLocalizer(cli_path=Path('agy.exe'), no_kill=True)
        with patch.object(localizer, 'install_cli', return_value=True) as install, \
             patch.object(localizer, 'install_desktop') as desktop, \
             patch('builtins.input', side_effect=['1', '0']), patch.object(app, 'safe_print'):
            app.run_interactive_cli(localizer)
        install.assert_called_once_with('ru')
        desktop.assert_not_called()


class CurrentIde(unittest.TestCase):
    def test_agy_extension_panel_locale_and_exact_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'IDE'; base = root/'resources'/'app'
            extension = base/'extensions'/'agy'
            extension.mkdir(parents=True)
            package = extension/'package.json'
            raw = json.dumps({'name': 'google-antigravity', 'contributes': {'commands': [
                {'command': 'antigravity.openSettings', 'title': 'Open Settings'}]}}).encode()
            package.write_bytes(raw)
            (base/'product.json').write_text('{"ideVersion":"2.6.0","commit":"fixture"}')
            panel = base/'out'/'jetskiAgent'/'main.js'; panel.parent.mkdir(parents=True)
            source = b'const machine = {command: "antigravity.openSettings", status: "Reading"};\n'
            panel.write_bytes(source)
            userdata = Path(temp)/'UserData'
            argv = userdata/'argv.json'; userdata.mkdir()
            argv.write_bytes(b'// keep user preference\n{"locale":"en", "unrelated":true}\n')
            old_argv = argv.read_bytes()
            self.assertEqual(extension, app.get_ide_ext_base(root))
            self.assertTrue(app.validate_ide_path(root))
            localizer = app.DagamiLocalizer(ide_path=root, ide_user_data=userdata, no_kill=True, log_fn=lambda *_: None)
            with patch.object(app, 'RU_PACK_ZIP', Path(temp)/'absent.zip'):
                self.assertTrue(localizer.install_ide())
                translated = panel.read_bytes()
                self.assertIn(app.PRELOAD_MARKER.encode(), translated)
                self.assertIn(b'antigravity.openSettings', translated)
                self.assertTrue(translated.startswith(source.rstrip()))
                self.assertIn('"locale":"ru"', argv.read_text())
                self.assertTrue(localizer.install_ide())
                self.assertEqual(translated, panel.read_bytes())
                self.assertTrue(localizer.install_ide('es'))
                self.assertEqual(panel.read_text().count(app.PRELOAD_MARKER), 1)
                self.assertIn('TARGET_LANG = "es"', panel.read_text())
                self.assertTrue(localizer.restore_all())
            self.assertEqual(raw, package.read_bytes())
            self.assertEqual(source, panel.read_bytes())
            self.assertEqual(old_argv, argv.read_bytes())

    def test_unrelated_agy_package_is_not_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate = root/'resources/app/extensions/agy'
            candidate.mkdir(parents=True); (candidate/'package.json').write_text('{"name":"unrelated"}')
            self.assertFalse(app.validate_ide_path(root))

    def test_windows_settings_and_extensions_are_different_roots(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(app.sys, 'platform', 'win32'), patch.dict(os.environ, {'APPDATA': temp}):
            defaults = app.get_default_paths()
            self.assertEqual(defaults['ide_user_data'], Path(temp)/'Antigravity IDE')
            self.assertEqual(defaults['ide_extensions'], Path.home()/'.antigravity-ide/extensions')


if __name__ == '__main__': unittest.main()
