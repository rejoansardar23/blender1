"""Copy tested demo outputs into static viewer assets; never copies arbitrary job outputs."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'artifacts/example'
target = ROOT / 'viewer/public/demo'
state = json.loads((source / 'render/progress.json').read_text())
if state['status'] != 'complete':
    raise SystemExit('Complete the preview render before publishing demo media')
target.mkdir(parents=True, exist_ok=True)
for src, name in [(source / 'scene.glb', 'scene.glb'), (source / 'preview.mp4', 'preview.mp4'),
                  (source / 'render/frames/000088.png', 'poster.png')]:
    shutil.copy2(src, target / name)
print('Copied sample GLB, MP4 and poster to viewer/public/demo; no remote deployment performed')
