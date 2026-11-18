# E02-F 首次配对开发试次
状态：BLOCKED（运行门槛未完成）；A0 NOT_RUN；A1 NOT_RUN。

本轮没有启动任何新Benchmark试次。已授权的两次尝试尚未消耗；未调用决策模型、独立verifier，未生成本轮answer.py/answer.FCStd，无reward、token usage、试次wall或行为差值可报告。历史0.314269不充当A0。离线fixture输出不充当能力成绩。

冻结目标：gpt-6.1-sol/high，同一固定开发题gnucleus-ai/freecad-6b54209a13，同公开输入/schema/执行器/终止策略；4次决策、2次CAD执行、工具60秒、模型420秒、总wall1200秒、总token软预算200000。A0 raw，A1仅增加GeometryObservation。串行、每组attempt1/retry0，无第三次。

尚未冻结可运行配置，尚未验证新Agent真实Harbor入口。具体缺口见E02_F_real_integration.md。既有relay/Runtime不能直接满足所有上限，必须先补两组共用预算控制并测试。200000替代早期协议100000；本轮不使用旧预算。

模型第一动作、A1利用反馈、局部修复/重复脚本、warning误导、DONE差异全部NOT_RUN，不推断。人工尺寸manifest仅用于离线fixture，未进入任何模型请求。
