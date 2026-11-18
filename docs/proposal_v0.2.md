GeoTree v0.2｜基于公开 CAD Benchmark 的搜索式 Agent Harness
内部开题 / 研发与实验协议（供自己、队友与 Codex 使用）
日期：2026-11-11｜赛道：第六届厦门大学人工智能挑战赛 · AI Agent 创新赛
项目对外名称可沿用 「智绘成型」；内部算法与系统代号 GeoTree。
状态：PLANNED / NOT IMPLEMENTED / NO OUR RESULTS。 本文是计划，不是成果报告。
一句话目标：不训练模型、不自建 Gym、不绑定 NX；在既有 3D CAD 基准上开发 GeoTree Harness，以公开完整成绩为外部参照，用自己的真实运行验证搜索和状态反馈是否有效。

0. 已冻结的决策与不再讨论的工作
项目	v0.2 决定	备注
作品对象	能独立执行 CAD 任务的 GeoTree Agent Harness	不是新 LLM/VLM 权重，也不是包装提示词的聊天应用
任务载体	公开 Parametric CAD Bench V3 与 CADWorld	FreeCAD 环境，取消自制 CAD Gym
最初的 NX 12.0	不作为必做依赖	原比赛方案获准调整；保留“可验证建模”的问题意识
基座模型	deepseek-flash（DeepSeek V4.1 Flash）优先；`gpt-6.1-terra` 作为第二模型候选	两者均有图像输入能力；需审计实际 API、调用格式和费用
方法参考	ToolTree：候选工具规划、前/后反馈、剪枝	GeoTree 不是直接照搬 MCTS；先做有限候选搜索
公开强基线	复用 CAD Bench / CADWorld 官方完整历史运行与排行榜	不重复付费重跑 Codex/Claude Code 等已有完整结果
直接归因对照	自研 GeoTree-NoSearch vs GeoTree-Search，尽量同模型/工具/预算	用于验证“搜索”的增量；可选少量 DSH 对照
DSH（DeepSeek Harness）	外部 Harness 参考与可选同模型对照	若无对应官方已发布成绩，不得虚称有 DSH 官方分数；不强制完整重跑
实验顺序	E00 协议和环境审计 → E01 最小闭环 → E02 搜索 → E03 小规模冻结消融 → E04 正式评测 → E05 展示	不在 E00 发起付费评测
最终展示	真实 Agent Demo + Harness 架构图 + Trace + 官方参考成绩 + 自研真实跑分/消融	不能只放排行榜截图


三个禁止偷换的概念：
1. 公开基线的分数 ≠ 相同模型下更换 Harness 的受控实验。 比如“GPT-6 Astra + Codex”不能被解释为“GPT-6.1 Terra + DSH”。
2. 两个基准不是同一分数体系。 CAD Bench V3 是连续奖励均值；CADWorld 是严格通过率，不能跨基准相加或平均。
3. 同名“GeoTree”不代表已有算法 Novelty。 是否有改进必须靠实测、消融及对相关工作的边界说明。
1. 科学/工程问题与假设
1.1 核心研究问题
多模态模型可以读工程图、看 FreeCAD 截图，并提出下一步 CAD 操作；但三维任务同时有几何约束、长程依赖、执行副作用、观察不充分等性质。
在基座模型固定、可用动作与观察权限一致时，面向 CAD 状态的有限预算候选规划 + 执行后反馈，是否比简单的逐步工具调用取得更好的最终任务质量？代价是多少？

