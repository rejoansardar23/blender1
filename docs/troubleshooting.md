# Troubleshooting

- **Kaggle authentication required:** add a supported API token securely in cloud environment
  settings or the GitHub Actions secret described in Kaggle setup. Never commit it. Username
  `rejoansardardd` is an identifier, not authentication.
- **Proxy CONNECT403:** current cloud egress denies Kaggle and the official Blender binary
  download. Needed domains include `www.kaggle.com`, `api.kaggle.com`, `kaggle.com`,
  `storage.googleapis.com`, `download.blender.org`; `api.github.com` is needed for API-based
  Pages control. Preserve existing network rules in environment settings.
- **No GPU:** the local Codex machine has none exposed. The GPU-only probe must fail.
  An explicit small CPU preview is supported; no claim of GPU acceleration follows.
- **OptiX fails:** notebook probe tries an actual CUDA render next. If both fail, inspect
  driver/runtime evidence instead of changing the job to CPU.
- **Unsupported denoiser:** local Blender4.3.2 lacks OpenImageDenoise. The renderer detects
  it and disables denoising; use more samples or a verified official build for final quality.
- **Different job fingerprint:** a scene, settings or renderer changed. Choose a new output
  directory; this prevents mixing inconsistent images into one video.
- **Expired Kaggle session:** retrieve any saved version outputs first, restore matching
  state/frames to the next session, rerun the same job. Lost unsaved frames must rerender.
- **Viewer looks different:** exported area lights, color transforms and Cycles shadows do
  not transfer perfectly to glTF. Review lighting is normalized in WebGL; final media is
  rendered by Blender.
- **No public viewer URL:** enable GitHub Pages with Actions as source, then run the manual
  Publish browser viewer workflow on the implementation branch. Deployment must succeed
  before an HTTPS URL can be reported as live.
- **Environment configuration save fails:** this task's configuration service returned
  INVALID_ARGUMENT on reads and a save attempt. Repository setup scripts remain reviewable,
  but they are not proof that environment draft fields were saved or published.
