# Blender MCP in the cloud

Installed from [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp), now named
**MCP for Blender** (`mcp-for-blender` package). This is a third-party integration,
not a Blender Foundation component. Source is pinned at commit
`2e4b0bc294694b1570d76ed01be657c22e6d02a0`, package **2.2.7**, addon **1.8**, addon
protocol **15**. Minimum Blender version declared by this addon is 3.0.

No software is required on the user's Windows computer. The server, Python
virtual environment, addon and virtual display are all inside this cloud machine.

## Verified on this instance

- Installed the GitHub source in `/workspace/tools/blender-mcp` and its server in
  `/workspace/tools/blender-mcp-venv` using verified HTTPS package downloads.
- Installed and enabled the matching addon in an isolated user scripts directory
  `/workspace/tools/blender-user/scripts/addons/blender_mcp.py`.
- Started GUI Blender **4.3.2** on the existing Xorg dummy driver, cloud display `:97`.
  The upstream addon explicitly refuses `blender --background`: its command queue
  needs Blender's GUI event timers. A virtual display supplies this without a local PC.
- Established an actual MCP stdio session, listed **nine tools**, then called
  `get_scene_info`. It returned the generated market's **388 meshes, 23 lights,
  one armature and one camera**. This checks the complete server/addon connection.
- The addon socket listens only at `127.0.0.1:9876`. Xorg TCP listening is disabled.
  Telemetry consent remains false; the stdio wrapper also disables telemetry and
  enables the upstream Python code validator (`BLENDER_MCP_SAFE_MODE=1`).

The newer **headless Blender Python runtime** installed separately is suitable for
batch builds and rendering. It does not replace this GUI executable for MCP; do not
claim that the GUI was upgraded merely because a newer `bpy` wheel is installed.

## Reproduce installation and start

From `/workspace/blender1`:

```sh
bash scripts/install_blender_mcp.sh
python3 scripts/start_blender_mcp.py --scene artifacts/example/scene.blend
/workspace/tools/blender-mcp-venv/bin/python scripts/probe_blender_mcp.py \
  --out artifacts/evidence/blender-mcp.json
```

The install script reuses the pinned source and isolated virtual environment. It
refuses to replace a modified source checkout. Dependencies are pinned in
`scripts/blender-mcp-requirements.txt`. It does not modify the animation repository's
source, a user's local computer, or client configuration.

`start_blender_mcp.py` reuses an already responsive addon without replacing its scene.
For a new process it launches the installed Xorg dummy driver if needed, starts GUI
Blender and confirms a **scene information response**, rather than just an open port.
The default GUI executable is `/usr/bin/blender`; select a later installed GUI binary
with `--blender /absolute/path/blender` or `BLENDER_GUI_BIN`.

Logs and process IDs are under `/workspace/tools/`: `xorg-console.log`,
`xorg-dummy.log`, `blender-mcp-gui.log`, and `blender-mcp-processes.json`. Stop only the
PIDs recorded by your start invocation after checking they still identify its processes.
Live processes need restarting after cloud environment restoration.

## Connect an MCP client

The tested server command is:

```sh
/workspace/blender1/scripts/blender_mcp_server.sh
```

A compatible Codex CLI running **on this cloud host** can register it using:

```sh
codex mcp add blender -- /workspace/blender1/scripts/blender_mcp_server.sh
```

Or supply an equivalent MCP configuration:

```json
{
  "mcpServers": {
    "blender": {
      "command": "/workspace/blender1/scripts/blender_mcp_server.sh"
    }
  }
}
```

This registration was **not applied to the managed Codex chat**. Installing a process
on disk does not dynamically add tools to this conversation; the hosting product must
support connecting that MCP client, generally with a new/reloaded session. The direct
cloud pipeline and tested MCP client probe remain usable now. Do not put a Windows
path in this configuration or expose port 9876 as a public web endpoint.

Asset-generation integrations (Meshy/Hyper3D/Sketchfab/etc.) have separate credentials,
network policies and possible costs; none was enabled or called during setup.
