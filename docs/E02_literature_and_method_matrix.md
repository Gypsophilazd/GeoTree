# E02-B：方法 Kill Search 与迁移矩阵

**状态：PARTIAL。** 八项工作均查阅指定论文或作者页面；六个官方源码入口有固定版本核查，其中 PhysCAD 仅 README；NaviAgent、Asymmetric Verification 未确认官方可执行源码。不是完整复现，无模型、数据集或训练依赖安装。证据强度不互相替代。

## 1. 核心问题、机制与训练（每项仅给可迁移结论）
|工作|具体问题与核心机制|是否训练|对目标几何/回滚的依赖|
|---|---|---|---|
|ToolTree|工具选择与长链决策；candidate expansion，LLM pre/post evaluation，双向剪枝及树搜索|推理侧机制本身不要求训练|上下文复制不是环境快照；真实有副作用工具需另行处理状态；mock 与 real 不等价|
|Gecko|执行前工具调用可行性；schema/规则+模型校验，维护模拟状态，GATS先模拟再修正|推理机制可不训练|模拟状态不等于 CAD kernel；未提供可证明的真实CAD回滚或几何oracle|
|NaviAgent|大工具集规划协调；工具网络、层次/双层规划与执行协调|原方法包含决策SFT与图模型学习，不是纯手写无训练图|API依赖图不同于几何拓扑；完整方法不直接提供CAD快照|
|ToolPro|多工具程序的副作用与重试；effect-aware replay、WRITE前缀/幂等约束、执行运行时|核心接口不要求新模型训练|exactly-once须依赖可记录的写入、幂等/重放协议；不能推广为任意FreeCAD脚本原子回滚|
|Asymmetric Verification|深搜索预算收益递减；候选生成与验证分工，把算力用于更可靠选择|核心为test-time计算分配|验证优势依任务成立；LLM事实核验不是确定性CAD目标正确性|
|Budget-Aware Agent|受限工具/计算预算；budget tracker、自验证与按预算继续探索/选答|推理机制不要求训练|原任务偏信息检索；并行轨迹不能直接迁移到共享CAD文档副作用环境|
|StepCAD|mesh到可编辑CAD程序；状态条件策略+几何引导局部编辑/beam|策略训练；发布权重与论文数据规模存在版本差异|明确使用输入目标mesh及IoU排序；本任务只有工程图，不能偷换成隐藏参考mesh|
|DeciCAD|CAD长程决策；语义动作、持久状态、结构化反馈及主动检查|完整方法包括SFT及几何反馈RL；接口思想本身可无训练借鉴|训练阶段的几何目标/奖励不可搬进测试观察；不能从论文假设当前接口具备快照|

