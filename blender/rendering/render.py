"""Run via Blender --background --python-exit-code 1 --python render.py -- ..."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import bpy
from pipeline.jobs import load_job, sha256, fingerprint, atomic_json, acquire_render_lock
from blender.rendering.gpu import configure_gpu


def readable_frame(path):
    if not path.is_file() or path.stat().st_size < 64:
        return False
    try:
        image = bpy.data.images.load(str(path), check_existing=False)
        valid = image.size[0] > 0 and image.size[1] > 0
        bpy.data.images.remove(image)
        return valid
    except RuntimeError:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--job', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--allow-cpu-preview', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    job = load_job(args.job)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    render_lock = acquire_render_lock(out)
    frames = out / 'frames'
    frames.mkdir(exist_ok=True)
    scene = bpy.context.scene
    state_path = out / 'progress.json'
    identity = fingerprint(job, bpy.data.filepath, [__file__, ROOT / 'blender/rendering/gpu.py'], runtime=bpy.app.version_string)
    if state_path.exists():
        previous = json.loads(state_path.read_text())
        if previous['fingerprint'] != identity:
            raise RuntimeError('Output belongs to a different job, scene or renderer. Use a new output directory.')
    else:
        previous = {'completed': {}}
        if any(frames.iterdir()):
            raise RuntimeError('Untracked frames exist. Use an empty output directory.')
    scene.render.engine = 'CYCLES'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = job['threads']
    scene.render.resolution_x, scene.render.resolution_y = job['resolution']
    scene.render.resolution_percentage = 100
    scene.render.fps = job['fps']
    scene.render.image_settings.file_format = job['format']
    scene.cycles.samples = job['samples']
    scene.cycles.use_adaptive_sampling = True
    import _cycles
    scene.cycles.use_denoising = bool(getattr(_cycles, 'with_openimagedenoise', False))
    print('DENOISING ' + str(scene.cycles.use_denoising), flush=True)
    scene.cycles.max_bounces = 4
    scene.render.use_file_extension = True
    scene.render.use_persistent_data = True
    scene.frame_start, scene.frame_end = job['frame_start'], job['frame_end']
    report = {'job_id': job['job_id'], 'fingerprint': identity, 'status': 'starting',
              'blender': bpy.app.version_string, 'job': job,
              'completed': previous.get('completed', {}), 'gpu': None}
    atomic_json(state_path, report)
    started = time.monotonic()
    try:
        if job['device'] == 'CPU':
            if not args.allow_cpu_preview or job['resolution'][0] > 960 or job['samples'] > 32:
                raise RuntimeError('CPU only allowed for explicit preview <=960px and <=32 samples. Pass --allow-cpu-preview.')
            scene.cycles.device = 'CPU'
            print('EXPLICIT CPU PREVIEW: no GPU acceleration claimed', flush=True)
        else:
            report['gpu'] = configure_gpu(scene, job['backend'])
            # Real tiny render through the selected GPU before production frames.
            width, height = scene.render.resolution_x, scene.render.resolution_y
            samples = scene.cycles.samples
            scene.render.resolution_x = scene.render.resolution_y = 32
            scene.cycles.samples = 1
            scene.frame_set(job['frame_start'])
            probe_started = time.monotonic()
            bpy.ops.render.render()
            report['gpu'].update(render_verified=True, probe_seconds=time.monotonic() - probe_started)
            scene.render.resolution_x, scene.render.resolution_y = width, height
            scene.cycles.samples = samples
            atomic_json(out / 'gpu-evidence.json', report['gpu'])
            print('GPU_RENDER_VERIFIED ' + json.dumps(report['gpu']), flush=True)
        extension = '.png' if job['format'] == 'PNG' else '.exr'
        report['status'] = 'rendering'
        atomic_json(state_path, report)
        for frame in range(job['frame_start'], job['frame_end'] + 1):
            target = frames / f'{frame:06d}{extension}'
            checkpoint = report['completed'].get(str(frame))
            if (job.get('resume', True) and checkpoint and readable_frame(target)
                    and sha256(target) == checkpoint['sha256']):
                print(f'RESUME {frame}', flush=True)
                continue
            scene.frame_set(frame)
            frame_started = time.monotonic()
            # Write to a temporary name; interrupted renders never become completed frames.
            temporary = frames / f'.{frame:06d}.partial{extension}'
            scene.render.filepath = str(temporary)
            bpy.ops.render.render(write_still=True)
            if not readable_frame(temporary):
                raise RuntimeError(f'Frame {frame} output did not decode')
            temporary.replace(target)
            report['completed'][str(frame)] = {'sha256': sha256(target),
                                               'seconds': time.monotonic() - frame_started}
            report['elapsed_seconds'] = time.monotonic() - started
            atomic_json(state_path, report)
            print('FRAME_COMPLETE ' + json.dumps({'frame': frame, 'total': job['frame_end'] - job['frame_start'] + 1}), flush=True)
        report['status'] = 'complete'
    except Exception as error:
        report.update(status='failed', error=str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic() - started
        atomic_json(state_path, report)


if __name__ == '__main__':
    main()
