# GeoTree E02-K3｜Harbor Agent ABI 修复

**PASS：原入口修复、Harbor 工厂及真实 CLI 无模型兼容性。NOT_RUN：任何新 Benchmark / Codex / 独立评分。** 日期：2026-11-13（Asia/Singapore）。

Harbor 0.23.0 的 BaseAgent 声明 `async setup(environment) -> None` 和 `async run(instruction, environment, context) -> None`。本机安装的 `Trial._setup_agent` 和 `Trial._run_agent_phase` 都以关键字传 `environment=`。原 EnhancedAgent 的两处 `env` 不符合此契约。已原位改为显式 `environment`，同步方法体；v2 显式按关键字委托，不用 kwargs 掩盖。run 仍返回 None，保留异常传播及 terminal sidecar，并写入 AgentContext 结束状态和 CAD 次数；不改变 Token 统计策略。

| 验收 | 状态 |
|---|---|
| 修复前同测试 | 退出1，复现 unexpected keyword argument |
| 真实 AgentFactory 导入及 inspect.signature / bind | 六个具体入口通过，包括 PairedAgent、旧 NoSearch、原 EnhancedAgent 和 v2 |
| Mock 关键字 await、返回 None、异常、AgentContext、Harbor ATIF schema | 4项永久测试通过 |
| 测试目录及旧 E01-P0E NoSearch | 19项单测通过；旧10项回归通过 |
| 真正 Harbor CLI | 本地 fixture k-df67ed5067c473aa-k1；CLI退出0，试次门禁确认 terminal=done；仅 Mock，评分禁用 |
| Enhanced 容器回归 | 实际 Trial 方法和隔离 FreeCAD：raw/good/bad/missing、超时反馈和现有修复夹具通过 |
| 回滚 | 只在额外副本恢复原字节及两处旧异常；新入口保留修复 |

**后续启动门槛**：先跑 `tests/test_harbor_agent_abi.py`；动态枚举 `geotree` 包内具体 BaseAgent，每个走真实工厂，不允许绕过绑定检查。该测试未接入历史冻结 launcher；不要重启旧 K0/K1。新的 live 配置应另行冻结本版 SHA。

证据根目录：`/home/gypsophila/geotree/work/e02-k3/`。before.sha256、after.sha256、abi.diff、VERIFICATION.txt、baseline.log、abi.log、unit.log、nosearch.log、cli.log、cli-gate.log、preflight.stdout/stderr、rollback.log。K2 历史结果未改；原源码精确副本保留，同旧 manifest 的源路径对应关系已校验。因为当前源码原位修复，旧 frozen manifest 的原路径不再代表旧源码；未改写旧清单。
