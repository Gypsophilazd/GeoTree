# GeoTree

GeoTree 是面向自主参数化 CAD Agent 的任务条件化验证与安全修复 Harness，基于 FreeCAD / OCC 与 Harbor。模型只提议动作；Harness 做校验、预算与反馈；Harbor 的任务容器执行 FreeCAD；独立评分不回流到模型。

已实现 NoSearch、EnhancedAgent、几何观察、公开文本约束提取、证据门禁、ATIF/trace、Windows Codex 邮箱，以及窄范围、可拒绝的副本修复。未知映射保留 UNKNOWN，无法实现的查询记 NOT_CHECKABLE。已验证的 FCStd 副本编辑不等于可重放的 answer.py 修复。没有实现 MCTS、通用工程图理解，也未证明跨任务性能提升。

## 本机快速开始（PowerShell）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -BuildSmokeImage
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1
```

使用 WSL2 Ubuntu、uv、Linux Docker；无需原服务器、数据集或模型账户。详细步骤、自己的 Codex 账户、Windows/WSL 共享目录、可选的完整 Harbor 工作流见 [Windows 环境说明](docs/windows-setup.md)。

- [英文 README 与模块图谱](README.md)
- [团队 Agent 指令](AGENTS.md)
- [研究摘要](experiments/summaries/research-status.md)；历史分数均为开发数据。
- [E02-L3 报告](docs/E02_L3_final_report.md)：L0 基础设施失败，0 次模型请求，reward 为 null；L1 未运行。
