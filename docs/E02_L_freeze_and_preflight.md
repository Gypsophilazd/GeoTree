# E02-L｜冻结与预检
2026-11-13 SGT。**PASS：公开任务冻结、ABI 门禁、本地真实 Harbor CLI Mock。PARTIAL：原生任务镜像待核验。NOT_RUN：L0/L1、真实模型、评分与反事实。**

任务 `gnucleus-ai/freecad-2002df3ce7`，digest `sha256:67a0fcb49ef3472055bde2a0684bd555d6ac464009e921d770313e9bf9800835`。公开 instruction SHA256 `77d0b12fe2547c8f1d36865de96e2f9f3fe4733a358f4e0dce66f2408a4c3af4`。沿 E02-J 已固定的 V3 成员顺序，排除已使用或冻结的旧任务，取首个有明确尺寸参数的未运行文本创建题；前序旧题 freecad-6b54209a13、freecad-06a5c206229 已排除。无成绩筛选。任务为 development，不是 holdout。仅提取公开 instruction/配置/Agent Dockerfile，不读取私有评分内容。

新入口 `geotree.enhanced_agent_l:EnhancedAgent` 复用 K3，参数切换为新任务和 L0/L1。首轮只用公开文字，无图像；工具动作仍为 check_workspace/run_freecad/done。产物 /app/answer.py、/app/answer.FCStd；公开任务契约重跑脚本，不发布仅改 FCStd 的修复。未添加目标规则或人工尺寸。固定同一 launcher 和执行器，L1仅开启现有后验 Worker。

Harbor 0.23.0、Docker 29.1.3、Codex CLI 0.167.0-alpha.4.1，已确认 ChatGPT 登录。原任务配置 CPU2/4096MiB/GPU0，agent no-network，原生独立 verifier。FreeCAD 1.1.0。Mock 缓存镜像为 `sha256:2e1e1306135a9c0d69febd0c5257c4585abe3be67f9ed8b5396de20e52ee4e76`，不冒充新题原生镜像。新题原生 Dockerfile 的基镜像已固定为 `sha256:7de9956cd783d48955835e61b8d212c26b2df901d5a5be8217bd58fb6c1bd5a4`；最终 Agent/verifier 镜像 digest 尚未核验，留空。必须在正式请求前核验原生 Agent 容器限制和 digest，评分后记录 verifier digest；L1 不得在镜像或基础设施不一致时继续。不能用原 Dockerfile 相同的旧题镜像哈希代替新题实际构建。

## 实测
ABI 启动前门禁为 tests/test_harbor_agent_abi.py；真实工厂和七个入口通过。本地 `bash work/e02-l/mock-cli.sh` 通过：原公开指令、隔离缓存 FreeCAD、三次 Mock 决策、一次 CAD、15 个 Mock token、真实 Worker；结果门禁返回 `ACCEPT: terminal=done`。评分禁用。Mock只有2项结构约束可测；不能从此推断模型行为或 Benchmark 成绩。原 K2 文件未改。启动器无授权实测退出64。L1 必须有同配对 L0 的实际 trial 成功及独立评分；两组各保留一次启动槽，不自动重试。

冻结配置 SHA256：`be9f0a3303d38537bae047ded2c4253ecf9e0641c56d2f83764e66fcc557a5db`；清单 SHA256：`cf4d9e0ce276565729c6ec8313ac8dbc7a0cc690c00a50d7f51b968b8c1695cd`。文件及日志位于 `/home/gypsophila/geotree/work/e02-l/`。

## 运行清单（未执行；只在明确授权及原生容器预检后）
同一个16位十六进制 pair ID，先 l0，检查实际 trial/terminal/独立评分及产物，再 l1。每组新 Unix deadline（从启动起1200秒），双端一致。
Ubuntu：`GEOTREE_L_RUN_APPROVED=EXPLICIT_PAIR_APPROVAL bash /home/gypsophila/geotree/work/e02-l/run-arm.sh l-<pairhex>-l0 <unix-deadline>`；第二组同命令以 l1 结尾。
Windows：先在当前进程记录授权开关 `$env:GEOTREE_L_RUN_APPROVED='EXPLICIT_PAIR_APPROVAL'`；实际 Agent 容器通过预检后，在同一 deadline 内运行 `python outputs/e02-l/relay.py l-<pairhex>-l0 outputs/e02-l/l-<pairhex>-l0 <unix-deadline>`；第二组替换两处 l0 为 l1。relay 不自动代替容器预检。不上传。任一共有基础设施故障立即停止，不修配置后续跑。需额外核对 answer.py/answer.FCStd、日志和独立评分，CLI exit=0 不代表成功。

预算：gpt-6.1-sol/high、串行、每组 attempt1/retry0、4决策/2CAD、420s/60s、总1200s、200k tokens软上限；两组至多8模型请求。L1固定 Worker 每次10秒、最多两次、计入总wall。
