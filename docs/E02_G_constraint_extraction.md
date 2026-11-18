# E02-G：公开工程图约束提取
**PASS（离线研究清单）；PARTIAL（覆盖）。** 固定公开图 1692×930 px，SHA256 `69a47a61dfd5afcc1881c66c4a2d1e5a2a30d6b9ae6d2365181b2e2c89dffc9d`。完整任务公开指令取自两组共有的首次 Observation，保存于 `/home/gypsophila/geotree/work/e02-g/public_instruction.txt`。模型历史脚本只用于核对实际坐标约定和描述差异，不能作为目标来源。

`/home/gypsophila/geotree/work/e02-g/public-specs.json` 有24条分析单元；每条有原标注、视图、原像素ROI [x0,y0,x1,y1]、单位、坐标定义、证据类别、映射状态、容差。多个孔分别分解位置、直径、中心线条件，故24不是图上标注总数。ROI只定位证据，不以像素估算替代标注。EXPLICIT 为直接标签，DERIVED 给出链式坐标（如29.5+34.5）或必要条件（THRU→轴线不截入材料）；INFERRED 仅是结构解释；UNKNOWN 证据不足。reviewed 仅表示标签/推导已审，不表示映射一定已审。mm 0.01、角度0.5°为本次诊断阈值，不是评分器或完整制造公差解释。

坐标只针对已复核的两份历史产物：左端高台对应 X 起点，前视竖直方向 Z 从底面起，横钻轴垂直前视沿Y；左孔对的 49 间距绕中心线一分为二。容差不用于选最接近期待值的候选。旋转、镜像、平移的新任务不能沿用此映射，先建立基准对应。右孔位置、20°侧部具体面、主腔深度/开口方向、多视图和C1边身份保留未决。逐约束 ROI 和测量详见验证报告。

**人工数据边界**：清单是研究辅助数据，不接进正式 Agent。未来 `ConstraintCandidateProvider.propose_constraints(public_instruction, drawing)` 仅输出候选；用独立可信的出处复核与几何映射审查签发 approved spec。忽略模型自填 reviewed/verified 权限字段，未经审查的来源/坐标/映射保持 UNKNOWN。本轮没有实现视觉提取，也未调用模型。
