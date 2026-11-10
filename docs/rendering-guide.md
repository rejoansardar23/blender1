# Rendering and recovery

Run commands from `/workspace/blender1`. Blender 4.3.2 and FFmpeg 7.1.5 were available
at the initial validation. Use `python3 -m pipeline --blender PATH ...` to select another
verified executable/runtime. Keep build and render versions compatible. Newer Blender
files are not promised to open in older runtimes.

`configs/presets.json` defines preview, draft, high-quality and cinematic sample budgets.
The tested preview is the explicit job in `configs/preview.json` (16 samples). Samples
and resolution are starting points, not automatic guarantees of publishing quality.
The small local preview is deliberately low resolution and visibly noisy. The installed
4.3.2 build has no OpenImageDenoise; the renderer detects that build capability.

## Render and encode

```sh
python3 -m pipeline render --job configs/preview.json --blend artifacts/example/scene.blend --out artifacts/example/render --allow-cpu-preview
python3 -m pipeline encode --frames artifacts/example/render/frames --fps 24 --out artifacts/example/preview.mp4
```

Repeat the identical render command to resume. `progress.json` must match scene/settings/
renderer hashes. Modify settings in a copied JSON and choose a new directory. Do not
fabricate completion markers or move arbitrary frames under an old checkpoint. Encoder
requires the complete expected frame range and matching hashes; it checks MP4 frame count
with ffprobe. `--audio path.wav` optionally adds supplied dialogue/music. No audio asset
was provided, so the demo is silent.

For GPU jobs, probe OptiX/CUDA using the notebook's actual tiny render before rendering
the full sequence. A detected GPU is insufficient. CPU device entries are disabled.
The notebook records the backend that actually succeeded and pins it in its render job.
On failure, retain `gpu-evidence.json` and logs; do not enable CPU for a production job.

## Validate assets and scene

```sh
python3 -m pipeline.asset_manager cache your-character.glb --cache artifacts/assets
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python pipeline/asset_manager.py -- import your-character.glb --out artifacts/imported.blend
blender -b artifacts/example/scene.blend --disable-autoexec --python-exit-code 1 --python pipeline/scene_validator.py -- --out artifacts/example/scene-validation.json
```

Asset import supports .blend, GLB/glTF, FBX and OBJ; inspect untrusted assets and their
licenses before use. This is import and QC, not automatic professional rigging.
See tool `--help` for separate character inspection. External Blender Python autoexecution
is disabled. Generated trusted scripts still have Python execution authority.
