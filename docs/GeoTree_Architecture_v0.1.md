# GeoTree Architecture v0.1 — NoSearch 冻结版

日期 2026-11-12；本版实现位于 `/home/gypsophila/geotree/src/geotree/nosearch.py` 和 `nosearch_agent.py`。现有 `DecisionBridgeAgent` / `GeoTreeNoModelAgent` 源码保持不变。本版不实现 MCTS 或 GeoTree-Lite。

## 模块及可替换接口

| 模块 | 已实现接口 | 职责 |
|---|---|---|
| ModelProvider | async propose(observation) -> ModelReply(payload, usage) | 只提出动作，不持有 Executor |
| CodexMailboxProvider | ModelProvider 实现 | 原子 Observation 文件、响应大小与超时、relay 错误信号；凭据不进入服务器 |
| JSONTransportProvider | ModelProvider 实现，注入 async transport | 为未来 DeepSeek 请求转换层预留统一输出；本轮没有实现或调用真实 DeepSeek HTTP 客户端 |
| MockProvider | ModelProvider 实现 | 与基模无关的离线行为序列与异常测试 |
| ObservationBuilder | build(instruction, history, turn, budget) | 仅公开任务指令、允许图片（外部附件）、动作反馈、剩余预算 |
| ActionProposal | frozen dataclass | request_id/action/code/reason，不包含任意目标容器或宿主路径 |
| ActionValidator | check(payload, observation) -> ActionProposal | 复用既有动作/AST 校验，检查 request ID、字段、预算；拒绝返回反馈，不执行 |
| Executor | async execute(proposal) -> feedback | 固定 /app 输出和工具入口；nullable 输出归一化；执行超时；容器非 root UID 65534 |
| FeedbackRecorder | record(event,data), step(action,feedback) | append-only raw JSONL、有效 ATIF-v1.8 序列；记录真实异常，不制造 score |
| NoSearch | k=1; select([proposal]) | 强制恰好一个候选，选择后只执行一次；多候选输入拒绝 |
| NoSearchRuntime | run(instruction) -> terminal status | 编排上述接口、预算、拒绝及工具超时反馈、正常/异常终止 |
| GeoTreeNoSearchAgent | Harbor BaseAgent 新入口 | 固定任务公开图片导出、受限容器 setup、运行 runtime、finally 写 terminal.json |

## 冻结的循环

1. 由任务公开 instruction 和上轮 feedback 构建 Observation；不加载隐藏 scorer 或答案。
2. 调用一个 ModelProvider，保留请求、响应及 provider usage。
3. 校验 Schema、request_id、动作类型、路径及预算。无效动作消费一次决策，写 rejected feedback；下轮可自行修正。
4. NoSearch 选择唯一候选。done 终止；其余动作由 Executor 执行。
5. stdout/stderr 的 None 归一为空串，各最多 12000 字符；非零退出、timeout、execution_error 全部反馈，不隐瞒。
6. 记录 raw trace 与 ATIF；达到 4 次决策或 done 后结束。之后由 Harbor 独立 verifier 评估最终产物，结果不回流给本试次决策。

运行器的 max_steps 可配置；本轮冻结为 4。Codex mailbox 最多等待 420 秒；单工具 timeout_sec=60、外层 wait_for=65。未知 provider 异常终止并保留 fatal/terminal；不是无条件重试。跨进程工具超时是否留下容器内子进程仍需专项验证，当前不宣称已彻底解决。

## 记录与 ATIF

JSONL 保留 observation、model_reply（含 usage）、feedback、fatal/terminal。ATIF 每个决策对应一个 source=agent 的 step，将 proposal/feedback 保留在 message，llm_call_count=1。可通过 Harbor 官方 validator。当前是最小有效编码，未将全部执行细节拆成标准 tool_calls/observation 边；研究分析优先使用并行 raw JSONL，不能称为完整工具语义标准化已经完成。

MockProvider 测试中的 llm_call_count 是逻辑决策次数，不是实际模型请求；离线目录不能混入真实费用汇总。真实 Codex 费用统计以 events JSONL 的 turn.completed.usage 为准，缺失不得填 0。

