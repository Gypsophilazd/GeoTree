# E02-L1｜原生镜像最终门禁
**BLOCKED：冻结 launcher 的 ID 契约与 L Agent/relay 不兼容。** 2026-11-13 SGT。

| 验收项 | 结果 |
|---|---|
| 任务、源码、配置 | 固定 2002df3ce7 digest 67a0fcb49ef3472055bde2a0684bd555d6ac464009e921d770313e9bf9800835；冻结清单全通过，配置 SHA be9f0a3303d38537bae047ded2c4253ecf9e0641c56d2f83764e66fcc557a5db |
| 原生 Agent | PASS，实际 Harbor 0.23.0 启动任务包自带 Dockerfile 构建产物 sha256:7ab295551e161d6c14604f1cfc7233dbc9f72c8760de87671008783d12e6a604，非旧题或 Mock 镜像；Agent 基镜像 sha256:7de9956cd783d48955835e61b8d212c26b2df901d5a5be8217bd58fb6c1bd5a4 |
| 原生 Verifier | PASS（环境可用性及镜像身份），使用 Harbor 原生独立环境路径，仅启动/inspect/停止，sha256:6d3ca9ee4cebe4919f66be94a5b87255a6118ad17cf1d47bccee6c2a930e1ff0；没有调用 verifier。Verifier 基镜像未独立核验，不读取评分构建配方来填补该项 |
| 原生无模型 Mock | PASS，freecad-2002df3ce7__c8SsJ2q，真实 Harbor 工厂和 Trial 生命周期，exception=null、terminal=done；check_workspace/run_freecad/done、ATIF 三步、answer.py / answer.FCStd 已留存；评分禁用，verifier_result=null |
| 实际隔离 | Agent CPU2、RAM4GiB、GPU无请求、非 privileged；任务 agent no-network，通过 Harbor sidecar；UID65534 对 /logs、/logs/verifier 无访问、Worker 不可写，无 Docker socket；Verifier 独立容器及挂载 |
| ABI/预算/Worker/NoSearch | PASS，native-regression.log；同一配置、首轮 Observation 去除随机 request_id 后一致，动作相同，预算相同；配对 Mock 仅 L1 成功 CAD 后调用 Worker；无评分回流 |
| 正式启动 | **BLOCKED**，见下 |

冻结 run-arm.sh 第7行仍要求 `^k-[0-9a-f]{16}-k[01]$`；L Agent 和 Windows relay 都要求 L 格式。用有效 L 格式及不可启动的 deadline=0 复测，第一处正则拒绝（退出1），无尝试槽保留。原生 Mock 使用单独的无模型命令，并不证明冻结 launcher 可用。需单独修订、测试并重新冻结 launcher 的 ID 校验（方法/模型/任务/预算均无需更换）。本轮未改冻结文件，不给出可启动正式试次的命令。

镜像完整元数据、挂载、资源、Mock SHA 与结果见 `/home/gypsophila/geotree/work/e02-l/native-image-manifest.json`。原生 Mock、Verifier 探针、回归和拒绝日志同目录。未启动 L0/L1、未调用真实 Codex、未生成评分。
