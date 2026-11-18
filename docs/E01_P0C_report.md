# GeoTree E01-P0C v2：子代理隔离评测报告

日期：2026-11-12。项目 `/home/gypsophila/geotree`；Windows Codex 经 SSH `gypsophila-tailscale` 执行。已阅读 E00、E01-P0、E01-P0B、E01 实施顺序与 v0.2 原文；旧报告中的历史 BLOCKED 不覆盖 P0B 已通过结果。原文未修改。

## 1. 结论

| 项目 | 状态 | 真实结果 |
|---|---|---|
| 本轮真实自定义 BaseAgent | PASS | 1 task、1 attempt、并发 1、retry 0，17 秒；reward=0.0，CLI 0，无 trial exception |
| 原生独立子代理及 SSH | PASS | fork_turns=none，连接探针输出 GEOTREE_CHILD_SSH_OK，退出 0；不是 CAD 考生尝试 |
| Windows CLI ChatGPT 登录 | PASS（状态检查） | codex-cli 0.167.0-alpha.4.1；codex login status 输出 Logged in using ChatGPT |
| Harbor 内置 Codex | PASS（源码接口审计） | 0.23.0 含 installed/codex.py；不等于已经实测 Codex 做题 |
| 严格考生隔离及凭据保护 | BLOCKED | 当前原生子代理继承广泛工具权限；Harbor 内置 ChatGPT auth 路径向任务环境上传 auth.json |
| Codex CAD 建模、轨迹、独立评分 | NOT_RUN | 尚未向考生交付题目；CAD 正式尝试数 0；无分数，不以无模型 0 分冒充 |
| 单题结果可比性 | DEVELOPMENT-ONLY | 单题开发 smoke，不是完整官方成绩，不是 GeoTree 能力成绩 |
| Qwen、GPU 模型、商业 API、训练、搜索、全量评测、上传 | NOT_RUN | 均未启动 |

## 2. 固定版本与真实试次

Harbor 0.23.0；固定上游 SHA `1e5c5c6db929a10a140d05e606882c671ae20729`；Ubuntu 24.04、Docker 29.1.3 / Compose 2.40.3。复用已有 FreeCAD 1.1.0 / verifier 0.6.0 镜像层，未安装 Codex 到容器、未下载模型或另行构建依赖。

数据集：`gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`。
任务：`gnucleus-ai/freecad-6b54209a13@sha256:741b7289accd15447a3a2ea1a7ffa21853fcafa07aa4a08b2d592a9877c3f2d9`。

Agent 为 `geotree.harbor_agent:GeoTreeNoModelAgent`，源码未修改。BaseAgent Python 运行在 Harbor 编排宿主进程，固定工具通过 environment.exec 在任务容器执行；**不是把 Python BaseAgent 导入容器**。其 setup/run、固定 /app 检查、日志与 ATIF 都已实测。没有实际 CAD 生成；独立 verifier 走缺失答案分支，reward 0.0 不证明正常几何评分分支已验证。

证据目录：`/home/gypsophila/geotree/work/e01-p0c/baseagent.QTacRt`。
trial：`freecad-6b54209a13__GzHtBAc`。

实际执行 `bash /home/gypsophila/geotree/work/e01-p0c/baseagent.QTacRt/run.sh`，退出 0；run.sh 内实际命令：
```bash
bash isolated.sh env PYTHONPATH=/home/gypsophila/geotree/src PYTHONDONTWRITEBYTECODE=1 .venv/bin/harbor run -d gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a -e docker -a geotree.harbor_agent:GeoTreeNoModelAgent --ek keep_containers=true --include-task-name '*freecad-6b54209a13' --n-tasks 1 --n-concurrent 1 --n-attempts 1 --max-retries 0 --jobs-dir "$d/jobs" --job-name "$name" --no-delete > "$d/stdout.log" 2>"$d/stderr.log"
```
其中 d=`/home/gypsophila/geotree/work/e01-p0c/baseagent.QTacRt`，name=`e01-p0c-baseagent-qtacrt`。启动时 cwd=`/home/gypsophila/geotree/work/e01-p0`。未使用 dry-run 或 upload；未重复 nop。

