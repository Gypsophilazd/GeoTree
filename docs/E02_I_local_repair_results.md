# E02-I：A1 局部修复实证
**PASS / VERIFIED（离线、有限验收）；无新 Benchmark 或评分。**

## 只读前置审查
历史 A0/A1 的脚本、CAD、轨迹、ATIF、公开图纸与 E02-G SHA 清单匹配；E02-H配准与原判决文件通过 evidence.sha256。A1 `UndersideCavity` 是 Body `Enclosure` 内长度型 Pocket，BaseFeature=`RaisedEndPad`，Profile=`UndersideCavityOutline`。三条阶段截线独立确认唯一引入反向开口的特征。草图在XY、Z=0，法向+Z，MapMode Deactivated、无 Support、AttachmentOffset为恒等；Body位姿为恒等。Pocket 长22 mm、Reversed=True、TaperAngle=0、Midplane=False。
- 只翻 Reversed 会把从Z=0起的切削送向−Z，不能从顶面打开，因此不试这一不成立的方案。
- 审计68条对象链接，受影响邻域记录51条；未见 Face/Edge 子元素依赖或表达式。后续Pocket依赖整对象的BaseFeature链，使用自身Sketch；参数关系保留并不保证布尔结果不变，因此仍需重算和差分。
- **只执行一次预定局部方案**：现有草图 Z: 0→28；现有 Pocket Reversed: True→False。**22 mm保持原值**，不认定为已核验的图纸目标深度。未替换或重建任一特征，未改历史 answer.py；C1是实验FCStd而非新的基准提交。

## C0/C1
两组各从同一只读A1副本打开，调用 recompute、saveAs、重开并实测；C0无参数修改（未标记dirty的对象可由FreeCAD跳过重算）。重开无Error/Invalid/Touched。C0与原始字节回滚件双向BRep布尔差均为0，保存字节不同但测得几何等同。

| 项 | C0 无编辑 | C1 局部修复 |
|---|---|---|
| SHA256 | `96e7142ca7a774a0d6368595df86603413697ba7a9ede7e1fe5743c1d5ecbfc6` | `5786a652980b917a14d8ba422d02dbe538267a1c339323f20abe06d3375ddc20` |
| 开口方向 | BOTTOM / FAIL | **TOP / PASS** |
| x=35/45/55,y=0 材料截线 | Z=22..28 mm | Z=0..6 mm |
| Shape / Solids | 有效 / 1 | 有效 / 1 |
| bbox | 141×86×40 mm | 141×86×40 mm |
| 体积 | 159644.866037 mm³ | 159741.594444 mm³ |
| 本阶段实测 wall | 5.831 s | 17.822 s |
| 旧检查 | 16/16 PASS | 16/16 PASS |

两组保留同一Body、12 Sketch、2 Pad、10 Pocket、Group、Tip与链接。受审的对象类型和参数签名中**只有两个计划属性变化**，12个Pad/Pocket的中间形状均保持有效单实体。原先未判定的深度归属、20°和完整通孔截面等没有被升级为PASS。

| 既有约束 | C0 实测 | C1 实测 |
|---|---:|---:|
| length | 141 mm / PASS | 141 mm / PASS |
| width | 86 mm / PASS | 86 mm / PASS |
| height | 40 mm / PASS | 40 mm / PASS |
| cross1_d | 2.8 mm / PASS | 2.8 mm / PASS |
| cross1_x | 29.5 mm / PASS | 29.5 mm / PASS |
| cross1_z | 13.38 mm / PASS | 13.38 mm / PASS |
| cross1_axis_obstruction | 0 mm / PASS | 0 mm / PASS |
| cross2_d | 2.8 mm / PASS | 2.8 mm / PASS |
| cross2_x | 64 mm / PASS | 64 mm / PASS |
| cross2_z | 21.98 mm / PASS | 21.98 mm / PASS |
| cross2_axis_obstruction | 0 mm / PASS | 0 mm / PASS |
| end_ramp_angle | 124.2 deg / PASS | 124.2 deg / PASS |
| left_mount_d_-1 | 7 mm / PASS | 7 mm / PASS |
| left_mount_wall_span_-1 | 7.5 mm / PASS | 7.5 mm / PASS |
| left_mount_d_1 | 7 mm / PASS | 7 mm / PASS |
| left_mount_wall_span_1 | 7.5 mm / PASS | 7.5 mm / PASS |

## BRep 副作用
- 新增材料 `C1−C0` = **17809.646003 mm³**，界内 X=5..110、Y=−16..16、Z=0..6。
- 移除材料 `C0−C1` = **17712.917597 mm³**，同XY、Z=22..28。净体积 +96.728407 mm³。
- 用原草图单闭合轮廓挤出0..28 mm得到精确的主腔扫掠体，不只依赖包围盒。两方向差集再减该扫掠体，测得 **0 / 0 mm³**，阈值1e−4 mm³。未观察到越界变化。
- 从 `CrossThroughHoles` 开始下游阶段净体积差约96.7284 mm³，说明横钻和移动后的主腔交会确实改变；它不是“下游BRep不变”。两个横钻的直径、孔位、轴线不受阻仍通过，扫掠体外无变化。就已验证范围没有不可接受的副作用；不承诺未知区域或完整孔截面、工程可用性。

## 五项合成控制与回滚
已正确TOP→REJECTED/no-edit；反向可定位→VERIFIED；未签发坐标→UNKNOWN/no-edit；带真实LinkSub(Face1)引用→REJECTED/no-edit；错误digest标识→REJECTED/no-edit。夹具输入标识用于注入哈希不匹配；真实输入及输出另以实际字节SHA256核验。五项均符合预设。
回滚只将额外的C1副本恢复为冻结A1原字节：真实SHA、FreeCAD重开和旧BOTTOM/FAIL复现；双向BRep差0/0。第一次回滚字节已正确恢复，但临时文件默认0600使非root复核失败；只给本次测试文件继承源模式后重试通过。两次日志和容器状态均保留，未重跑真实C1。

证据根：`/home/gypsophila/geotree/work/e02-i/`；原始输出 geotree-e02-i-1/results.json、C0.FCStd、C1.FCStd，修复状态 repair-proposal.json，BRep/属性差分 property-diff.json；命令/输出/退出见 VERIFICATION.txt、run-1.stdout/stderr/exit、rollback.log、containers.txt。FreeCAD缓存镜像，CPU2/RAM4GiB/GPU0/断网/非root/只读根；只读加载任务副本，原件复核哈希不变。
