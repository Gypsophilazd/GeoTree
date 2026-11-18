# E02-E：消融与下一轮批准门槛

**状态：DESIGN / NOT_RUN。本轮无新增真实CAD试次或模型请求。**

## 1. 消融配置
|组|策略|反馈|k|识别目标|
|---|---|---|---|---|
|A0|NoSearch|Raw|1|同环境基线|
|A1|NoSearch|Geometry Observer|1|几何观察独立贡献|
|A2|静态候选过滤/排序|Raw|≤3|多候选独立贡献|
|A3|同A2候选策略|Geometry Observer|≤3|两者交互|
|A4可选|动态预算策略|Geometry Observer|1..3|成本-收益而非额外算力堆叠|

配对差值 ΔG=A1−A0，ΔC=A2−A0，交互=(A3−A2)−(A1−A0)。A4先于A3成熟前不运行。G2必须先通过候选契约与依赖检查测试；未验证排序质量时公开标static Best-of-N。

## 2. 冻结原则
同模型ID与可核验版本、effort、provider认证路径、任务digest、镜像digest、Harbor版本、Executor、图片字节、合法工具权限、任务时限与输出限制。不得以移动别名假装同版本；实际模型ID/可用性先确认。保留 `configs/comparison_v0.1.json` 原文件，本协议不把拟议DeepSeek名称当成已可用服务；本轮无API购买/调用。

各组都使用相同公开指令/图纸；当前人工审查的本题尺寸manifest仅供离线诊断。若将人工结构化目标传给A1，则A0也必须拥有同一目标信息，否则混入额外人工信息，单列人工辅助条件。Observer只把已有信息变成可测量的反馈，不偷偷增加答案。按task规范给出泛化schema，不在prompt写本题正确几何。

两种预算对照必须分别报告：
1. 固定动作上限：研究交互效果，同时完整披露候选额外token；
2. 固定总token/工具/wall上限：检验搜索增益是否只是增加算力。候选生成、排序LLM、失败/拒绝、观察、图片处理与所有重试都计入，不能仅计执行的候选。
实际provider若不能严格限制累计token，则明确标软预算overshoot，保留最后一次请求实际usage；严格同token比较阻塞，不伪称硬上限。

## 3. 指标与失败处理
- Mean continuous reward（每题最终一次独立verifier结果）；不是success rate。
- 每题配对差值及分布；样本足够后配对bootstrap区间，单题不做显著性推断。
- artifact可解析、shape_valid、单实体、命名Body/特征树；公开约束PASS/FAIL/UNKNOWN及覆盖率分母。
- model/tool调用、输入/缓存输入/输出/reasoning token原字段；避免将包含关系重复加总。
- wall、CPU/RAM观察成本、provider实付金额与估算金额分列；订阅不等于token成本为零。
- Perception/Planning/Parameter/Tool Execution/State Observation/Verification/Unknown：只按证据归因，盲于组别复核。
- 无评分、容器启动失败、预算超限单列；不能把缺失reward擅自补为0或剔除失败组。有效结果均值同时报告分母及缺失率；预注册保守敏感性分析。
- 固定并发1、每组每题attempt1、retry0；基础设施失败保留，不为获得非零reward重刷。

## 4. 下一轮最小真实实验（需另行批准）
目的仅验证G1能否在真实模型闭环中提供可用状态，不声称最终能力收益。
建议：同一既有开发题 `gnucleus-ai/freecad-6b54209a13`，新建A0/A1各一次，共**2个串行开发试次**，而不是与历史P0E跨配置直接比较。历史0.314269只作背景，不当作新A0。
- 固定gpt-6.1-sol / High；沿用可信Windows ChatGPT Decision Bridge，不复制auth，不用商业Key；实际模型配置变更则停在预检。
- 每试次最多4次模型决策、最多2次CAD执行，每次执行≤60秒，Observer≤10秒；试次wall≤900秒，relay单次≤420秒且受总wall限制。
- 提议总token软上限100000/试次（含所有决策，按实际usage计），输出≤16000/试次；若配置和实际基线表明不足，在开始前重新批准预算，不执行后扩大。
- 无新增镜像/模型下载，CPU2、RAM4GiB、pids128、GPU0、network none（任务容器），保持任务原生上限中更严格者；总新增证据磁盘预算1GiB。
- 先完成真实reader固定命令、schema输出和artifact hash绑定；两组执行权限相同。A1增加只读观察，额外CPU/wall计入。
- 监控内存可用量、CPU/IO等待和本轮容器；持续明显竞争或OOM压力时停止GeoTree本轮，不触碰RL。建议停止阈值：连续3个10秒样本 available<8GiB 或 iowait>20%，并保存原因；若本轮隔离上限与官方协议不一致，DEVELOPMENT-ONLY。
- 不自动替换为未见任务，不增加试次或自动重试；独立verifier只在结束后评分，反馈不进入搜索。

上述预算是待批准配置，不是已执行事实。G1收益研究下一步应预注册小型未参与开发的配对题集（例如5题、A0/A1各一次），题目只读取公开任务元数据选取；该题集需另行批准，校验是否具有可测公开尺寸且排除当前开发题。最终holdout再次独立，不以开发集调参后结果代替。

## 5. Go/No-Go
G1进入真实实验前：离线13项、6个FreeCAD案例、旧Mock回归通过；真实reader接线、任务协议与token计量仍须预检。G2之前：能将观测违例映射到局部修复、证明候选检查可靠；没有则保留G1。G3之前：先建立跨题风险/成本记录。所有外部Codex/Claude公开成绩只作外部参考，不替代同模型对照，也不作GeoTree自身成绩。


证据根目录：`/home/gypsophila/geotree/work/e02/`。日期：2026-11-12。本文将历史真实试次、离线测试、待验证设计严格分开。
