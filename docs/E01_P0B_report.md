# GeoTree E01-P0B｜单题真实执行链路

2026-11-12（Asia/Singapore），远程项目 `/home/gypsophila/geotree`。接续 E01 P0 与 P0B 只读预检。用户随后明确授权使用共享 Docker 存储、下载本次构建依赖，并取消另行约定容量上限；原先对既有容器、daemon 和全局配置的限制继续保留。

| 验收项 | 状态 | 结果 |
|---|---|---|
| v0.2 原文 | PASS | 已原样同步到 `docs/proposal_v0.2.md`（28,493 B，SHA-256 `6b4a611b323ac26f42ed3bca8c6de49c2da66f9d99c8e8ccc325df2d9d3c6fc7`）。当前 E01 优先本地 Qwen；未改原文。 |
| 首次执行 | BLOCKED → 已修复 | 项目环境缺 Docker Buildx。侧车构建子命令退出 125，`unknown flag: --file`；Harbor CLI 虽退出 0，结果为 0 个完成试次、1 个 RuntimeError，无 reward。 |
| 真实单题 nop | PASS | 修复后实际完成 1 个任务，Harbor 退出 0；Agent 和独立 verifier 均有各自的 Docker 启停记录。Verifier 写出可解析 reward 0.0，无 trial 异常。 |
| 最小无模型 BaseAgent | PASS（实现及接口测试） | `src/geotree/harbor_agent.py`，类 `geotree.harbor_agent:GeoTreeNoModelAgent`。真实 Harbor 工厂导入、CLI dry-run、记录型环境的生命周期/权限检查与官方 ATIF 校验均通过。 |
| BaseAgent 真容器试次 | PASS | 同一固定单题实际执行，独立 verifier reward=0.0，ATIF 校验通过；详见本轮续跑证据。 |
| 模型、搜索、CADWorld、全量 Benchmark、上传 | NOT_RUN | 本轮均未启动。 |

## 版本、实际命令和原始证据

- Harbor **0.23.0**，E00 固定源码 SHA `1e5c5c6db929a10a140d05e606882c671ae20729`；Docker 29.1.3、Compose 2.40.3。运行期镜像检查：FreeCAD 1.1.0，verifier 包 0.6.0、v2 scorer。
- CAD Bench V3 数据集 digest `sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`；任务 `gnucleus-ai/freecad-6b54209a13` digest `sha256:741b7289accd15447a3a2ea1a7ffa21853fcafa07aa4a08b2d592a9877c3f2d9`。
- 工作根 `/home/gypsophila/geotree/work/e01-p0`；首个失败 job `live-nop.NLOTrH/`，成功 job `live-nop.F0DWk8/`，各有 `run.sh`、`runner.log`、`stdout.log`、`stderr.log`、`exit`。两个 job 各固定一个任务、单 attempt、零自动重试；首个未启动任务容器，修复后单独发起一个新 job。
- Buildx 修复：从 Ubuntu archive 下载 `docker-buildx_0.30.1-0ubuntu1~24.04.1_amd64.deb`（16,802,158 B；SHA-256 `30723359cf4825afa5ac2087cf5833163f80fb74802bc32e0ed6c9efc13e4b3c`）。用 `dpkg-deb -x` 解包，仅把二进制安装到项目隔离 HOME 的 `home/.docker/cli-plugins/docker-buildx`。未使用 sudo、未安装系统软件包、未改 daemon 配置。完整命令与实际版本输出在 `live-nop.NLOTrH/buildx-setup.log`。
- 成功 job 的实际 CLI（stdout/stderr 由 `run.sh` 重定向，退出码写入 `exit`）：

```bash
cd /home/gypsophila/geotree/work/e01-p0
bash isolated.sh .venv/bin/harbor run \
  -d gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a \
  -e docker -a nop --include-task-name '*freecad-6b54209a13' \
  --n-tasks 1 --n-concurrent 1 --n-attempts 1 --max-retries 0 \
  --jobs-dir /home/gypsophila/geotree/work/e01-p0/live-nop.F0DWk8/jobs \
  --job-name e01-p0b-nop-f0dwk8 --no-delete
```

