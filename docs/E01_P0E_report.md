# GeoTree E01-P0E：完整执行回归与 NoSearch 架构冻结

日期：2026-11-12。项目 `/home/gypsophila/geotree`。历史 P0D 失败及原始日志保留不变；本轮新增且只新增 **1 次 DEVELOPMENT-ONLY 单题试次**，attempt=1、retry=0、并发=1，无上传。

## 1. 验收结论

| 项目 | 状态 | 真实结果 |
|---|---|---|
| 离线执行回归 | PASS | nullable 输出、拒绝动作反馈、工具超时、非法响应、最大预算、trace/ATIF、relay 正常/异常终止均有测试 |
| 基模可替换 | PASS（离线） | MockProvider 与 JSONTransportProvider 均运行相同核心循环；未调用 DeepSeek API |
| 真实完整反馈闭环 | PASS / DEVELOPMENT-ONLY | workspace 检查→反馈→第二次模型决策→CAD 执行→反馈→第三次模型 done |
| CAD 产物 | PASS（有效产物，不代表精确匹配） | answer.py 9968 B；answer.FCStd 176568 B；一个 PartDesign::Body，含 Sketch/Pad/Pocket/SubtractiveLoft，无 Part::Feature |
| 独立 verifier | PASS | separate 容器实际运行；reward **0.314269**；trial exception=null，Harbor CLI exit=0 |
| ATIF | PASS（Schema）；最小语义编码 | 官方 validator 通过，3 个模型 step；原始动作/usage 同时保存在 raw trace/CLI JSONL |
| NoSearch 架构 | PASS | 新模块独立实现；两个旧入口哈希不变；NoSearch k=1，预留 k≤3 契约 |
| 正式协议/榜单成绩 | DEVELOPMENT-ONLY | 仅固定开发单题、外置 Codex 决策、开发隔离修改，非正式完整评测 |
| DeepSeek A0/A1、Lite、MCTS、训练、全量 Benchmark | NOT_RUN | 仅冻结对照设计，不执行方法实验 |

**本次 reward 是 Codex + GeoTree-NoSearch 开发接入结果，不是 DeepSeek 方法成绩，也不用于声称搜索收益。** 历史 P0D 仍为失败，未覆盖或替换。

## 2. 固定版本、执行配置

- Harbor 0.23.0；上游 SHA `1e5c5c6db929a10a140d05e606882c671ae20729`；FreeCAD 1.1.0；独立 verifier 0.6.0；Docker 29.1.3 / Compose 2.40.3。
- 数据集 `gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`。
- 任务 `gnucleus-ai/freecad-6b54209a13@sha256:741b7289accd15447a3a2ea1a7ffa21853fcafa07aa4a08b2d592a9877c3f2d9`。
- 新 Harbor import path `geotree.nosearch_agent:GeoTreeNoSearchAgent`。复用已通过的 Codex mailbox / Decision Bridge 方式；`DecisionBridgeAgent` 和 `GeoTreeNoModelAgent` 原文件未修改。
- Windows codex-cli 0.167.0-alpha.4.1，ChatGPT 登录，显式模型 `gpt-6.1-sol`，effort=high；事件未提供服务端精确 snapshot ID，不编造。
- 本轮最多 4 个决策，模型等待 420 秒/回合，工具 60 秒（外层 65 秒）。最终使用 3 个决策、2 个模型可见工具动作，其中 1 次实际 FreeCAD 脚本执行；另有可信 setup/路径 guard 等基础设施 exec，不隐含计为模型决策。

证据目录：`/home/gypsophila/geotree/work/e01-p0e/nosearch.vFTvcn`；trial：`freecad-6b54209a13__PPMxty3`。
实际启动命令（cwd=`/home/gypsophila/geotree/work/e01-p0`）：
```bash
bash /home/gypsophila/geotree/work/e01-p0e/nosearch.vFTvcn/run.sh
```
脚本中的实际 Harbor 命令：
```bash
bash isolated.sh env PYTHONPATH=/home/gypsophila/geotree/src PYTHONDONTWRITEBYTECODE=1 .venv/bin/harbor run -d gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a -e docker -a geotree.nosearch_agent:GeoTreeNoSearchAgent --ek keep_containers=true --include-task-name '*freecad-6b54209a13' --n-tasks 1 --n-concurrent 1 --n-attempts 1 --max-retries 0 --jobs-dir "$d/jobs" --job-name "$name" --no-delete > "$d/stdout.log" 2>"$d/stderr.log"
```
d=`/home/gypsophila/geotree/work/e01-p0e/nosearch.vFTvcn`，name=`e01-p0e-nosearch`。Windows 转发完整参数与每次 prompt 保存于 `work/e01-p0e/windows-evidence/relay.ps1`、request-*.txt；所有模型原始响应、JSONL 事件、usage、exit 同目录保留。

