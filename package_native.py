"""Package only a real native build supplied by its target host."""
from pathlib import Path
import argparse
import hashlib
import os
import struct
import tarfile
import zipfile
from app_info import APP_VERSION
from platform_support import native_asset_name
ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', choices=['win32','linux','darwin'], required=True)
    parser.add_argument('--arch', choices=['x64','arm64'], required=True)
    parser.add_argument('--input', type=Path, required=True)
    options = parser.parse_args()
    source = options.input.resolve()
    if not source.exists(): raise FileNotFoundError(source)
    expected = source/'Contents'/'MacOS'/'DagamiLanguagePack' if options.platform == 'darwin' else (source/('AntigravityLocalizer.exe' if options.platform == 'win32' else 'DagamiLanguagePack') if source.is_dir() else source)
    if not expected.is_file(): raise FileNotFoundError(expected)
    if options.platform != 'win32' and not os.access(expected,os.X_OK): raise ValueError('Native executable mode is missing')
    with expected.open('rb') as stream: header=stream.read(64)
    if options.platform=='win32' and header[:2]!=b'MZ': raise ValueError('Expected a native PE file')
    if options.platform=='linux':
        if header[:4]!=b'\x7fELF' or len(header)<20 or header[5]!=1: raise ValueError('Expected a native little-endian ELF file')
        machine=struct.unpack_from('<H',header,18)[0]
        if machine!=({'x64':62,'arm64':183}[options.arch]): raise ValueError('ELF CPU does not match package name')
    if options.platform=='darwin':
        if header[:4] not in (b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf'): raise ValueError('Expected a thin native Mach-O file')
        endian='<' if header[:4]==b'\xcf\xfa\xed\xfe' else '>'
        machine=struct.unpack_from(endian+'I',header,4)[0]
        if machine!=({'x64':0x1000007,'arm64':0x100000c}[options.arch]): raise ValueError('Mach-O CPU does not match package name')
    out = ROOT/'release_dist';out.mkdir(exist_ok=True)
    name = native_asset_name('v'+APP_VERSION,options.platform,options.arch)
    if options.platform == 'win32': name=f'DagamiAntigravityLanguagePack-v{APP_VERSION}-Windows-{options.arch}.zip'
    target = out/name
    if target.suffix == '.zip':
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
            for item in sorted(source.rglob('*')) if source.is_dir() else [source]:
                if item.is_file(): archive.write(item,source.name+'/'+item.relative_to(source).as_posix() if source.is_dir() else item.name)
            archive.write(ROOT/'PORTS.md','PORTS.md')
    else:
        # TAR keeps .app framework symlinks and executable modes intact.
        if source.is_dir():
            for item in source.rglob('*'):
                if item.is_symlink() and not item.resolve().is_relative_to(source): raise ValueError('Bundle link leaves its folder')
        with tarfile.open(target,'w:gz',dereference=False) as archive:
            archive.add(source,arcname=source.name)
            archive.add(ROOT/'PORTS.md',arcname='PORTS.md')
            archive.add(ROOT/'LICENSE',arcname='LICENSE')
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_name(target.name+'.sha256').write_text(digest+'  '+target.name+'\n','ascii')
    print('Native package:',target)

if __name__ == '__main__': main()