stdout.log、stderr.log、runner.log、exit、job/trial result.json、agent/geotree-events.jsonl、agent/trajectory.json、verifier/test-stdout.txt、reward.json 均保留。container-logs 含本轮三个容器 inspect 与 Docker stdout/stderr；events.raw.jsonl 保留生命周期。容器均已停止并保留，常驻进程停止退出 143，不混同于固定工具退出 0。官方 ATIF 校验记录见 atif-validation.log；结果字段核验见 verification.log。

## 3. 共享训练资源

仅采集整机资源统计与容器状态，不读取其他训练代码、命令行、数据或日志。执行前 56 逻辑 CPU，load average=4.26/5.31/5.92，MemAvailable=54,095,425,536 B；采样 CPU idle 约 93%，iowait=0，CPU/memory/IO PSI avg10=0。

本轮实际 Docker inspect（resource-limits.json）：Agent 与 verifier 各 NanoCpus=2000000000（2 CPU）、Memory=4294967296（4 GiB）、MemorySwap=8589934592（总内存+swap 上限），DeviceRequests=null，Privileged=false。未请求 GPU。遵循任务原生 cpus=2、memory_mb=4096、gpus=0，未更改资源协议。

侧车没有独立 CPU/内存硬上限，Harbor 宿主编排也没有 cgroup 限额；因此不宣称整条链路存在完整硬隔离。运行期 vmstat 1 秒采样保存在 resource-during.txt，未发现明显整机资源争用；该短时观察不能证明现有 RL 吞吐完全无影响。未读取 GPU 进程内容，也未要求训练停止。Docker 无运行容器不等于不存在宿主机 RL 训练。

未终止、暂停或修改现有训练；未 prune、重启 daemon、改全局配置、CUDA 或驱动。本轮只结束自己启动的 vmstat 监控。后续更长测试前应给新建侧车和编排进程设置资源限制，并接入只针对本试次的停止机制；资源配置偏离原生协议时继续标为 DEVELOPMENT-ONLY。

## 4. 子代理、认证、网络与工具权限

原生调用 collaboration.spawn_agent(task_name="isolated_connectivity_probe", fork_turns="none")，未继承父对话；仅给 SSH printf 指令。实际命令、输出和退出码见 work/e01-p0c/child-probe.txt。这个探针只验证原生创建及独立 SSH，不是 Harbor Codex Agent，不算 CAD 尝试，没有接收任务输入或隐藏资料。

当前 spawn_agent 接口没有 tools allowlist、独立 OS 用户或沙箱根参数。子代理可用 exec_command 继承宿主机访问面。仅在提示词中说“只用 /app”不构成严格隔离，也不能保证其访问不到同用户的任务缓存、verifier 或其他项目。因此没有把这名子代理转为 CAD 考生。

