#!/usr/bin/env bash
set -euo pipefail
cd /workspace/blender1
mkdir -p /workspace/tools/.uv-cache
export UV_CACHE_DIR=/workspace/tools/.uv-cache
command -v blender
blender --version
ffmpeg -version
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s kaggle -p test_control.py -v
uv venv --python 3.12 /workspace/tools/kaggle-venv
uv pip install --python /workspace/tools/kaggle-venv/bin/python -r kaggle/requirements.txt
(cd viewer && npm ci --cache /tmp/animation-npm-cache && npm run build)

bash scripts/install_blender_runtime.sh
bash scripts/install_blender_mcp.sh
