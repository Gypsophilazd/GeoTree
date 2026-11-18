# GeoTree E01 · P0 执行报告

日期：2026-11-12（Asia/Singapore）  
执行位置：Windows → SSH `gypsophila-tailscale` → `/home/gypsophila/geotree`  
依据：`docs/E00_audit.md`、`docs/E01_next_steps.md` 与 E00 锁定的 Harbor v0.23.0 源码提交 `1e5c5c6db929a10a140d05e606882c671ae20729`。

**结论：P0 未完成。隔离工具链、官方数据集核验与单题预检通过；真实试跑停在 Docker 镜像构建之前。未获得任何评分，也未开始 BaseAgent。**

| 检查项 | 状态 | 实际证据 |
|---|---|---|
| 开题文档 `docs/proposal_v0.2.md` | **BLOCKED** | 远程目标路径不存在；在远程 GeoTree 目录、Windows Codex 工作区和本对话所用附件目录范围内按原始文件名/关键字查找，未找到可读原件。未创建占位文档，未用 E00 Prompt 代替原件。 |
| 项目内 uv、Harbor | **PASS** | uv 0.13.7，Harbor 0.23.0，系统解释器 Python 3.12.3。91 个 Harbor 及依赖 wheel 校验哈希后离线安装；`uv pip check` 输出 `All installed packages are compatible`，`harbor --version` 输出 `0.23.0`。 |
| V3 数据集与单题包 | **PASS** | Harbor 匿名元数据返回 100 题、0 个数据集级文件，digest 与 E00 一致。选中 `gnucleus-ai/freecad-6b54209a13`，对象元数据大小 1,821,079 B；只下载该任务，Harbor 输出 `Successfully downloaded 1 task(s)`。 |
| Docker 权限及镜像预检 | **PASS（部分）** | 当前用户可访问 Docker 29.1.3、Compose 2.40.3；目标 base 不在本机缓存。从 Docker Hub 读取并按 SHA-256 验证 manifest；未拉取镜像。 |
| 单题 Harbor 配置预检 | **PASS** | Harbor 0.23.0 返回 `Dry run OK — 1 trial(s); nothing was run.`，退出 0。官方 CLI 明确标注仅验证配置/元数据，不执行任务。 |
| 真实单题 nop smoke | **BLOCKED / NOT_RUN** | 官方单题没有给出两个最终预构建镜像；需要从两个 Dockerfile 构建。已核实公共基础层大小，但尚未核实完整依赖下载量及构建占用，且构建会写入共享 Docker 存储。未启动构建、容器或 verifier；真实 trial 输出 0 个。 |
| 最小 Harbor BaseAgent、轨迹与模型契约 | **NOT_RUN** | 真实 nop smoke 是前置条件，未启动。无 ATIF、无 LLM 请求、无费用、无完整 Benchmark、无公开上传。 |

## 已核验的下载与权限

- 项目可写，未执行 sudo、未改系统 Python 或其他项目；Docker 默认 context 使用本机 daemon，存储根 `/var/lib/docker`，驱动 `overlayfs`。项目盘剩余约 1.4T；可用空间充足不等于已经批准共享构建。未清理、重启或修改已有 Docker 对象。
- 工具先查询公开 PyPI 元数据：uv wheel 17,202,345 B；Harbor 0.23.0 wheel 2,142,100 B，包含在 91 个 wheel 的合计 91,096,755 B 中。依赖按 Linux x86_64/CPython 3.12 选择，按锁文件的 SHA-256 和声明长度验证后离线安装；uv + wheel 正文合计 108,299,100 B，不含少量元数据请求。依赖环境、cache、下载、临时 HOME 均落在项目的 `work/e01-p0/`。
- 数据集 `gnucleus-ai/cad-bench@v3` 的确切 digest：`sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`。任务 digest：`sha256:741b7289accd15447a3a2ea1a7ffa21853fcafa07aa4a08b2d592a9877c3f2d9`；下载缓存位于项目内 `work/e01-p0/home/.cache/harbor/tasks/`。无需个人登录。
- 任务声明 schema 1.3、`[verifier].environment_mode="separate"`、verifier 600 秒、agent 9,000 秒且运行阶段 `no-network`；声明收集 `/app/answer.py` 与 `/app/answer.FCStd`。这证明独立 verifier 是**配置要求**，不证明已启动。
- agent 与 verifier 共用 `condaforge/miniforge3@sha256:7de9956cd783d48955835e61b8d212c26b2df901d5a5be8217bd58fb6c1bd5a4`。实查 Linux/amd64 manifest digest 为 `sha256:a3eb8ae8c3866dfa622e9293eb18f39252936d88b3073b084dd9d48e1ddf53d5`，压缩层 29,732,978 + 140,418,378 = **170,151,356 B（约 162.3 MiB）**，config 3,689 B。**这不是全部镜像/依赖下载大小**。
- agent Dockerfile 另解算 FreeCAD 1.1.0、NumPy、SciPy、Node.js、Git、APT OCR 与 Python 依赖；verifier Dockerfile 另解算 FreeCAD、OCP、APT 及 `gnucleus-freecad-validator[render]==0.6.0` 等。两个构建的传输量、解包峰值与去重收益都未测；任务声明的 10,240 MB 是环境资源请求，不是构建下载上限。项目 PATH 未找到 conda/mamba 可用于当前环境原样解算。按“安装与下载前先核对实际大小和权限”停在这里。

