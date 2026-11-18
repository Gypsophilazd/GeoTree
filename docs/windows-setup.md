# Windows with WSL2

Use Windows 10/11 with WSL2 Ubuntu and Docker Desktop in Linux containers mode with integration enabled for that distro. Install uv inside Ubuntu (for example via pipx), and make sure it is on PATH. Python 3.12 is selected by uv; native Windows Python 3.12+ is only needed for direct unit/relay checks. Harbor 0.23.0 is installed from the Linux hash lock. FreeCAD 1.1.0 is in the dedicated Linux smoke image, not the Windows Python environment.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\doctor.ps1 -Distro Ubuntu
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -Distro Ubuntu -BuildSmokeImage
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1 -Distro Ubuntu
```

Omit `-BuildSmokeImage` when reusing a compatible cached image. In WSL, use `GEOTREE_SMOKE_IMAGE=<local ID or tag> bash scripts/smoke-linux.sh`. The standalone test uses a read-only repository mount, network none, CPU2, 4 GiB, no GPU, and temporary CAD. A second, synthetic Harbor check is `bash scripts/smoke-harbor.sh` and accepts `GEOTREE_HARBOR_SMOKE_IMAGE=<local tag>`. It records test evidence in a new temporary folder and disables grading. It uses Harbor's actual factory and orchestration with a synthetic mailbox, not Codex. The image build fetches FreeCAD but does not download a benchmark. `-PythonOnly` skips Docker.

If a mounted Windows path causes performance or permission issues, put a separate checkout in the WSL Linux filesystem for dependencies and Docker, and use only a shared Windows-drive path for the mailbox. Use a private local directory, not a sync service. `wsl -l -v` must show the distro with version 2. Test `docker info` inside that same distro.

## Optional authorized Harbor task

Run only with explicit authorization for model calls and with an independently authorized **single** local Harbor task directory. Benchmark acquisition, credentials, private scorer bundles and task identity are operator-managed, not shipped. Verify the task digest via its upstream registry, the expected instruction hash, the actual image identities/runtime configuration, network disabled for the contestant, CPU 2/RAM 4096 MiB/GPU 0, no Docker socket/credential mounts, and a separate verifier before permitting live actions. The checked-in native Dockerfile documents the historical build input; it requires its legitimate upstream license context and is not used for the synthetic smoke. Do not treat a smoke image as a benchmark-native identity.

For example, with a private shared location accessible on both sides (adjust drive/distro), in WSL:

```bash
export GEOTREE_RUN_ROOT=/mnt/d/private-geotree-mailbox
export GEOTREE_INSTRUCTION_SHA256='<expected SHA256 of upstream public instruction>'
task='/absolute/linux/path/to/authorized/single/task'
id=l-0123456789abcdef-l0   # use a new 16-hex pair prefix for each authorized evaluation
deadline=$(($(date +%s)+1200))
bash scripts/run-arm.sh --check-only "$id" "$deadline" "$task"
```

For a new authorized live stage refresh the deadline. On the trusted Windows host, configure your own Codex CLI and check its login status independently (no copying auth.json); then use the **same** deadline, ID and matching shared directory path:

```powershell
$env:GEOTREE_SHARED_RUN_ROOT = 'D:\private-geotree-mailbox'
$env:GEOTREE_L_RUN_APPROVED = 'EXPLICIT_PAIR_APPROVAL'
$trial = 'l-0123456789abcdef-l0'
$deadline = Read-Host 'Enter the WSL Unix deadline'
$evidence = Join-Path $env:GEOTREE_SHARED_RUN_ROOT "$trial-windows"
py -3.13 .\bridge\windows\relay.py $trial $evidence $deadline
```

In WSL, only after the actual checks and explicit approval:

```bash
export GEOTREE_L_RUN_APPROVED=EXPLICIT_PAIR_APPROVAL
export GEOTREE_SEPARATE_VERIFIER_CONFIRMED=YES
bash scripts/run-arm.sh "$id" "$deadline" "$task"
```

The launcher runs the same entry for L0 (raw) and L1 (enhanced), with ABI gate, result checks and a single-attempt reservation; L1 requires a successful matching L0. Reserve a new private run root only for a separate authorized experiment, never to bypass a failure. Run corresponding L1 only when authorized. No upload option is used. The CLI flag `--check-only` validates ABI, public instruction hash and declared limits only; it does not certify runtime images or actual mounts. Relay is an opt-in appliance for own-account Codex, with schema and event controls, not a substitute for host isolation. For the historical drawing arm, the same relay recognizes `f2-<16 hex>-a0/a1` and the fixed public `drawing.png` under its `f2` mailbox; the historical PairedAgent expects the original public drawing task. Generic providers can integrate using the Python ModelProvider or JSON transport, not via an undocumented API.
