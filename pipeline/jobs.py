"""Validated render contracts and content-addressed resume state."""
import hashlib
import json
from pathlib import Path
import re


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_job(path):
    job = json.loads(Path(path).read_text())
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', job.get('job_id', '')):
        raise ValueError('job_id must be 1–80 letters, digits, underscores or hyphens')
    for key in ('samples', 'frame_start', 'frame_end', 'fps', 'threads'):
        if type(job.get(key)) is not int or job[key] < 1:
            raise ValueError(f'{key} must be a positive integer')
    if job['frame_end'] < job['frame_start'] or job['frame_end'] > 1000000:
        raise ValueError('Invalid frame range')
    resolution = job.get('resolution')
    if not isinstance(resolution, list) or len(resolution) != 2 or any(
            type(v) is not int or v < 2 or v > 16384 or v % 2 for v in resolution):
        raise ValueError('resolution must contain two positive even integers <= 16384')
    if job.get('engine') != 'CYCLES' or job.get('device') not in ('GPU', 'CPU'):
        raise ValueError('This renderer supports CYCLES with explicit GPU or CPU device')
    if job.get('backend') not in ('AUTO', 'CUDA', 'OPTIX'):
        raise ValueError('backend must be AUTO, CUDA or OPTIX')
    if job.get('format') not in ('PNG', 'OPEN_EXR'):
        raise ValueError('format must be PNG or OPEN_EXR')
    if type(job.get('resume', True)) is not bool:
        raise ValueError('resume must be boolean')
    return job


def fingerprint(job, blend, renderer_files=(), runtime=None):
    payload = {'job': job, 'blend_sha256': sha256(blend), 'runtime': runtime,
               'renderer': {Path(p).name: sha256(p) for p in renderer_files}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def acquire_render_lock(directory):
    """Hold the returned handle for the entire render; kernel releases on process exit."""
    import fcntl
    handle = open(Path(directory) / '.render.lock', 'a')
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise RuntimeError('A render already owns this output directory') from None
    return handle
