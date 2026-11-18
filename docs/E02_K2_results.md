# E02-K2｜真实试次结果
2026-11-13（Asia/Singapore）。**K0 BLOCKED（唯一一次尝试已消耗）；K1 NOT_RUN（共同入口故障，停止后续组）。** 未形成配对，无模型或方法性能结论。

| 指标 | K0 | K1 |
|---|---|---|
| 作业ID | k-020578104839436d-k0 | 未创建 |
| Harbor trial | freecad-06a5c206229__JVPwXhH | 未创建 |
| 任务 | gnucleus-ai/freecad-06a5c206229，digest sha256:0a4939b8e768105a8a243a4d1e520c5bffbf8e7384204753113e20971998e04f | 同冻结配置，未执行 |
| attempt/retry | 1/0 | 0/0 |
| 启动/结束 | 00:52:49.447 / 00:54:50.132 SGT | — |
| Harbor试次wall | 120.686秒（仅基础设施阶段） | — |
| 模型请求/Token/CAD动作 | 0/0/0 | 0/0/0 |
| answer.py / answer.FCStd | 未生成 | 未生成 |
| 独立verifier | 未运行，reward=null，不是0分 | 未运行 |
| VERIFIED/可信FAIL/行为改变/无据重建或提前DONE | NOT_RUN | NOT_RUN |
| 增强Token/开销、可重放修复 | 无对照数据 | NOT_RUN |

## 根因和停止门槛
冻结前复核源码SHA、入口导入、Windows Codex CLI与ChatGPT登录，通过；任务实际主容器已启动，2 CPU / 4 GiB / 无GPU请求。Harbor 0.23.0 在准备阶段调用 `self.agent.setup(environment=self.agent_environment)`。冻结新入口签名为 `setup(self, env)`，抛出原文：
```
TypeError: EnhancedAgent.setup() got an unexpected keyword argument 'environment'
```
先前独立容器预检直接按位置传参，故没有覆盖真实 Harbor 调度的关键字 ABI。此错误发生在 Agent 建立 mailbox、运行模型及执行任何CAD动作之前。Windows 启动器观察到“Harbor exited before model request”，未启动 Codex relay。Harbor CLI 退出0不代表trial成功；trial result.json含TypeError且verifier_result为null，日志明确没有重试。两个本轮环境容器均退出，未更改其他训练。

复核同一冻结入口的 `run(self, instruction, env, context)` 也不能用 BaseAgent 约定的 `environment=` 绑定；这是第二个静态检测到的ABI差异，实际试次没有进入run，未当成第二个运行异常。配对门禁检测不到trace即停止，未改冻结源码、未生成K1运行标识、未补跑K0。K0反事实检查无产物，NOT_RUN。

## 保全和证据
实际命令保留于runner日志：`GEOTREE_K_RUN_APPROVED=EXPLICIT_PAIR_APPROVAL bash /home/gypsophila/geotree/work/e02-k/run-arm.sh k-020578104839436d-k0 1794503560`。固定模型参数gpt-6.1-sol/high仅为冻结配置，实际无模型调用。预算/权限/评分权限未扩大。冻结校验在试后再次通过。
证据根：`/home/gypsophila/geotree/work/e02-k/k-020578104839436d-k0/`。保留 failure-summary.json、read-failure.py、实际Harbor stdout/stderr、runner日志、容器限制、任务锁/试次result/job.log。模型事件、ATIF、CAD制品及评分是“未产生”，不生成替代证据。未读取隐藏参考或评分器实现，未公开上传。此任务不再进行开发试次。
