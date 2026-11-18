# E02-K｜Enhanced Agent 接线
**PASS：真实 Harbor 环境接口、MockProvider、固定公开任务文本；PARTIAL：未运行真实模型或目标包试次。** 2026-11-13（Asia/Singapore）。

- 新入口 `geotree.enhanced_agent:EnhancedAgent`，旧 NoSearch 入口与历史文件哈希保持不变。复用 E02-F2 的有限预算 NoSearch Runtime（原 NoSearch/ActionValidator/Recorder）、Mailbox ModelProvider、CAD Executor、ATIF。
- 固定任务 `gnucleus-ai/freecad-06a5c206229@sha256:0a4939b8e768105a8a243a4d1e520c5bffbf8e7384204753113e20971998e04f`。实际使用的文本必须匹配 E02-J 已冻结公开 instruction SHA `748281ae72fccb4316490b016b5b6b55b776da176b9757cb9ef2a8c3f931960e`（先校验原字节；对 Harbor 传入文本只容忍首尾空白差异，两组统一规范化）。没有图片。仅检查公开 instruction/task 配置白名单字段；未取用归档中的其他成员内容。
- 两组安装同一 root-owned 固定 Worker，CAD 仍以 UID65534执行，动作只为 check_workspace / run_freecad / done；不增加 Shell、模型工具、文件权限。只在K1成功执行CAD后，以相同UID运行固定只读验证 Worker。仅打开固定普通文件 `/app/answer.FCStd`，校验 SHA 前后不变，不执行 answer.py 作为测量、不传入人工清单或评分信息。通过 GeometryObserver、文本候选和 EvidenceGate 生成真实报告，按 action_id、产物hash、公开文本hash绑定；压缩反馈并单独保留完整 Worker 事件。K0/K1 首观察和可用动作离线相同；K1只多后验验证。
- 可测且已独立复核的规则才可硬FAIL；没有FAIL不进入修复，缺件/未知不能强制修改。真实任务公开指令要求评测时重跑 answer.py，单改FCStd不构成可重放提交；本轮固定为 K1 验证及修复决策、不发布原生CAD单文件补丁。该端盖的外径/厚度不是已有“隔离单Pad显式长度编辑”类型，实际检测时返回 UNKNOWN/no_supported_safe_repair_mapping。若未来输入呈现该类型，在此任务的提交契约下仍返回 REJECTED/submission_requires_replayable_answer_py。未新增任务专用修复脚本。

## 真实容器、无模型验收
通过实际 Harbor DockerEnvironment.exec/UnixOps 在缓存FreeCAD的独立Compose fixture 运行（不是 Harbor Bench试次）。同一冻结公开指令、简化探针，仅检查已有条件，不是端盖完整解。合规/反例/缺件均进入真实几何 Worker；已通过只读程序、/logs拒绝、无Docker socket、退出与哈希绑定检查。旧测试夹具在同容器中单独执行原 SafeRepair，测得 VERIFIED 与0/0 mm³包络外差；只写临时副本，K任务发布规则仍拒绝。
 
| 离线场景 | 结果 | K1 Worker墙钟 |
|---|---|---:|
| Raw同输入/同脚本 | 无增强反馈、无Worker调用 | 0 |
| 合规尺寸 | 4 PASS、27 NOT_CHECKABLE、无FAIL、Repair NOT_RUN | 0.471 s |
| 直径反例 | 1可信FAIL，原FCStd hash保持，修复 UNKNOWN | 0.463 s |
| 缺件（执行退出0） | MISSING、无硬FAIL | 0.286 s |
| 独立冻结单Pad修复 | 0.087 s、VERIFIED；不发布到任务路径 | — |
| Worker超时 | 注入超时，保留原CAD结果并附ERROR | — |

每个Mailbox Mock场景3步、1次CAD执行、3×5个夹具token（非真实用量），原始trace/ATIF/增强开销均通过。复用预算测试：4决策/2CAD、总deadline与单次deadline、旧ID拒绝、软预算越界。文本Windows relay 的 Job Object 测试退出0/7/124，模拟孙进程退出、父进程存活；当前CLI 0.167.0-alpha.4.1，登录状态为ChatGPT，只做本地检查，无发模型请求。真实命令入口无明确授权时在启动Harbor前 exit64。

证据 `/home/gypsophila/geotree/work/e02-k/`：run-preflight.sh、preflight.stdout/stderr/exit、preflight-summary.json、各Mock试次的agent/trace.jsonl、trajectory.json、verification.jsonl、enhancement-cost.json、budget.log、relay-tests.log、preservation.log、task-meta.json。fixture CPU2/RAM4GiB/GPU0/断网，预检退出后只停止本轮容器；未干预其他训练。未把固定工具、UID/ACL及AST当成任意Python安全证明。
