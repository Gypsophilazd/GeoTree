# E02-A：公开输入与既有产物分析

**状态：PASS（读取、确定性测量）；PARTIAL（质量错误归因）。**

## 1. 证据与边界
既有单题 `gnucleus-ai/freecad-6b54209a13`，gpt-6.1-sol / High，k=1，3 次决策。历史独立 continuous reward **0.314269**，DEVELOPMENT-ONLY，不是成功率。该题已经用于开发，排除最终独立评测。本轮未查询评分器或隐藏参考，也未产生新分数。

原始证据：`/home/gypsophila/geotree/work/e01-p0e/nosearch.vFTvcn/jobs/e01-p0e-nosearch/freecad-6b54209a13__PPMxty3/` 下的 `agent/trace.jsonl`、`agent/trajectory.json`、`artifacts/app/answer.py`、`artifacts/app/answer.FCStd`；公开图纸位于 `/home/gypsophila/geotree/work/e01-p0e/windows-evidence/drawing.png`。源文件 SHA256：
- answer.py：`db9f695a867703ec96a55c1270468f2f5a80661c6fcf5839ca8951605c9a27f8`
- answer.FCStd：`26d7b8ee0f6db73e8f5aae9534fba3a914dd3c45c21fe68a1b7f2ae9f4b9ee18`

## 2. 公开要求、实现与不确定性
图纸是唯一几何来源；任务文字要求一个命名特征驱动的 PartDesign Body、单实体，排除 baked Part::Feature。

|要求/参数|公开来源与脚本实现|判断|
|---|---|---|
|整体长、宽、高|图示 141、86、40；脚本映射 X/Y/Z|来源明确；实测满足整体包围盒，不代表内部结构正确|
|台阶与轮廓|27、72、130.8 等图示尺寸；脚本 x=0,12.6,27,99,130.8,141；y=±32,±43,±25.4|99=27+72 是派生值；跨视图对应关系仍需逐项复核|
|主腔与圆角|脚本 x=5..110、y=±16、R3、深22；图有105、32、4×R3|部分数值可追溯；全部位置/深度映射未形成独立校核|
|安装孔与横钻|脚本直径7、2.8、3；图有相应直径，横钻标 THRU|直径标签明确；位置、轴向及穿透范围需单独验证|
|侧口|脚本 outer y=-25.4，inner y=-14.8，距离10.6，用 tan(20°)计算内侧顶部|20°有标注；-14.8、10.6 未找到独立明确标签，属于建模解释，不标成已证实错误|
|端部/窗口|凸缘 y=±13；端钻深6；窗口 x=133..138|这些具体数值未完成公开来源映射；不借隐藏几何补齐|
|草图参数化|12 Sketch；均未添加尺寸/几何约束|具备命名特征树，但未 FullyConstrained；不等于形状错误，也不单凭此归因分数|

图纸尺寸、派生尺寸、推测尺寸须使用不同 provenance。当前 manifest 只核对 5 个可解释项目；未知目标体积为 null。公差0.01mm是本次诊断数值公差，不冒充官方评分公差。

## 3. 实际 FreeCAD 状态（离线 API 实测）
`work/e02/observer-results.json` 的 existing：
- shape_valid=true，solid_count=1，body_count=1。
- volume=154123.68473754305 mm³；bbox=141×86×40.000000000000014 mm。
- 12 Sketch、2 Pad、8 Pocket、1 SubtractiveLoft、1 Body。
- 特征状态 Up-to-date；Profile / Sections / BaseFeature 引用解析未发现缺失或循环。
- 12 个草图均 constraint_count=0、fully_constrained=false，仅记 warning。
- 整体尺寸及 body/solid 数检查 5 PASS；target_volume UNKNOWN。

实际序列及阶段体积（mm³，显示精度截断，原始 JSON 保留全精度）：
MainPad 254520 → RaisedEndFlange 256080 → UndersideReliefs 245580 → SlopingEndUnderside 240684 → RoundedMainCavity 166933.965 → FloorAndEndWindows 163048.347 → LugSlots 160079.147 → MountingHolesDiameter7 158924.612 → TaperedSidePort 154425.893 → CrossDrillsDiameter2p8 154194.371 → EndDrillsDiameter3 154123.685。
所有已列减料操作都降低体积；没有证据把它们描述为执行失败或无效空操作。仅检查存储形状，未 recompute/save，源文件哈希保持不变。

## 4. 轨迹与终止
真实顺序 check_workspace → run_freecad → done；run_freecad exit=0，耗时2.798630603秒，stderr空，stdout：
```
Solid count: 1 Valid: True Volume: 154123.68473754305
```
模型做了有意义的单实体/有效性断言，但没有可见的独立尺寸映射检查、截图比对或多视图验收。DONE 的理由仅为脚本成功保存和一个有效实体；当时 remaining_steps=2（含本次 DONE）。因此**终止依据偏弱**有证据；“再给一步必然改善”没有证据。

## 5. 可证伪的失败假设
|类别|证据/当前结论|能区分原因的后续实验|
|---|---|---|
|Perception Error|部分尺寸跨视图映射未核对；具体误读 UNKNOWN|独立、盲于 reward 的图纸尺寸-视图-特征标注；比较原提取表与公开标注|
|Planning Error|采用整脚本一次成模；缺少逐特征验收；序列确实执行|固定视觉提取与预算，仅切换逐特征检查，观察是否减少结构遗漏|
|Parameter Error|若干数值无明确来源；是否导致差异 UNKNOWN|固定结构计划，将公开来源参数与估计参数分别登记；只对公开可证实项做定向检查|
|Tool Execution Error|exit0、无stderr、有效单实体；未支持该归因|合法缺Profile/空Shape/双实体合成对照验证检测能力，不称为当前题故障|
|State Observation Error|原反馈只有模型自行打印三项；缺bbox/依赖/维度对应|A0 vs A1同模型同预算，比较错误感知、修复率、DONE依据|
|Verification Error|有效性被用于结束，缺目标一致性证据|在自制“有效但尺寸错”模型检测误终止；真实题不拿 reward 反馈决策|
|Unknown / Insufficient Evidence|整体尺寸、实体、有效性全通过但历史reward部分匹配|需要更多公开要求的可验证映射；单题不识别特定错误的因果贡献|

## 6. 研究结论
几何反馈适于发现执行异常、空/多实体、依赖问题、已映射尺寸违背，不能替代视觉理解、特征规划及未知目标几何。现有证据不支持“基本 Observer 已解决主要质量问题”。优先 G1 是降低不可观测性并建立可解释实验，而非已经证明收益；G2/G3暂不执行。


证据根目录：`/home/gypsophila/geotree/work/e02/`。日期：2026-11-12。本文将历史真实试次、离线测试、待验证设计严格分开。
