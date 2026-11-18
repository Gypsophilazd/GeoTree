# E02-G：实际 FreeCAD 核对与合成缺陷
**PASS（真实产物只读复核、离线测试）；PARTIAL（真实目标错误尚未证实）。**
原始 script/CAD 双哈希、公开图、轨迹动作顺序和 A1 动作-产物绑定核验；前后历史原件及 trace/ATIF/图纸 SHA256 未变。两组 check_workspace → run_freecad → done，首稿在结构化反馈前。评分只见历史 E02-F2 报告（0.330496 / 0.212255），没有加载进本轮测量或冻结条件，不从差分归因。

每件16/24可检查（66.7%）、16 PASS、0 FAIL、7 UNKNOWN（29.2%）、1 NOT_CHECKABLE（4.2%），共8项未判定（33.3%）。这不是完整任务覆盖率。检查列的候选映射完整轴/面信息在 measurements.json，表列目标来源为1692×930图上的像素框。

| ID | 公开来源 | 期望/出处/置信 | A0 | A1 | 映射与原因 |
|---|---|---|---|---|---|
| length | front [548, 491, 890, 521]：141 | 141 mm / EXPLICIT / reviewed | PASS · 141 | PASS · 141 | outer extension lines; orientation checked against asymmetric raised end in both stored artifacts and scripts；唯一测量 |
| width | lower plan [408, 551, 563, 758]：86 | 86 mm / EXPLICIT / reviewed | PASS · 86 | PASS · 86 | outer extension lines; orientation checked against asymmetric raised end in both stored artifacts and scripts；唯一测量 |
| height | front [448, 331, 565, 435]：40 | 40 mm / EXPLICIT / reviewed | PASS · 40 | PASS · 40 | outer extension lines; orientation checked against asymmetric raised end in both stored artifacts and scripts；唯一测量 |
| cross1_d | front [600, 316, 709, 383]：2×Ø2.8 THRU | 2.8 mm / EXPLICIT / reviewed | PASS · 2.8 | PASS · 2.8 | front view shows bore circles at dimensioned X,Z from left and bottom; corresponding Y-axis concave cylindrical wall, no diameter filtering；唯一测量 |
| cross1_x | front [549, 421, 707, 457]：29.5 | 29.5 mm / EXPLICIT / reviewed | PASS · 29.5 | PASS · 29.5 | front view shows bore circles at dimensioned X,Z from left and bottom; corresponding Y-axis concave cylindrical wall, no diameter filtering；唯一测量 |
| cross1_z | front [526, 370, 709, 481]：13.38 | 13.38 mm / EXPLICIT / reviewed | PASS · 13.38 | PASS · 13.38 | front view shows bore circles at dimensioned X,Z from left and bottom; corresponding Y-axis concave cylindrical wall, no diameter filtering；唯一测量 |
| cross1_axis_obstruction | front [600, 316, 709, 383]：2×Ø2.8 THRU | 0 mm / DERIVED / reviewed | PASS · 0 | PASS · 0 | front view shows bore circles at dimensioned X,Z from left and bottom; corresponding Y-axis concave cylindrical wall, no diameter filtering; zero solid intersection along identified axis is a necessary condition, not a full aperture test；centerline_only_not_full_bore_clearance |
| cross2_d | front [600, 316, 709, 383]：2×Ø2.8 THRU | 2.8 mm / EXPLICIT / reviewed | PASS · 2.8 | PASS · 2.8 | front view shows bore circles at dimensioned X,Z from left and bottom; corresponding Y-axis concave cylindrical wall, no diameter filtering；唯一测量 |
| cross2_x | front [549, 421, 707, 457]：29.5 + 34.5 | 64 mm / DERIVED / reviewed | PASS · 64 | PASS · 64 | front view shows bore circles at dimensioned X,Z from left and bottom; corresponding Y-axis concave cylindrical wall, no diameter filtering；唯一测量 |
| cross2_z | front [526, 370, 709, 481]：21.98 | 21.98 mm / EXPLICIT / reviewed | PASS · 21.98 | PASS · 21.98 | front view shows bore circles at dimensioned X,Z from left and bottom; corresponding Y-axis concave cylindrical wall, no diameter filtering；唯一测量 |
| cross2_axis_obstruction | front [600, 316, 709, 383]：2×Ø2.8 THRU | 0 mm / DERIVED / reviewed | PASS · 0 | PASS · 0 | front view shows bore circles at dimensioned X,Z from left and bottom; corresponding Y-axis concave cylindrical wall, no diameter filtering; zero solid intersection along identified axis is a necessary condition, not a full aperture test；centerline_only_not_full_bore_clearance |
| end_ramp_angle | front [806, 376, 892, 435]：124.20 | 124.2 deg / EXPLICIT / reviewed | PASS · 124.2 | PASS · 124.2 | lower right oblique line from x=130.8 to right extent; unique lower end plane spanning Y; compare obtuse supplement of XZ slope；唯一测量 |
| left_mount_d_-1 | lower plan [562, 583, 975, 761]：4×Ø7 depth 7.5 | 7 mm / EXPLICIT / reviewed | PASS · 7 | PASS · 7 | left pair at x=7.6, 49 separation about indicated centerline; either Y sign; wall concavity and axis test, not radius-selected；唯一测量 |
| left_mount_wall_span_-1 | lower plan [853, 697, 975, 762]：4×Ø7 depth 7.5 | 7.5 mm / EXPLICIT / reviewed | PASS · 7.5 | PASS · 7.5 | axial span of unique cylindrical wall at reviewed left pair; proxy for cylinder depth only, not blind-floor certification；唯一测量 |
| left_mount_d_1 | lower plan [562, 583, 975, 761]：4×Ø7 depth 7.5 | 7 mm / EXPLICIT / reviewed | PASS · 7 | PASS · 7 | left pair at x=7.6, 49 separation about indicated centerline; either Y sign; wall concavity and axis test, not radius-selected；唯一测量 |
| left_mount_wall_span_1 | lower plan [853, 697, 975, 762]：4×Ø7 depth 7.5 | 7.5 mm / EXPLICIT / reviewed | PASS · 7.5 | PASS · 7.5 | axial span of unique cylindrical wall at reviewed left pair; proxy for cylinder depth only, not blind-floor certification；唯一测量 |
| mount_blind_floor | lower plan [853, 697, 975, 762]：4×Ø7 depth 7.5 | —  / INFERRED / unconfirmed | UNKNOWN | UNKNOWN | cylinder span alone cannot prove no breakthrough beyond bore；insufficient_source_or_coordinate_mapping |
| right_mount_position | lower plan [850, 546, 941, 740]：3 / 5 / 50.8 nearby; exact center mapping not verified | — mm / UNKNOWN / unconfirmed | UNKNOWN | UNKNOWN | 尚无独立映射；insufficient_source_or_coordinate_mapping |
| main_recess_depth | front [795, 363, 829, 430]：22 | 22 mm / EXPLICIT / reviewed | UNKNOWN | UNKNOWN | target feature/side correspondence not independently verified；insufficient_source_or_coordinate_mapping |
| main_recess_open_side | upper/lower plan [554, 145, 813, 699]：visible/hidden line interpretation | —  / INFERRED / unconfirmed | UNKNOWN | UNKNOWN | view association and hidden-line convention still need independent review；insufficient_source_or_coordinate_mapping |
| main_recess_radii | lower plan [563, 613, 648, 677]：4×R3 | 3 mm / EXPLICIT / reviewed | NOT_CHECKABLE | NOT_CHECKABLE | explicit corner callout; no robust corner-to-face query yet；no_supported_measurement |
| side_detail_angle | end view [1188, 349, 1264, 427]：20° | 20 deg / EXPLICIT / reviewed | UNKNOWN | UNKNOWN | side-detail surfaces and sign not independently mapped; pocket TaperAngle alone insufficient；insufficient_source_or_coordinate_mapping |
| left_recess_step | front [503, 379, 628, 439]：15 | 15 mm / EXPLICIT / reviewed | UNKNOWN | UNKNOWN | plan/section location of projection line not independently disambiguated；insufficient_source_or_coordinate_mapping |
| side_chamfers | front [773, 414, 843, 465]：8×C1 | 1 mm / EXPLICIT / reviewed | UNKNOWN | UNKNOWN | eight distinct edge identities not verified；insufficient_source_or_coordinate_mapping |