1.2 可证伪假设
- H1（搜索）：`GeoTree-Search` 优于工具与环境反馈相同的 GeoTree-NoSearch；主要体现在复杂依赖、状态改变和恢复类任务中。
- H2（成本）：搜索可能提高任务质量，但增加模型调用、时间与 Token；必须同时报告收益—成本曲线，不能仅比较成功率。
- H3（模型规模交互）：在不同多模态基模上，Harness 增益可能不同；不预设较强模型必然获益更少。
- H4（跨交互方式）：同一规划框架在 代码/工具驱动 CAD 和 截图/GUI 驱动 CAD 中可能部分通用，但状态访问权限必须分别满足官方协议。
可能的否定结果： 强基模贪心执行已足够好；候选搜索只是多花 Token；GUI 环境下预检查信息不足；执行器不稳定比规划更突出。允许这些成为真实结论，不能为了“创新点”筛选任务。
2. 两个公开 Benchmark：就用现有考场，不造 Gym
2.1 主基准：Parametric CAD Bench V3
- 官方说明：https://www.gnucleus.ai/cad-bench/benchmark
- 官方榜单：https://www.gnucleus.ai/cad-bench/leaderboard
- Harbor 数据集：https://hub.harborframework.com/datasets/gnucleus-ai/cad-bench/v3
- 任务数量：100，其中 30 Text-to-CAD Create / 30 Create+Edit / 40 Engineering Drawing-to-CAD。
- 官方发布的运行环境：Harbor 0.23.0；FreeCAD 1.1.0；gnucleus-freecad-validator 0.6.0（v2 scorer）；Harbor schema 1.3。
- 核心指标：每题 reward ∈ [0,1] 的平均连续奖励，榜单使用 0–100 表示。失败或无分任务计 0；可附带 Perfect 数量、子类型结果、费用、时间、有效任务数。
- 官方完整提交协议：100 题完整 cohort；每题 1 attempt、0 retries；遵守 9000 秒限制和有效模型 reasoning effort 的官方规则；保留失败记录、生成 CAD 文件、评分输出和轨迹；完整提交需要公开 Harbor job 并经审核。
- 官方要求 Agent 与 validator 隔离，不得把验证答案、标准答案或隐藏评价字段暴露给做题 Agent。
- 官方示例数据摘要（审计时须在当前版本核实）：`sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`。
使用方式：先做 合法 smoke test / 冻结的开发子集，再视预算决定能否对 GeoTree 完整跑 100 题。小样本必须标注“内部开发/子集结果”，不能称为官方完整分数或提交排名。

不可预先假定：任何自研 Python/TypeScript Harness 都能直接作为 harbor -a 参数运行。需要根据 Harbor 的实际 Agent 接口开发启动器/适配层，不能仅改一个字符串就当作完成。
2.2 次基准：CADWorld
- 官方仓库：https://github.com/Zdong104/CADWORLD
- 项目页面：https://cad-world.github.io/
- 200 个 FreeCAD Computer-Use 任务，Agent 通过截图观察、通过 GUI 指令操作，结果以保存的 .FCStd 文件由宿主侧验证。
- 核心指标：strict pass rate（全部检查通过的任务占比）；可分析具体类型、操作步骤、失败归因。
- 官方测试采用固定 GUI 交互预算；正式复现必须检查对应论文/仓库版本的步数和配置，不能把 README 的短 smoke-test 步数当正式条件。
- 安装环境：Linux/Ubuntu、Docker、KVM、`uv`，虚拟机镜像约 35 GB；默认 VM 资源约 8 vCPU、8 GB RAM（审计时核实）。
- 自定义 Agent：官方仓库允许 --agent module:Class，需实现 reset() 与 predict(instruction, obs)；`obs` 包含截图，返回能被 CADWorld 接受的动作格式。
- 轨迹输出：`traj.jsonl`、截图、录屏、运行日志、`result.xlsx` 等，按当前 README 核实。
关键协议边界： 在标准 GUI-only 评测下，不能让 GeoTree 额外通过 Shell、FreeCAD Python API 或隐藏 evaluator 读取几何真值，否则已经不是与官方 GUI-only 基线同一种考题。几何理解可来自允许的截图、UI 可见状态和合法动作反馈。
2.3 解释两个分数时应当这样写
维度	CAD Bench V3	CADWorld
核心能力	代码/工具驱动的参数化 CAD 生成、编辑、工程图理解	真实 FreeCAD GUI 的观察与操作
官方样本数	100	200
核心结果	平均连续奖励（0–100 量表）	严格任务通过率（%）
样本最小单元	一个官方 task/trial	一个官方 GUI 任务
对外报告	Overall + Create/Edit/Image 子项	Overall + 工作流/类别子项
官方历史成绩的角色	外部强系统参考	外部强系统参考


