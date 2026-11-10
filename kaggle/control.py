"""Cloud-side staging and official Kaggle CLI controller; never assumes successful jobs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
IDENTITY = re.compile(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$')


def identity(value):
    if not IDENTITY.fullmatch(value):
        raise argparse.ArgumentTypeError('Expected owner/slug containing letters, numbers, _ or -')
    return value


def prepare(bundle, dataset, kernel, out, license_name):
    bundle = Path(bundle)
    out = Path(out)
    if not bundle.is_file():
        raise ValueError('Build the render bundle before staging')
    if out.exists():
        raise ValueError('Staging path already exists; choose a new directory to preserve prior jobs')
    data = out / 'dataset'
    code = out / 'kernel'
    data.mkdir(parents=True)
    code.mkdir()
    shutil.copy2(bundle, data / 'render-bundle.zip')
    (data / 'dataset-metadata.json').write_text(json.dumps({
        'id': dataset, 'title': dataset.split('/')[1].replace('-', ' ').title(),
        'licenses': [{'name': license_name}],
    }, indent=2) + '\n')
    metadata = json.loads((HERE / 'kernel-metadata.json').read_text())
    metadata['id'] = kernel
    metadata['title'] = kernel.split('/')[1].replace('-', ' ').title()
    metadata['dataset_sources'] = [dataset]
    (code / 'kernel-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    shutil.copy2(HERE / 'render_notebook.ipynb', code / 'render_notebook.ipynb')
    print(f'Prepared private dataset and GPU notebook in {out}')
    print('Upload dataset, wait for dataset readiness, then submit the GPU notebook.')


def run(*args):
    cli = shutil.which('kaggle')
    if not cli:
        raise RuntimeError('Install cloud CLI: python3 -m pip install -r kaggle/requirements.txt in an isolated environment')
    # Let the official CLI handle supported token/OAuth/legacy authentication.
    subprocess.run([cli, *map(str, args)], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--dataset', type=identity, required=True)
    p.add_argument('--kernel', type=identity, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--license', required=True, help='Kaggle license identifier; confirm asset rights first')
    p = sub.add_parser('upload')
    p.add_argument('--stage', type=Path, required=True)
    p.add_argument('--new-version', help='Version notes for an existing dataset; default creates private dataset')
    p = sub.add_parser('submit')
    p.add_argument('--stage', type=Path, required=True)
    p.add_argument('--accelerator', default='NvidiaTeslaT4')
    p.add_argument('--timeout', type=int, default=3600)
    p = sub.add_parser('dataset-status')
    p.add_argument('dataset', type=identity)
    p = sub.add_parser('status')
    p.add_argument('kernel', help='owner/slug or owner/slug/version')
    p = sub.add_parser('output')
    p.add_argument('kernel', help='Pin owner/slug/version for reproducible output retrieval')
    p.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == 'prepare':
            prepare(args.bundle, args.dataset, args.kernel, args.out, args.license)
        elif args.action == 'upload':
            directory = args.stage / 'dataset'
            if args.new_version:
                run('datasets', 'version', '-p', directory, '-m', args.new_version)
            else:
                run('datasets', 'create', '-p', directory)
        elif args.action == 'submit':
            if args.timeout <= 0:
                raise ValueError('Timeout must be positive')
            run('kernels', 'push', '-p', args.stage / 'kernel', '--accelerator', args.accelerator,
                '--timeout', args.timeout)
        elif args.action == 'dataset-status':
            run('datasets', 'status', args.dataset)
        elif args.action == 'status':
            run('kernels', 'status', args.kernel)
        elif args.action == 'output':
            run('kernels', 'output', args.kernel, '-p', args.out)
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