## 实际命令和原始日志

所有路径以下均以 `/home/gypsophila/geotree/work/e01-p0` 为基准。脚本使用项目内 HOME/XDG/TMP；Harbor 命令通过 `env -i` 的 `isolated.sh` 执行，未继承用户凭据。

| 已执行操作 | 可复现命令或脚本 | 原始证据 |
|---|---|---|
| uv 准备与依赖解析 | `bash -x prepare-tools.sh`；`python3 wheel-plan.py` | `logs/package-metadata.log`、`logs/prepare-tools.log`、`logs/wheel-plan.log`、`requirements.lock`、`wheel-plan.json` |
| Harbor 安装、版本、兼容性检查 | `env -i PATH=/usr/local/bin:/usr/bin:/bin LANG=C.UTF-8 bash -x install-tools.sh` | `logs/install-tools.log`、`logs/harbor-run-help.log`、`logs/final-state.log` |
| 官方 V3 和任务对象大小 | `timeout 90 bash isolated.sh .venv/bin/python dataset-preflight.py` → 退出 0 | `logs/dataset-preflight.log`、`selected.json` |
| 单题包 | `bash isolated.sh .venv/bin/harbor task download gnucleus-ai/freecad-6b54209a13@sha256:741b7289accd15447a3a2ea1a7ffa21853fcafa07aa4a08b2d592a9877c3f2d9 --cache` → 1 个任务 | `logs/task-download.log`、`logs/task-runtime-config.log` |
| OCI manifest 与本机 Docker | `timeout 50 bash isolated.sh /usr/bin/python3 oci-preflight.py` → 退出 0；`docker info`、`docker compose version`、`docker image inspect` | `logs/image-inputs.log`、`logs/oci-preflight.log`、`oci-amd64.json` |
| 单题 dry-run | `timeout 90 bash -x nop-preflight.sh` → 退出 0 | `logs/nop-dry-run.log` |

实测 Harbor 命令：

```bash
cd /home/gypsophila/geotree/work/e01-p0
bash isolated.sh .venv/bin/harbor run \
  -d gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a \
  -e docker -a nop --include-task-name '*freecad-6b54209a13' \
  --n-tasks 1 --n-concurrent 1 --n-attempts 1 --max-retries 0 \
  --jobs-dir jobs --job-name e01-p0-v3-nop --dry-run
```

## 下一步

1. 提供原始开题文档或可访问路径，再按原文放入 `docs/proposal_v0.2.md`。
2. 先确认共享 Docker 构建允许的网络下载量和峰值磁盘占用；可先批准只对这一题做依赖解算和容量核算，或由管理员提供经过核验的两套本地缓存镜像。未核实之前不去掉 `--dry-run`。
3. 核验资源后，用同一条命令去掉 `--dry-run`，仍不加上传参数，并把 stdout/stderr 和退出码保存到项目内。验收要看到真实的 agent/容器生命周期、独立 verifier 执行和可解析 reward 文件；仅退出 0、缺失 reward 或环境失败都不算评分链路通过。若 nop 得到真实 0，也只代表无作答的 smoke，不是 GeoTree 成绩。
4. 只有真实 smoke 通过才实现最小无模型 `BaseAgent`，先验证 import path、生命周期和 ATIF；本阶段不启动搜索，不接真实 LLM。
