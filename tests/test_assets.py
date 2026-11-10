import json
from pathlib import Path
import tempfile
import unittest
from pipeline.asset_manager import cache_asset


class AssetCacheTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.cache = self.root / 'cache'
        self.source = self.root / 'source'
        self.source.mkdir()

    def test_deduplication_and_corruption_detection(self):
        source = self.source / 'model.glb'
        source.write_bytes(b'asset version one')
        first, manifest = cache_asset(source, self.cache)
        second, other = cache_asset(source, self.cache)
        self.assertEqual(first, second)
        self.assertEqual(manifest, other)
        first.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            cache_asset(source, self.cache)

    def test_sidecar_versions_change_asset_identity(self):
        source = self.source / 'model.gltf'
        source.write_text(json.dumps({'buffers': [{'uri': 'mesh.bin'}]}))
        sidecar = self.source / 'mesh.bin'
        sidecar.write_bytes(b'one')
        first, _ = cache_asset(source, self.cache)
        self.assertEqual((first.parent / 'mesh.bin').read_bytes(), b'one')
        sidecar.write_bytes(b'two')
        second, _ = cache_asset(source, self.cache)
        self.assertNotEqual(first, second)

    def test_sidecars_cannot_escape_source_directory(self):
        source = self.source / 'model.gltf'
        (self.root / 'private.bin').write_bytes(b'private')
        for uri in ('../private.bin', 'https://example.com/mesh.bin'):
            source.write_text(json.dumps({'buffers': [{'uri': uri}]}))
            with self.subTest(uri=uri), self.assertRaises(ValueError):
                cache_asset(source, self.cache)


if __name__ == '__main__':
    unittest.main()
