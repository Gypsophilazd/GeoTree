# GeoTree E06 Studio｜发布验收

日期：2026-11-24（Asia/Singapore）。

- **发布位置：** [GitHub main](https://github.com/Gypsophilazd/GeoTree/tree/main)。源码发布提交为 [`f288939e27ec40524841c0a0e901d77c7a2ec97c`](https://github.com/Gypsophilazd/GeoTree/commit/f288939e27ec40524841c0a0e901d77c7a2ec97c)；[v0.1.0-studio-mvp](https://github.com/Gypsophilazd/GeoTree/tree/v0.1.0-studio-mvp) 指向含本报告的版本。
- **同步位置：** Windows `D:\GeoTree`。原 `.git` 及远端历史保留；正常快进，未强推。已比对服务器白名单快照与 Windows 暂存 Git blob 的 SHA256：100 个源码与素材文件，1,202,080 字节（约 1.15 MiB，不含本报告和 Git 历史）。GitHub 的源码提交独立浅克隆 pack 为 864.72 KiB。最终发布树含本报告共 101 个文件。
- **保留：** Studio API 与 WebGL 视口、真实 FreeCAD 特征网格、Codex Windows Relay、DeepSeek 适配、Harbor Agent 和证据门、主动几何检查、受限修复、依赖锁与 Dockerfile、Benchmark Lab 精简数据、可编辑六页 PPT、架构与必要截图。
- **排除：** 原始工作目录、模型调用和推理事件、Harbor trial、日志、任务数据集和私有评分器、大型 CAD 与镜像、生成结果和凭据。旧实验文档和清单从当前发布树退役，保留在原 Git 历史；原服务器历史未改。公开合成件只提交源代码和约束说明，运行时实际生成 CAD。

## 实测

| 环境 | 结果 |
|---|---|
| Windows Python 3.13 | 锁文件哈希安装；24 项核心测试通过，FreeCAD 专项按设计跳过；4 项 Studio/API 测试通过；NoSearch、预算、候选回归、Windows Relay 进程测试、Mock/HTML 通过。 |
| Ubuntu 独立发布快照，Python 3.12 | 新 `.venv` 用哈希锁安装；核心/Studio/脚本回归通过；FreeCAD 容器内主动测量测试 4/4。 |
| Ubuntu 上已有 FreeCAD 1.1.0 镜像 | 实际无模型 Studio smoke：三角形 66.047735° → 90°、范围外 BRep 差为零、隔离修复、独立重放和 STL 网格导出通过。发布 Dockerfile 提供构建路径；本次实测复用了现有镜像，未将其打包。 |
| GitHub 独立浅克隆 | 读取并核对源码提交、文件白名单及敏感目录排除；在新克隆运行 Studio/API 4/4 通过。 |

本机未安装可用的 WSL2 Ubuntu，故 Windows 本机 Docker/FreeCAD 链路未运行；Linux 端已实测。没有发起真实模型、DeepSeek 付费请求或 CAD Benchmark。B0 NOT_RUN，B1 两题 0.0，B2 一题 0.814775、另一题 FAILED/reward=null；均为历史记录，见 [CSV](presentation/benchmark_results.csv)。

## 启动

在 WSL2 Ubuntu 或独立 Ubuntu 中，于克隆根目录执行：

```bash
bash scripts/setup-linux.sh
docker build -f docker/smoke.Dockerfile -t geotree/freecad:1.1.0 .
bash scripts/studio-smoke.sh
bash scripts/studio-start.sh
```

打开 <http://127.0.0.1:8765/>。项目只绑定环回地址；远程使用 SSH 端口转发。Windows 模型桥需要自有 Codex 登录及支持相应 CLI 选项；DeepSeek 需显式授权和服务端配置。Mock 只验证消息链路，真实无模型 CAD 验证使用随仓库发布的合成件。旧 LIVE 截图不代表新安装产生了新模型请求。