3. 强基线：哪些只引用，哪些一定要自己跑
3.1 已公开的强系统：不花费 Token 重跑
CAD Bench V3 当前公开历史结果示例（查询于 2026-11-11，数值为平均连续奖励 ×100，不是成功率）：
模型 + Harness	官方 Overall	来源性质
Claude Opus 5.5 + Claude Code 2.1.280	61.03	官方完整公开运行
Claude Opus 5.5 + mini-swe-agent 2.4.6	57.96	官方完整公开运行
GPT-6 Astra + Codex 0.154.0	56.87	官方完整公开运行
Gemini 3.8 Flash + mini-swe-agent 2.4.6	36.19	官方完整公开运行


来源：https://www.gnucleus.ai/cad-bench/leaderboard；任何最终报告必须再次记录查询日期、版本、官方 run URL 与评分口径。

CADWorld 当前公开历史结果示例（查询于 2026-11-11，百分数为严格通过率）：
官方报告行	通过率	来源性质
Opus 5.5 EXT	41.5%	后续扩展实验
GPT-6 Astra EXT	33.0%	后续扩展实验
DeepSeek V4.1 Flash EXT	7.5%	后续扩展实验


来源：https://cad-world.github.io/。`EXT` 与原论文实验不是同一发表批次；必须保留标注。排行榜行通常混合基模、Harness、模型 effort、工具、运行环境等因素，禁止单独归因于模型或 Harness。
3.2 我们的基模：优先省预算，但必须能看图
选项	模型 ID	用途	约束
M0 主模型	deepseek-flash	开发与第一轮 GeoTree 实测	已有官方视觉输入支持；需核实 API 模式、图像传输、Tool Calling、价格与额度
M1 验证模型	gpt-6.1-terra	多模型迁移/演示备选	官方支持图片输入；工具调用经 Responses API；API 费用独立于 ChatGPT/Codex 开发额度
额外强模型	暂不指定	可选冲刺对照	不因为官方已有高分就承担完整复跑成本


官方模型资料：https://api-docs.deepseek.com/guides/vision/、https://developers.openai.com/api/docs/models/gpt-6.1-terra。
模型选型与公平性原则：同一对照必须固定精确模型 ID、版本或查询日期、输入图像尺寸/压缩策略、推理 effort、工具列表、系统提示版本、可观察状态及预算。不同提供商是否支持完全同构的采样配置，先审计再决定。

3.3 DSH 的位置：不是非跑满不可
- DeepSeek Harness 官方源：https://github.com/deepseek-ai/deepseek-harness。
- DSH 采用可插拔能力/工具机制，有自定义模型提供商配置；但 DSH ≠ 一个保证能直接进入 Harbor/CADWorld 的现成 Agent。
- 优先： 以其默认架构和工具能力作为工程参考，检查与两套 Benchmark 的接口、视觉消息、状态保存的适配成本。
- 可选： 若发现可稳定接入且预算允许，对预先冻结的少量任务做 M0 + DSH vs M0 + GeoTree 同模型同权限对照。
- 不做： 为了“证明超过 DSH”而重新跑完公开已有的 100/200 题强模型基线；若没有 DSH 完整同模型数据，只把 DSH 标为“参考/未做完整直接比较”，绝不虚构 DSH 成绩。
3.4 必须做的内部方法消融
组别	模型	Observation / Tool	搜索	目的
G0：GeoTree-NoSearch	M0（固定）	与 G1 完全一致	关闭	基线：同一运行器、同一状态反馈，直接选择单动作
G1：GeoTree-Search	M0（固定）	与 G0 完全一致	开启	测搜索与剪枝本身的附加收益
G2：GeoTree-Search (M1)	M1（可选）	与该模型可支持的同等协议	开启	模型迁移与适用边界
G3：DSH (M0)	M0（可选、限小样本）	尽量等价并明示差异	DSH 原机制	外部 Harness 的直接对照


主要因果证据：G1 − G0（配对任务），而不是 G1 与官方其它模型/其它 Harness 的差值。
4. GeoTree v0.2 初定 Harness 架构
4.1 统一任务循环（而非堆多个 LLM）
Benchmark Task ──► Adapter (CAD Bench / CADWorld)
                        │
             allowed task + observation
                        ▼
         ┌───── GeoTree Runtime ─────┐
         │ Model Provider Adapter    │  M0 / M1, multimodal I/O
         │ Observation/History Store │  images + action outcomes
         │ Candidate Generator      │  next-step alternatives
         │ Pre-Check & Prune         │  schema / visible preconditions
         │ Budgeted Search Policy    │  limited candidates; optional tree
         │ Action Executor           │  benchmark-allowed actions ONLY
         │ Post-Check & State Update │  observation-based progress check
         │ Trace/Cost Recorder       │  no hidden grader / no raw chain-of-thought
         └─────────────┬─────────────┘
                       │
                selected action
                       ▼
           Benchmark Environment
                       │
                real tool/GUI result
                       └──────── feedback ──► Runtime

        Official evaluator (isolated, receives final artifact)
