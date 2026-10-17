"""Optional per-user Linux menu entry; no sudo and no global file changes."""
from pathlib import Path
import os
import sys


def main():
    if not sys.platform.startswith('linux'): raise SystemExit('Run this on Linux')
    root=Path(__file__).resolve().parent
    native=root/'DagamiLanguagePack'
    command=[str(native),'--gui'] if native.is_file() else [sys.executable,str(root/'launch.py'),'--gui']
    if any(any(c in token for c in '\n\r\\"`$%') for token in command):
        raise SystemExit('Use an app folder without quotes, percent signs or shell symbols')
    icon=root/'dagami-language-pack.png'
    if not icon.exists(): icon=root/'assets'/'app-icon-256.png'
    folder=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local'/'share'))/'applications'
    folder.mkdir(parents=True,exist_ok=True)
    target=folder/'ru.dagami.languagepack.desktop'
    text='\n'.join(['[Desktop Entry]','Version=1.0','Type=Application',
        'Name=Dagami Language Pack','Comment=Language packs for Antigravity Desktop and IDE',
        'Exec='+' '.join('"'+token+'"' for token in command),
        'Icon='+str(icon),'Terminal=false','Categories=Development;Utility;',
        'StartupWMClass=DagamiLanguagePack',''])
    target.write_text(text,'utf-8')
    print('Menu entry:',target)

if __name__ == '__main__': main()
