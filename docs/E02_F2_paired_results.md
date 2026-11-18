# E02-F2 A0/A1 开发配对结果
**PASS / DEVELOPMENT-ONLY。** 两组各一次，A0 先完成、A1 随后启动。均 Harbor exit 0、无 trial exception、独立 verifier separate。历史 0.314269 未用作 A0。

| 指标 | A0 Raw | A1 Geometry |
|---|---:|---:|
| 试次 | f2-6de7a8e60cc44ace-a0 | f2-6de7a8e60cc44ace-a1 |
| 连续 reward | 0.330496 | 0.212255 |
| 终止 / ATIF steps | done / 3 | done / 3 |
| 决策 / 执行动作 / CAD 脚本 | 3 / 2 / 1 | 3 / 2 / 1 |
| input / cached input / cache write | 117158 / 0 / 0 | 119507 / 0 / 0 |
| output / reasoning output（output 子集） | 7227 / 3554 | 8680 / 4748 |
| input+output / 软预算 overshoot | 124385 / 0 | 128187 / 0 |
| Harbor trial wall | 636.927 s | 598.911 s |
| 启动器到退出（按 deadline-1200 估算） | 647.56 s | 608.51 s |
| 工作区工具 / CAD工具 | 0.164 / 2.783 s | 0.171 / 3.586 s |
| Reader内核测量 / Reader起点至反馈入日志 | 未在loop运行 | 0.391 / 0.904 s |
| 最终存储形状（离线同一 API 复核） | 有效、1实体 | 有效、1实体 |
| bbox / 体积 | 141×86×40 mm / 152095.556 mm³ | 141×86×40 mm / 159644.866 mm³ |
| 特征类型计数 | 1 Body / 12 Sketch / 2 Pad / 10 Pocket | 1 Body / 12 Sketch / 2 Pad / 10 Pocket |

## 逐步行为
1. 两组先 check_workspace，成功后各提交一个完整脚本，均正常退出、stdout/stderr 空。A0 说明主腔深度与侧开口为推断；A1 也在首次生成时说明主腔和侧凹几何为推断。
2. A0 仅收到 exit=0 和空输出，DONE 理由明确提到没有独立几何验证。A1 在下一决策的 history 中收到真实有效性、单实体、包围盒、体积、特征与依赖。观察匹配动作 `df88f080-c6d1-4781-8996-ec02ff1bf806`，哈希与最终产物相等。
3. A1 DONE 引用了一个 Body、有效单实体、141×86×40 mm，并明确 20°细节仍未验证。它利用反馈改善了**终止解释**，但未做局部修复或重跑，也未声称整个设计已证实正确。
4. A1 反馈 12 个欠约束 warning、0 geometry errors、0 execution errors；3个 UNKNOWN：target_geometry_correctness、target_volume、unmapped_dimensions。目标约束列表为空，PASS=0、FAIL=0，不代表满足所有目标。A0 在线无几何反馈；离线复核也有12 warning、3 unknown。两组0拒绝、0 CAD错误，无 warning 导致的修改。

A1−A0 = **−0.118241**。两份脚本在几何反馈出现前已不同，之后均直接 DONE；结果差值不是 Observer 的因果估计。单题也不能推断总体收益。A1 最后一步输入比 A0 多2348 tokens（包含反馈及其他上下文差异，不单独归因）；整轮 +3802 input+output tokens。A1 wall 更短不表示 Observer 加速，运输重连和模型生成占主要时间。

## 产物与索引
- A0 answer.py SHA256 `b2b766479cbfcb47a1fd96642aff4e21f813173f09c4f387617d54f39fee7dee`；answer.FCStd `75df192ef4553167d2d5561ab6b479c63733eb069c5c80fb60b6b1a7e715186a`。
- A1 answer.py SHA256 `e64bdbc3536730c15a32e0574762fab9c7923a6b8c3f547a05d754b53f1f5941`；answer.FCStd `a61bddab72ce0f9639ca270d2d11169d1fb41ba6c6b63f5847e2fecf70071861`。
- `/home/gypsophila/geotree/work/e02-f2/<trial-id>/summary.json` 含完整 artifact 路径、特征树、逐轮 usage 和反馈；geometry-final.json 为离线复核；实际 Harbor result.json、trace.jsonl、trajectory.json 及 Windows events/usage/response/exit 均保留。未读取 verifier 私有数据；reward 仅作事后分析。
