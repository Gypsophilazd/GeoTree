# E02-F2 接线与验收
日期：2026-11-12（Asia/Singapore）。**PASS / DEVELOPMENT-ONLY**：真实固定 Reader 已随 A1 运行，A0 和 A1 各一次完成。尚未建立跨任务生产稳定性。

## 实现与冻结
- 新入口 `geotree.paired_agent:PairedAgent`；A0/A1 共用 Runtime、Budget、Mailbox、ActionValidator、NoSearch、Executor、FeedbackRecorder。两组均安装相同受信 Reader；仅 A1 在成功 CAD 执行后调用并附加几何反馈。旧入口及既有报告通过 SHA256 保全检查。
- 固定读取命令：`HOME=/tmp/geotree-home OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /opt/conda/bin/python -I /opt/geotree-observer/reader.py`。仅处理 `/app/answer.FCStd`；受信目录不可由 UID65534 改写。CAD 执行前移除本试次固定输出位置的旧产物，非0不观察；读取失败与执行结果分开。A1 观测带 action_id、时间、artifact SHA256、状态。不读取人工 manifest 或隐藏参考。
- 每组4次决策、2次CAD、CAD进程60秒、模型420秒、总 wall 1200秒、token 200000软预算。单次等待受剩余总时间约束；CAD 进程使用容器内 timeout。超预算停止新动作并记录 overshoot。Windows supervisor 使用 Job Object 管理子进程树；每组独立邮箱，request_id 和 deadline 校验，原始 CLI 事件及退出原因保存。
- Harbor 0.23.0、FreeCAD 1.1.0、Codex CLI 0.167.0-alpha.4.1、ChatGPT 登录、`-m gpt-6.1-sol`、high。模型ID为实际 CLI 请求参数，事件未另给可核验后端权重版本。两组的 task、environment、agent、verifier 和 bridge lock 字段相等；任务 digest `sha256:741b7289accd15447a3a2ea1a7ffa21853fcafa07aa4a08b2d592a9877c3f2d9`。两组图纸与动作 schema 的 SHA256 各自相等。派生容器镜像 ID 不同，实测 RootFS 层及 Env/Cmd/Entrypoint/User/WorkingDir 一致，记录在 image-parity.json。
- 两组实测 2 CPU / 4 GiB / 无 GPU 请求；保留任务网络侧车。真实主容器 UID65534 的 /logs 遍历、/logs/verifier 读取及 Reader 写入权限探测均被拒绝；评分运行在 separate 环境。仅检查权限，不读取隐藏内容。凭据留在 Windows。权限检查及 AST 不等于任意 Python 沙箱证明。资源抽样未见持续 IO 等待，未操作其他 RL 进程或容器。

## 预检证据
证据根目录：`/home/gypsophila/geotree/work/e02-f2/`。
| 检查 | 实测 |
|---|---|
| 旧 NoSearch | legacy.log，exit 0，既有回归通过 |
| 共享预算和 ATIF | budget.log，4决策、2CAD、旧ID拒绝、软预算越界、单次/总deadline、ATIF |
| 真实无模型容器 | preflight.log，使用 Harbor DockerEnvironment.exec 和 UnixOps 上传；安装、不可写、合成 verifier ACL、无产物错误、JSON/hash、两组Mock邮箱和ATIF通过。初次 fixture 构造缺少 Harbor 属性，三份失败日志保留，修正测试夹具后通过 |
| Windows 进程 | relay-tests.log，正常0、异常7、超时124，确认模拟孙进程退出、父进程存活 |
| 两组真实运行 | 各自 config.json、sha256.txt、actual-limits.txt、Harbor stdout/stderr、job/lock/result、原始轨迹和 Windows 原始事件 |
| 保全 | baseline.sha256、preservation.log；项目根原无 Git 仓库，在 source-snapshot 单独保存提交 `996a7bcecd5a25453f38d3dccbb4645fe26aa882`，source.diff、source.sha256 |

复现命令记录：`bash work/e02-f2/run-pair-arm.sh <trial-id> <unix-deadline>`；真实已运行的完整 Harbor 参数在两组 runner.log。Windows 命令与预算由 launch_pair.py 和 relay.py 保留。每组 Harbor attempt=1/retry=0；CLI 在同一请求内部经历 WebSocket 重连并回退 HTTPS，不等于额外 Harbor 试次，但影响 wall time。未追加尝试。
