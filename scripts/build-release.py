#!/usr/bin/env python3
"""Build safe source distribution archives without bundling runtime/private files."""
from pathlib import Path
import hashlib
import re
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.search(r"VERSION = '([^']+)'", (ROOT / 'nuvio' / 'core.py').read_text(encoding='utf-8')).group(1)
PREFIX = 'Nuvio-Control-Center'
FILES = (
    '.gitattributes', '.gitignore', 'CHANGELOG.md',
    'CONTRIBUTING.md', 'LICENSE', 'README.md', 'SECURITY.md', 'install.sh', 'uninstall.sh',
    'install-windows.cmd',
    'Dockerfile', 'compose.yaml', '.dockerignore',
)
DIRS = ('docs', 'nuvio', 'web', 'systemd', 'windows', 'scripts', 'tests', '.github', 'macos')
EXCLUDE = ('__pycache__', '.pytest_cache', '.venv', 'venv', 'dist', '.git')


def source_files():
    collected = [ROOT / filename for filename in FILES]
    for directory in DIRS:
        collected += list((ROOT / directory).rglob('*'))
    return sorted((p for p in collected if p.is_file() and not any(
        part in EXCLUDE for part in p.relative_to(ROOT).parts) and p.suffix not in
        ('.pyc','.ipk','.key','.pem','.log','.zip','.gz') and p.name not in ('auth.json','config.json','state.json')),
        key=lambda p: str(p))


def build():
    output_dir = ROOT / 'dist'
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f'{PREFIX}-v{VERSION}'
    paths = source_files()
    if len(paths) < 20:
        raise RuntimeError('Unexpectedly few files; refusing to package incomplete distribution')
    zipped = output_dir / f'{stem}.zip'
    tgz = output_dir / f'{stem}.tar.gz'
    with zipfile.ZipFile(zipped, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in paths:
            rel = path.relative_to(ROOT).as_posix()
            name = PREFIX + '/' + rel
            info = zipfile.ZipInfo.from_file(path, arcname=name)
            info.compress_type = zipfile.ZIP_DEFLATED
            data = path.read_bytes()
            if path.suffix in ('.ps1', '.cmd'):
                # Windows users extracting a ZIP get CRLF like a git checkout would.
                data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if path.suffix == '.sh':
                info.external_attr = (0o100755 << 16)
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with tarfile.open(tgz, 'w:gz') as tar:
        for path in paths:
            rel = path.relative_to(ROOT).as_posix()
            tar.add(path, arcname=PREFIX + '/' + rel, recursive=False)
    checksums = output_dir / f'{stem}-SHA256SUMS.txt'
    with checksums.open('w', encoding='utf-8') as out:
        for item in (zipped, tgz):
            out.write(hashlib.sha256(item.read_bytes()).hexdigest() + '  ' + item.name + '\n')
    print(f'Packaged {len(paths)} public files:')
    print(zipped)
    print(tgz)
    print(checksums)
    return zipped,tgz


if __name__ == '__main__':
    build()
