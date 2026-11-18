# E02 实施报告

## 1. 总结
- **PASS**：既有证据核查、确定性GeometryObserver、自制FreeCAD案例、可替换Mock闭环、旧入口兼容性哈希。
- **PARTIAL**：真实质量错误归因、源码可得性、G1真实Harbor reader接入；几何反馈提升reward未验证。
- **BLOCKED**：DeciCAD可执行源码复核（当前官方关联仓库仅README）；缺少公开可证实目标几何的项保持UNKNOWN。
- **NOT_RUN**：新增真实CAD Benchmark、真实模型决策、独立verifier、本轮A0–A4、G2/G3、训练、全量任务。

本轮没有新CAD成绩、模型调用=0、模型API token=0；历史reward0.314269不重记为E02成绩。浏览论文和审计工具的开销不混入CAD模型计量。

## 2. 读取与版本
读取开题、E01-P0E报告、Architecture v0.1、comparison v0.1及NoSearch/Agent/policies/decision_bridge源码；原入口未重构。固定历史Harbor0.23.0、FreeCAD1.1.0、verifier0.6.0；本轮FreeCAD版本也由API输出。
数据集digest `8a786725d3648a76282fc5868df06da3d5e00d603f283573a53430803465d78a`；task digest `741b7289accd15447a3a2ea1a7ffa21853fcafa07aa4a08b2d592a9877c3f2d9`。本轮未再下载任务/镜像。

## 3. 实际新增文件
- `/home/gypsophila/geotree/src/geotree/geometry_observer.py`：只读FCStd/OCC状态、特征依赖、公有约束及UNKNOWN。
- `/home/gypsophila/geotree/src/geotree/geometry_feedback.py`：可选G1 Executor装饰层、观察超时/失败隔离。
- `/home/gypsophila/geotree/tests/test_geometry_contract.py`：7个契约测试。
- `/home/gypsophila/geotree/tests/test_geometry_feedback.py`：6个Mock集成/异常测试。
- `/home/gypsophila/geotree/tests/freecad_observer_fixtures.py`：6个真实FreeCAD API离线案例。
- `/home/gypsophila/geotree/work/e02/public_constraints.json`：公开来源审查清单（仅诊断，不嵌入通用代码）。
- 本轮5份 `docs/E02_*.md`；证据/源码清单均在 `work/e02/`。

## 4. 实际测试与命令
所有相对命令从 `/home/gypsophila/geotree` 执行；isolated.sh自身切换到work/e01-p0，故测试路径使用绝对路径。

### 基线（旧Mock回归）
```
bash work/e01-p0/isolated.sh env PYTHONPATH=/home/gypsophila/geotree/src .venv/bin/python /home/gypsophila/geotree/work/e01-p0e/test_nosearch.py
```
exit0。`work/e02/mock-regression.log`保留10条PASS：nullable输出、反馈、ATIF、拒绝、超时、非法响应、预算、JSON transport、relay/adapter终止等。AST检查不是沙箱证明。

### 新增单元/集成
```
bash work/e01-p0/isolated.sh env PYTHONPATH=/home/gypsophila/geotree/src .venv/bin/python -m unittest discover -s /home/gypsophila/geotree/tests -p 'test_geometry*.py' -v
```
exit0，literal摘要 `Ran 13 tests in 0.013s` / `OK`；`work/e02/all-unit-tests.log`。
Mock真实调用NoSearchRuntime，生成并用Harbor Trajectory校验ATIF，检查下一轮history含结构化GeometryObservation、无reward；这些是测试fixture，非模型轨迹或能力成绩。测试临时trace在测试结束清理；持久证据为测试代码和日志。
观察失败/超时不覆盖执行exit；执行非0不观察旧产物；非几何动作不调用reader；拒绝未类型化payload。

