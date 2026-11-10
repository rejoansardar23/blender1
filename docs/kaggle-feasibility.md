# Kaggle rendering feasibility and evidence

Assessment date: **10 November 2026**. This is a conditional integration with a prepared
notebook, **not a validated Kaggle render**. No Kaggle session has been launched and no
Kaggle GPU result is available from this implementation session.

## What was verified

1. The official Kaggle API documentation supports creating/updating **and running** a
   notebook using `kaggle kernels push -p DIRECTORY`; it supports `--accelerator` and
   `--timeout`. `--no-run` saves code without executing it. Notebook metadata declares
   privacy, GPU/internet requirements and attached dataset sources.
2. The official interface exposes notebook status and downloadable version outputs:
   `kaggle kernels status owner/slug[/version]` and
   `kaggle kernels output owner/slug/version -p DIRECTORY`.
3. Private dataset create/version operations provide the large scene/asset upload route.
   A notebook can attach that dataset; this does not require a persistent SSH server.
4. **Kaggle CLI 2.2.5 installed and its command help executed in Codex Cloud**. Its wheel
   omitted a `six` dependency required on import; `six==1.17.0` is pinned alongside it.
   A writable `KAGGLE_CONFIG_DIR` avoids the read-only home directory here.
5. Seven offline tests pass: staging private GPU metadata/copying the bundle, preserving
   existing stage directories, propagation of subprocess failures, identifier validation,
   compilation of notebook code cells, trusted archive extraction, checksum mismatch refusal
   and archive path escape refusal. These do not exercise the remote API.
6. A read-only `kernels status` request was attempted. The official CLI stopped at
   **Authentication required** before contacting Kaggle. Required token variables are
   absent; both legacy and current credential-file locations are absent. Managed
   environment status declares no Kaggle credential bindings.
7. Direct HTTPS probes to `www.kaggle.com` and `download.blender.org` receive **403 from
   this environment's destination policy**. This establishes a network configuration
   blocker, independently of missing credentials. Official Kaggle source on GitHub
   is accessible.

## What remains unverified

| Question | Evidence-based answer |
|---|---|
| Does this account have GPU time? | Unknown. Check Notebook settings and account usage in Kaggle; API metadata cannot grant entitlement. |
| Which GPU will it receive? | Current official CLI docs name T4 ×2 and L4 plus restricted/admin/competition accelerator types. T4 is a requested default here, never a promised allocation. Do not rely on historical P100 availability. |
| What are the quotas/session lengths? | Account/platform-dependent and subject to change. No live account limits were readable here. Historical “30 GPU hours/week” or “12-hour sessions” must not be treated as current guaranteed allowances. Read the current allocation/session maximum in the browser before each large job. `--timeout` cannot exceed the platform maximum. |
| Can Blender run in a notebook? | Kaggle's official image documentation permits evaluating installation of missing packages. The prepared installer targets official Linux Blender **5.2.3**, matching the upgraded cloud headless runtime. It requires a matching official SHA256 manifest before extraction or execution. The URL follows the established release naming convention; its availability, installation and required shared libraries still need testing on the actual Kaggle image. |
| CUDA or OptiX? | Blender Cycles can use supported NVIDIA hardware/drivers. The job requests GPU only. A **real tiny Cycles render** records the selected backend/device before production rendering. GPU enumeration or `nvidia-smi` alone is insufficient evidence. Actual Kaggle driver/build compatibility remains untested. |
| Is a GPU claimed here? | No. Codex does not expose an NVIDIA GPU; neither Kaggle authentication nor a Kaggle execution session is available. |
| Are notebook Internet/downloads available? | Metadata requests Internet; account policies, restrictions and runtime settings may deny it. Offline execution needs a separately prepared verified Blender dependency dataset. |
| Is rendering permitted by Kaggle rules? | Not established by source-code access. Review the current Kaggle terms, acceptable use and Notebook guidance in your account before spending quota. The implementation does not evade time limits, entitlement or authentication. |

## Supported design

Codex builds and packs a trusted self-contained scene and source bundle. A **private Kaggle
dataset** transports that bundle. The notebook requests an available authorized GPU,
installs verified Blender, performs the GPU smoke render, renders frame checkpoints,
encodes MP4 and writes output/logs under `/kaggle/working`. Kaggle's saved version outputs
are the handoff back to Codex or a browser download.

