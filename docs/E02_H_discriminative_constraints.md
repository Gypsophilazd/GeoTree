# E02-H3/H4：可区分的主腔约束
**VERIFIED_TARGET_CONSTRAINT：105×32、4×R3 标注的主腔开口朝上（+Z）。** 不是直接文字“TOP”，而是公开投影派生：H1由安装盲孔与底部右斜面独立定向；同一105×32圆角内轮廓在Top可见、Bottom遮挡。前视中该区主体上沿仍是28台面，不显示另一个高出该平面的凸台。内侧24×16窗为另一轮廓，在两视图能看见，不用于定向。结论只针对主腔开口侧，不为全部口袋轮廓及深度背书。

| 产物 | 公开期望 | OCC投影 / 实体核验 | 判决 |
|---|---|---|---|
| A0 | TOP | y=±16、x≈45两侧长边在Top可见，Bottom仅隐藏；x=35/45/55、y=0截线均只剩 Z=0..5.5 | **PASS** |
| A1 | TOP | 同长边在Bottom可见，Top仅隐藏；同3条截线均只剩 Z=22..28 | **FAIL**（开口侧相反） |

两件各有 (45,±18) 处完整 Z=0..28 材料侧壁基准。检查器要求两侧长边的HLR证据与多条占据截线一致；不按体积、分数、Face编号或特征名选择结果。任一证据缺失或身份不唯一即UNKNOWN。匹配范围仅验证标注主腔在可区分的长边/中心区域，不证明整个圆角轮廓。

**22 mm：PARTIALLY_SUPPORTED，不判深度FAIL。** 正视22标注 ROI [795,362,828,427] 上端与28台面共高，下端约在 Z≈6；与主腔可能的隐线高度一致。但邻近右端台阶/孔壁与侧部窗口底缘投影重合，像素上未能把该引出线端点唯一关联到主腔底边。A0 局部实际从28向下22.5 mm；A1 从0向上22 mm，数值相同不抵消方向错误。对 20° 和 4×R3 的角度/圆角数值本轮 NOT_CHECKABLE，R3标注只作轮廓识别线索。

**局部归属（只读）：** 检查储存的 PartDesign 链中间 BRep（stages.jsonl），A1 的三个探针在 RaisedEndPad 后均为 0..28，第一次一致变成 22..28 的是紧接着的 `UndersideCavity` Pocket，Profile=`UndersideCavityOutline`，后续特征没有改变该区的开口侧。A0 首次相应转变发生于 RoundedMainPocket（容差内后续不变）。因果局部定位来自实际中间形状，而非根据命名猜测。可将A1违例归属该Pocket及其草图平面；直接翻转 Reversed 未测试，也不保证其他布尔、深度和孔连通性。

**控制（PASS，5/5）**：合成合法同向开口→PASS；合法反向开口→FAIL；无可信目标方向→UNKNOWN；实际反射后未重签坐标→UNKNOWN；同一反射件明确保留世界基准重新审查后→FAIL。镜像是实际BRep变换；最后一项不声称程序能自动推断配准。夹具为参数化Pad/Pocket，只用于验证方向谓词。

结构化结果：`/home/gypsophila/geotree/work/e02-h/geotree-e02-h-1/result.json` 含 constraint_id、public_source、view_alignment_evidence、expected/measured_relation、artifact_hash、mapping_status、verdict、uncertainty_reason、截线/HLR证据。两个产物 SHA 分别为 `75df192ef4553167d2d5561ab6b479c63733eb069c5c80fb60b6b1a7e715186a` / `a61bddab72ce0f9639ca270d2d11169d1fb41ba6c6b63f5847e2fecf70071861`。原始和独立副本哈希复核通过。

执行：`bash /home/gypsophila/geotree/work/e02-h/run.sh geotree-e02-h-1` 已跑 exit0（复验换新容器名）。另用同镜像只读运行 attribute.py。源码、run-1.stdout/stderr/exit、stages.jsonl、containers.txt、preservation.log在 `/home/gypsophila/geotree/work/e02-h/`。2 CPU / 4 GiB、GPU0、断网、非root、只读CAD；原 NoSearch、Reader、历史结果不变。未读取评分器实现、隐藏参考或评分结果，也未用分数解释图纸。
