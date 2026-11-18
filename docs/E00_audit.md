# GeoTree E00｜技术接入审计

审计日期：2026-11-12（Asia/Singapore）。执行位置：Windows PowerShell → SSH 别名 `gypsophila-tailscale` → Ubuntu，项目根目录 `/home/gypsophila/geotree`。**未读取到本地开题文档**（`docs/proposal_v0.2.md` 不存在），本轮依据 `docs/E00-audit-prompt.txt`。本报告不含 GeoTree 实验成绩。

## 决策

| 组件 | 判定 | 证据级别与最短下一步 |
|---|---|---|
| Parametric CAD Bench V3 | **GO（接入契约）；本机跑通 BLOCKED** | 官方提交规则允许自定义 agent；Harbor 0.23.0 工厂接受 import path。准备项目内 Harbor 后，用单任务 `nop` 验证容器、日志和 verifier，再换自定义入口。 |
| CADWorld GUI-only | **GO（接入契约）；本机 VM BLOCKED** | 上游 loader 与任务列表经离线执行验证；本机 KVM 权限、QEMU/uv、项目 VM 镜像未就绪。先修权限，再跑 `gui_probe`。 |
| DeepSeek Harness（DSH）作为首阶段严格同模型对照 | **NO-GO（首阶段）；可后续评估** | 有 headless/SDK，不只是 Web；未见对应的公开 DSH 跑分，也未实测隔离、图像、工具回传及 trace。先用同模型 GeoTree-NoSearch 作受控对照。 |
| GeoTree-Lite | **GO（E01 设计）；NOT_RUN（尚无实现/实测）** | 两个 adapter 都有可见反馈；每回合排序最多 3 个候选、只执行 1 个，即可检验候选选择的价值，无需真实回滚或声称 MCTS。 |

## 主机证据

| 检查 | 状态 | 命令与实际摘要 |
|---|---|---|
| 系统、CPU | PASS / LOCALLY-VERIFIED | `grep PRETTY_NAME /etc/os-release` → Ubuntu 24.04.5 LTS；`uname -srmo` → Linux 7.0.0-38-generic x86_64 GNU/Linux；`nproc` → 56；`/proc/cpuinfo` → vmx。 |
| 内存、磁盘、权限 | PASS / LOCALLY-VERIFIED | `free -h` → 62 GiB 总内存、54 GiB 可用、8 GiB swap；`df -hP .` → /dev/sda2，1.4T 可用；`findmnt -T . -no TARGET,FSTYPE` → / ext4；项目可写；用户 gypsophila (uid 1000)，在 docker/sudo 组，不在 kvm 组。未运行 sudo；未测额外配额/GPU（NOT_RUN）。 |
| Docker | PASS / LOCALLY-VERIFIED | Docker CLI/daemon 均为 29.1.3；`docker info --format '{{.ServerVersion}} {{.OSType}} {{.Architecture}}'` → `29.1.3 linux x86_64`，退出 0；Compose 2.40.3；镜像列表按 gNucleus/FreeCAD/CADWorld/OSWorld 名称筛选无结果，不代表没有其它标签或 digest 的镜像。未启动容器。 |
| KVM | BLOCKED / LOCALLY-VERIFIED | `/dev/kvm` 存在，root:kvm；`test -r /dev/kvm && test -w /dev/kvm` → 否；ACL 未给当前用户访问。CPU 支持不等于当前账号能启动 VM。 |
| 运行工具 | PARTIAL / LOCALLY-VERIFIED | Python 3.12.3，Git 2.43.0，Node v18.19.1；QEMU (`qemu-system-x86_64`/`qemu-img`)、uv、Harbor、pnpm、常用 FreeCAD/FreeCADCmd 命令未在 PATH 找到；未搜索项目外的其他安装。DSH 源码构建要求 Node ≥24.9.0 / pnpm 11.28.5。 |
| VM 镜像 | BLOCKED / LOCALLY-VERIFIED | 本轮 CADWorld checkout 路径下未找到 `vm_data/FreeCAD-Ubuntu.qcow2`。上游估计需约 35 GB 可用空间；这不是实测下载字节数，另需预留 VM overlay、容器层和日志空间。 |

