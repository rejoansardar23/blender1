#!/usr/bin/env bash
set -euo pipefail
studio_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
tools_root="${STUDIO_TOOLS_ROOT:-/workspace/tools}"
mcp_commit=2e4b0bc294694b1570d76ed01be657c22e6d02a0
mkdir -p "$tools_root"
export UV_CACHE_DIR="$tools_root/.uv-cache"
if [ ! -d "$tools_root/blender-mcp/.git" ]; then
  git clone https://github.com/ahujasid/blender-mcp.git "$tools_root/blender-mcp"
fi
actual_commit="$(git -C "$tools_root/blender-mcp" rev-parse HEAD)"
if [ "$actual_commit" != "$mcp_commit" ]; then
  if [ -n "$(git -C "$tools_root/blender-mcp" status --porcelain)" ]; then
    printf '%s\n' 'MCP checkout has local changes; refusing to replace it.' >&2
    exit 1
  fi
  git -C "$tools_root/blender-mcp" fetch origin "$mcp_commit"
  git -C "$tools_root/blender-mcp" checkout --detach "$mcp_commit"
fi
if [ ! -x "$tools_root/blender-mcp-venv/bin/python" ]; then
  uv venv "$tools_root/blender-mcp-venv"
fi
uv pip install --python "$tools_root/blender-mcp-venv/bin/python" -r "$studio_root/scripts/blender-mcp-requirements.txt"
uv pip install --python "$tools_root/blender-mcp-venv/bin/python" --no-deps "$tools_root/blender-mcp"
export BLENDER_MCP_DISABLE_TELEMETRY=1
export XDG_DATA_HOME="$tools_root/data"
"$tools_root/blender-mcp-venv/bin/mcp-for-blender" install-addon --addons-dir "$tools_root/blender-user/scripts/addons"
printf '%s\n' 'Installed pinned MCP server and cloud Blender addon. Start with python3 scripts/start_blender_mcp.py.'