## 能区分形状，尚不能区分哪份符合图纸
在两件共用坐标取 (X,Y)=(45,0)，从 Z=-1 至41 作竖直轴线与实体求交。A0 剩余材料 **Z=0..5.5 mm**，A1 **Z=22..28 mm**。对应脚本分别从上方与下方切主腔。它们不是同一几何，尽管包围盒、实体数、粗特征计数相同。由于目标开口方向/22标注与主腔的对应未充分审定，此处仍 UNKNOWN；探针不是目标判决。下一步首选独立视图归属复核，尤其核对公开显隐线和观察方向；不要根据历史评分猜哪个开口方向正确。

## 已知缺陷夹具
13个独立合成参数化模型（在容器内构造；均有效单实体）。13/13 状态与预设一致：5 正控PASS、5 负控FAIL、2 UNKNOWN、1 NOT_CHECKABLE。可判定10/13（76.9%），UNKNOWN 2/13（15.4%）；FP 0/5、FN 0/5，仅对这5组配对控制，不能外推自动修复准确率。
| Case | 预设 | 实测 | 数值 | 测量 ms |
|---|---|---|---:|---:|
| length_ok | PASS | PASS | 30.0 | 4.684 |
| length_bad | FAIL | FAIL | 29.0 | 4.166 |
| diameter_ok | PASS | PASS | 7.0 | 5.279 |
| diameter_bad | FAIL | FAIL | 6.0 | 4.917 |
| position_ok | PASS | PASS | 12.0 | 5.169 |
| position_bad | FAIL | FAIL | 13.0 | 4.848 |
| through_ok | PASS | PASS | 0.0 | 9.567 |
| blind_bad | FAIL | FAIL | 5.0 | 8.650 |
| angle_ok | PASS | PASS | 124.2 | 5.060 |
| angle_bad | FAIL | FAIL | 130.0 | 6.146 |
| target_unknown | UNKNOWN | UNKNOWN | None | 0.074 |
| ambiguous_identity | UNKNOWN | UNKNOWN | None | 6.022 |
| unsupported | NOT_CHECKABLE | NOT_CHECKABLE | None | 4.247 |

FreeCAD 1.1.0。单件打开/24条检查/关闭/哈希验证约 **5.128 s / 6.006 s**；夹具测量中位 5.060 ms（不含生成）。单次容器约11.84 s、exit 0。CPU2、4 GiB、GPU0、network none、非root、只读根与挂载；只挂 CAD 副本、specs 和可信测量源码，不读取旧脚本、不启动模型/Benchmark、不启动评分容器。合成脚本在内存生成几何，未编辑历史件。

证据：`/home/gypsophila/geotree/work/e02-g/` 下 original-hashes.json、preservation.log、measurements.json、run-1.stdout/stderr/exit、container.txt、resources.log、deliverables.sha256。命令：`bash /home/gypsophila/geotree/work/e02-g/run.sh geotree-e02-g-1`（保留已退出容器；复核时用新名）。
