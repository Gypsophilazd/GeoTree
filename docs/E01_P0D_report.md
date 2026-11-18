# GeoTree E01-P0D：Decision Bridge 最小链路报告

2026-11-12；项目 `/home/gypsophila/geotree`。接续 P0C，不重复既有 nop、无模型 BaseAgent、FreeCAD 或 verifier smoke。

## 一、七项结论

| 问题 | 状态 | 实际结论 |
|---|---|---|
| Codex 能否作为受控动作提议器 | PASS / DEVELOPMENT-ONLY | 独立 codex exec 输出 Schema JSON，真实提议 check_workspace；消息经校验后执行于任务容器 |
| 认证是否留在可信环境 | PASS（本轮操作范围） | 使用 Windows 现有 ChatGPT 登录；未复制 auth.json、未注入 API key、未把凭据传到 Ubuntu 或容器 |
| 完整 Observe–Decide–Execute 循环 | BLOCKED | Observe→Decide→Validate→Execute 已真实发生；反馈序列化因 stderr=None 崩溃，未到下一轮 Decide |
| 有效 CAD 文件 | NOT_RUN | 未进入 run_freecad；没有 answer.py / answer.FCStd，未伪造或由父代理补做 |
| 独立 verifier 与分数 | NOT_RUN | 本轮 verifier_result=null；Harbor 在 agent 异常后终止，不能把它写成 reward=0 |
| 官方协议符合性 | DEVELOPMENT-ONLY | 外置 Windows 决策桥、上下文及工具边界尚未获得严格协议验证；无正式可比成绩 |
| 下一轮直接实现 NoSearch | BLOCKED（实测验收）；可继续开发 | 已有 k=1 顺序入口；先验证反馈修复、权限与完整一次闭环，再称为可用 NoSearch |

**最低成功条件“真实模型决策→任务容器动作”有证据支持；完整 CAD 闭环尚未完成。** 本轮只有一次真实 task attempt，未因失败再跑。

## 二、版本与冻结配置

沿用 Harbor 0.23.0、Ubuntu 24.04、FreeCAD 1.1.0 和缓存镜像；固定上游 SHA `1e5c5c6db929a10a140d05e606882c671ae20729`。

- 数据集 `gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`。
- 任务 `gnucleus-ai/freecad-6b54209a13@sha256:741b7289accd15447a3a2ea1a7ffa21853fcafa07aa4a08b2d592a9877c3f2d9`。
- Windows CLI 0.167.0-alpha.4.1，ChatGPT 登录；真实任务显式 `-m gpt-6.1-sol`、`model_reasoning_effort="high"`。这是实际请求配置；CLI JSONL 未提供服务端解析后的精确模型快照，故不编造 snapshot ID。
- 新模块 `src/geotree/decision_bridge.py` / `DecisionBridgeAgent`；原 `harbor_agent.py` 未改。
- 并发 1、attempt 1、max-retries 0、无上传。最多 4 个动作、单次决策等待 300 秒、工具超时 60 秒；任务总限额仍 9000 秒。脚本最大 24000 字符、消息最大 30000 B、stdout/stderr 各截断到 12000 字符。
- 真实试次使用 `work/e01-p0d/decision_bridge.frozen.py` 对应版本；后续修复版本仅做离线测试。

## 三、Codex JSON smoke 与上下文边界

非 CAD smoke 最初使用不支持的 `--disable skills`，在发请求前退出 1，错误保存在 smoke-initial-config-error.txt。去掉该参数后输出 `{"action":"check_workspace","reason":"protocol smoke"}`，退出 0。未发生 CAD 尝试重试。

真实决策从独立最小目录启动，并启用 `--ignore-user-config --ignore-rules --ephemeral --skip-git-repo-check -s read-only --output-schema --json`；禁用 shell_tool、unified_exec、multi_agent、skill_search、apps、plugins、remote_plugin、in_app_browser、shell_snapshot；启用 skip_host_skill_discovery；project_doc_max_bytes=0，web_search=disabled。stdin 显式为空；只给任务公开文字、允许的工程图和 Observation。完整参数及 prompt 见 windows-evidence/relay.ps1、request-0.txt。

事件扫描只出现 error/agent_message，没有 command_execution、file_change 或 MCP item；未发现非预期工具动作。**这不是强制工具隔离证明**：read-only 不是禁止读取宿主机，禁用开关也未完成所有工具/连接器负向测试。主进程拥有可信转发所需 SSH，模型提示未收到 SSH 地址/命令，CLI 未观察到 SSH 调用；不能据此宣称操作系统级访问能力已彻底剥离。