规划、执行、验证是模块职责，不意味着必须并行跑三个 LLM。 系统只展示模型输出的行动摘要、候选和可观察理由、工具日志、结果检查；不需要或不应该声称暴露模型不可见的内部思维链。
4.2 各模块最小接口契约（待 E00 确认）
TaskInput:      {task_id, instruction, images?, initial_artifacts?, allowed_actions, budget}
Observation:    {screenshot?, visible_ui_state?, tool_outputs?, action_history, budget_left}
ActionProposal: {action_type, arguments, local_confidence?, declared_preconditions?}
Precheck:       {valid, reason_codes, observable_evidence}
Execution:      {requested_action, accepted_action, tool_status, new_observation, elapsed_ms}
Postcheck:      {observed_change, progress_evidence, error_reason, next_decision}
Trace:          {task_id, model_id, harness_sha, action, feedback, token_cost, timestamps}
上述只是项目内部抽象，不代表 Benchmark 原生字段就叫这些名字。适配器必须翻译到当前官方接口，不能偷偷升级 Agent 的观察权限。
4.3 搜索算法的务实第一版
GeoTree-Lite：`Generate k → Validate → Rank → Execute 1 → Observe → Replan`。
1. 基模给出最多 k=2~3 个候选下一动作（初始超参数，非既定最优值）。
2. 执行前检查格式、动作权限、可见界面或历史约束，剔除非法/不可执行候选。
3. 以任务进展的可观察线索、预计风险、所需动作数与预算进行有限候选排序。
4. 只执行一个选定动作，立即获取真实观察，再决定继续、修复、放弃。
5. 遇到不可确认的真实状态时，优先读取允许观察；若无法验证，则保守地停止/标记不确定，不能声称成功。
ToolTree 可借鉴： pre-evaluation、post-evaluation、bidirectional pruning、候选路径评价与有限预算搜索。其官方仓库的默认 mock 主要是计划级评测，真实工具 backend 需要适配，不能将复制 MCTS 代码等同于在 CAD 中完成真实树搜索。

暂不承诺： 完整 MCTS、任意 GUI 动作的 checkpoint/rollback、每一步的多分支真实执行。如果环境不能可靠快照，那么不能在正式 trial 内把不同候选分支都实际执行后又当作“同一个未改变的世界”。这时搜索只能在可观测历史/动作提议层面进行。
4.4 两个 Adapter 特别注意
- CAD Bench Adapter： 先审计官方任务允许哪些命令、文件、FreeCAD 接口及图像输入。只能使用公开任务条件与允许工具，不得通过独立验证器读答案。对输出的 FreeCAD 工程文件负责。
- CADWorld Adapter： 仅使用允许的截图与 pyautogui 动作；遵守 reset() / predict()、规范化动作输出，区分模型原话与真正执行的动作；如动作被校验器转成 WAIT，日志中必须保留事实。
4.5 让算法可复现，而不是让提示词越来越长
必须版本化：模型路由、任务 ID、随机种子、Prompt 版本、动作集、图片序列化、candidate_count、budget、剪枝阈值、工具执行记录、有效 reasoning effort、git SHA、结果与成本。

