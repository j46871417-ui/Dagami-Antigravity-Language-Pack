"""OS paths and build names, with no GUI or optional imports."""
from pathlib import Path
import os
import platform
import sys


def architecture(machine=None):
    name = (machine or platform.machine()).lower()
    if name in ('amd64','x86_64','x64'): return 'x64'
    if name in ('arm64','aarch64'): return 'arm64'
    raise ValueError('Supported CPU types: x64 and arm64')


def update_state_dir(system=None, home=None, environ=None):
    system = system or sys.platform
    home = Path(home) if home else Path.home()
    env = os.environ if environ is None else environ
    if env.get('DAGAMI_LANGUAGE_STATE'): return Path(env['DAGAMI_LANGUAGE_STATE'])
    if system == 'win32':
        base = Path(env.get('LOCALAPPDATA', home/'AppData'/'Local'))
    elif system == 'darwin':
        base = home/'Library'/'Application Support'
    else:
        base = Path(env.get('XDG_STATE_HOME', home/'.local'/'state'))
    return base/'DagamiAntigravityLanguagePack'/'updates'


def native_asset_name(tag, system=None, arch=None):
    system = system or sys.platform
    arch = arch or architecture()
    if system == 'win32': return 'AntigravityLocalizer.exe'
    label = {'linux':'Linux','darwin':'macOS'}[system]
    return f'DagamiAntigravityLanguagePack-{tag}-{label}-{arch}.tar.gz'
