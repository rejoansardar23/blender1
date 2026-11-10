"""Start GUI Blender on a cloud virtual display; its addon needs GUI event timers."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def probe():
    try:
        with socket.create_connection(('127.0.0.1', 9876), timeout=2) as connection:
            connection.settimeout(4)
            connection.sendall(b'{"type":"get_scene_info","params":{}}')
            data = b''
            while True:
                data += connection.recv(65536)
                try:
                    result = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if result.get('status') == 'success':
                    return result
                return None
    except (OSError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', default=os.environ.get('BLENDER_GUI_BIN', '/usr/bin/blender'))
    parser.add_argument('--scene', type=Path)
    parser.add_argument('--tools', type=Path, default=Path('/workspace/tools'))
    args = parser.parse_args()
    tools = args.tools.resolve()
    tools.mkdir(parents=True, exist_ok=True)
    current = probe()
    if current:
        print('Existing cloud Blender MCP responded to get_scene_info; leaving its scene unchanged.')
        return
    env = dict(os.environ)
    env.update(DISPLAY=':97', XDG_CONFIG_HOME=str(tools / 'config'),
               XDG_DATA_HOME=str(tools / 'data'), XDG_CACHE_HOME=str(tools / 'cache'),
               BLENDER_USER_SCRIPTS=str(tools / 'blender-user/scripts'),
               BLENDERMCP_NO_UPDATE_CHECK='1', BLENDER_MCP_DISABLE_TELEMETRY='1')
    display_ready = subprocess.run(['xdpyinfo', '-display', ':97'], env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    started = {}
    if not display_ready:
        xorg = shutil.which('Xorg') or '/usr/lib/xorg/Xorg'
        with open(tools / 'xorg-console.log', 'a') as log:
            process = subprocess.Popen([xorg, ':97', '-config', str(ROOT / 'scripts/blender_mcp_xorg.conf'),
                                        '-logfile', str(tools / 'xorg-dummy.log'), '-nolisten', 'tcp', '-noreset'],
                                       env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        started['xorg_pid'] = process.pid
        for attempt in range(30):
            if subprocess.run(['xdpyinfo', '-display', ':97'], env=env, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0:
                break
            if process.poll() is not None:
                raise RuntimeError('Virtual display failed; see /workspace/tools/xorg-console.log')
            time.sleep(0.2)
        else:
            raise RuntimeError('Virtual display did not become ready')
    command = [args.blender, '--disable-autoexec', '--threads', '1']
    if args.scene:
        command.append(str(args.scene.resolve()))
    command += ['--python-exit-code', '1', '--python', str(ROOT / 'scripts/enable_blender_mcp.py')]
    with open(tools / 'blender-mcp-gui.log', 'a') as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
    started['blender_pid'] = process.pid
    (tools / 'blender-mcp-processes.json').write_text(json.dumps(started, indent=2))
    # First software-GL shader compilation can be slow. Probe functional scene response.
    for attempt in range(120):
        if probe():
            print('Cloud Blender MCP ready: get_scene_info succeeded at 127.0.0.1:9876')
            return
        if process.poll() is not None:
            raise RuntimeError('GUI Blender exited; see /workspace/tools/blender-mcp-gui.log')
        time.sleep(0.5)
    raise RuntimeError('Blender scene response not ready; see /workspace/tools/blender-mcp-gui.log')


if __name__ == '__main__':
    main()