### FreeCAD离线
```
bash work/e02/run_observer.sh
```
**已执行一次，exit0**；容器名 `geotree-e02-observer`已保留，重复命令须选新离线容器名而非删除历史容器。真实命令全文在脚本。
缓存镜像ID `work/e02/observer-image.txt`；日志 `freecad-tests.stdout`、空stderr、`freecad-tests.exit`=0；JSON `observer-results.json`。

|案例|实际结果|
|---|---|
|既有answer.FCStd|valid、1 solid/Body、141×86×40、5个公开检查PASS，target volume UNKNOWN|
|合法参数化小Pad但指定尺寸不符|shape valid，尺寸FAIL，证明valid≠correct|
|两个分离实体compound|solid_count2，not_single_solid|
|缺Profile的Pad|依赖warning/空shape诊断|
|空文档|无可选择结果，UNKNOWN|
|外部执行错误输入|execution_errors与几何状态分开保存|

六案不等于六次Benchmark。本轮未构造损坏BRep覆盖所有内核错误；未验证所有特征类别、拓扑命名、重算一致性。实际历史产物观察CPU查询约0.298秒（仅observer函数时间，非全容器wall）。

### 命令纠错记录
一次直接执行isolated.sh得到exit126（脚本无执行位）；改为bash启动。随后相对tests路径在脚本切换cwd后导致ImportError/exit1；改绝对路径后12项通过，加入超时案例后13项通过。源码下载一次SSL EOF后重试成功。没有把失败命令覆盖成实验成功，最终通过仅指已修正命令。

## 5. 资源与边界
离线容器network none、CPU2、RAM/Swap4GiB、pids128、UID65534、rootfs只读、cap-drop ALL、no-new-privileges、/tmp tmpfs256MiB；无GPU或Docker socket。只挂本项目源码、产物副本、约束、fixture（readonly）。`container-inspect.txt`保留实际State/HostConfig/Mounts。没有挂载verifier/参考模型或RL目录。
执行前约52.86GB available，短采样CPU idle约89%、iowait0；前后记录 `resources-before.txt` / `resources-after.txt`。未监测每毫秒峰值，不宣称已证明绝无RL影响；未停止、修改其他训练进程/容器。未修改daemon/全局配置，未清理旧对象。
仅3份小型论文PDF及精选源码下载；精确字节/SHA见references中的两个manifest。未安装研究repo、下载模型/大型数据。所有第三方源码仅阅读，未执行。

## 6. 保全、回退与完成边界
`baseline-hashes.txt`及`baseline-preservation.log`确认原5个源码文件和开题原文均保持原hash；历史artifact hash也前后核对。旧入口从未接入新装饰层，保持原行为；需要退出G1时不启用新装饰层即可，无需改旧agent或删除证据。新增模块是增量实现，不将旧代码回滚伪称执行过新试次。

G1目前是**离线可测Observer+Mock接线**，不是已跑通的真实新Harbor试次。下一阶段需实现固定命令reader、核验相同任务权限及公开信息公平性，再按E02_experiment_protocol申请2个串行DEVELOPMENT-ONLY配对试次。G2/G3仅设计，无搜索收益结论。


证据根目录：`/home/gypsophila/geotree/work/e02/`。日期：2026-11-12。本文将历史真实试次、离线测试、待验证设计严格分开。

## 7. 最终复核补记
- 旧Mock回归再次执行，exit0，完整输出见 `work/e02/mock-regression-final.log`。
- FreeCAD输出末行原文：`PASS 6 FreeCAD observer cases (existing + 5 synthetic); no benchmark or model run`。
- 3份PDF总计 2419734 bytes；11份manifest精选源码总计 268146 bytes（不含API元数据、额外README及日志）。项目新增工作目录的实际占用以 `resources-after.txt` 的du为准，不把文件逻辑大小冒充Docker全局存储增量。
- 五份报告已重新打开验证UTF-8；源代码/测试经过解析与真实运行，最终文件SHA见 `work/e02/final-artifacts.json`。
