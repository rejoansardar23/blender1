"""Minimal command adapter for official Blender bpy, not a general Blender CLI.

Supports this studio's documented background pipeline flags. Unsupported flags fail
instead of being silently ignored. GUI, add-on installation CLI, file conversion
CLI and arbitrary Blender flags must use a full Blender executable.
"""
import os
from pathlib import Path
import runpy
import sys
import traceback


def main(argv):
    import bpy
    if argv == ['--version']:
        print(f'Blender {bpy.app.version_string} (official bpy; headless Python runtime)')
        return 0
    arguments = list(argv)
    blend = None
    script = None
    expression = None
    extra = []
    threads = None
    factory = False
    exit_code = 1
    index = 0
    while index < len(arguments):
        arg = arguments[index]
        if arg == '--':
            extra = arguments[index + 1:]
            break
        if arg in ('--background', '-b', '--disable-autoexec'):
            pass
        elif arg == '--factory-startup':
            factory = True
        elif arg in ('--python', '--python-expr', '--threads', '-t', '--python-exit-code'):
            index += 1
            if index >= len(arguments):
                raise ValueError(f'{arg} requires a value')
            value = arguments[index]
            if arg == '--python':
                script = value
            elif arg == '--python-expr':
                expression = value
            elif arg in ('--threads', '-t'):
                threads = int(value)
                if threads < 1 or threads > 1024:
                    raise ValueError('threads must be between 1 and 1024')
            else:
                exit_code = int(value)
                if not 1 <= exit_code <= 255:
                    raise ValueError('python exit code must be 1–255')
        elif not arg.startswith('-') and blend is None:
            blend = str(Path(arg).resolve())
        else:
            raise ValueError(f'Unsupported headless adapter option: {arg}')
        index += 1
    if script is None and expression is None:
        raise ValueError('Specify --python SCRIPT or --python-expr CODE')
    # Never execute embedded Python from a supplied project automatically.
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    if factory:
        bpy.ops.wm.read_factory_settings(use_empty=False)
    if blend:
        bpy.ops.wm.open_mainfile(filepath=blend, use_scripts=False)
    if threads:
        bpy.context.scene.render.threads_mode = 'FIXED'
        bpy.context.scene.render.threads = threads
    sys.argv = [sys.argv[0], '--', *extra]
    print(f'Blender {bpy.app.version_string} (official bpy headless runtime)', flush=True)
    try:
        if script:
            runpy.run_path(script, run_name='__main__')
        if expression:
            exec(expression, {'__name__': '__main__'})
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        return exit_code
    return 0


if __name__ == '__main__':
    try:
        result = main(sys.argv[1:])
    except Exception:
        traceback.print_exc()
        result = 1
    # This is a single-command process: flush output before terminating.
    # Keep the script result as the process exit status.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(result)
