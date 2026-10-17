"""Build on the target OS. No tag, push, release, or upload is performed."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
from app_info import APP_NAME, APP_VERSION
from platform_support import architecture
ROOT = Path(__file__).resolve().parent


def embedded_tk_data():
    """Copy scripts only for Tcl 9 zipfs; normal Tk uses PyInstaller's hook."""
    import tkinter
    root = tkinter.Tk(); root.withdraw()
    try:
        paths = [(root.tk.eval('info library'), '_tcl_data'), (root.tk.eval('set tk_library'), '_tk_data')]
        if not any(source.startswith('//zipfs:') for source, _ in paths): return []
        def copy_virtual(source, target):
            target.mkdir(parents=True, exist_ok=True)
            for item in root.tk.splitlist(root.tk.call('glob', '-nocomplain', '-directory', source, '*')):
                name = str(root.tk.call('file', 'tail', item))
                if root.tk.call('file', 'isdirectory', item):
                    copy_virtual(item, target/name)
                else:
                    channel = root.tk.call('open', item, 'rb')
                    try:
                        data = root.tk.call('read', channel)
                        if not isinstance(data, bytes): raise TypeError('Expected Tcl binary data')
                        (target/name).write_bytes(data)
                    finally: root.tk.call('close', channel)
        extra = []
        for source, name in paths:
            target = ROOT/'build'/'tk-data'/name
            copy_virtual(source, target)
            extra.append((str(target), name))
        return extra
    finally: root.destroy()


def windows_version():
    parts = tuple(map(int, APP_VERSION.split('.'))) + (0,)
    path = ROOT/'build'/'windows-version.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("""VSVersionInfo(
 ffi=FixedFileInfo(filevers=%r, prodvers=%r, mask=0x3f, flags=0, OS=0x40004, fileType=0x1, subtype=0, date=(0,0)),
 kids=[StringFileInfo([StringTable('040904B0', [
 StringStruct('CompanyName', 'Dagami'), StringStruct('FileDescription', %r),
 StringStruct('FileVersion', %r), StringStruct('ProductName', %r),
 StringStruct('ProductVersion', %r), StringStruct('OriginalFilename', 'AntigravityLocalizer.exe')
 ])]),VarFileInfo([VarStruct('Translation', [1033,1200])])]
)""" % (parts, parts, APP_NAME, APP_VERSION, APP_NAME, APP_VERSION), 'utf-8')
    return path


def write_spec(system, arch, onefile=False, identity=None):
    if system not in ('win32','linux','darwin'): raise ValueError('Unsupported build OS')
    if system == 'darwin' and onefile: raise ValueError('macOS uses a folder .app bundle')
    name = 'AntigravityLocalizer' if system == 'win32' else 'DagamiLanguagePack'
    extension = '.ico' if system == 'win32' else '.icns' if system == 'darwin' else '-256.png'
    icon = ROOT/'assets'/('app-icon'+extension)
    if not icon.is_file(): raise FileNotFoundError(icon)
    datas = [(str(ROOT/'translations'), 'translations'), (str(ROOT/'assets'), 'assets')]
    datas += embedded_tk_data()
    options = dict(name=name, debug=False, bootloader_ignore_signals=False,
                   strip=False, upx=False, console=False)
    if system == 'win32': options.update(icon=str(icon), version=str(windows_version()))
    if system == 'darwin': options.update(icon=str(icon), target_arch='arm64' if arch == 'arm64' else 'x86_64', codesign_identity=identity, argv_emulation=False)
    script = f"a = Analysis([{str(ROOT/'language_pack.py')!r}], pathex=[{str(ROOT)!r}], binaries=[], datas={datas!r}, hiddenimports=[])\npyz = PYZ(a.pure)\n"
    kwargs = ', '.join(f'{key}={value!r}' for key,value in options.items())
    if onefile:
        script += f'exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], {kwargs})\n'
    else:
        script += f'exe = EXE(pyz, a.scripts, [], exclude_binaries=True, {kwargs})\n'
        script += f'coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name={name!r})\n'
    if system == 'darwin':
        info = {'CFBundleDisplayName':'Dagami Language Pack', 'CFBundleName':'Dagami Language Pack',
                'CFBundleShortVersionString':APP_VERSION, 'CFBundleVersion':APP_VERSION,
                'NSHighResolutionCapable':True, 'LSApplicationCategoryType':'public.app-category.developer-tools',
                'LSMinimumSystemVersion':'15.0'}
        script += f"app = BUNDLE(coll, name='DagamiLanguagePack.app', icon={str(icon)!r}, bundle_identifier='ru.dagami.languagepack', info_plist={info!r})\n"
    path = ROOT/'build'/'spec'/f'{name}-{system}-{arch}.spec'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script, 'utf-8')
    return path, name


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--onedir', action='store_true', help='Folder app (the default)')
    mode.add_argument('--onefile', action='store_true', help='Optional single file on Windows or Linux')
    parser.add_argument('--no-package', action='store_true', help='Keep only the unpacked native app')
    parser.add_argument('--package', action='store_true', help='Also make an OS/CPU-specific archive')
    parser.add_argument('--codesign-identity', help='Existing macOS signing identity; not a password')
    options = parser.parse_args()
    system, arch = sys.platform, architecture()
    if options.codesign_identity and system != 'darwin': parser.error('Signing identity is macOS-only')
    env = dict(os.environ, PYTHONIOENCODING='utf-8', ANTIGRAVITY_SKIP_KILL='1')
    env['DAGAMI_LANGUAGE_STATE'] = str(ROOT/'build'/'check-profile')
    for script in ('extract_ru_dict.py','build_language_packs.py','verify_build_artifact.py'):
        subprocess.run([sys.executable, script], cwd=ROOT, env=env, check=True)
    spec, name = write_spec(system, arch, options.onefile, options.codesign_identity)
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm',str(spec)], cwd=ROOT, env=env, check=True)
    if system == 'darwin':
        folder = ROOT/'dist'/'DagamiLanguagePack.app'
        executable = folder/'Contents'/'MacOS'/name
    elif options.onefile:
        executable = ROOT/'dist'/(name + ('.exe' if system == 'win32' else ''))
        folder = executable
    else:
        folder = ROOT/'dist'/name
        executable = folder/(name + ('.exe' if system == 'win32' else ''))
    if system == 'win32':
        from app_updates import validate_exe
        validate_exe(executable, APP_VERSION)
    subprocess.run([str(executable), '--verify-bundle'], cwd=ROOT, env=env, timeout=60, check=True)
    if system == 'linux' and folder.is_dir():
        shutil.copy2(ROOT/'assets'/'app-icon-256.png', folder/'dagami-language-pack.png')
        shutil.copy2(ROOT/'install_desktop.py', folder/'install_desktop.py')
    report = {'platform':system,'arch':arch,'version':APP_VERSION,'path':str(folder),
              'resource_check':'passed','gui_check':'not_run','signed_developer_id':bool(options.codesign_identity)}
    report_file = ROOT/'build'/f'native-{system}-{arch}.json'
    report_file.write_text(json.dumps(report, indent=2),'utf-8')
    if options.package and not options.no_package:
        subprocess.run([sys.executable,'package_native.py','--platform',system,'--arch',arch,'--input',str(folder)],cwd=ROOT,env=env,check=True)
    print('Native app:',folder)
    print('Resource check passed; GUI and real IDE use need host validation.')

if __name__ == '__main__': main()
