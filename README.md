# Cloud Animation Studio

A cloud-only Blender production foundation: build a scene, inspect it in WebGL,
render validated frame jobs, encode video, and stage a private Kaggle GPU notebook.
Nothing needs to be installed on your personal computer.

**Current scope:** a working six-second stylized animation prototype, not an automatic
studio-quality movie generator. The Kaggle integration is implemented but awaits an
authenticated GPU run. See [the evidence assessment](docs/kaggle-feasibility.md).

## Blender upgrade and MCP

**Blender 5.2.3 LTS** is installed as the official headless Python runtime, with tested
Cycles rendering and denoising. Select it using `python3 -m pipeline --blender
./scripts/blender-headless ...`. The GUI binary remains 4.3.2; Blender MCP is installed
from pinned GitHub source and tested against that cloud GUI. See [version evidence](docs/blender-version.md)
and [MCP setup](docs/blender-mcp.md). Installing MCP has not dynamically registered
tools in this managed chat.

## Quick start in the cloud

```sh
cd /workspace/blender1
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s kaggle -p test_control.py -v
python3 -m pipeline build --project projects/example_project/scene.json --out artifacts/example
python3 -m pipeline render --job configs/preview.json --blend artifacts/example/scene.blend --out artifacts/example/render --allow-cpu-preview
python3 -m pipeline encode --frames artifacts/example/render/frames --fps 24 --out artifacts/example/preview.mp4
python3 -m pipeline package --project-dir artifacts/example --job configs/kaggle.json --out artifacts/render-bundle.zip
```

The explicit CPU preview is 480×270, 16 samples and 144 frames at 24fps. Production
configuration requests GPU at 1920×1080. A missing GPU stops the job; it never launches
an expensive production CPU fallback. Existing output directories reject changed scenes
or settings. Use a new directory after changing either.

```sh
cd viewer
npm ci --cache /tmp/animation-npm-cache
npm run dev
npm run build
npm run test:browser # Chromium must be available; see viewer/README.md
```

The browser viewer includes the sample GLB and supports orbit/zoom, animation playback
and scrubbing, authored camera selection, local GLB import, images and videos. WebGL uses
review lighting; Blender renders remain the reference. The [Pages workflow](.github/workflows/pages.yml)
is a manual deployment, not evidence that a public site has been deployed.

## Kaggle account handoff

The prepared notebook IDs use **rejoansardardd**. Follow [Kaggle setup](docs/kaggle-setup.md)
for browser authentication, private dataset upload, GPU settings, submission and output
retrieval. No Kaggle credential or GPU allocation is currently available to this task.
Do not put credentials into repository files or chat.

## Layout

- `blender/scene_builder/`: original market, robot rig, animation, camera and lighting.
- `blender/character_tools/`: supplied-asset inspection.
- `blender/rendering/`: real Cycles GPU selection and resumable frame rendering.
- `pipeline/`: validated jobs, independent CLI stages, asset cache/import and basic QC.
- `kaggle/`: official notebook batch integration, checksum-verified installer and GPU probe.
- `viewer/`: Three.js viewer, browser tests and sample media.
- `projects/`, `configs/`: scene breakdown, timing and render presets.
- `docs/`: architecture, setup, rendering, evidence and limitations.
- `scripts/`: cloud setup and delivery helpers.
- `artifacts/`: ignored Blender files, bundles, frames, logs and videos. Keep large production
  assets in private object storage or Kaggle datasets; source Git is not a render archive.

See [architecture](docs/architecture.md), [rendering](docs/rendering-guide.md),
[troubleshooting](docs/troubleshooting.md), and [validation status](docs/status.md).