## 执行边界与已知限制

任务容器保持原生 CPU/RAM/GPU 配置。可信 setup 仅在本轮新容器内将 /app 和 /tmp/geotree-home 赋予 UID 65534，chmod 700 /logs；模型脚本以非 root 运行。任务容器不接收 auth.json、SSH 密钥、Docker socket 或其它项目挂载。脚本上传及容器调度属于可信宿主执行器，不是模型工具。

现有 AST 过滤是功能白名单和明显危险操作筛选，不是 Python 安全沙箱证明。FreeCAD API 的全部文件能力、表达式组合、符号链接 TOCTOU、容器逃逸以及所有宿主侧工具禁用并未穷尽证明。当前仅允许受控 DEVELOPMENT-ONLY；任何正式对照前冻结同样工具边界并完成必要负向测试。此次不扩张认证工程；保留核心功能所需的边界问题清单。

未来可将 Executor 替换为类型化 Sketch/Pad/Pocket 操作协议，不改变 ModelProvider/Runtime。不要将任意 shell 命令、宿主路径、verifier feedback 加入 Observation。模型 proposal 不得指定执行用户、容器 ID、挂载或网络策略。

## A0/A1 对照协议

机器可读配置 `/home/gypsophila/geotree/configs/comparison_v0.1.json`，状态 DESIGN_FROZEN_EXECUTION_NOT_AUTHORIZED。

- A0：DeepSeek V4.1 Flash + GeoTree-NoSearch（k=1）。
- A1：同模型 + GeoTree-Lite（k≤3，候选提议层排序，每回合只执行一个；尚未实现）。
- 精确 API 名 deepseek-flash；2026-11-12 [官方模型文档](https://api-docs.deepseek.com/quick_start/pricing/)映射 DeepSeek-V4.1-Flash-1017。执行前复核映射，变动则停止并新建配置版本，禁止悄然混用。
- 两组固定相同任务 digest、图片原件、工具/校验器版本、反馈、环境、effort、总决策和工具预算；只有 policy/candidate_count 不同。未核验的 effort/API 参数不能冒称已经生效。
- 所有模型请求（包括候选生成/排序）、输入/缓存/输出/reasoning token（接口提供时）、工具次数、wall time 均计费计数；按实际日期价目计算 USD。A1 更多候选成本须显式报告，用配对结果及 score-vs-cost 曲线解释，不靠忽略额外调用制造收益。
- 现有单题已多次用于开发，只能归入 seen development。正式 evaluation_tasks 尚未选定；冻结不重叠集合、预算上限、prompt 哈希后方可实验。本轮没有授权 DeepSeek API 开支。
- `docs/baseline_snapshot.md` 中官方 Codex、Claude Code 等历史结果继续作为外部参考，不替代同模型 A0/A1 因果对照。DSH 为可选项，不阻塞主线。

## 冻结与下一阶段门槛

旧入口保持兼容；本版新入口独立 import path `geotree.nosearch_agent:GeoTreeNoSearchAgent`。原始历史失败永不重写。当前执行证据、失败和 token 统计见同目录 E01_P0E_report.md。

下一阶段直接围绕 NoSearch → Lite 方法开发：补核心功能缺陷、接入统一 DeepSeek transport、冻结配对子集与预算；不继续扩张 Codex 登录方案。正式方法实验要求：有效 CAD 产物/完整反馈链、独立评分、可比权限、完整 usage 和失败保留。即使 Codex 开发测试成功，也不称为 DeepSeek/GeoTree-Lite 已有成绩。

### SearchPolicy 类型契约

`src/geotree/policies.py` 提供结构化 `SearchPolicy` Protocol（k 与 select），现有 NoSearch 以结构类型满足该接口；Runtime 的 policy 属性可替换。`CandidateBatch` 限制 1≤候选数≤3，供后续 Lite 接口使用；没有实现多候选生成或排序，也没有在本轮真实试次启用它。A0/A1 设计预算为每题总 token 上限 100000、费用上限 1 USD，仅是待授权的计划上限，不授权任何 API 支出。
