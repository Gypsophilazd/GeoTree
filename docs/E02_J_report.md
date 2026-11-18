# E02-J｜跨任务验证与自主约束发现
2026-11-13（Asia/Singapore）。**PASS：两条新公开输入上的离线接口与测量。PARTIAL：自动目标覆盖及修复迁移。BLOCKED：带公开起始CAD的编辑槽位。NOT_RUN：真实模型、Harbor试次、评分、k≤2搜索。** E02-G/H/I制品、旧源码和A0/A1历史SHA核验通过。

## 开发集冻结
固定 [Harbor V3](https://hub.harborframework.com/datasets/gnucleus-ai/cad-bench/v3) 摘要 `sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`。按固定成员返回顺序排除旧题，从前16个位置筛选（15个新instruction），取首个文本创建和首个工程图。未读任何模型成绩。精确入口文件、输入SHA和选择规则见 `/home/gypsophila/geotree/work/e02-j/development-freeze.json`、selection-rule.txt、screened-instructions.json。
| 类别 | 任务与固定摘要 | 公开输入和范围 |
|---|---|---|
| 文本创建 | gnucleus-ai/freecad-06a5c206229 / `sha256:0a4939b8e768105a8a243a4d1e520c5bffbf8e7384204753113e20971998e04f` | instruction.md，液压缸端盖，显式参数与正文角色 |
| 工程图 | gnucleus-ai/freecad-3a953b7617 / `sha256:144aac6d9549c40b2a8e9371cc9b211280fe4bdcca2026d90bd1246a5f5cf1e5` | instruction.md + 3a953b7617.png，带剖视的安装框 |
| 已有CAD编辑 | **BLOCKED** / 未冻结ID | 本轮有限instruction筛选及前三个包的环境索引未确认公开起始FCStd；[官方V3说明](https://www.gnucleus.ai/cad-bench/news/cad-bench-v3)使用create-and-edit类别，不等同于提供现成起始CAD。未用合成件或另一类任务替代，不推断整个V3绝无此类公开资产。 |

单文件对象指针缺失（archive-only）后，按固定指针使用内存中的公开任务归档；筛选15个包共5,164,416 B，额外复核一次已筛包的公开说明，未落地归档。只对根instruction及已选题明确命名的环境图像调用extractfile，未提取、读取或运行参考CAD/评分器成员。不会下载完整数据集或将这些题当最终holdout。

## 代码
- `/home/gypsophila/geotree/src/geotree/constraint_candidates.py`：统一候选与逐字来源/跨度；文本支持参数表、明确XYZ尺寸、Pad长度编辑、特征存在与孔位语法。解析绝对参数，不猜未写语义；单位/角度/一般孔径可提出但不自动绑定几何。视觉走现有ModelProvider.propose的结构化适配接口，仅Mock；固定图像sha与像素尺寸，ROI边界/枚举/有限数校验，禁止reviewed/verified额外字段。
- `/home/gypsophila/geotree/src/geotree/evidence_gate.py`：独立重放文本匹配，冲突/被篡改→AMBIGUOUS；图像提议→CANDIDATE；无可靠查询→UNSUPPORTED/NOT_CHECKABLE。VERIFIED先通过来源准入；只有唯一有效实测才可硬FAIL。复用GeometryObserver及OCC bbox。新增圆柱体规则只接受正文明确“实心圆柱体、外径、轴向厚度”角色，几何须找到唯一全周外圆柱且径向包围吻合；不按期望尺寸择优。破碎外壁等保守UNKNOWN。
- `/home/gypsophila/geotree/src/geotree/safe_repair.py`：新型SET_ISOLATED_PAD_LENGTH，重测可信FAIL与实际源SHA、检查无下游消费/不支持依赖、旧形状为准确棱柱、独立副本修改、保存重开、旧PASS回归及双向BRep包络差；独占发布新FCStd，不覆盖源。没有调用旧题修复脚本作为生产路径，也不把旧REANCHOR_PLANAR_POCKET自动迁移。
- `/home/gypsophila/geotree/src/geotree/verification_harness.py`：NoSearch外置Provider/Executor装饰，k=1，候选→真实测量反馈→修复建议/检查/可结束。回执重绑公开文本和artifact digest，不让无关修复记录提升DONE资格。运行时旧动作schema未变，REQUEST_INSPECTION为建议，Mock停止时显式保留不确定性；生产回执仍需接入可信隔离worker。

## 测量结果：非Benchmark产物
| 输入 | 自动候选 / 可判定 | 结果 |
|---|---:|---|
| 端盖文本 + 独立简化圆柱正控 | 31 / 4（12.9%） | 80 mm外径、130 mm轴向厚度、1 Body/1 solid全PASS；27 NOT_CHECKABLE |
| 同文本，独立直径/厚度负控 | 每件31 / 4 | 78 mm和128 mm缺陷分别触发唯一硬FAIL；另外三项仍PASS |
| 工程图指令 + 图纸 + 简化参数化探针 | 3（2文本+1 Mock视觉） / 2结构 | 2 PASS、1 UNKNOWN；**0个自动可信图纸几何尺寸**。剖视224 mm和另一视图219 mm不能凭单个ROI统一为整体轴长 |
| 合成已有件 | 3 / 3 | Pad长度9→12 mm；X跨度与结构均回归PASS；扫掠体外差0/0 mm³、双向准确棱柱差0/0；一次已验证提交 |

端盖探针故意未建全内部几何：PASS只限4项，未检查居中、复杂侧部和半径语义。候选覆盖为“输出数”；没有标注全集，不能报告抽取召回率。已知尺寸缺陷2/2检出，单件端盖正控4项无误报；这不等于跨任务低误报率。修复正控1/1通过，错误哈希、真实Face消费、已正确件均拒绝，未绑定约束UNKNOWN。旧E02-I五项合成门禁重跑通过，旧原件未再次编辑。

NoSearch九个Mock回放场景通过：合规结束、FAIL→修复建议、已验证修复、拒绝不安全、拒绝错artifact回执、文本覆盖不足、图纸歧义、缺件、无效体。ATIF及trace在traces-v2。回放输入是同一隔离worker的实测记录；未执行Mock生成脚本，未在Harbor跑整题。模型可见字段测试未发现评分、隐藏参考、真值字段，worker未挂载该类文件。没有把隐藏分数送给策略。

## 已完成 / 未完成的权限边界
A 可直接复用：字面参数抽取、独立准入重放、确定性查询、保全和拒绝门禁、单Pad事务。B 人工辅助：E02-H旧图配准/签发只用于旧夹具回归；新图的视图关系没有人工替模型补齐。C VLM候选：新图的标注、剖面和孔位映射需要图像候选；目前仅接口测试。D 未知：复杂局部语义/图纸对齐、带下游依赖的安全编辑。当前主要瓶颈是**从数字到唯一特征与坐标的对应**，不是提取更多数字。已能自动发现一小类可信FAIL；只证明窄操作可在合成件上自动修复，尚未证明对新真实Bench制品自动修复。

## 复现与资源
根目录 `/home/gypsophila/geotree/work/e02-j/`：run-freecad.sh geotree-e02-j-2（复跑用新名）、freecad-2.stdout/stderr/exit、container-v2.txt、geotree-e02-j-2/results.json、test_protocol.py、protocol-v2.log、legacy-runtime.log、preservation.log。缓存FreeCAD，2 CPU / 4GiB / GPU0 / 断网 / 非root / 只读根。最终容器exit0，约1.20s；单次合成修复工作器约0.090s。无RL干预，无模型/付费调用/Benchmark尝试。第一轮及加紧回执绑定后的复测均为离线夹具，不计正式尝试。