搜索是否比单步更强，不应靠“增加更多隐藏提示词、额外工具、模型思考轮数”偷偷获得优势。 至少展示等步数、等资源/预算或 score-vs-cost 曲线。
5. 评测协议与可信度
5.1 运行划分
1. E00 审计：不调用付费模型，不产生分数；只验证仓库、协议、环境与适配接口。
2. Smoke：官方允许的 1～数题调试任务，确认真实截图、动作、保存文件、独立评分链跑通；明确标记“debug”，不能作为论文/榜单分数。
3. Development：预先冻结小型子集，查找故障并调方法；保留全部尝试和失败。
4. Evaluation：冻结方法和参数后，再选择可负担的独立评测任务；若成本允许，完成官方要求的完整 cohort。若没跑满，所有结果都必须标注“非官方完整评测”。
公开 benchmark 的任务可能已被开发者看过；应记录开发任务与报告任务的重叠，不能把公开题集经过反复调参后的成绩称为完全无污染的泛化验证。
5.2 主要指标
CAD Bench V3：
- Overall = 100 × mean(reward_t)，每个 t 属于标准任务集，失败/无结果为 0。
- 三个类型各自平均分（Create、Create+Edit、Image-to-CAD）。
- Perfect tasks / scored tasks / invalid artifacts / verifier failures。
CADWorld：
- StrictPass = (# 全部必要检查通过的任务) / (# 全部官方任务)。
- 分工作流通过率、GUI 动作数、无效输出被标准化为 WAIT 的频率、是否保存最终 .FCStd。
跨基准共有： 输入/输出 Token、API 费用、模型调用次数、CAD 工具/GUI 调用次数、总耗时、超时与崩溃率、失败类型（感知/规划/动作格式/执行/验证/预算）。
5.3 对比的三种证据层级
证据等级	可以声称什么	不可以声称什么
A：同模型/同任务/同协议的 GeoTree 消融	“在当前任务与预算条件下，搜索造成的配对增量”	小样本一律推广为领域 SOTA
B：同 Benchmark、不同模型/Harness 的官方历史成绩	“我们与公开强系统有多少性能差距/大致位置”	“优于 DSH 是因为搜索”“Harness 带来 x pp 因果增益”
C：开发子集/现场 Demo	“方法能运行、产生指定日志/成品、若干任务成功”	“已获得官方完整榜单成绩”


如果有足够样本，计算配对差值和 bootstrap 95% CI；对样本不足的结果只做描述性统计。最好展示按难度/类别分层的结果、失败例，以及分数对 Token/时间预算的曲线。
5.4 防止无意中的“不公平”
- 不修改 benchmark tasks、隐藏检查器、参考答案或评分脚本。
- 不让 Agent 拥有基线没有的额外感知渠道，却在同一榜单口径比较。
- 不能把“DeepSeek Flash + GeoTree”与“GPT-6 Astra + Codex”的差异解释成 GeoTree 的因果提升。
- 不主动丢弃难题、失败试次或超时试次。
- 单次 trial 的候选动作与多次 benchmark attempt 不同；任何 reset/retry 必须在该 benchmark 规则允许的范围内。
- 自己做的中途评分、LLM judge 和官方最终 evaluator 必须明确分开。
6. 环境隔离与 Codex 的角色
6.1 推荐部署
Windows PC / Codex (开发、SSH、审计、发起实验)
            │
            └─SSH / VS Code Remote─► Ubuntu 24.04 主机
                                   ├─ /project/GeoTree (源码/文档，独立 venv)
                                   ├─ /project/third_party (官方仓库，固定 SHA)
                                   ├─ sandbox: CAD Bench V3 / Harbor / Docker
                                   ├─ sandbox: CADWorld / QEMU-KVM / Docker
                                   ├─ model API: DeepSeek / OpenAI（密钥注入）
                                   └─ results/ (不可改原始轨迹 + 报告)
Codex 是开发者/审计者，不是正式评测时的“隐形帮手”。 Codex 可以写 GeoTree 的适配器、分析断点、整理日志，但真正做题的是受限任务容器内的 GeoTree + 选定基模。Codex 不可利用宿主机权限实时帮助考生看答案。

ChatGPT Pro 订阅可以用于 Codex 开发的相应额度，不等于自动为 GeoTree 提供 DeepSeek/OpenAI API 调用预算。正式评测的独立 API 授权、费用上限与 Rate Limit 需要自行确认。
6.2 安全与系统约束
- 实验项目不触碰现有服务器上的科研代码、GPU 训练任务、SSH/Tailscale 网络服务及其他工作目录。
- 第一次运行前检查 /dev/kvm、Docker、可用磁盘、内存、网络；CADWorld VM 下载约 35 GB 必须先确认空间并由人授权。
- sudo、Docker 服务变更、系统包修改、大镜像下载、付费模型调用、公开上传等操作需要明确授权。
- 密钥只保存在受保护的本地环境变量或 Secret 注入中；不输出、不提交、不复制到日志与 Prompt。
- 正式评分器与考生环境分离；保存任务日志的哈希与模型/代码/任务版本。
7. 开发任务与 Stop/Go 条件（以 2026-12-05 初赛为目标）
阶段	工作	可交付物	Gate
E00：协议/环境审计	检查 Linux、仓库版本、官方榜单快照、Harbor Agent contract、CADWorld Agent contract、模型 I/O 和 DSH 接口	docs/E00_audit.md、`docs/baseline_snapshot.md`、适配风险表	能说清楚合法的最小运行路径；未跑付费任务
E01：最小做题闭环	单 Agent、单模型、单任务，真实观察→执行→反馈→保存→官方评测	可运行 GeoTree-NoSearch，完整 trace	至少一个官方调试任务跑通并能复现
E02：GeoTree-Lite	有限候选生成、pre-check、排序、执行后评估、预算管理	GeoTree-Search + 单元测试	有可审计候选、剪枝、执行/验证记录
E03：冻结开发子集	相同 M0 运行 G0/G1；统计失败原因、Token、耗时	消融表和案例记录	只在真实结果支持时才声称搜索收益
E04：标准化评测	预算允许时完整跑 CAD Bench V3；CADWorld 优先一个标准协议的小规模测试，并尽力扩展	本地得分/若完成官方 cohort 则正式结果	不混淆小样本与官方榜单；不强制花钱冲排名
E05：现场演示	指定官方 benchmark task 的合法演示、架构图、Trace UI、最终模型文件与答辩	稳定 Demo + 可验证录屏备份 + 技术报告	真实工具闭环与自主代码贡献清晰


及时降级原则：
- Harbor custom agent 接入太难：先打通 CADWorld 自定义 Agent；CAD Bench 作为后续，不能卡死全部进度。
- KVM 不可用或 CADWorld VM 资源不足：先完成 CAD Bench；不冒称已有跨环境实验。
- 搜索收益为零或负：保留架构与可靠性实验，以“搜索何时无益、成本几何”客观呈现；不随意筛题。
- API 预算不足：以官方历史成绩做外部参照，用极小成本的真实 Demo + 冻结子集消融，不硬凑官方全量榜单。
- 单任务环境不支持安全回滚：保持有限候选执行前排序，不做假 MCTS。
8. 代码与记录文件约定
建议目录，仅是设计；E00 不得把未创建的模块说成已经实现。

GeoTree/
├── AGENTS.md                     # 给 Codex 的项目规则（适用范围内自动发现）
├── README.md                     # 复现指南与项目入口
├── pyproject.toml / package.json # 根据实际接口选一种主要运行语言
├── docs/
│   ├── proposal_v0.2.md          # 此开题（可复制到 repo）
│   ├── MEMORY.md                 # 人工维护的事实/实验决策索引；非通用自动记忆标准
│   ├── E00_audit.md
│   ├── baseline_snapshot.md
│   └── experiments/
├── src/geotree/
│   ├── core/                     # 单 Agent 运行器、预算、候选搜索
│   ├── models/                   # 两个模型提供商适配器
│   ├── adapters/                 # cad_bench / cadworld
│   └── telemetry/                # action/observation/usage traces
├── tests/
├── configs/
├── third_party/                   # 官方代码只读使用、记录 Git SHA
└── results/                       # 原始轨迹不可原地改写，配置、分数、图表
AGENTS.md 是项目执行规则；`docs/MEMORY.md` 是人工/Agent 维护的研究事实摘要，不保证被所有 Harness 自动读取；`SKILL.md` 是以后有稳定标准化评测流程时才需要制作的可复用操作说明。不为了“Agent 含量”而堆三类文件。

推荐 results/<benchmark>/<run_id>/manifest.json 至少包含：`benchmark_name/version/task_digest`、`task_ids`、`model_id/provider`、`harness_git_sha`、`effort/temperature/seed`、`image_policy`、`allowed_tools`、`search_k`、`budgets`、`cost`、`started_at`、`status`、`score_file`、`trace_path`。失败试次也必须保留。
9. 比赛要求与现场叙事
校赛 Agent 赛道要求自主目标分解、工具调用、环境反馈循环，明确排斥纯多轮聊天套壳；评分重视 Agent 架构（30）、自主闭环（25）、工程规范（15）、答辩展示（15）、场景价值（15）。

建议叙事顺序：
1. 问题：即使模型能看工程图，复杂 CAD 多步操作仍会产生规划错误、动作无效与反馈失配。
2. Baseline：先交代两套公开 Benchmark 及历史强系统，不伪称为自测。
3. 方法：在同基模下，用执行前候选筛选、有限预算规划和执行后反馈组织 GeoTree。
4. 真实 Demo：任务输入/截图 → 候选操作 → 选择/剪枝理由 → 实际 GUI/工具动作 → 回传状态 → 保存可编辑结果 → 标准评分器输出。
5. 实验：有真实数据才展示分数；优先给 G0/G1 同模型消融，以及相较官方参考系统的背景位置。
6. 边界：资源、输入观察权限、MCTS 不可回滚、榜单与我们模型不同等问题如实说明。
验收的最低标准： 至少一个真实任务可稳定交互完成并被标准评价器检查；能清楚解释自研代码与官方框架的边界；有完整调用链与实际生成 CAD 文件。不承诺一定超过 SOTA，也不把“校赛可行”冒充“已具论文 Novelty”。
10. 给 E00 的第一道审计题
先回答，暂不写搜索算法：
1. 两个 Benchmark 的官方精确版本、下载体量、依赖、可使用工具以及完整评分口径是什么？
2. Harbor 可以用什么真实接口接入一个全新 Agent？`--agent` 接受什么，最小可执行的 adapter 是什么？
3. CADWorld 的自定义 Agent reset/predict 实际签名、图片格式、动作契约及 evaluator 隔离是什么？
4. DSH 的图像输入、模型路由、命令行/SDK 与外部控制接口在哪里？是否值得用作同模型对照，或者工作量过高？
5. ToolTree 的哪些模块能复用？默认 mock 与 real 模式各有什么限制？
6. 在不付费、不碰原有科研环境的条件下，能跑什么级别的 smoke test？
7. 当前公开强基线的版本、完整来源 run、模型与 Harness 配置能否复核？
8. 如果不存在 API Key / KVM / Docker / 足够磁盘空间，应如何无损降级？
产物：`docs/E00_audit.md` + docs/baseline_snapshot.md + 一个简明的推荐启动顺序与 GO/NO-GO 表。Codex 任务的完整操作约束见另一文件《GeoTree_E00_Codex_审计Prompt_v0.2.md》。
11. 资料（核查日期 2026-11-11）
校赛材料（用户提供）
- 《第六届厦门大学人工智能挑战赛通知-终版》：Agent 赛道规则、架构/闭环/现场演示与评分细则。
- 《智绘成型_第六届厦大AI挑战赛设计方案_官方模板版》：原 NX 12.0 方案；已获确认允许改题。
官方 Benchmark 与历史结果
- CAD Bench V3 运行协议：https://www.gnucleus.ai/cad-bench/benchmark
- CAD Bench V3 历史榜单：https://www.gnucleus.ai/cad-bench/leaderboard
- CAD Bench V3 Harbor：https://hub.harborframework.com/datasets/gnucleus-ai/cad-bench/v3
- CADWorld 项目/历史结果：https://cad-world.github.io/
- CADWorld 代码与 Agent API：https://github.com/Zdong104/CADWORLD
- CADWorld action contract：https://github.com/Zdong104/CADWORLD/blob/main/docs/MODEL_OUTPUT_CONTRACT.md
方法、基模与外部 Harness
- ToolTree（ICLR 2026）实现：https://github.com/SYang2000/ICLR_2026_ToolTree
- DeepSeek Harness：https://github.com/deepseek-ai/deepseek-harness
- DSH 自定义模型配置：https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.md
- DeepSeek Vision：https://api-docs.deepseek.com/guides/vision/
- OpenAI GPT-6.1 Terra：https://developers.openai.com/api/docs/models/gpt-6.1-terra
文件治理：官方网页与 API 文档可能更新。E00 应将当前 Git SHA、原始参考链接、抓取日期与未证实事项写进审计报告，不以本开题的描述替代运行事实。