## 3. 真实动作、文件与评分

1. Codex 返回 check_workspace，环境工具退出 0，stdout=`workspace_and_drawing_ok\n`，stderr 归一为空串。
2. 该反馈实际进入第二条 Observation。Codex 自主根据允许的工程图生成 run_freecad 脚本，父代理未提供几何答案或修改最终脚本。
3. `/opt/conda/bin/python /app/answer.py` 以 UID 65534 执行，退出 0，用时约 2.799 秒。真实 stdout：`Solid count: 1 Valid: True Volume: 154123.68473754305`。该内容也实际进入第三条 Observation。
4. 第三次 Codex 返回 done；relay 读取 terminal.json 后退出 0，记录 `PASS relay terminal received`。随后 Harbor 收集产物并运行独立 verifier。

文件（已重新读取并核验 ZIP/XML；没有重新建模）：

| 文件 | 大小 | SHA-256 |
|---|---:|---|
| answer.py | 9968 B | db9f695a867703ec96a55c1270468f2f5a80661c6fcf5839ca8951605c9a27f8 |
| answer.FCStd | 176568 B | 26d7b8ee0f6db73e8f5aae9534fba3a914dd3c45c21fe68a1b7f2ae9f4b9ee18 |

绝对产物目录 `/home/gypsophila/geotree/work/e01-p0e/nosearch.vFTvcn/jobs/e01-p0e-nosearch/freecad-6b54209a13__PPMxty3/artifacts/app`。解析产物 Document.xml 确认一个 PartDesign::Body，命名特征树包含 Sketcher::SketchObject、PartDesign::Pad/Pocket/SubtractiveLoft；无 Part::Feature。脚本报告单实体有效，独立 grader 给出非零连续 reward；这不代表全部图纸细节正确，更不代表满分。

