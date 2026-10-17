"""Prepare unpacked source ports; these are not native executable builds."""
from pathlib import Path
import json
import hashlib
import shutil
from app_info import APP_VERSION
ROOT=Path(__file__).resolve().parent
FILES=['language_pack.py','launch.py','dagami_ag_localizer.py','native_design.py',
       'app_info.py','app_updates.py','update_ui.py','platform_support.py',
       'localizer_core.py','localizer_state.py','jsonc_utils.py','js_literals.py',
       'dagami_translator_builder.py','dagami-ag-localizer.sh','PORTS.md','LICENSE',
       'ASSET_SOURCES.json','install_desktop.py','build_release.py','package_native.py',
       'verify_build_artifact.py','extract_ru_dict.py','build_language_packs.py','requirements.txt','build_icon.py']


def prepare(out):
    out=Path(out)
    for name in ('Linux','macOS'):
        target=out/name;target.mkdir(parents=True,exist_ok=True)
        for file in FILES+(['Launch.command'] if name=='macOS' else []):
            shutil.copy2(ROOT/file,target/file)
        for folder in ('translations','assets'):
            for source in (ROOT/folder).rglob('*'):
                if not source.is_file() or '__pycache__' in source.parts: continue
                dest=target/source.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,dest)
        for file in target.glob('*.sh'): file.chmod(0o755)
        if name=='macOS': (target/'Launch.command').chmod(0o755)
        (target/'PORT_KIND.json').write_text(json.dumps({'kind':'source','version':APP_VERSION,'platform':name,'needs':'Python 3.10+ and Tk','native_binary_built':False},indent=2),'utf-8')
        hashes={file.relative_to(target).as_posix():hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(target.rglob('*')) if file.is_file() and file.name!='FILES_SHA256.json'}
        (target/'FILES_SHA256.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),'utf-8')
        print('Source port:',target)

if __name__ == '__main__': prepare(ROOT/'ports')
