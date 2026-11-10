"""Run with Blender --background --factory-startup --python-exit-code 1 --python this_file -- --out file.json."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import bpy
from blender.rendering.gpu import configure_gpu

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=Path('gpu-evidence.json'))
parser.add_argument('--backend', choices=['AUTO', 'OPTIX', 'CUDA'], default='AUTO')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
args.out.parent.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.resolution_x = scene.render.resolution_y = 32
scene.render.resolution_percentage = 100
scene.cycles.samples = 1
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(args.out.with_suffix('.png').resolve())
scene.render.threads_mode = 'FIXED'
scene.render.threads = 2
started = time.monotonic()
evidence = {'blender': bpy.app.version_string, 'actual_gpu_render_passed': False, 'attempts': []}
try:
    candidates = ['OPTIX', 'CUDA'] if args.backend == 'AUTO' else [args.backend]
    for backend in candidates:
        attempt = {'backend': backend, 'actual_gpu_render_passed': False}
        try:
            Path(scene.render.filepath).unlink(missing_ok=True)
            configuration = configure_gpu(scene, backend)
            bpy.ops.render.render(write_still=True)
            if not Path(scene.render.filepath).is_file():
                raise RuntimeError('GPU render returned without a frame')
            evidence['configuration'] = configuration
            evidence['actual_gpu_render_passed'] = True
            attempt['actual_gpu_render_passed'] = True
        except Exception as exc:
            attempt['error'] = str(exc)
        evidence['attempts'].append(attempt)
        if evidence['actual_gpu_render_passed']:
            break
    if not evidence['actual_gpu_render_passed']:
        raise RuntimeError('No Cycles GPU backend passed an actual render; CPU fallback is disabled')
except Exception as exc:
    evidence['error'] = str(exc)
    raise
finally:
    evidence['elapsed_seconds'] = round(time.monotonic() - started, 3)
    args.out.write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence, indent=2))
