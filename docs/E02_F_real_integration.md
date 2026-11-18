# E02-F 真实接入进度
状态：PARTIAL，尚未完成验收。2026-11-12。

已读取E02五份报告、NoSearchRuntime、GeometryObserver、GeometryFeedbackExecutor、现有Harbor Agent及Windows relay。新增src/geotree/geometry_reader.py与tests/test_fixed_geometry_reader.py。旧源码SHA256核对通过，清单work/e02-f/baseline.sha256。

Reader使用固定命令：
```
HOME=/tmp/geotree-home OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /opt/conda/bin/python -I /opt/geotree-observer/reader.py
```
仅读取/app/answer.FCStd；独立进程不执行answer.py；受信代码拟安装到root拥有的只读脚本目录。使用UID65534，输出关联artifact SHA256、action_id、观察时间；保存stdout/stderr/退出码。不传入人工public_constraints.json，约束清单为空，目标正确性仍UNKNOWN。调用者必须在每次动作后设置action_id；尚未完成新Harbor Agent接线，因此尚未证明真实动作绑定。

PASS：15项单元/Mock测试，包括原ATIF校验；旧NoSearch回归；缓存FreeCAD镜像下6个fixture，退出0。日志work/e02-f/unit.log、legacy.log、fixtures.log；实际命令脚本work/e02-f/run-fixtures.sh。fixture包含历史产物和合成模型，不是新Benchmark试次，也不是本Reader完整真实环境预检。

PARTIAL：尚缺固定Reader真实environment.exec端到端预检、新Harbor入口、两组共同执行预算封装、relay进程超时终止及总wall预检。现有relay虽然有等待Observation的420秒期限，但同步codex exec本身没有进程超时控制；旧Runtime也没有最多2次CAD执行的独立上限。复用原入口原样运行不满足本次冻结要求，不能直接开跑。

认证检查返回Logged in using ChatGPT；未复制凭据。资源短采样available约54.29GB，CPU idle约93%、iowait0；未干预RL。历史容器元数据有/logs/verifier挂载；旧setup用/logs权限保护，但新试次尚未实测访问拒绝。未读取该挂载内容。

当前是代码增量与离线验证，不是已完成真实接入。完整隔离、资源与预算门槛尚未确认；没有证据宣称服务器本身不可用。
