#!/usr/bin/env bash
# Installs official Blender bpy into a cloud-only isolated Python environment.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STUDIO_RUNTIME_ROOT="${STUDIO_RUNTIME_ROOT:-/workspace/tools/blender-5.2.3}"
STUDIO_UV_CACHE="${STUDIO_UV_CACHE:-/workspace/tools/.uv-cache}"
mkdir -p "$STUDIO_UV_CACHE"
export UV_CACHE_DIR="$STUDIO_UV_CACHE"
# The managed image supplies Python 3.13. uv may provision a verified interpreter
# on another supported cloud image. Existing inherited proxy/CA trust is retained.
if [[ ! -x "$STUDIO_RUNTIME_ROOT/bin/python" ]]; then
  uv venv --python 3.13 "$STUDIO_RUNTIME_ROOT"
fi
uv pip install --python "$STUDIO_RUNTIME_ROOT/bin/python" --require-hashes \
  -r "$SCRIPT_DIR/blender-runtime-requirements.txt"
"$STUDIO_RUNTIME_ROOT/bin/python" -c 'import bpy; print("Installed official Blender bpy", bpy.app.version_string); assert bpy.app.version == (5, 2, 3)'
