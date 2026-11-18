# GeoTree E00｜Adapter 矩阵

日期：2026-11-12。以下为接口设计，不是实现。上游版本与证据见 [E00_audit.md](E00_audit.md)。

## A. Parametric CAD Bench V3 / Harbor

| 契约 | Benchmark ↔ GeoTree | 验收点 |
|---|---|---|
| Benchmark input → GeoTree input | Harbor `run(instruction, environment, context)` 接文字；在容器内把任务指定的工程图读为 bytes，并传为 provider image part；编辑用任务当前 CAD 状态/产物，不假设总是预置文件。 | 固定 digest、每题先由 task instruction 解出允许的输入/输出；无扩展数据源。 |
| GeoTree action → tool | 只在 `environment.default_user` 下执行经验证的任务工具，如任务内 FreeCAD 运行与 /app 文件操作；模型提议不是宿主命令。 | 执行器限制工作区和出网；保留 shell/文件错误为文本，不能误编码成图片。 |
| Benchmark feedback → observation | stdout/stderr/退出码、任务文件状态、允许的视图或自检结果；trace 记录候选、动作和反馈。 | verifier 分数、测试目录、隐藏几何均不回流 agent；同模型两条件接收相同观测。 |
| Final artifact → validator | 按题指定路径保存 CAD/必要输出，Harbor 单独 verifier 用 0.6.0/v2 scorer；产物、配置、agent log、ATIF 一并留存。 | 初始 nop 缺产物/0 分可预期，须以真正产生 verifier 结果判定链路跑通；不能用退出 0 替代。 |

## B. CADWorld 原生 GUI-only runner

| 契约 | Benchmark ↔ GeoTree | 验收点 |
|---|---|---|
| Benchmark input → GeoTree input | `module:Class` 无参构造，`reset` 清历史，`predict(instruction, obs)` 仅使用 PNG 截图、任务参考图和文本；初始文件由环境预置。 | 不传 VM IP、terminal、a11y、host 文件或 FreeCAD 内部对象给模型。 |
| GeoTree action → tool | 声明式 `GuiAction`（click/move/drag/scroll/press/hotkey/write/WAIT/DONE/FAIL）经过参数/坐标/白名单检查，由 adapter 序列化成固定 GUI 调用。 | 自定义入口无自动 sanitizer；不执行模型生成的 Python 字符串，不允许用键鼠打开 shell、注入脚本或绕开观察限制。 |
| Benchmark feedback → observation | runner 执行 1 个动作，回传下一帧截图；可用自己的上一动作与 GUI 变化做反馈。 | 无模拟多分支、无快照复位、无内部几何/评分回流；记录原响应、解析、执行与时间。 |
| Final artifact → evaluator | 在 GUI 中保存题目要求的 .FCStd/附件，然后 DONE；runner 在 host 拿产物跑真实检查。 | DONE ≠ PASS；按题存截图、traj、result、diagnostics、产物；不以分步 reward 作为最终通过依据。 |

## 共享与隔离

- **共享**：Observation/ActionProposal/ActionResult 抽象、不可变候选排序、step 计时、模型 token/美元预算、错误语义、原始和生效 effort、图像 MIME/大小校验、日志脱敏。
- **隔离**：Harbor 允许的任务文件/FreeCAD 工具与 ATIF；CADWorld 只允许 GUI 动作、截图和原生 JSONL。不能共用工具白名单、隐藏评分、环境状态、轨迹记账或终止判据。
- **Provider 特定**：DeepSeek Chat 的 image_url/tool_call_id/reasoning history；OpenAI Responses 的 input_image、output items/call_id 和 reasoning.effort；输出上限、缓存字段、思考回放和错误处理保留 provider 原值。统一可见字段：指令、图片、schema、调用 ID/结果、token、耗时。先用合成图/录制响应校验 bytes→data URL→JSON→本地回读；实际 provider 接收/回传另做单次受控 smoke。
- **GeoTree-Lite**：每个可见状态生成 k≤3 候选 → schema、权限及重复动作过滤 → 在同一次决策内排序 → 最多执行 1 个 → 用实际反馈更新下一轮历史；无候选时选择确定性 WAIT/FAIL 策略。NoSearch 用 k=1，共享执行器与模型快照、effort、工具、输入、上限及预算，报告实际成本差异。不把排序分数当 evaluator 奖励。
- **DSH**：Harbor 可考虑在既定容器内运行 headless/SDK 并桥接日志与图片；需锁 plugin/profile、工作目录、模型出网与 ATIF，估计 2–4 工程日验证。CADWorld 需要隔离 SDK 默认 shell/files 工具、仅暴露 GUI 动作或单步输出，维护 session 跨步、截图和预算；估计 3–6 工程日验证，取决于工具配置与 SDK API。自研薄 adapter 粗估 Harbor 1–3 日、CADWorld 1–3 日，均不含 VM 审批、完整评测、provider/网络故障。估算非实测。
