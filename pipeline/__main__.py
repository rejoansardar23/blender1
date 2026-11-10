"""Independent, repeatable build/render/encode/package stages."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from pipeline.jobs import atomic_json, load_job, sha256

ROOT = Path(__file__).resolve().parents[1]


def run(command, log=None):
    print('+ ' + ' '.join(map(str, command)), flush=True)
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        with open(log, 'w') as stream:
            process = subprocess.Popen(list(map(str, command)), stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                stream.write(line)
                stream.flush()
                print(line, end='', flush=True)
            if process.wait():
                raise subprocess.CalledProcessError(process.returncode, command)
    else:
        subprocess.run(list(map(str, command)), check=True)


def encode(frames, fps, output, audio=None):
    frames, output = Path(frames), Path(output)
    progress = frames.parent / 'progress.json'
    if not progress.is_file():
        raise ValueError('Missing progress.json: only validated render outputs can be encoded')
    state = json.loads(progress.read_text())
    if state.get('status') != 'complete':
        raise ValueError('Render is incomplete; resume it before encoding')
    job = state['job']
    if fps != job['fps']:
        raise ValueError('FPS differs from render job; explicitly retime in editing instead')
    if job['format'] != 'PNG':
        raise ValueError('EXR needs a color-managed display conversion before H.264 encoding')
    for number in range(job['frame_start'], job['frame_end'] + 1):
        path = frames / f'{number:06d}.png'
        record = state['completed'].get(str(number))
        if not path.is_file() or not record or sha256(path) != record['sha256']:
            raise ValueError(f'Missing or modified frame {number}; resume the render')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.stem + '.partial.mp4')
    count = job['frame_end'] - job['frame_start'] + 1
    command = ['ffmpeg', '-v', 'error', '-y', '-framerate', str(fps), '-start_number',
               str(job['frame_start']), '-i', str(frames / '%06d.png')]
    if audio:
        command += ['-i', str(audio)]
    command += ['-frames:v', str(count), '-c:v', 'libx264', '-crf', '20',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    if audio:
        command += ['-af', 'apad', '-c:a', 'aac', '-t', str(count / fps)]
    command += [str(temporary)]
    run(command)
    probe = subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams',
                                     'v:0', '-show_entries', 'stream=nb_read_frames,width,height,r_frame_rate',
                                     '-of', 'json', str(temporary)], text=True)
    metadata = json.loads(probe)['streams'][0]
    if int(metadata['nb_read_frames']) != count:
        raise ValueError('Encoded frame count does not match render job')
    temporary.replace(output)
    atomic_json(output.with_suffix('.metadata.json'), metadata)


def package(project, job_path, output):
    project, output = Path(project).resolve(), Path(output).resolve()
    job = load_job(job_path)
    if not (project / 'scene.blend').is_file():
        raise ValueError('Build scene.blend first')
    output.parent.mkdir(parents=True, exist_ok=True)
    files = {}
    for directory in ('pipeline', 'blender', 'kaggle'):
        for path in (ROOT / directory).rglob('*.py'):
            if '__pycache__' not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = path
    files['project/scene.blend'] = project / 'scene.blend'
    job_text = json.dumps(job, indent=2)
    manifest = {name: sha256(path) for name, path in files.items()}
    manifest['job.json'] = hashlib.sha256(job_text.encode()).hexdigest()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, path in files.items():
            archive.write(path, name)
        archive.writestr('job.json', job_text)
        archive.writestr('manifest.json', json.dumps(manifest, indent=2))
    atomic_json(output.with_suffix('.sha256.json'), {'file': output.name, 'sha256': sha256(output)})
    print(f'Bundle created: {output} ({output.stat().st_size} bytes)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', default=os.environ.get('BLENDER_BIN', 'blender'))
    commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('build')
    build.add_argument('--project', required=True)
    build.add_argument('--out', required=True)
    render = commands.add_parser('render')
    render.add_argument('--job', required=True)
    render.add_argument('--blend', required=True)
    render.add_argument('--out', required=True)
    render.add_argument('--allow-cpu-preview', action='store_true')
    video = commands.add_parser('encode')
    video.add_argument('--frames', required=True)
    video.add_argument('--fps', type=int, required=True)
    video.add_argument('--out', required=True)
    video.add_argument('--audio')
    bundle = commands.add_parser('package')
    bundle.add_argument('--project-dir', required=True)
    bundle.add_argument('--job', required=True)
    bundle.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.command == 'build':
        out = Path(args.out).resolve()
        out.mkdir(parents=True, exist_ok=True)
        run([args.blender, '--background', '--factory-startup', '--disable-autoexec', '--threads', '4',
             '--python-exit-code', '1', '--python', ROOT / 'blender/scene_builder/build_scene.py',
             '--', '--config', Path(args.project).resolve(), '--blend', out / 'scene.blend',
             '--glb', out / 'scene.glb'], out / 'build.log')
        if not (out / 'scene.blend').is_file() or not (out / 'scene.glb').is_file():
            raise ValueError('Builder did not produce required outputs')
    elif args.command == 'render':
        load_job(args.job)
        out = Path(args.out).resolve()
        extra = ['--allow-cpu-preview'] if args.allow_cpu_preview else []
        run([args.blender, '--background', '--disable-autoexec', Path(args.blend).resolve(), '--threads', '4',
             '--python-exit-code', '1', '--python', ROOT / 'blender/rendering/render.py',
             '--', '--job', Path(args.job).resolve(), '--out', out, *extra], out / 'render.log')
    elif args.command == 'encode':
        encode(args.frames, args.fps, args.out, args.audio)
    elif args.command == 'package':
        package(args.project_dir, args.job, args.out)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
