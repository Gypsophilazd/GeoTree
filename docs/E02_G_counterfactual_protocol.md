# E02-G：冻结反事实协议
**NOT_RUN；须另外授权真实 Codex 请求。** 可读配置在 `/home/gypsophila/geotree/work/e02-g/counterfactual-frozen.json`。冻结 A1 原始已提交 CAD、原脚本和 DONE 前历史；去掉原有通用几何块，两组共同使用同一 raw history、instruction、原始图（按 hash）和完整公开 spec（只含目标、无实测）。两组都不拿隐藏评分。唯一处理差异是 C1 注入 task_grounded_verification 的已测结果；C0无此块。额外人工信息不做单边输入。不给模型直接文件或执行权限；状态通过同一冻结 artifact hash 标识并留档，不重新生成 CAD。

同一可信 Windows Codex 路径、gpt-6.1-sol/high、420秒、同一软预算、同一提示/响应 schema、每组一次，无追加。**最小规模：2 次模型请求、0 次 CAD 工具执行**；确定性观察已离线生成，仅复用。模型输出 intent ∈ DONE/REQUEST_INSPECTION/LOCAL_REPAIR/REBUILD/STOP、constraint_ids、evidence、localized_edit_description。只记录建议，任何后续几何执行另行授权，不在本协议默认执行。

盲评输出：区分证据充分的DONE、指出未覆盖的有限DONE、针对未知的定向检查、基于可信FAIL的局部修复、对UNKNOWN误判FAIL、无证据重建/停止。当前清单没有真实FAIL，所以合理反事实变化更可能是主动核对主腔方向而非自动改件。必须引用可观察事实并承认未验证处；模型自称“全符合”不能记作正确。报告行为差异/usage/wall，不称为质量改善或统计显著性。
