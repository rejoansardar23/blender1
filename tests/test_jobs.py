import copy
import json
from pathlib import Path
import tempfile
import unittest
from pipeline.jobs import load_job, fingerprint, acquire_render_lock
from pipeline.__main__ import encode

ROOT = Path(__file__).resolve().parents[1]


class JobContractTests(unittest.TestCase):
    def setUp(self):
        self.job = json.loads((ROOT / 'configs/kaggle.json').read_text())
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def load(self, value):
        path = self.root / 'job.json'
        path.write_text(json.dumps(value))
        return load_job(path)

    def test_production_device_is_explicit(self):
        self.assertEqual(self.load(self.job)['device'], 'GPU')
        for device in ('auto', '', None):
            self.job['device'] = device
            with self.assertRaises(ValueError):
                self.load(self.job)

    def test_rejects_bad_frame_ranges_and_resolution(self):
        for key, value in [('frame_end', 0), ('frame_start', 200), ('fps', True),
                           ('resolution', [1921, 1080]), ('backend', 'CPU'),
                           ('job_id', '../../other'), ('resume', 'true')]:
            job = copy.deepcopy(self.job)
            job[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.load(job)

    def test_scene_or_settings_changes_invalidate_resume(self):
        blend = self.root / 'scene.blend'
        blend.write_bytes(b'version1')
        first = fingerprint(self.job, blend)
        blend.write_bytes(b'version2')
        self.assertNotEqual(first, fingerprint(self.job, blend))
        blend.write_bytes(b'version1')
        self.job['samples'] += 1
        self.assertNotEqual(first, fingerprint(self.job, blend))

    def test_runtime_changes_invalidate_resume(self):
        blend = self.root / 'scene.blend'
        blend.write_bytes(b'version1')
        self.assertNotEqual(fingerprint(self.job, blend, runtime='4.3.2'),
                            fingerprint(self.job, blend, runtime='5.2.3'))

    def test_concurrent_render_is_rejected_and_lock_releases(self):
        handle = acquire_render_lock(self.root)
        try:
            with self.assertRaisesRegex(RuntimeError, 'already owns'):
                acquire_render_lock(self.root)
        finally:
            handle.close()
        acquire_render_lock(self.root).close()

    def test_encode_rejects_incomplete_and_missing_frames(self):
        frames = self.root / 'frames'
        frames.mkdir()
        state = {'status': 'failed', 'job': self.job, 'completed': {}}
        progress = self.root / 'progress.json'
        progress.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            encode(frames, 24, self.root / 'video.mp4')
        state['status'] = 'complete'
        progress.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, 'frame 1'):
            encode(frames, 24, self.root / 'video.mp4')


if __name__ == '__main__':
    unittest.main()
