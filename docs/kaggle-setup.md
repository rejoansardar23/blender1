# Kaggle setup — no installation on your computer

Start with [the feasibility record](kaggle-feasibility.md). The cloud-only CPU scene/viewer
works independently. **The Kaggle stage has not yet been executed.**

## One-time browser setup

1. Sign in to [Kaggle](https://www.kaggle.com/). Complete any required phone/account
   verification, review current terms and Notebook GPU usage rules, and check the GPU
   availability and remaining quota shown in Notebook settings.
2. For browser-only operation, no Kaggle token is needed in Codex: upload the generated
   `artifacts/render-bundle.zip` to a **private dataset**, create a notebook by importing
   `kaggle/render_notebook.ipynb`, attach the dataset, enable Internet and an available
   NVIDIA GPU, then choose **Save Version → Save & Run All**. A notebook must access only
   assets/code you own or are authorized to use.
3. For Codex/API automation, generate an API token in
   [Kaggle API settings](https://www.kaggle.com/settings/api). Enter it securely as
   `KAGGLE_API_TOKEN` in environment secret settings; **never paste it into chat, project
   files or notebook source**. Allow `www.kaggle.com` and `api.kaggle.com`, then the exact
   upload/download redirect hosts reported by Kaggle if a tested operation requires them.
   `download.blender.org` is needed for Codex to test the official installer; the notebook
   itself downloads that binary from inside Kaggle. A domain allowlist is not authentication.
4. If the proxy supplies tokens only for selected HTTPS destinations, configure the
   credential destination scope for Kaggle's actual API host. The official CLI must use
   that injected binding, not copy it into files. New redirects require network access,
   not permission to send the Kaggle token to arbitrary storage hosts.

The supplied Kaggle username is `rejoansardardd`. The checked-in metadata uses
`rejoansardardd/chai-market-gpu` and private input dataset
`rejoansardardd/chai-market-render`. These names reserve nothing until an authorized
request succeeds. The GitHub username and Kaggle username are independent.

## Cloud commands after authorization

Run from `/workspace/blender1`. The cloud headless runtime uses official `bpy==5.2.3` (Blender 5.2 LTS); the
preinstalled desktop executable remains 4.3.2. Python and FFmpeg are available. The
Kaggle installer targets the matching official standalone **5.2.3** release; its
release-directory URL follows Blender's naming convention and has not been fetched
from this environment because the download host is blocked. Local module rendering
does not establish that the standalone Kaggle binary has installed successfully. Use a virtual environment for the official CLI; no Windows software is needed:

```sh
python3 -m venv /workspace/.venvs/kaggle
/workspace/.venvs/kaggle/bin/python -m pip install -r kaggle/requirements.txt
export PATH="/workspace/.venvs/kaggle/bin:$PATH"
export KAGGLE_CONFIG_DIR=/workspace/.kaggle
```

Build/package using the root README, then stage an owned bundle. Select an appropriate
Kaggle license identifier; `CC0-1.0` below is an example only for content you can release
under that license. A private dataset still needs valid license metadata.

```sh
python3 kaggle/control.py prepare --bundle artifacts/render-bundle.zip \
  --dataset rejoansardardd/chai-market-render \
  --kernel rejoansardardd/chai-market-gpu \
  --license CC0-1.0 --out artifacts/kaggle-stage
python3 kaggle/control.py upload --stage artifacts/kaggle-stage
python3 kaggle/control.py dataset-status rejoansardardd/chai-market-render
```

Wait until the dataset reports ready before submitting. To update an existing dataset,
use `upload --new-version 'Describe the changed scene'` with a freshly staged bundle.
Keep each job's archive SHA256 and actual dataset version; `dataset_sources` by slug
resolves the available dataset version at notebook submission time.

```sh
python3 kaggle/control.py submit --stage artifacts/kaggle-stage \
  --accelerator NvidiaTeslaT4 --timeout 3600
python3 kaggle/control.py status rejoansardardd/chai-market-gpu
```

Submission is a real external job and can consume GPU quota. It is not automatically run
by installation or by reading this document. The default timeout is a requested cap,
subject to the lower platform maximum. The account's actual entitlement decides whether
a requested accelerator can be allocated.

Record the notebook version printed/visible after submission; after it finishes:

```sh
python3 kaggle/control.py output rejoansardardd/chai-market-gpu/VERSION \
  --out artifacts/kaggle-output/VERSION
```

Inspect `gpu-evidence.json` for `actual_gpu_render_passed: true`, the device/backend and
Blender version; confirm completed render progress and validate the MP4. No such Kaggle
GPU evidence exists yet in this repository. Never label a notebook submission or a
successful `nvidia-smi` as proof that Cycles rendered on GPU.

## GitHub Actions (optional controller)

Once source is pushed, add repository Actions secret `KAGGLE_API_TOKEN` through GitHub's
browser settings. `Kaggle render controller` is a manual workflow with separate
`submit`, `status` and `retrieve` operations. Submit references an already uploaded
private dataset; retrieve requires an explicit `owner/slug/version` and publishes output
as a GitHub Actions artifact for browser download. It does not leave a hosted renderer
running, provision a GPU, or guarantee notebook completion. The workflow has been
prepared and reviewed locally but has not run against a Kaggle account.

## Failure and expired-session recovery

- **Authentication required:** check the secure token binding/account and API access;
  do not invent credentials or disable authentication.
- **403 CONNECT / destination denied:** add the precise required hosts in environment
  settings and retry a fresh connection. Do not bypass the proxy or TLS verification.
- **Checksum mismatch:** stop; delete only the failed partial download and retry the
  official manifest/archive after diagnosing transfer/trust problems.
- **No GPU or Cycles backend failure:** inspect the probe output and the account's
  accelerator/driver entitlement. The production job stops; no CPU production fallback.
- **Missing shared library:** retain the Blender error and install that exact distro
  runtime package using the notebook image's package manager with signature checks.
- **GPU quota/session expiration:** retrieve saved partial outputs if available and
  rerun a bounded remaining range in a permitted new session. Do not assume a killed
  session persisted files. Keep matching frame-state metadata when restoring a checkpoint.
- **Internet disabled:** enable Internet if allowed; otherwise prepare a separate
  verified Blender/tools dataset. This offline dependency route is not implemented/tested.
