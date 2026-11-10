# Blender versions in this cloud environment

The upgraded **headless Blender runtime is 5.2.3 LTS**, installed as the official
Blender Foundation `bpy==5.2.3` Python package from PyPI into
`/workspace/tools/blender-5.2.3`. It uses Python 3.13.5, already present in the cloud
image. The wheel and dependency hashes are pinned in
`scripts/blender-runtime-requirements.txt`. No software is needed on your computer.

`/usr/bin/blender` remains the preinstalled **4.3.2 full desktop executable**. The
new runtime is not a replacement GUI executable. Access to the official standalone
binary download host `download.blender.org` was denied by the cloud network policy,
and saving the proposed environment network draft failed. The installed headless
package comes through the allowed official PyPI route with TLS and hash verification.

## Install or refresh

From `/workspace/blender1`:

```sh
scripts/install_blender_runtime.sh
scripts/blender-headless --version
```

The installation script uses a separate virtual environment and leaves the system
Blender installation intact. `STUDIO_RUNTIME_ROOT` can change the install location;
set `STUDIO_BLENDER_PYTHON` to its `bin/python` when running the adapter from that
location. The default paths are for the managed cloud environment.

## Use the upgraded runtime

```sh
python3 -m pipeline --blender ./scripts/blender-headless build \
  --project projects/example_project/scene.json --out artifacts/blender523
python3 -m pipeline --blender ./scripts/blender-headless render \
  --job configs/preview.json --blend artifacts/blender523/scene.blend \
  --out artifacts/blender523/render --allow-cpu-preview
```

`scripts/blender-headless` supports the subset of Blender background flags used by
this repository. It rejects unsupported options. It disables automatic execution
of Python embedded in supplied `.blend` files; explicit `--python` scripts still
execute as requested. It does not offer a desktop interface or the Blender main
event loop needed by the upstream Blender MCP add-on. The MCP cloud desktop keeps
using the full Blender 4.3.2 executable; the MCP startup helper supports selecting
another full executable when one is available.

Keep 5.2 project outputs in separate directories. New `.blend` files are not
assumed backward compatible with 4.3.2. See the Kaggle installer and feasibility
report for its pinned standalone version. Kaggle installation and GPU execution
remain unverified until an authenticated notebook run succeeds.

## Verified in this instance

- `bpy.app.version_string` reports **5.2.3 LTS**.
- A real 16×16 Cycles CPU render succeeded. OpenImageDenoise is compiled into this
  runtime (`_cycles.with_openimagedenoise == True`). This does not establish GPU
  availability.
- The example market scene built and exported a GLB successfully using 5.2.3.
  The scene builder handles both Blender 4.3 legacy action curves and Blender 5
  layered-action curves.
- Example frame 88 rendered at 480×270/8 samples through the existing pipeline
  using 5.2.3, denoising enabled, in approximately 4.5 seconds including scene
  preparation on the shared CPU. It produced a validated checkpoint and PNG.
- A scene saved by Blender 4.3.2 loaded into 5.2.3 and frame 88 rendered at
  480×270/16 samples with denoising, validated checkpoint and PNG. The image was
  visually inspected; the market, waving robot, lights and props appear correctly.
  This shared-CPU run took approximately 7.7 seconds for the frame.
- The compatibility change was also tested by rebuilding the scene with 4.3.2.
- An intentional Python exception returned the requested process exit code 9.
- Evidence files are under `artifacts/upgrade-check/`; the runtime install,
  scene-build and render were executed, not merely documented.

Sources: [official Blender bpy package](https://pypi.org/project/bpy/5.2.3/) and
[official PyPI release metadata](https://pypi.org/pypi/bpy/5.2.3/json), checked
10 November 2026. PyPI's reported latest version was 5.2.3 during this session;
no claim is made that the inaccessible standalone release listing was checked.

Verified Linux wheel: `bpy-5.2.3-cp313-cp313-manylinux_2_28_x86_64.whl`,
SHA256 `8ef4a335930d647233c661ae21be1abf81207af33e1440fc5a4fc2f2f2d44db7`.