This is a batch notebook job, not a permanently reachable GPU host, mount, remote shell
or render daemon. Submission can be automated only after authentication, account GPU
entitlement, network permissions and first successful runtime validation. A successful
`kernels push` response would establish submission only, not successful GPU rendering.

## Durability and recovery limits

- Save and run a notebook version to request retained outputs. Live notebook state,
  `/kaggle/working` during an interrupted session, and detached Codex processes are not
  guaranteed durable. Monitor the actual version, retrieve outputs and keep an external copy.
- Within a surviving session, rerun the render cell with the same job for validated
  checkpoint resume. Across expired sessions, first retrieve any retained partial frames
  and job/state metadata, then restore them to the new session's render directory. If no
  partial outputs were retained, those frames must be rerendered.
- `render-artifacts.zip` packages frames and render state; `animation.mp4`, GPU evidence
  and logs are independent files. Retain the archive outside Kaggle before deleting inputs.
- For long films, split frame ranges into bounded jobs below observed session/storage
  limits. Keep scene checksum, exact job configuration, Blender version and asset license
  manifest with every job. Do not run concurrent jobs beyond account policy.

## Alternatives if Kaggle cannot support this workload

An authorized rented GPU VM or a Blender render farm offers a more appropriate durable
batch-render contract for production. Providers such as RunPod, Vast.ai or dedicated
Blender farms need separate credentials, billing, verified CUDA/OptiX support and storage.
None has been provisioned or tested here. Small explicit CPU previews remain available
in Codex; expensive production jobs never fall back silently to CPU.

## Sources and reproduction

Retrieved successfully through the cloud proxy on **2026-11-10**:

- [Official Kaggle CLI/API kernels commands](https://github.com/Kaggle/kaggle-api/blob/main/docs/kernels.md)
  — submission, acceleration, timeout, version status/output. The docs list accelerators
  as of September 2026 and explicitly note restricted types.
- [Official kernel metadata schema](https://github.com/Kaggle/kaggle-api/blob/main/docs/kernels_metadata.md)
  — `enable_gpu`, `enable_internet`, private state and dataset sources.
- [Official dataset commands](https://github.com/Kaggle/kaggle-api/blob/main/docs/datasets.md)
  — private default, create/version/status.
- [Official authentication documentation](https://github.com/Kaggle/kaggle-api/blob/main/docs/README.md#authentication)
  — browser OAuth, API token and legacy credentials.
- [Official Kaggle notebook Docker image project](https://github.com/Kaggle/docker-python)
  — CPU/GPU notebook environments and missing-package installation guidance.
- The official API Git remote HEAD observed during research was
  `fdc788faffe3f29ae317480325c44080a00a5434`.

References **not retrievable in this environment** (policy 403); review in browser:

- [Kaggle Notebook documentation](https://www.kaggle.com/docs/notebooks)
- [Kaggle terms](https://www.kaggle.com/terms)
- [Target Blender 5.2 release directory](https://download.blender.org/release/Blender5.2/)
- [Blender GPU rendering reference](https://docs.blender.org/manual/en/5.2/render/cycles/gpu_rendering.html)

The initial local GPU probe was executed with the preinstalled Blender 4.3.2 and correctly failed with exit 1:
OptiX is absent from this build, and CUDA enumerated only an AMD CPU, which was disabled.
The saved `/tmp/studio-gpu-probe.json` has `actual_gpu_render_passed: false`.
This is a tested GPU-denial gate, **not a Kaggle hardware test**.

After the user requested an upgrade, the cloud headless module was upgraded to official
`bpy==5.2.3` (Blender 5.2 LTS). Its actual CPU smoke render and OIDN denoising passed
in Codex. This verifies that module runtime only: the matching standalone binary URL,
Kaggle dependency installation and Kaggle GPU rendering remain **unverified**. The
Kaggle installer now targets 5.2.3 and still refuses unchecked downloads.

No live quota figure, service-policy approval, GPU allocation, throughput estimate or
end-to-end Kaggle success is inferred from these unvisited references.