主来源：[ToolTree](https://github.com/SYang2000/ICLR_2026_ToolTree)、[Gecko](https://proceedings.mlr.press/v306/zhang26cv.html)、[NaviAgent](https://proceedings.mlr.press/v306/jiang26be.html)、[ToolPro](https://proceedings.mlr.press/v306/liu26cb.html)、[Asymmetric Verification](https://proceedings.iclr.cc/paper_files/paper/2026/hash/bc26087d3f82e62044fc77752e86737e-Abstract-Conference.html)、[Budget-Aware Agent](https://github.com/google-research/budget-aware-agent)、[StepCAD论文](https://arxiv.org/abs/2610.03799)、[DeciCAD论文](https://arxiv.org/abs/2610.21755)。

## 2. 最小迁移与否决条件
|工作|当前接口能迁移什么|复杂度（借鉴/原法）|价值与不能证明的部分|
|---|---|---|---|
|ToolTree|候选schema、能力、依赖前检；只执行一个|中/高|有价值的是拒绝不可行动作；没有状态隔离和可信评分就不做MCTS，也不把Best-of-N改名树搜索|
|Gecko|静态工具契约与前置条件清单|低/中高|不要用LLM模拟体积/合法性覆盖真实OCC结果；模拟便宜不等于可信|
|NaviAgent|从真实Profile/BaseFeature构造依赖表|低/高|先用确定性图，不引入训练图模型；规划依赖不能证明目标尺寸正确|
|ToolPro|intent_id、前状态hash、执行结果ledger、重复动作拒绝|中/高|可减少重复提交；中断时状态未知应停止/核查，不自动重放全脚本；本轮未实现事务|
|Asymmetric Verification|先明确哪些验证比生成便宜且准确|低/中|有效性便宜；目标正确性未必便宜。没有oracle不能用自评分代替验证|
|Budget-Aware Agent|统一token/tool/wall ledger，保留执行预算|低/中|动态k仅启发式；需同总成本对照，防止搜索额外Token造成伪增益|
|StepCAD|观察中间形状、明确局部编辑与可执行状态|中/很高|“CAD几何搜索”已有近邻；目标mesh依赖使原IoU排名不适用本设置|
|DeciCAD|观察/动作/执行分层，语义化特征检查|中/高|“语义动作+状态反馈”非空白；创新只能来自受限公开图纸条件下机制及可解释实验|

## 3. 固定源码审计记录
以下均只读取源码，未运行第三方工具、训练或测评。
- ToolTree `fed7a608ca54ba2e75078f9a1f409c9aa7fab18f`，既有 `/home/gypsophila/geotree/work/e00-src/tooltree`。`src/mcts/tree_search.py:_expand` 对候选pre_evaluate/剪枝/topK；`_execute`交ToolManager；`_record_execution`保存实际输出；读取的代码确实区分规划上下文和工具执行。README默认mock，真实工具须适配。缓存键/上下文复制不自动覆盖CAD副作用。
- Gecko `1f5607984a124f5efd56c60b040f723b775b1a57`：`gecko/utils/request_validator.py`含确定性schema及语义检查；`response_generator.py`通过模型生成模拟响应并维护状态；`state_update_enriched.py`推导状态路径。代码确认不是FreeCAD物理仿真。[官方源码](https://github.com/camel-ai/gecko)
- ToolPro `9a634427fa3cc92fcf4d57206e6c2aeb681b66c2`：`core/replay_guard.py:check_write_prefix`、`replay_policy.py:evaluate_write_replay_policy`、`transaction_context.py`。存在WRITE前缀、nondeterministic和幂等条件；事务代码不是对所有外部服务的无条件保证。[官方源码](https://github.com/morgen52/toolpro_icml26)
- Budget-Aware `37d23f66c512734db476313cf436a506edbec9e0`：`src/agent_budget_tracker.py`、`agent_bats.py`、`select_answer.py`。工具预算和继续生成/选答逻辑已读；选择器含模型调用，评估函数含gold参数，评估与规划须分离。[官方源码](https://github.com/google-research/budget-aware-agent)
- StepCAD `1255622569c1a52a7d890d332359ab28d6a9e3da`：`infer.py`有时间预算、权重入口；`src/stepcad/refine.py`的 `refine(...target_mesh,K=2...)`、`Scorer(target_mesh)`、候选排序明确依赖目标mesh。未执行权重下载。README发布版3.5M与论文1.5M须区分，不混用结果。[官方源码](https://github.com/ghadinehme/StepCAD)、[作者方法页](https://ghadinehme.com/stepcad.github.io/)
- DeciCAD链接的 PhysCAD `ea431b94ce784acf49e8f731d9ecf2cfda6fc712`，本次tree只有README：**BLOCKED（可执行源码复核）**；方法判断仅论文级。[官方入口](https://github.com/PhysAGI/PhysCAD)
- NaviAgent、Asymmetric Verification：**PARTIAL（论文已核查、官方源码未确认）**，没有用同名第三方实现替代。

下载文件、字节数、SHA及commit见 `work/e02/references/source-manifest.json`、`papers-manifest.json`。仅小型文本与3篇论文PDF；源码未安装。版本与文件树JSON保留供复核。

## 4. Kill decision
不复现ToolTree全树、不引入Gecko模拟几何、不训练NaviAgent/StepCAD/DeciCAD、不搬入目标mesh IoU、不把事务论文视作现成CAD回滚。先建立G1可追溯观察，待信号覆盖真正错误后再判断G2；G3先作为预算设计而非优效方法。


证据根目录：`/home/gypsophila/geotree/work/e02/`。日期：2026-11-12。本文将历史真实试次、离线测试、待验证设计严格分开。