## 真实试次验收

| 容器（短 ID） | 角色 | 实测启动 → 停止（+08:00） |
|---|---|---|
| `4ed9c0ebd805` | Agent `...__env` | 19:11:32 → 19:11:38 |
| `a56b4963e8f5` | 独立 verifier `...__verifier__trial` | 19:21:26 → 19:21:28 |

两者均有 `start/stop/die/destroy` 事件；容器停止时 `die` 记录为 143，不是 CLI 或 verifier 评分退出码。Harbor 保留 `agent_result` 和 `verifier_result.rewards.reward=0.0`，无 `exception_info`；`verifier/reward.json` 为 `{"reward":0.0}`，`verifier/reward.txt` 为 `0`。未生成 `answer.py` 或 `answer.FCStd`，符合 nop 的行为。总耗时约 20 分 6 秒。**真实 0 仅是无模型基础设施 smoke，不是 GeoTree 能力成绩。**

成功目录内：`events.trial.jsonl`（按本 trial 两个 Compose project 过滤）、`verified-smoke.txt`、`agent-build.log`、`verifier-build.log`、`sidecar-build.log`、Harbor 的 `job.log`、`trial.log`、两级 `result.json`、`verifier/test-stdout.txt` 和 reward 文件均保留。Compose 已清理本试次创建的容器，未另存 daemon 的 `docker logs` 流；生命周期以原始 Docker events 为证，评分以 Harbor 输出与 reward 文件为证。没有执行 prune、删除既有对象、重启 daemon、访问隐藏评分资料或公开上传。

## 下载与新增磁盘

- BuildKit 记录 Miniforge 基础压缩层 29.73 + 140.42 MB，隔离侧车基础层 1.36 + 14.13 MB。Agent 构建的 Conda 解算日志分别报 844 MB 和 43 MB，APT 报 29.4 MB；verifier 的 Conda 报 880 MB，APT 报 58.0 MB，另有 pip 软件包和仓库元数据。日志中的标称下载量不是整机网络流量计数，不把这些数当精确传输总量。
- `docker-after.txt` 中 Agent 与 verifier 镜像分别为约 6.47 GB、6.71 GB，有共享层；侧车约 72.7 MB；Docker 构建缓存快照为 12.57 GB。镜像、共享层与缓存不能直接相加。
- 同一共享文件系统的前后净变化 **21,896,998,912 B（20.39 GiB）**；每 12 秒采样中的最高相对占用 **21,897,035,776 B（20.39 GiB）**。这是文件系统测量，不是任务独占配额，也不保证采到瞬时峰值。见 `disk-before.txt`、`disk-after.txt`、`docker-disk-samples.tsv`、`docker-before.txt` 与 `docker-after.txt`。

## 最小适配器与验证边界

`/home/gypsophila/geotree/src/geotree/harbor_agent.py`，SHA-256 `470fabe2855e4650bafa121c5d282ef651d10449c74b48d2efbc6c4d68e82040`。不执行任务文本；仅允许一个固定、10 秒超时的 `/app` 存在性检查，不指定提权用户、不写 CAD 或访问网络，并拒绝 model 参数。生成 `geotree-events.jsonl` 和 ATIF-v1.8 `trajectory.json`（零 LLM 调用）。

在成功目录 `adapter-test/` 中，`test_adapter.py` 通过真实 Harbor 工厂加载；记录型环境分别返回 0 与 19，验证 setup 不执行工具、run 仅调用固定工具一次、错误明确上报且仍写轨迹、传入模型时拒绝执行。Harbor 自带的 `python -m harbor.utils.trajectory_validator` 对两份轨迹均输出 `Trajectory is valid`。另以真实 Harbor CLI 和相同任务过滤器做 adapter dry-run，报告 `1 trial(s); nothing was run`。完整命令及结果见 `adapter-test/verification.log` 和 `adapter-test/harbor-dry-run.log`。后续若需要验证适配器在真实容器内的日志收集，可复用现有镜像做同题无模型运行；Qwen 和搜索均不在本次范围。

