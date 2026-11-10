"""Offline tests; no Kaggle account or hardware assertions."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('studio_kaggle_control', HERE / 'control.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class StagingTests(unittest.TestCase):
    def test_private_metadata_and_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            bundle = directory / 'bundle.zip'
            bundle.write_bytes(b'fixture')
            stage = directory / 'stage'
            control.prepare(bundle, 'alice/demo-assets', 'alice/demo-render', stage, 'CC0-1.0')
            metadata = json.loads((stage / 'kernel/kernel-metadata.json').read_text())
            self.assertIs(metadata['is_private'], True)
            self.assertIs(metadata['enable_gpu'], True)
            self.assertEqual(metadata['dataset_sources'], ['alice/demo-assets'])
            self.assertEqual((stage / 'dataset/render-bundle.zip').read_bytes(), b'fixture')
            with self.assertRaises(ValueError):
                control.prepare(bundle, 'alice/demo-assets', 'alice/demo-render', stage, 'CC0-1.0')

    def test_subprocess_failure_propagates(self):
        import subprocess
        with patch.object(control.shutil, 'which', return_value='/fake/kaggle'):
            with patch.object(control.subprocess, 'run', side_effect=subprocess.CalledProcessError(2, 'kaggle')):
                with self.assertRaises(subprocess.CalledProcessError):
                    control.run('kernels', 'status', 'alice/demo')

    def test_notebook_cells_compile(self):
        notebook = json.loads((HERE / 'render_notebook.ipynb').read_text())
        for index, cell in enumerate(notebook['cells']):
            if cell['cell_type'] == 'code':
                compile(''.join(cell['source']), f'cell-{index}', 'exec')

    def test_reject_invalid_identity(self):
        import argparse
        for value in ['https://kaggle.com/owner/repo', '../file', 'owner/slug;anything']:
            with self.assertRaises(argparse.ArgumentTypeError):
                control.identity(value)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('studio_blender_install_test', HERE / 'setup/install_blender.py')
        self.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.installer)

    def make_archive(self, filename=None):
        import io, tarfile
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:xz') as archive:
            member = tarfile.TarInfo(filename or f'blender-{self.installer.VERSION}-linux-x64/blender')
            content = b'fake executable used only as installer test fixture'
            member.size = len(content)
            member.mode = 0o755
            archive.addfile(member, io.BytesIO(content))
        return buffer.getvalue()

    def responses(self, archive, checksum=None):
        import io, hashlib
        expected = checksum or hashlib.sha256(archive).hexdigest()
        manifest = f'{expected}  {self.installer.ARCHIVE}\n'.encode()
        return lambda url, timeout: io.BytesIO(manifest if url.endswith('.sha256') else archive)

    def test_installer_verifies_and_extracts(self):
        archive = self.make_archive()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(self.installer.urllib.request, 'urlopen', side_effect=self.responses(archive)):
                binary = self.installer.install(Path(tmp))
                self.assertEqual(binary.name, 'blender')
                self.assertTrue(binary.is_file())

    def test_installer_rejects_checksum_mismatch(self):
        archive = self.make_archive()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(self.installer.urllib.request, 'urlopen', side_effect=self.responses(archive, '0' * 64)):
                with self.assertRaisesRegex(RuntimeError, 'SHA256 mismatch'):
                    self.installer.install(Path(tmp))
                self.assertFalse((Path(tmp) / f'blender-{self.installer.VERSION}-linux-x64/blender').exists())

    def test_installer_rejects_archive_escape(self):
        archive = self.make_archive('../outside-blender')
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(self.installer.urllib.request, 'urlopen', side_effect=self.responses(archive)):
                with self.assertRaisesRegex(RuntimeError, 'escaped'):
                    self.installer.install(Path(tmp))


if __name__ == '__main__':
    unittest.main()
