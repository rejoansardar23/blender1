"""Download official Blender 5.2.3 Linux build and verify its release checksum."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import shutil
import tarfile
import urllib.request

VERSION = '5.2.3'
ARCHIVE = f'blender-{VERSION}-linux-x64.tar.xz'
# Official release URL convention; this exact 5.2.3 URL needs network/runtime validation.
BASE = f'https://download.blender.org/release/Blender{VERSION.rsplit(".", 1)[0]}/'


def digest_file(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def install(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    checksum_text = urllib.request.urlopen(BASE + f'blender-{VERSION}.sha256', timeout=60).read().decode()
    hashes = [line.split()[0] for line in checksum_text.splitlines()
              if len(line.split()) == 2 and line.split()[1].lstrip('*') == ARCHIVE]
    if len(hashes) != 1 or len(hashes[0]) != 64:
        raise RuntimeError('Official checksum manifest has no unique Blender Linux archive entry')
    archive = destination / ARCHIVE
    if not archive.exists() or digest_file(archive) != hashes[0]:
        partial = archive.with_suffix('.partial')
        with urllib.request.urlopen(BASE + ARCHIVE, timeout=120) as response, partial.open('wb') as output:
            shutil.copyfileobj(response, output)
        if digest_file(partial) != hashes[0]:
            partial.unlink(missing_ok=True)
            raise RuntimeError('Blender SHA256 mismatch; refusing to use downloaded artifact')
        partial.replace(archive)
    root = destination / f'blender-{VERSION}-linux-x64'
    # Always extract verified archive; do not trust an unrelated cached executable.
    with tarfile.open(archive) as source:
        for member in source.getmembers():
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise RuntimeError('Archive path escaped installation directory')
        source.extractall(destination, filter='data')
    binary = root / 'blender'
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise RuntimeError('Verified release did not contain executable Blender')
    return binary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=Path('/kaggle/working/tools'))
    args = parser.parse_args()
    print(install(args.destination))