独立评分的原始 reward.json：`{"reward": 0.314269}`；verifier_result 与其一致。Agent/Verifier 互为独立 Compose project，容器及时间戳详见 verified-result.json、container-logs/*.inspect.json 和 events.raw.jsonl。verifier/test-stdout.txt 本次为空，空文件原样保留；分数证据来自真实 reward/result 文件，未编造评分 stdout。

总耗时约 **11 分 16 秒**：2026-11-12 20:53:13 至 21:04:29（+08）。Agent execution 20:53:20–21:03:34；verifier 21:03:36–21:04:29。模型工具执行退出 0，容器常驻进程停止时 143 属正常生命周期结束，不混作脚本错误。

## 4. 模型调用、Token 与轨迹

真实模型决策完成 **3 次**；未启动额外候选、重置或第二个 Benchmark。传输层重连/HTTPS 回退记录保留，不算 task retry。原始 CLI usage：

| 决策 | input_tokens | cached_input_tokens | output_tokens | reasoning_output_tokens |
|---|---:|---:|---:|---:|
| 0 | 38965 | 0 | 75 | 0 |
| 1 | 39035 | 36480 | 8214 | 4076 |
| 2 | 39126 | 15232 | 151 | 84 |
| 合计 | 117126 | 51712 | 8440 | 4160 |

cached 是 input 的分类，不额外相加；reasoning 与 output 的计量口径保留 CLI 原字段，不擅自重复加总。cache_write_input_tokens 总计 0。以上是 CLI 报告的实际 usage，不是账单审计；ChatGPT 订阅用量不换算为未经核验的 API 美元费用。

ATIF 真实 trajectory.json 经 `python -m harbor.utils.trajectory_validator` 返回 `Trajectory is valid`；包含 3 个 step，llm_call_count 总和 3。当前最小 ATIF 将 proposal/feedback 放在 message，而不是完整标准 tool_calls/observation 链；真实命令、退出状态、stdout/stderr、usage 有并行 JSONL。Schema PASS 不等于所有标准化工具语义和成本字段均已完善。下一阶段可补记录映射，不必再扩张 Codex 认证。

本轮 relay 事件审计没有发现 command_execution/file_change/MCP 等额外工具 item。仍有约 39k 输入 token 的系统/运行时上下文，未证明上下文彻底最小化；不把禁用开关和事件审计当 OS 权限隔离证明。

## 5. 离线测试及边界

服务器测试命令（cwd=`/home/gypsophila/geotree/work/e01-p0`）：
```bash
bash isolated.sh env PYTHONPATH=/home/gypsophila/geotree/src .venv/bin/python ../e01-p0e/test_nosearch.py
```
退出 0，完整输出见 offline-tests.log：nullable stdout/stderr、下一决策含真实格式反馈、拒绝动作不调用工具、timeout 反馈、非法 payload、最大预算截断、provider 替换、mailbox 超时/错误、adapter 正常/异常 terminal，以及基本 import/path 拒绝测试均 PASS。SearchPolicy/CandidateBatch 单测见 policy-tests.log；Windows relay 正常/error/timeout 状态测试见 windows-evidence/relay-tests.log。Mock 结果仅属离线，不计入模型调用或成绩。

边界控制：本轮容器中固定 /app 目录、非 root UID 65534、/logs 权限 700、输出路径/符号链接 guard、禁止明显越界语法、任务 no-network 未修改、没有 Docker socket/其他项目挂载或隐藏参考输入。可信 SSH relay 和登录凭据留在 Windows，不复制 auth.json。

**没有建立任意 Python/FreeCAD 程序的完整安全沙箱证明。** AST 组合、FreeCAD API 文件访问面、TOCTOU、容器安全及宿主 CLI 工具权限的全面负向测试尚有边界。本轮依用户授权仅受控开发测试；不能据此宣称严格官方协议完全满足。共享 /logs 的时序/写权限通过非 root 与父目录禁止访问收窄，仍不将其表述为形式化安全证明。

## 6. 共享科研资源

原生任务 2 CPU / 4 GiB / GPU=0；实际 Docker inspect 验证资源设置，DeviceRequests=null、Privileged=false、未共享宿主 PID namespace。侧车/Harbor 宿主仍未实现完整硬限额，此限制原样报告。没有下载/加载 Qwen，没有使用 RTX 5090 D v2，没有更改既有训练或 Docker daemon。

运行前 MemAvailable 54,781,300,736 B，短时 CPU idle 88–89%，memory/IO PSI avg10=0。期间 vmstat、前后磁盘和 Docker df 留存；抽样未见明显持续资源争用，不代表对 RL 吞吐做过精确因果测量。

模型执行后的一次 Docker stats 抽样：Agent CPU 0%、1.828 MiB / 4 GiB、Block IO 532 kB / 180 kB；侧车 CPU 2.59%、24.4 MiB。这是空闲阶段实测，不是 FreeCAD 峰值或整个试次的 CPU 积分。没有伪造峰值内存数据。

全部本轮容器已停止并保留用于证据；只停止本轮 vmstat，relay 正常终止。未清理其他对象，也未重复运行本题。

## 7. 架构与对照冻结

详见 `docs/GeoTree_Architecture_v0.1.md`、`configs/comparison_v0.1.json`。已实现 ModelProvider、ObservationBuilder、ActionProposal、ActionValidator、Executor、FeedbackRecorder、NoSearch；SearchPolicy Protocol 和 CandidateBatch 预留 k≤3。MockProvider 与 JSONTransportProvider 证明循环不依赖 Codex；未来 DeepSeek HTTP 请求/认证层仍未实现，不能把通用 transport 接口叫作已跑通 DeepSeek。

A0/A1 固定同一 `deepseek-flash`（官方 2026-11-12 映射 DeepSeek-V4.1-Flash-1017）、任务、图片、工具/反馈与预算；仅 NoSearch 与 Lite 策略不同。每题设计预算 100000 total tokens、1 USD 上限，均为待授权计划，不授权本轮 API 支出。API effort 支持、实际版本、正式评测子集及 prompt 哈希仍是方法实验开跑前门槛。官方外部历史 Codex/Claude Code 成绩保留，DSH 可选不阻塞。

## 8. 后续门槛

本轮 CAD、反馈、独立评分核心闭环已经通过。下一阶段进入 NoSearch / Lite 方法开发：实现 DeepSeek transport、冻结同模型配置/开发与评测划分、补完整成本与 ATIF 工具映射，再实现只执行一个候选的 k≤3 策略。保留现有受控开发边界，不继续扩张 Codex 登录/身份隔离工程；只修阻塞核心功能的问题。没有 MCTS、训练或全量评测。
