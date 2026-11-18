# E02-L2 实验状态
NOT_RUN：历史授权仅覆盖 K2，不覆盖此题 L0/L1；本轮未发起真实请求、未占用试次。无真实产物、奖励、模型反馈利用、可信 FAIL 或可重放修复数据。真实模型请求与消耗均为0，增量成本未测。
原生镜像复用 L1 已核验记录：Agent sha256:7ab295551e161d6c14604f1cfc7233dbc9f72c8760de87671008783d12e6a604；Verifier sha256:6d3ca9ee4cebe4919f66be94a5b87255a6118ad17cf1d47bccee6c2a930e1ff0。实际 live 容器仍需核对镜像身份、权限和资源，不一致则停止。
获授权后：Ubuntu 与 Windows 分别执行以下命令，共享同一16位十六进制 pair ID 和该组 Unix deadline。先 L0；确认 trial 无异常、终态、两件 CAD 产物、独立评分及基础设施一致性再用同 pair ID 启动 L1，并设置该组新 deadline。
```bash
GEOTREE_L_RUN_APPROVED=EXPLICIT_PAIR_APPROVAL bash /home/gypsophila/geotree/work/e02-l/run-arm.sh l-<pairhex>-l0 <deadline>
```
```powershell
$env:GEOTREE_L_RUN_APPROVED='EXPLICIT_PAIR_APPROVAL'
python outputs/e02-l/relay.py l-<pairhex>-l0 outputs/e02-l/l-<pairhex>-l0 <deadline>
```
第二组将 l0 换成 l1。仅在实际 Agent 容器预检通过后启动 relay；固定 gpt-6.1-sol/high，串行各一次，4决策/2CAD，420/60秒，总1200秒，20万Token软上限，不上传。
