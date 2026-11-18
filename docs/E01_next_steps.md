# GeoTree E01｜实施顺序与启动条件

截至 2026-11-12。下面是后续命令与验收门槛，E00 未执行这些命令。先打通 CAD Bench V3，CADWorld 不阻塞主线。

1. **P0｜锁定依赖与授权。** 在 `/home/gypsophila/geotree` 内建隔离工具环境，确认 Harbor 0.23.0。用户确认项目内安装/下载范围后，用已批准的 uv 二进制：`UV_TOOL_DIR="$PWD/work/uv-tools" UV_TOOL_BIN_DIR="$PWD/work/bin" UV_CACHE_DIR="$PWD/work/uv-cache" uv tool install harbor==0.23.0`。不要改系统 Python。先核实 V3 发布 digest、容器镜像大小和批准的下载上限；当前尚未测得镜像占用。Docker daemon 已可用，无需改配置。
2. **P0｜CAD Bench 单题无模型链路。** 从项目根运行下列命令。它可能下载官方数据/镜像，只在第 1 步确认后启动。期望容器、任务、verifier 日志与 trial 结果齐全；缺 CAD 的 0 分是合理结果，不是能力得分。不要启用 upload，先检查任务启动时是否隔离评分资源。
   ```bash
   ./work/bin/harbor --version
   ./work/bin/harbor run -d gnucleus-ai/cad-bench@v3 -e docker -a nop \
     --n-tasks 1 --n-concurrent 1 --n-attempts 1 --max-retries 0
   ```
3. **P0｜自定义 Harbor 最小入口。** 实现一个确定性无模型 `BaseAgent`，先只用任务可见目录/白名单工具，生成开发用日志和有效 ATIF；将它装到 Harbor 解释器可导入的位置，再把第 2 步的 `-a nop` 换成 `-a geotree.harbor_agent:GeoTreeAgent`（拟创建，不是现有命令）。固定单题开发选择，验日志、产物路径、网络、权限与 verifier 隔离，检查工程图真的进入图像字段。
4. **P0｜供应商离线契约。** 用合成 PNG、录制/构造的 Chat 和 Responses 响应测截图往返、tool ID、预算字段、错误/超限、日志脱敏。只有明确批准凭据的使用和美元上限后才做小规模真实文本+图像+工具回传；未批准前不发 API 请求。ChatGPT/Codex 不作为隐含 API 预算。
5. **P1｜准备 CADWorld VM。** 用户批准后由管理员确认 `kvm` 访问（例如 `sudo usermod -aG kvm gypsophila`，重连后复核）；如需系统安装，确认 `sudo apt install qemu-system-x86 qemu-utils` 与服务依赖后再执行。沿用可用 Docker，不更改已有容器。批准项目内依赖 `uv sync`、[约 35 GB 可用空间的 VM 准备](https://github.com/Zdong104/CADWORLD#freecad-vm-image)与 Docker 镜像下载；预留 overlay/录制空间，CAM 再批准装 FreeCAD 1.1.x console。可先检查官方 VM 文件 hash 或使用管理员已验证的现成镜像，不触碰其他项目。
6. **P1｜CADWorld 单题 GUI-only smoke。** 从本轮 no-checkout 仓库固定 SHA 在项目内另备一个干净 checkout；依赖/VM 准备好后进入该 checkout。下面从官方任务列表仅选择一个任务，不修改上游文件，不下载 VM，不调用模型。若日志/截图成功但没有保存 CAD，不能报评测能力 PASS。
   ```bash
   python3 - <<'PY' > /home/gypsophila/geotree/work/cadworld-e01-one.json
   import json
   with open("evaluation_examples/test_all.json", encoding="utf-8") as fp:
       tasks = json.load(fp)
   domain, ids = next((k, v) for k, v in tasks.items() if v)
   print(json.dumps({domain: ids[:1]}))
   PY
   uv run python scripts/python/run_cadworld.py --headless --no-download_vm \
     --test_all_meta_path /home/gypsophila/geotree/work/cadworld-e01-one.json \
     --agent gui_probe --observation_type screenshot --action_space pyautogui \
     --max_steps 1 --no-skip_finished \
     --result_dir /home/gypsophila/geotree/work/cadworld-e01-results
   ```
7. **P1｜实现 Lite 与受控消融。** 只有单轨通过后才加 k≤3 候选层。先在预先选定的开发任务上对照 NoSearch 与 Search；固定模型快照、effort、步数、动作权限、试次预算，保留失败。对 CAD Bench 记连续奖励，CADWorld 记严格通过率，两者均报告实际用量及延时。正式完整任务与公开提交另外审批。
8. **P2｜单独决定是否接 DSH。** 仅当指定同模型 route、允许工具、图像、预算与 trace 可重复后才纳入；否则保留外部官方基线和 NoSearch，不阻塞 GeoTree。
