# 当前真实模块
Windows Codex/ChatGPT 日志通过桥接交给 FastAPI；DeepSeek Responses 和 Mock 是并列路径，DeepSeek 本轮只做 Fake HTTP 回归。Studio 生成由 geotree 动作校验和隔离 FreeCAD 运行共同完成；存储文件包含状态、事件、脚本、FCStd 和特征重建 Mesh。历史检查调用真实 E04 OCC，合成修复调用 E05。Harbor 是另外的独立编排/评分入口，复用 GeoTree 的脚本校验、OCC 证据以及 FreeCAD 工具约定；不是与 Studio 共用同一个持久化运行时。

- CAD-Assistant / ICCV 2025：CAD 专用工具。https://openaccess.thecvf.com/content/ICCV2025/html/Mallis_CAD-Assistant_Tool-Augmented_VLLMs_as_Generic_CAD_Task_Solvers_ICCV_2025_paper.html
- SPADA / ICML 2026：可执行测试及修复。https://proceedings.mlr.press/v306/zheng26q.html
- DeciCAD / arXiv 2026 预印本：语义动作及可持久状态。https://arxiv.org/abs/2610.21755
- CAD Bench V3 / 独立离线评分入口。https://cadbench.ai/benchmark

不复现上述方法的训练或完整系统。
