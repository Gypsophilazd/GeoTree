# E02-L3｜最终报告

2026-11-14 SGT。**L0 BLOCKED（一次 Harbor attempt 已启动并消耗）；L1 NOT_RUN。未形成真实模型配对。**

| 项目 | L0 | L1 |
|---|---|---|
| 任务 | gnucleus-ai/freecad-2002df3ce7；sha256:67a0fcb49ef3472055bde2a0684bd555d6ac464009e921d770313e9bf9800835 | 同一冻结任务，未启动 |
| 作业 / 试次 | l-64880971b5cc4be7-l0 / freecad-2002df3ce7__cqemj8q | 无 |
| 实际模型请求 / Token / CAD 执行 | 0 / 0 / 0 | 0 / 0 / 0 |
| 产物及 SHA | 未生成 answer.py 或 answer.FCStd | 无 |
| 独立 Verifier / reward | 未运行 / null（不是0分） | 未运行 / null |
| Trial / 终态 | RuntimeError: relay_error / error | 未产生 |
| Harbor trial wall | 17.177 秒（仅基础设施，不是建模成本） | — |

## 停止原因与责任归属

冻结哈希、ABI、ChatGPT 登录及实际容器 CPU2/RAM4GiB/GPU0、非 privileged、Worker/日志权限预检通过。新版启动器确实通过了 L 格式，Harbor 到达首轮 Observation。Windows 启动胶水在首条模型请求前要求实际镜像与原生门禁镜像的 RootFS 和整个 Config 相等。实际镜像 ID sha256:311678964c37356064f82ad1fce448a50ad5cc84884f9f83552b51d7c86061ec，参照镜像 ID sha256:7ab295551e161d6c14604f1cfc7233dbc9f72c8760de87671008783d12e6a604。事后 inspect 确认 RootFS layers 完全相同，Config 仅 Labels 字段不同。**不是已证实的运行时或依赖差异；是本轮的比较条件把标签差异误判成不可接受的镜像漂移。**

启动器断言退出并发出 relay-error 标记；Agent 等待中止，未发模型请求。Harbor CLI exit=0，但实际试次异常且结果门禁拒绝。该失误发生在已经占用真实 attempt 后，未改条件重启，也未启动 L1。冻结方法、预算和源码未改；无上传，试次容器已退出。

## 方法结论

可信约束覆盖、真实目标 FAIL、反馈影响、可重放修复、额外 Token 和时间成本全部 NOT_RUN，无法从这次失败推断 Enhanced Harness 的行为价值。维持 k=1；不推进 Safe Repair 或有限搜索。优先在独立无模型夹具验证镜像身份门禁能正确区分标签变化与实际执行配置变化，并在占用真实尝试前验收。方法上仍可优先考虑 Active Verification，但本轮没有数据支持其相对收益。

## 证据

/home/gypsophila/geotree/work/e02-l/l-64880971b5cc4be7-l0/ 保留原始 Harbor trial result、配置与 lock、trace、terminal、runner/启动错误、image-comparison.json 和试后冻结校验。首轮 observation 存在，但没有模型事件、真实制品或评分，未填补虚构记录。冻结配置 SHA256 be9f0a3303d38537bae047ded2c4253ecf9e0641c56d2f83764e66fcc557a5db。
