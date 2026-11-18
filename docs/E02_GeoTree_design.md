# E02-D/E：GeoTree 候选架构与首步决策

**决策：G1优先；G2、G3为待验证设计，不实现MCTS。** G1已实现确定性Observer及可选执行器装饰层、Mock闭环；真实Harbor接线与模型收益未验证。

## 1. 不改变的接口
现有 ModelProvider → ObservationBuilder → ActionValidator → Executor → FeedbackRecorder → NoSearchRuntime / SearchPolicy 保持原样。`DecisionBridgeAgent`、`GeoTreeNoModelAgent`、NoSearch旧入口及开题原文哈希保持不变。当前 Executor 接收整脚本，不是事务化局部CAD编辑器。

新增 `src/geotree/geometry_observer.py`：GeometryObservation / observe_document / inspect_file / check_constraints；新增 `src/geotree/geometry_feedback.py`：GeometryFeedbackExecutor。

最小可复用接线（reader须由可信适配器在同一受限任务环境实现，本轮未伪装成真实Harbor接线）：
```python
from geotree.geometry_feedback import GeometryFeedbackExecutor
from geotree.nosearch import NoSearchRuntime
# read_geometry: async () -> GeometryObservation
runtime = NoSearchRuntime(provider,
    GeometryFeedbackExecutor(existing_executor, read_geometry, timeout_sec=10),
    recorder, max_steps=4)
status = await runtime.run(public_instruction)
```
旧ObservationBuilder已经把执行feedback放入下一轮history；无需更改基模接口。MockProvider验证run_freecad→结构化几何feedback→下一次done，trace/ATIF可解析。真实reader必须使用environment.exec固定命令和明确允许路径，不接收模型指定任意观察路径；运行时mount、用户、资源与网络边界需在下一轮预检。

## 2. GeometryObserver契约
- 检查自身合法可见FCStd，不读参考/评分器，不调用LLM，不执行answer.py，不recompute/save。
- 输出 shape_valid、solid_count、volume、bbox、body_count、特征类型/依赖、草图约束状态、execution_errors、geometry_errors、constraint_checks、unknown_fields。
- 来源manifest独立传入；每项包含metric、expected、op、tolerance、source.kind/locator/reviewed、mapping_reviewed。没有来源、未知目标、未审查映射、非有限数值输出UNKNOWN。
- 本题manifest只做诊断，不嵌入通用模块，不自动充当正式模型的额外人工提示。未来公开约束提取若由模型完成，其不确定性必须保留；模型自称reviewed不能获得可信来源身份。
- Shape有效不等于目标正确；feature underconstrained只是warning。多Body/多个候选结果不猜最终对象；空/无结果显式未知或几何错误。
- 读取存储形状，Touched/Error提示可能过时；当前PASS仅指存储状态对应检查，不证明重算后的状态。未实现全局拓扑命名稳定性及所有FreeCAD依赖类型。
- allowed_root、后缀、20MB及symlink检查是输入防护，不是安全沙箱。CAD解析须留在隔离容器。离线容器本轮只挂观察代码、历史产物副本、公开约束与fixture；无Docker socket、隐藏数据或其他项目挂载。
- 装饰层仅在run_freecad exit0后观察；非0不读取可能过期产物；观察错误/超时不覆盖原执行结果。PASS表示观察成功，不表示任务成功。

## 3. 五类信息分离
|类型|来源|允许用途|
|---|---|---|
|模型计划|ActionProposal|待验证意图，不写成已发生状态|
|静态检查|schema/工具契约/真实依赖清单|确定性可行性，不推断几何结果|
|执行前估计|预算、风险、假设|标estimated/unknown，不作为测量|
|真实反馈|environment.exec及OCC观察|带request_id、artifact hash、时间、状态|
|最终Benchmark评分|独立verifier|只在试次结束后汇总，永不进入搜索history|

## 4. 三个候选方法
### G1 Geometry-Grounded Feedback（首选）
k=1。将真实shape、特征、已映射约束与Unknown加入反馈。预期降低不可见执行错误和证据不足DONE；本题基本指标全过，所以不承诺提升其reward。首步同时维护公开要求-特征映射的研究记录，先解决“能发现什么错误”。不增加一次LLM做简单几何查询。

### G2 ToolTree-Lite（DESIGN / NOT_RUN）
CandidateGenerator一次返回1..3个ActionProposal及预期前置条件；CandidateEvaluator分别做schema、能力、依赖、风险/成本检查。只对可证实项排序：明确硬违例淘汰→可证明前置条件覆盖→修改范围/预计成本；无法区分时稳定tie-break并记录无可靠优劣依据，不用隐藏reward。不声称预测未执行后的精确体积。
只执行一个候选；保留所有候选及拒绝原因。当前整脚本方案差异若无法几何排序，应标Best-of-N/static filtering，而非有几何基础的树搜索。先建立局部动作/操作账本，再考虑状态分支。未执行候选不能记录tool结果。

### G3 Budget-Aware GeoTree（DESIGN / NOT_RUN）
BudgetController读取实际token/tool/wall累计与保留预算；前置条件明确k1，有可定位参数/依赖不确定才考虑k2，结构多解且有判别信号才考虑k3。预算不足回k1或结束；先预留已选动作、观察和产物保存时间。阈值是预注册启发式，不是最优策略。预算控制不能补救没有可靠ranker。

## 5. 状态、副作用和成本
设计ledger包含intent_id、state_before_hash、action_hash、phase(proposed/validated/started/committed/uncertain)、state_after_hash、result。重放必须核对前状态和已提交记录；进程中断导致uncertain时先停止核查，不能自动重建整个模型。此ledger与局部修复尚未实现；现有trace只是记录，不等同exactly-once。
若未来副本试执行，先审任务允许目录、CPU/RAM及复制成本，并保留每个分支的独立hash；本轮未申请或执行候选分支。历史产物始终保留。

## 6. 为什么先G1
证据：真实执行成功而任务质量未充分验收；基本几何检查全PASS仍有部分reward，说明缺少目标关联信号。G1低成本、无训练、易构造可证伪测试，适合先完成校赛可解释基线。G2增加token且排序依据薄弱，G3依赖风险估计成熟度，均后置。StepCAD/DeciCAD已经存在几何搜索/状态反馈，GeoTree的潜在贡献应限定为图纸可见信息条件下、固定基模与预算的可解释机制实验，尚未证明novelty或性能优越。


证据根目录：`/home/gypsophila/geotree/work/e02/`。日期：2026-11-12。本文将历史真实试次、离线测试、待验证设计严格分开。
