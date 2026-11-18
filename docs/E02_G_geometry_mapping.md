# E02-G：确定性几何映射
**PASS（离线映射实现与实测）；PARTIAL（身份归因和覆盖）。** 新增 `/home/gypsophila/geotree/src/geotree/task_geometry.py`，不修改原 Observer、Reader、NoSearch 或 Agent。Contract：ConstraintSpec → GeometryQuery → 结构化 ConstraintResult（JSON记录）。结果包含 expected/measured/unit/source/mapping_status/candidate_mapping/status/reason/repair_target；警告和整体正确性不与约束FAIL混淆。

| 查询 | 度量与身份 | 保守退化 |
|---|---|---|
| bbox | 已确认图纸轴的最终单实体包围盒 | 坐标不明 UNKNOWN |
| 横钻直径/孔位 | 从最终 BRep 选沿Y的凹圆柱；独立X/Z窗口，按同轴线分组；至少一段全周圆柱壁；不按目标孔径筛选 | 缺失、多个轴、同轴变径、全周证据不足均 UNKNOWN |
| 横钻中心线 | OCC line ∩ solid，测轴线材料长度 | PASS只说明中心线畅通，不证明完整孔径跨全段、入口/出口拓扑；几何布尔异常 UNKNOWN |
| 左安装孔壁跨度 | 由平面图位置筛选沿Z的唯一壁，测轴向范围 | 壁分裂、多段 UNKNOWN；不把壁跨度等同盲孔底部正确 |
| 端斜面角 | 选与右端、底面共达边界、沿Y跨较宽的唯一倾斜平面；法向算XZ锐角，再取补角 | 两候选不选最近角；20°侧细节不是这条124.2°端斜面 |
| R3/其他 | 标注明确与否独立于测量可实现性 | 可信目标但无查询为 NOT_CHECKABLE；身份或出处欠定为 UNKNOWN |

面索引不作为身份。记录轴线、半径、壁段、面法向/包围盒，不从特征名、Sketch 字面参数或 reward 判断几何。ROI 是已审的候选搜索范围，不是测量公差。大偏移可能移出ROI→UNKNOWN，不能宣称检出所有错误。PASS/FAIL仅对该度量和容差；不覆盖完整形状。此实现用 OCC 测量和只读存储形状，不重新计算或保存历史件；测量耗时也包含逐条有效性检查，未优化。

**多视图可行性（PARTIAL）**：原图四视图，前视X/Z和端视Z已能定位；尚未独立确认上下平面视图对应方向、第一/第三角投影或显隐线图例，纸面 scale 0.800 也不能直接换算像素。已做确定性主腔探针（见验证报告），未生成渲染相似分数。下一步用至少两个非共线公开基准配准各视图，锁定观察方向、比例及镜像；从 OCC 抽可见轮廓与隐藏边分别叠图核对。先验收跨视图方向，才可把“开口朝上/下”转为目标条件；不能从局部像素相似度直接打正确率。

**可行动反馈**：结果 FAIL 有目标、公差、测量、来源和候选，但只有经独立特征归属确认（例如真实几何由特定 Pocket/Profile 控制、依赖可追踪）才填 repair_target。当前无已核实真实 FAIL，全部 repair_target=null。最小 RepairProposal：artifact_sha256、constraint_id、feature_identity、parameter、proposed_value、unit。未来先核对artifact hash与参数权限，再在副本上执行一项，复测目标和无关约束，失败不提交；本轮不执行修复。
