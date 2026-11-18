# E02-I：最小 Repair Contract
**PASS（单任务离线实现），NOT_RUN（生产Agent接入）。** 实现位于 `/home/gypsophila/geotree/work/e02-i/repair.py`，不接入旧 Executor、NoSearchRuntime 或 SearchPolicy。输入目标是 E02-H 对公开图纸人工审查后的 `main_cavity_open_side=TOP`，不是通用 CAD 知识。输出实例 repair-proposal.json。

字段：artifact_sha256、constraint_id、target_feature_identity（Body/Pocket/Profile）、expected_relation、measured_relation、proposed_operation、parameter_changes、prerequisite_checks、affected_dependencies、confidence、uncertainty、execution_status 与带时刻 events。状态：
- PROPOSED：尚未实作，无候选输出几何结果。
- VALIDATED：输入 digest 与框架签发匹配、可信 FAIL、唯一阶段 BRep 转变及 Profile 对应，支持的固定操作满足前置条件。
- EXECUTED：副本文档已编辑，不代表重算、重开或几何验收成功。
- VERIFIED：重算/重开、方向、保全约束、结构与影响范围均通过。
- REJECTED：输入哈希不符、已经合规、操作/依赖不安全，或执行后失败；失败副本仅作证据。
- UNKNOWN：来源/坐标/特征身份不足，不执行。

唯一操作 `REANCHOR_PLANAR_POCKET`：在已有固定坐标中移动未附着的XY草图，再翻转已有长度 Pocket。非默认Body位姿、非长度型/带锥度/不符平面、表达式、或任一 subelement 依赖均拒绝。按实际 Body 历史和3条中心截线找唯一变化阶段，不仅相信对象名。参数只由可信脚本和签发的任务框架导出；无模型输入文件路径、shell或命令执行接口。不能把这个任务的数值、孔形ROI或对未覆盖依赖类型的检查当成跨任务修复器。源只读挂载，保存新文档，保留事件、差分、控制件与验收。撤销只作用于单独的 disposable 测试副本，保留C1及原始文件。