额外上下文仍有疑点：非 CAD smoke input_tokens=38329，真实一次决策 input_tokens=38894。即使关掉用户配置、项目文档及技能发现，系统/运行时上下文仍显著；未证明只有我们显式给出的 Observation。没有继承父代理审计对话的显式 fork/resume 操作。

两次请求均出现 WebSocket 超时、5 次传输层重连，然后回退 HTTPS；这不是 benchmark task retry，也不是重做 CAD。事件日志保留实际 usage。本轮未另行购买或调用独立模型 API；订阅额度是否消耗以账户记录为准，未宣称免费或零 token。

## 四、Bridge 实现与真实证据

可信 Windows relay 只接收固定 mailbox 的 Observation 和固定公开 drawing.png；schema 固定为 request_id/action/code/reason，动作枚举 check_workspace/run_freecad/done。BaseAgent 生成随机 request_id，原子接收响应、核对字段/大小/预算。远端 SSH/SCP 由 relay 执行，不把通用终端作为模型工具。

固定图片来源 `/app/6b54209a13.png`，由 Harbor environment.download_file 导出；没有复制整套任务包、verifier、隐藏参考或其他目录。没有把隐藏 reward 作为 Observation。

run_freecad 设计只允许 FreeCAD/Part/Sketcher/math 导入，限制危险名字、反射、路径字符串和保存目标；上传目标固定为 /app/answer.py，执行命令固定为 `/opt/conda/bin/python /app/answer.py`。这是保守 AST 开发过滤器，**不是经过证明的 Python 安全沙箱**，当前存在功能覆盖与组合绕过审计空缺。它在本轮没有收到建模脚本，尚未实测 CAD 执行。下一轮须加强路径/链接、权限、工具与共享日志防篡改边界，不可因离线几条拒绝测试通过就宣布严格隔离。

真实证据目录：`/home/gypsophila/geotree/work/e01-p0d/bridge.hkf7iB`；trial `freecad-6b54209a13__FLPMWqy`。

实际启动命令：
```bash
cd /home/gypsophila/geotree/work/e01-p0
bash /home/gypsophila/geotree/work/e01-p0d/bridge.hkf7iB/run.sh
```
内部命令完整保留于 run.sh/runner.log：
```bash
bash isolated.sh env PYTHONPATH=/home/gypsophila/geotree/src PYTHONDONTWRITEBYTECODE=1 .venv/bin/harbor run -d gnucleus-ai/cad-bench@sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a -e docker -a geotree.decision_bridge:DecisionBridgeAgent --ek keep_containers=true --include-task-name '*freecad-6b54209a13' --n-tasks 1 --n-concurrent 1 --n-attempts 1 --max-retries 0 --jobs-dir "$d/jobs" --job-name "$name" --no-delete > "$d/stdout.log" 2>"$d/stderr.log"
```
d 为上面的目录，name=`e01-p0d-bridge`。

真实 Codex 响应：
```json
{"request_id":"9f8649bf-e7c7-4276-b4b4-47806909d028","action":"check_workspace","code":"","reason":"Verify the FreeCAD bridge and required output path."}
```

Docker 事件匹配同一个 execID，证明命令
`test -d /app && test -f /app/6b54209a13.png && printf 'workspace_and_drawing_ok\n'`
发生 exec_create、exec_start、exec_die，exitCode=0，见 workspace-action-events.json。**这只是任务工作目录和公开图片检查，不是 CAD 建模轨迹。**

紧接着 feedback 构造处 `result.stderr[:12000]` 触发 `TypeError: 'NoneType' object is not subscriptable`。因此 stdout/stderr 没有被成功写入 bridge-trace，也没传回第二个 Observation；不能用预期 printf 文本冒充已保存的 stdout。原始 Docker 事件提供动作及退出码证据，Harbor traceback 提供失败位置。

CLI 退出 0，但 job 显示 1 个 TypeError，verifier_result=null。总 runtime 2m22s。真实 raw JSONL 仅有 Observation、proposal、validation，无完整 execution feedback 或 ATIF；本轮未声称 ATIF 合格。缺失 CAD 的 artifact-copy 错误一并保留，不删除失败试次。

## 五、资源、凭据与数据

任务原生 2 CPU / 4 GiB，gpus=0；复用缓存镜像，无本地模型下载/加载，无 GPU 请求。资源前置采样有 56 CPU、约 51.1 GB 可用内存、CPU idle 93%、memory/IO PSI avg10=0。运行期 vmstat 保存在 resources-during.txt；仅观察到整机用量波动，未见持续内存/IO压力，不保证 RL 吞吐完全无影响。未读取训练私有内容，未停止任何训练。