## 上游锁定与证据位置

以下浅克隆均在 `work/e00-src/`，使用 `--depth 1 --filter=blob:none --no-checkout`，用 `git show HEAD:<path>` 取所需源码；未安装依赖、未执行上游安装脚本。

| 来源 | 固定版本 | 关键位置 |
|---|---|---|
| [Harbor](https://github.com/harbor-framework/harbor/tree/1e5c5c6db929a10a140d05e606882c671ae20729) | v0.23.0 / `1e5c5c6db929a10a140d05e606882c671ae20729` | `src/harbor/cli/jobs.py:592,1050,1150,1168`；`agents/factory.py:111,198`；`agents/base.py:324–379`；`agents/nop.py`；`verifier/verifier.py:167–268` |
| [CADWorld](https://github.com/Zdong104/CADWORLD/tree/5e9529ff984b5426a5c194b94a09dc84cbe7fa7a) | `5e9529ff984b5426a5c194b94a09dc84cbe7fa7a` | `README.md`；`docs/MODEL_OUTPUT_CONTRACT.md`；`scripts/python/run_cadworld.py:90–199,330–381,413–447`；`scripts/python/benchmark/run_single.py:30–42,184–259`；`desktop_env/desktop_env.py:307–315,388–432` |
| [DSH](https://github.com/deepseek-ai/deepseek-harness/tree/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb) | `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb` | `docs/cli-help.md:100–169`；`docs/user/guide/providers.md:59–117`；`docs/user/guide/python-sdk.md`；`packages/llm/llm-deepseek/src/{adapter,models,config}.ts`；`packages/llm/llm-pi-ai/src/provider.ts:25–50` |
| [ToolTree](https://github.com/SYang2000/ICLR_2026_ToolTree/tree/fed7a608ca54ba2e75078f9a1f409c9aa7fab18f) | `fed7a608ca54ba2e75078f9a1f409c9aa7fab18f` | `src/mcts/tree_search.py:42,119,208,276,352,359,377`；`src/mcts/pruning.py`；`src/evaluation/judge.py:67,91`；`src/tools/{tool_manager,real_tools}.py` |

## CAD Bench V3 — SOURCE-VERIFIED / 本地运行 NOT_RUN

[官方规则](https://www.gnucleus.ai/cad-bench/benchmark)、[Harbor 数据集](https://hub.harborframework.com/datasets/gnucleus-ai/cad-bench/v3)、[发布报告](https://www.gnucleus.ai/cad-bench/news/cad-bench-v3)。`gnucleus-ai/cad-bench@v3`：100 题（文本创建 30、创建后编辑 30、工程图转 CAD 40），公布 digest `sha256:8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`。未拉取/逐任务验本地 digest。Hub 页所列 Harbor ≥0.20.0 是 schema 1.3 最低支持；正式复现固定 Harbor 0.23.0、FreeCAD 1.1.0、gnucleus-freecad-validator 0.6.0/v2 scorer。适配器和输出路径以具体 task instruction 为准，不假设所有任务同名输出；本轮未核验某一道题的本地 task bundle。

Harbor 入口 `-a` 接受注册名（如 `nop`、`codex`、`claude-code`、`mini-swe-agent`）或 Python import path `package.module:ClassName`；旧 `--agent-import-path` 为兼容选项。适配器安装到 Harbor 所用的 Python 环境，继承 `BaseAgent`，实现 `name`/`version`、`async setup(environment)`、`async run(instruction,environment,context)`。默认按编排器设置的 agent 用户执行；不得用 host agent 权限绕开任务边界。允许任务所需的 FreeCAD 自动化/文件操作及已选 provider 出网；工作限于 /app 任务状态。验收方在分离 verifier 环境评分，隐藏参考几何不作为 observation；通用 Harbor verifier 的脚本/奖励读取代码不等于 V3 具体隔离配置已实测。

正式提交命令（**仅引用，未运行**）：

```bash
harbor run -d gnucleus-ai/cad-bench@v3 -a YOUR_AGENT -m YOUR_MODEL \
  --n-concurrent 4 --n-attempts 1 --max-retries 0 --upload --public
```

一套完整 100 题、每题 1 attempt、0 retry、9,000 秒、最大可用 effort（记录生效值；不支持则先问维护方）。失败/未评分按 0 纳入平均连续奖励；只允许经维护方审查的窄义基础设施故障替换，保留原试次。公开 Harbor job 保留配置、CAD、verifier 输出、agent log、ATIF `trajectory.json`（完整旧 `trajectory.jsonl` 也可），然后向维护方提交 PR。0–100 量纲是连续分，不是通过率。用 `nop` 走链路不需要模型凭据，但本机 Harbor 未安装，不能把 Docker 连通性当评分 smoke；下一轮命令见 E01。

## CADWorld — SOURCE-VERIFIED，部分 LOCALLY-VERIFIED

[官网](https://cad-world.github.io/)、[论文附录 D/E/K/L](https://arxiv.org/html/2609.16251v2)。Linux/KVM/Docker/QEMU/uv；仓库 `pyproject.toml` 要 Python ≥3.12（README 建议 3.12/3.13）；主机 FreeCAD 1.1.x console 对 CAM 和相应离线重评估尤其重要。VM 默认 64G 虚拟盘、8G RAM、8 vCPU，镜像 `vm_data/FreeCAD-Ubuntu.qcow2`，缺失时默认自动下载；`--no-download_vm` 可强制关闭下载（缺失会报错）。真实评测指定 `evaluation_examples/test_all.json`；源码默认指向未在固定树中找到的 `test_small_cases.json`，应显式传入存在的清单。README 的 3/25 步和 `test_easy.json` 不是正式设置；README/API smoke 示例会调用模型，改用上游 `gui_probe` 才是无模型的基础设施探针。

Loader 通过 `importlib.import_module`、`getattr` 和无参构造解析 `--agent package.module:Class`。`reset` 支持无参；runner 会先尝试传 logger、VM IP、步数；GeoTree GUI-only 不使用 VM IP/主机状态。`predict(instruction, obs) -> (response_dict, list[str])`；默认 `obs["screenshot"]` 是 PNG bytes，另有 `instruction_images`（如题目提供）与指令；a11y/terminal 不加入正式 GUI-only 输入。历史上下文在 API runner 默认 10 轮，1920×1080；正式 100 个模型回合，当前源码可在同一回合执行多个 action 并逐 action 写行，不用 JSONL 行数代替步数。论文列 reset 15s、动作后 0.3s、评分前 2s；记录 wall time/timeout，未核实统一的正式整题 wall-clock 上限，不把延时或 100 步写成秒级限额。

默认 API 路径接受 `{"reason":"…","action":"…"}` 或短 `actions` 列表，规范化到 literal-only 的 pyautogui click/drag/scroll/press/write/hotkey 等、`time.sleep` 或 `WAIT`/`DONE`/`FAIL`；非法模型输出转 WAIT。**自定义 agent 直接交给 runner，不自动经过 API agent sanitizer**；实际 `DesktopEnv.step` 可转发 Python 命令，所以必须在自研 adapter 内限制为 GUI 动作。保存任务指定的原生 .FCStd 和必要附产物，`DONE` 本身不等于成功。Host `env.evaluate()` 按任务检查保存产物，严格全检查通过才是 1；失败 0。结果 `results/<run_id>/<example_id>/` 含 `traj.jsonl`、截图、`result.txt`、诊断 `evaluation.json`、能取到的产物；run 根有 `args.json` 和 `result.xlsx`。JSONL 记录 `step_num, action_timestamp, action, response, reward, done, info, screenshot_file`；API response 可含 `raw_response`、解析动作、`executed_action`，自研需显式填入并区分来源。

**实际离线 smoke（退出 0）**：Ubuntu Python 3.12 使用 `git show HEAD:scripts/python/run_cadworld.py` → AST 提取并执行固定 SHA 中的 `load_agent/distribute_tasks/GuiProbeAgent/NoopAgent`，输入为内存合成模块 `e00_fixture:Agent`、空观测、两步预算和真实 task 元数据。结果：自定义无参构造通过；gui_probe 返回 WAIT,DONE，下一次无动作；noop 依次 WAIT、DONE；清单含 11 类、200 条且不重复。**未启动 VM、未执行任何 GUI 动作、未评分。** 完整 GUI smoke：BLOCKED。

## 外部方法与模型 — CONFIG_REVIEW_ONLY

- **DSH（MIT）**：官方 Web 快速入口 `npx @deepseek-ai/dsh web`，但非唯一入口。`dsh headless --json`、stdio JSON-RPC `dsh sdk`/`dsh sdk-minimal`、Python `deepseek-harness-sdk` 均有源码/文档。Python wheel 包运行时，通常不依赖系统 Node；本机未安装验证。工具由 profile/plugins/MCP 配置，最小 profile 仍含 shell、read_image、working_directory。直连 DeepSeek adapter 默认走 Anthropic-compatible **Messages**，内建 `deepseek-flash` 标注 text+image 并有附件序列化。pi-ai 注册 `openai-responses`；固定快照未确认 Terra 的现成 catalog 条目，先配置显式 model route（`input: [text,image]`，`api: openai-responses`），再验证图片与 tool result；不要将通用 provider 支持等同于模型已跑通。两榜检查结果：`NO_MATCHING_PUBLISHED_RUN`（未见 DSH 搭配候选模型的对应组合，不代表私有实验不存在）。
- **ToolTree（MIT）**：`ToolTreeSearch._get_candidate_actions/_expand` 提候选、pre-judge 与阈值筛选；`_execute/_record_execution` 写执行结果；`LLMJudge.post_evaluate`、`BidirectionalPruner`、`_backpropagate` 做执行后判断与回传；`src/evaluation/benchmarks.py` 负责通用任务归一化，不是 CAD scorer。默认 mock 提供计划级结果，real 由 `ToolManager` 调 executor，真实工具可用不意味着可重放 GUI 状态。真实 GUI checkpoint/rollback：**NOT SUPPORTED**（固定源码未发现完整保证）。独立写小循环更适合约束不同的 CAD executor；移植可沿用 judge/去重/pruning 逻辑，但要替换工具、状态与评分抽象，且额外模型 judge 会影响预算与消融控制。
- **DeepSeek `deepseek-flash`**：官方映射 DeepSeek-V4.1-Flash-1017；[Vision](https://api-docs.deepseek.com/guides/vision/)、[Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)、[定价](https://api-docs.deepseek.com/quick_start/pricing/)。JPEG/PNG/GIF/WebP；可发 data URL、外链或 Files API，建议直接发授权本地 PNG 字节的 base64 data URL，校验 MIME/体积（inline 受 48 MiB 请求体限制）。Chat 用 `image_url`、`choices[].message.tool_calls` 与 `tool_call_id`，保持 thinking 模式所需的历史字段；Responses 用 `input_image`，并按响应协议回送结果。1M context，最多 384K 输出；美元/百万 token（缓存命中输入/未命中输入/输出）峰时 0.006/0.30/1.20，非峰 0.003/0.15/0.60，非报价承诺。
- **OpenAI `gpt-6.1-terra`**：[模型](https://developers.openai.com/api/docs/models/gpt-6.1-terra)、[函数调用](https://developers.openai.com/api/docs/guides/function-calling)。文本/图像输入，工具调用必须使用 Responses；`input_image`、`function_call`、`function_call_output` 按 `call_id` 配对。1,050,000 context、922,000 最大输入、128,000 最大输出，effort 到 max。标准美元/百万 token：输入 1、缓存命中 0.05、输出 5；>272K 输入触发长上下文加价，账号实际 rate limit/预算未核验。Codex 是开发工具，不等于 GeoTree 的 API 额度；[符合条件的订阅者](https://developers.openai.com/api/docs/guides/chatgpt-api-credits)可以单独激活并绑定 API 组织，不能直接把 Codex 限额当推理预算。
- 两家均未读取密钥、未发推理请求；截图端到端、图文与工具同轮、工具回传都 NOT_RUN。E01 先做离线序列化/回放，再按批准的每次输出上限、总调用数和美元上限验证。

本轮只在项目内写报告、源码审计材料和少量网页证据；没有安装依赖、下载任务/VM 镜像、改权限、跑正式评测、访问评测真值、调用付费模型或上传成绩。
