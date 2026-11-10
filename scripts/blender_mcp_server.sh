#!/usr/bin/env bash
set -euo pipefail
tools_root="${STUDIO_TOOLS_ROOT:-/workspace/tools}"
export BLENDER_MCP_DISABLE_TELEMETRY=1
export BLENDER_MCP_SAFE_MODE=1
export XDG_DATA_HOME="$tools_root/data"
export XDG_CONFIG_HOME="$tools_root/config"
export BLENDERMCP_ADDONS_DIR="$tools_root/blender-user/scripts/addons"
exec "$tools_root/blender-mcp-venv/bin/mcp-for-blender" --host 127.0.0.1 --port 9876
