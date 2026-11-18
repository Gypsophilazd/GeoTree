# E02-K｜真实试次状态与运行清单
**K0 NOT_RUN；K1 NOT_RUN；等待本轮明确用户授权。** 未创建真实试次ID，未消耗模型请求、Token或CAD Bench尝试；无独立reward、真实产物或真实终止原因。离线数据不得填入正式指标。核心“真正参与新Bench试次”尚未达成。

## 冻结设置
`/home/gypsophila/geotree/work/e02-k/frozen.json` / frozen.sha256。固定V3 dataset digest与06a5c206229 task digest，Harbor0.23.0；任务元数据 CPU2 / RAM4096MiB / GPU0、agent no-network、独立原生verifier（600秒任务配置）。保留其策略，不更改环境或评分权限。两组均 gpt-6.1-sol/high、现有Windows ChatGPT登录、文本且无图片、同一schema/执行器/公开信息、每组attempt1/retry0，顺序K0再K1，不上传。每组4次决策、2次CAD脚本（每次60秒）、单次模型420秒、整体1200秒、200k tokens软上限。K1仅在CAD成功后固定检查，最多2次、各10秒并计入整体；无额外模型请求或原生文件独立修复提交。两组最多8次模型决策请求、合计软预算400k tokens；只作为授权上界，非实际消耗。

## 未来获准后的运行顺序（未执行）
1. 记录明确授权。复核frozen.sha256、CLI登录/参数、服务器内存、I/O与现有训练；不触碰RL。实际agent主容器确认同样的限制、隔离与镜像前置条件；不足即停。
2. 按 `k-<16hex>-k0` 生成新ID和同一Unix deadline，在Ubuntu用 `bash /home/gypsophila/geotree/work/e02-k/run-arm.sh <id> <deadline>`，Windows并行启动文本relay `python relay.py <id> <fresh-local-log-dir> <deadline>`。两端批准开关须在真实授权后设置；原装置无授权时拒绝运行。保留真实原始事件、JSONL、ATIF、模型用量、工具计时、产物SHA、独立评分及退出码。
3. K0完成后核对任务digest、有效产物/trace、独立verifier和基础设施错误；共同故障即停止K1，不重试。K0有合法件时，对冻结只读副本调用 `bash /home/gypsophila/geotree/work/e02-k/diagnose-k0.sh <k0-id>`；只挂公开文本和CAD副本，不挂评分，不将输出回流任一模型。不适用时标记原因。
4. K1用同配置新ID `k-<16hex>-k1`，只一次；分别记录模型决策数、Token字段、CAD/Worker/修复调用数和墙钟、已验证覆盖、可信FAIL、UNKNOWN/NOT_CHECKABLE、无依据修复（应为0）、结束原因、产物有效率与连续reward。只比较同题开发结果，不能作总体性能或因果断言。

K0反事实诊断本轮 **NOT_RUN**（没有K0真实产物）。未来仅用同一Worker，区分生成差异、覆盖不足、检出但不可修复、以及可重放修复通过。无可信FAIL时不宣称修复。只读诊断脚本已做bash语法检查；真实输入路径尚无可执行实证。