## 本轮续跑：真实无模型 BaseAgent（2026-11-12 19:58 +08）

状态 **PASS（基础设施 smoke，不是能力成绩）**。沿用上述 Harbor 0.23.0 和数据集/任务 digest，无源代码更改、无新模型。历史记录型环境测试仍为单元测试，不替代此次实际运行。

证据目录：`/home/gypsophila/geotree/work/e01-p0/live-adapter.vXtIaU`。实际命令完整保留于 `run.sh` / `runner.log`：

```bash
bash isolated.sh env PYTHONPATH=/home/gypsophila/geotree/src PYTHONDONTWRITEBYTECODE=1 .venv/bin/harbor run -d gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a -e docker -a geotree.harbor_agent:GeoTreeNoModelAgent --ek keep_containers=true --include-task-name '*freecad-6b54209a13' --n-tasks 1 --n-concurrent 1 --n-attempts 1 --max-retries 0 --jobs-dir "$d/jobs" --job-name "$name" --no-delete > "$d/stdout.log" 2>"$d/stderr.log"
```

脚本中 d 为上述绝对证据目录，name 为 `e01-p0b-adapter-vxtiau`。CLI 退出码 `0`，1 trial、0 errors、reward `0.0`，总耗时 19 秒。

- Agent 容器 `1d022387b7d5`：19:58:39–19:58:44；实际 setup/run 完成，唯一工作目录检查返回 0，日志 outcome=`workspace_ok`。
- 独立 verifier 容器 `faa4de2a86c7`：19:58:48–19:58:50；评分输出 `candidate did not produce /app/answer.FCStd`；reward.json 为 `{"reward": 0.0}`。该检查验证缺失答案分支及评分传递，不代表有效 CAD 答案的几何评分正确性已验证。
- 容器停止退出码 143，来自生命周期结束时停止常驻进程，不是 agent 工具退出码。`exception_info=null`，无 OOM。侧车运行时健康检查均退出 0；停止后 inspect health 标识为 unhealthy，保留原始记录。
- `--ek keep_containers=true` 本轮生效，3 个新容器均已停止并保留。`container-logs/` 含每个容器的 inspect、stdout、stderr 和 docker logs 退出码。容器主进程日志可以为空；exec 的评分输出另在 trial/verifier/test-stdout.txt。未移除任何既有对象。
- 官方 ATIF validator 校验真实 `agent/trajectory.json` 通过，详见 `atif-validation.log`。`verification.log` 验证实际生命周期、独立 verifier、无模型及结果字段。轨迹记录 llm_call_count=0。
- 构建前后共享磁盘已用量 390668193792 → 390671093760 B，净增 **2,899,968 B**。这是共享文件系统观测差值，不是精确独占使用量。此次复用已有镜像层；没有显式依赖下载命令，也未计量网络传输字节，不将其声明为精确零下载。
- `docker-before.txt` / `docker-after.txt` 保留完整 `docker system df -v`；`docker-root.txt`、`containers-before.txt`、`containers-after.txt`、`disk-before.txt`、`disk-after.txt`、`events.raw.jsonl` 保留本轮环境记录。
- Harbor 日志含缺失 answer.py/answer.FCStd 的 artifact-copy 警告，符合本适配器不生成 CAD 的设计；trial 无异常。没有修改 benchmark ground truth 或读取隐藏评分数据。

### 更新后的下一步
P0B 到此完成。后续阶段可另行验证本地 Qwen 接口及有效 CAD 输出；本轮不启动该阶段。前文“可再执行适配器真容器试次”的建议已由本节完成，不再是待办。