保留容器 inspect/logs、Docker events、磁盘前后和 Docker df。原生侧车及 Harbor 编排没有完整硬资源上限，延续 P0C 的已知限制。没有改 Docker daemon、CUDA、驱动或其他项目。终止的只有本轮 Windows relay（在确认 Harbor 已失败后仍等待下一条 Observation）及本轮 vmstat；未重启任务。

认证仍由 Windows Codex 可信进程使用。同步到服务器的 windows-evidence 只有我们创建的 schema、公开输入、请求/响应、事件和脚本；没有复制 CODEX_HOME、auth.json 或配置文件。任务容器 no-network 配置未改变。外置模型通信不等于已获得官方网络协议认可，需维护方确认。

## 六、修复与回归（仅离线，不覆盖真实结果）

修复 stdout/stderr 的 None 处理：`(result.stdout or '')[:12000]` 与 `(result.stderr or '')[:12000]`。原版本在真实 Harbor ExecResult 的离线夹具上复现退出 1；修复后执行 Observe→Decide→Execute→反馈→DONE，断言工具恰调用一次，退出 0。这个通过结果是 **离线夹具测试**，不是第二次真实任务成功。

MODIFIED_FILE、DIFF_FILE、VERIFICATION.txt、可执行 ROLLBACK.sh 均在 `/home/gypsophila/geotree/work/e01-p0d/`。回滚在独立副本验证，恢复原始字节后同夹具再次出现原 TypeError/退出 1；实际模块保留修复。原无模型入口哈希保持不变。

完整精确 BASELINE/MODIFIED/ROLLBACK 命令、输入、输出与退出码：

```text
# Patch verification — offline only
Changed fields: feedback.stdout and feedback.stderr normalize None to empty string before truncation.
Original SHA256: 56a065ba66385a35cc39c574f6550b3ff4b5bd1a0393dca54c0d86a865af18dc
MODIFIED_FILE: /home/gypsophila/geotree/work/e01-p0d/MODIFIED_FILE
DIFF_FILE: /home/gypsophila/geotree/work/e01-p0d/DIFF_FILE
VERIFICATION.txt: /home/gypsophila/geotree/work/e01-p0d/VERIFICATION.txt
ROLLBACK.sh: /home/gypsophila/geotree/work/e01-p0d/ROLLBACK.sh
Commands cwd: /home/gypsophila/geotree/work/e01-p0
BASELINE command: bash isolated.sh .venv/bin/python ../e01-p0d/test_feedback.py ../e01-p0d/decision_bridge.frozen.py
Input: recorded offline ExecResult(return_code=0, stdout="fixture-ok\n", stderr=None); exit 1.
Literal error: TypeError: 'NoneType' object is not subscriptable
MODIFIED command: bash isolated.sh .venv/bin/python ../e01-p0d/test_feedback.py ../../src/geotree/decision_bridge.py
Same fixture input; exit 0.
Literal output: PASS offline Observe-Decide-Execute-feedback-DONE; nullable stderr normalized; one tool call
ROLLBACK command: bash /home/gypsophila/geotree/work/e01-p0d/ROLLBACK.sh /home/gypsophila/geotree/work/e01-p0d/rollback-test.py
Literal output: PASS original bridge bytes restored; exit 0.
Restored behavior test: bash isolated.sh .venv/bin/python ../e01-p0d/test_feedback.py ../e01-p0d/rollback-test.py
Same fixture; exit 1; TypeError: 'NoneType' object is not subscriptable.
Only separate rollback copy restored. Live source retains offline fix. No second real task attempt.
```

## 七、下一步

1. 不自动重刷本题；新一轮需明确登记新的开发尝试及历史失败。
2. 先补 nullable 输出、拒绝动作反馈、完整 trace/ATIF 与 relay 终止信号的离线测试；当前失败后的 relay 靠父进程终止，不是健壮生命周期。
3. 固定更小且可审计的模型上下文，完善全工具禁用验证；严审 AST 执行器或改为类型化 FreeCAD 操作接口。
4. 再验证一次完整的结果反馈及 CAD 生成、独立 verifier；目前还不具备“直接可用的 GeoTree-NoSearch”验收证据。
5. 维持 k=1，无 MCTS、无多候选实执行、无训练或全量 Benchmark。仅在稳定后讨论 GeoTree-Lite。
