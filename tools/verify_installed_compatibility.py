"""Verify copies of installed public program files; never touch user settings.

Runs native CLI only with --help / --version, using an isolated test home.
GUI rendering/login still require separate manual verification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import dagami_ag_localizer as app
from localizer_state import PatchState


def fingerprint(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desktop-root', type=Path)
    parser.add_argument('--ide-root', type=Path)
    parser.add_argument('--cli-file', type=Path)
    options = parser.parse_args()
    if not any(vars(options).values()): parser.error('Choose at least one application.')
    tracked, baselines, results = {}, {}, {}
    def copy(source, target, state_root=None):
        tracked[source] = fingerprint(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        # An installed app can already be localized. Read only its hash-linked
        # ORIGINAL program file; do not carry absolute manifests or user settings
        # into the fixture, and never acquire/create state in the installed app.
        state = PatchState(state_root) if state_root else None
        if state and state.manifest.is_file():
            state.entries = json.loads(state.manifest.read_text('utf-8'))
            data = state.original(source)
            if data is None: raise ValueError('Expected an original program file')
            target.write_bytes(data)
        else:
            shutil.copyfile(source, target)
        baselines[target] = fingerprint(target)
    with tempfile.TemporaryDirectory(prefix='dagami-language-compat-') as folder:
        scratch = Path(folder)
        if options.desktop_root:
            source = app.get_desktop_asar_path(options.desktop_root)
            stage = scratch/'Desktop'; target = stage/'resources/app.asar'
            copy(source, target, app.resolve_desktop_path(options.desktop_root))
            localizer = app.DagamiLocalizer(desktop_path=stage, no_kill=True)
            assert localizer.install_desktop(), 'Desktop install failed'
            first = fingerprint(target)
            assert localizer.install_desktop() and fingerprint(target) == first, 'Non-idempotent Desktop install'
            header, data = app.read_asar(target)
            entry = header['files']['dist']['files']['preload.js']; offset = int(entry['offset'])
            script = scratch/'preload.cjs'; script.write_bytes(data[offset:offset+entry['size']])
            subprocess.run(['node', '--check', str(script)], check=True, capture_output=True, timeout=20)
            assert localizer.install_desktop('es'), 'Desktop language switch failed'
            assert localizer.restore_all() and fingerprint(target) == baselines[target], 'Desktop rollback mismatch'
            results['desktop'] = 'install, repeat, switch, JS syntax, byte-exact restore: PASS'
        if options.ide_root:
            source_ext = app.get_ide_ext_base(options.ide_root)
            source_app = source_ext.parent.parent
            stage = scratch/'IDE'; target_app = stage/'resources/app'
            target_ext = target_app/'extensions'/source_ext.name
            paths = [source_app/'package.json', source_app/'product.json', source_ext/'package.json',
                     source_ext/'dist/extension.js', source_app/'out/jetskiAgent/main.js',
                     source_app/'out/nls.messages.json', source_app/'out/nls.keys.json']
            for source in paths:
                if source.is_file(): copy(source, target_app/source.relative_to(source_app), app.resolve_ide_path(options.ide_root))
            assert app.validate_ide_path(stage), 'IDE detection failed'
            localizer = app.DagamiLocalizer(ide_path=stage, ide_user_data=scratch/'UserData',
                ide_extensions=scratch/'Extensions', no_kill=True)
            started = time.monotonic()
            assert localizer.install_ide(), 'IDE install failed'
            panel = target_app/'out/jetskiAgent/main.js'
            patched = fingerprint(panel)
            assert app.PRELOAD_MARKER in panel.read_text('utf-8'), 'Missing IDE runtime'
            subprocess.run(['node', '--check', str(panel)], check=True, capture_output=True, timeout=30)
            assert localizer.install_ide() and fingerprint(panel) == patched, 'Non-idempotent IDE install'
            assert localizer.install_ide('es'), 'IDE language switch failed'
            assert localizer.restore_all(), 'IDE rollback failed'
            for source in paths:
                if source in tracked:
                    target = target_app/source.relative_to(source_app)
                    assert fingerprint(target) == baselines[target], 'IDE rollback mismatch'
            results['ide'] = {'checks': 'detection, install, repeat, switch, JS syntax, byte-exact restore: PASS',
                              'total_seconds': round(time.monotonic()-started, 2)}
        if options.cli_file:
            source = options.cli_file; target = scratch/'CLI/agy.exe'
            copy(source, target, source.parent)
            env = dict(os.environ, HOME=str(scratch/'Home'), USERPROFILE=str(scratch/'Home'),
                       APPDATA=str(scratch/'AppData'), LOCALAPPDATA=str(scratch/'LocalAppData'))
            for name in ('HOME', 'APPDATA', 'LOCALAPPDATA'): Path(env[name]).mkdir(parents=True, exist_ok=True)
            def run(flag):
                return subprocess.run([str(target), flag], capture_output=True, text=True, encoding='utf-8',
                    errors='strict', timeout=20, env=env, cwd=scratch, check=True)
            version = run('--version').stdout.strip()
            before = run('--help')
            localizer = app.DagamiLocalizer(cli_path=target, no_kill=True)
            assert localizer.install_cli(), 'CLI install failed'
            after = run('--help')
            help_before, help_after = before.stdout+before.stderr, after.stdout+after.stderr
            assert set(re.findall(r'(?m)^  (-[-a-z]+)', help_before)) == set(re.findall(r'(?m)^  (-[-a-z]+)', help_after)), 'CLI flags changed'
            assert 'Модель сессии' in help_after and 'Команды CLI:' in help_after, 'CLI help not translated'
            assert run('--version').stdout.strip() == version, 'CLI version changed'
            first = fingerprint(target)
            assert localizer.install_cli() and fingerprint(target) == first, 'Non-idempotent CLI install'
            assert localizer.restore_all() and fingerprint(target) == baselines[target], 'CLI rollback mismatch'
            results['cli'] = {'version': version, 'checks': 'native help/version, flag preservation, repeat, byte-exact restore: PASS'}
        for source, expected in tracked.items():
            assert fingerprint(source) == expected, 'Installed source changed during validation'
    print(json.dumps({'installed_files_unchanged': True, 'results': results,
                      'not_verified': ['live GUI rendering', 'interactive CLI', 'Linux/macOS', 'future upstream builds']}, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