Windows 已安装 codex exec，支持非交互新会话；未启动额外 exec 考生会话。Ubuntu PATH 未找到 codex。官方认证文档支持 ChatGPT 登录，与独立 API key 分开；本地 login status 已确认 ChatGPT。此检查不证明容器模型请求或账号剩余额度已验证。参见 [官方认证文档](https://learn.chatgpt.com/docs/auth)。无密钥值读取、输出或传输，无付费 API 请求。

Harbor 0.23.0 installed/codex.py:1299–1396 已保存源码片段及哈希：默认 API key；CODEX_AUTH_JSON_PATH / CODEX_FORCE_AUTH_JSON 可选择 auth.json，但随后 environment.upload_file 将该文件上传到容器，并为 agent 用户提供读取。此路径与本轮“不得向任务容器暴露宿主登录凭据”的要求不兼容，未启用。不能把支持 ChatGPT 登录直接推导成当前方案满足凭据隔离。

任务 [agent].network_mode="no-network"；task.toml 注释明确允许经 agent.extra_allowed_hosts / --allow-agent-host 配置模型供应商域名。故不是“所有模型出网一概禁止”，但本轮没有修改 allowlist 或测试 ChatGPT 所需端点；也未借宿主网络绕过约束。当前无模型 agent 只运行固定工作目录检查，未加入额外观察。

本轮 inspect 显示 agent 绑定自己的 /logs/agent、/logs/artifacts 及 /logs/verifier；独立 verifier 绑定 /logs/verifier。没有读取这些挂载中的隐藏参考内容。该共享输出挂载的时序和写权限尚未完成防篡改验证，不能仅凭 separate 标志断言敌对考生与评分全隔离。

### 阻塞解除的具体门槛

1. 提供可强制移除宿主 shell/SSH/通用文件访问的考生运行面，只暴露 task-scoped Executor；或隔离 OS/VM 会话，并保留外部可信认证进程。
2. 实现和审计不向 CAD 沙箱提供 ChatGPT bearer/refresh 凭据的认证边界；不能简单复制 auth.json。当前内置适配器没有完成这个验证。
3. 验证任务可见输入白名单、路径穿越/符号链接/容器 ID 越权拒绝、禁止 Docker socket/宿主挂载/隐藏评分输入，且最终评分输出不可被考生覆盖。
4. 对实际模型端点逐项核验 no-network 供应商例外；外置决策桥若偏离官方安装路径，明确 DEVELOPMENT-ONLY 并寻求协议确认。
5. 完成上述后冻结一次试次的模型、预算、prompt、权限与资源停止阈值，再给独立上下文考生任务。父代理只监控基础设施，不修答案；失败保留，不自动重试。

本轮无考生 CAD 文件、无考生 ATIF、无考生 reward。这些字段是 NOT_RUN，不是零分或基础设施失败的正式尝试。

## 5. 后续 GeoTree Adapter 设计（未实现）

| 模块 | 契约 | 隔离要求 |
|---|---|---|
| ModelProvider | propose(observation, budget) -> ActionProposal[] + usage | 精确模型/effort；凭据在可信边界；不持有执行器外权限 |
| Observation | task_id、允许的文字/图片、工具返回、预算余量 | 仅明确允许输入；无宿主路径、参考答案或最终评分反馈 |
| ActionProposal | action_id、tool_name、typed arguments、可公开摘要 | 不保存或声称记录隐含思维链 |
| Executor | execute(trial_capability, proposal) -> exit/stdout/stderr/artifacts | capability 绑定单 trial；白名单、超时、路径和资源校验 |
| Verifier Feedback | terminal_score(final_artifacts) -> immutable reward | 试次结束后才独立评分；不回流为本次搜索 oracle |
| SearchPolicy | select(proposals, visible_history) -> one action | NoSearch k=1；以后 Lite k≤3，仅执行一个候选，无真实分支回滚承诺 |

NoSearch 顺序为 observe → propose(1) → validate → execute → append trace，直到 DONE/预算结束，冻结产物后独立评分。Lite 仅在该链路稳定后新增候选生成/可见证据排序；两者比较固定模型、工具、任务、预算。若 Codex 原生子代理不提供可替换决策接口，只登记为 Codex infrastructure baseline，绝不改名为 GeoTree 成绩。

建议考生系统提示模板（尚未用于 CAD 试次）：
```text
你是单试次 CAD 考生。输入仅为 TaskInput 和允许的 Observation。
仅调用 task-scoped Executor 暴露的工具；遵循给定步骤及时间预算。
自主生成任务要求的最终 CAD 文件；记录动作、工具结果和错误。
不读取 verifier、隐藏参考或其他任务，不访问宿主文件或凭据。
收到 DONE 或预算耗尽后停止，不重置试次，不请求父代理修复答案。
```
提示模板不是权限控制；必须先通过上述强制隔离门槛。
