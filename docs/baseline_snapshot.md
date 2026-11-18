# GeoTree E00｜公开基线快照

核查日期：2026-11-12。此处全是外部历史参照，未重跑。**不是 GeoTree 实验数据，不是 DSH 同模型对照，也不能据此判断 Harness 因果效应。** 只纳入当前两个官方结果页上可核实的模型行；不将展示页的“14 个评估 agent”补成 14 条可见模型成绩。

## Parametric CAD Bench V3

官方页面标注 Harbor 快照 2026-09-24。分数为 **100 题平均连续奖励，0–100 量纲，含失败/未评分的 0**，± 为榜单 95% CI。Hub 某些 Overview 只对已评分试次汇总，不能用该数覆盖 V3 榜单分母。所有 13 个 Run 链接均逐项访问：9 个抓到 job 页，另 4 个网页工具超时但从 Ubuntu 匿名 GET 返回 HTTP 200（仅证明 HTTP 响应，不证明数据完整）。

| benchmark | task_version | model | harness | harness_version | effort | reported_score | metric | task_count | date_or_snapshot | official_run_url | source_url | notes |
|---|---|---|---|---|---|---|---|---:|---|---|---|---|
| CAD Bench | V3 | Claude Opus 5.5 | Claude Code | 2.1.280 | max | 61.03 ± 7.53 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/2bfed91c-0043-43ed-b797-84ab3057d102) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | SSH HTTP 200；网页抓取超时，未核实页内细节 |
| CAD Bench | V3 | Claude Opus 5.5 | mini-swe-agent | 2.4.6 | max | 57.96 ± 7.82 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/72514eba-0a7f-44e8-b154-ad2ecc7ff5fb) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | 公开 job 页可读；93 completed / 5 timeout / 2 error |
| CAD Bench | V3 | GPT-6 Astra | Codex | 0.154.0 | max | 56.87 ± 6.85 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/9fcdc97e-bf05-48eb-920d-67401d369e00) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | SSH HTTP 200；网页抓取超时，未核实页内细节 |
| CAD Bench | V3 | Claude Fable 5.1 | Claude Code | 2.1.270 | max | 56.75 ± 7.18 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/1306c4c5-ad62-497b-8241-7b99bea19b4b) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | 公开 job 页可读 |
| CAD Bench | V3 | Claude Opus 5 | Claude Code | 2.1.270 | max | 50.86 ± 7.45 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/85a26704-d90e-42eb-a3c4-77ec1a12642d) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | job 页可读 |
| CAD Bench | V3 | Gemini 3.8 Flash | mini-swe-agent | 2.4.6 | high | 36.19 ± 6.97 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/eefb6a64-e30f-40b1-bf89-c3d357b34be7) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | job 页可读 |
| CAD Bench | V3 | Grok 4.7 | Grok Build | 1.0.30 | high | 34.82 ± 6.64 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/380ceb1c-8581-491d-9377-1ab480c54f7d) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | job 页可读；榜单备注：指标按 100 题、现链接 96 条 trial |
| CAD Bench | V3 | GPT-5.6 Sol | Codex | 0.154.0 | max | 29.98 ± 6.17 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/ae948a69-a2c8-4686-906a-0acedc6423bf) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | SSH HTTP 200；网页抓取超时，未核实页内细节 |
| CAD Bench | V3 | Grok 4.6 | Grok Build | 1.0.30 | high | 27.72 ± 6.30 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/ecfb96c6-cee8-47c3-982a-3a9701408dfa) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | job 页可读 |
| CAD Bench | V3 | Gemini 3.8 Flash | Antigravity | 1.2.7 | high | 27.56 ± 6.72 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/57efd748-baff-46b4-86b8-66f327122029) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | job 页可读 |
| CAD Bench | V3 | Kimi K3 | mini-swe-agent | 2.4.6 | max | 24.92 ± 6.40 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/704e63f0-86a0-4ca4-a606-e59954081ad8) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | job 页可读 |
| CAD Bench | V3 | Muse Spark 1.3 | mini-swe-agent | 2.4.6 | max | 20.92 ± 5.81 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/aee96aa1-3969-4753-8792-8fb1f4cf142c) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | job 页可读 |
| CAD Bench | V3 | GPT-5.6 Terra | Codex | 0.154.0 | max | 17.24 ± 5.84 | mean continuous reward (0–100) | 100 | 2026-09-24 | [Run](https://hub.harborframework.com/jobs/8f0d4c3b-f42c-493e-a804-ecb80b8a5a94) | [官方榜](https://www.gnucleus.ai/cad-bench/leaderboard) | SSH HTTP 200；网页抓取超时，未核实页内细节；非 GPT-6.1 Terra |

## CADWorld

官网主设置为截图 GUI、100 步/题、200 题、所有必需检查通过才算成功。EXT 是 2026-10 扩展评估，不是 2026-09 论文主结果。逐行数据取自[官方结果页](https://cad-world.github.io/#results)加载的 [JS 数据](https://cad-world.github.io/assets/js/main.js?v=10)（Ubuntu 匿名 GET，数组 `models`，取 `scores[0]`）；论文设置见[附录 D/E](https://arxiv.org/html/2609.16251v2)。表中 UNKNOWN 意为未取得足以确认的精确 Harness/版本、effort、逐 run 链接或不可变任务版本；不把本轮 CADWorld 源码 SHA 倒填成历史运行 SHA。通过题数为依据公布比例和 200 题换算，不是独立审计的逐题数据。

| benchmark | task_version | model | harness | harness_version | effort | reported_score | metric | task_count | date_or_snapshot | official_run_url | source_url | notes |
|---|---|---|---|---|---|---|---|---:|---|---|---|---|
| CADWorld | 200题公开设置；SHA UNKNOWN | Opus 5.5 | UNKNOWN | UNKNOWN | UNKNOWN | 41.5% | strict pass rate | 200 | 2026-10 EXT | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | EXT；83/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | Sonnet 5.5 | UNKNOWN | UNKNOWN | UNKNOWN | 33.5% | strict pass rate | 200 | 2026-10 EXT | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | EXT；67/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | GPT-6-Astra | UNKNOWN | UNKNOWN | UNKNOWN | 33.0% | strict pass rate | 200 | 2026-10 EXT | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | EXT；66/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | GPT5.4 | 官方 API runner / OpenAI 原生 computer tool | UNKNOWN | UNKNOWN | 17.5% | strict pass rate | 200 | 2026-09 论文 | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | 论文；35/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | Opus4.8 | 官方 API runner / Anthropic 原生 computer tool | UNKNOWN | UNKNOWN | 16.0% | strict pass rate | 200 | 2026-09 论文 | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | 论文；32/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | GLM-5.3-Flash | UNKNOWN | UNKNOWN | UNKNOWN | 12.5% | strict pass rate | 200 | 2026-10 EXT | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | EXT；25/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | DeepSeek-V4.1-Flash | UNKNOWN | UNKNOWN | UNKNOWN | 7.5% | strict pass rate | 200 | 2026-10 EXT | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | EXT；15/200；GUI-only 主设置；扩展运行由 Yuanmu.ai 赞助 |
| CADWorld | 200题公开设置；SHA UNKNOWN | Kimi K2.6 | UNKNOWN | UNKNOWN | UNKNOWN | 7.5% | strict pass rate | 200 | 2026-09 论文 | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | 论文；15/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | Qwen3.8-27B | UNKNOWN | UNKNOWN | UNKNOWN | 1.5% | strict pass rate | 200 | 2026-10 EXT | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | EXT；3/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | OpenCUA | UNKNOWN | UNKNOWN | UNKNOWN | 1.5% | strict pass rate | 200 | 2026-09 论文 | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | 论文；3/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | Holo 3.1 | UNKNOWN | UNKNOWN | UNKNOWN | 0.5% | strict pass rate | 200 | 2026-09 论文 | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | 论文；1/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | Qwen3.6 | UNKNOWN | UNKNOWN | UNKNOWN | 0.0% | strict pass rate | 200 | 2026-09 论文 | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | 论文；0/200；GUI-only 主设置 |
| CADWorld | 200题公开设置；SHA UNKNOWN | MiniMax M3 | UNKNOWN | UNKNOWN | UNKNOWN | 0.0% | strict pass rate | 200 | 2026-09 论文 | UNKNOWN | [官方结果](https://cad-world.github.io/#results) | 论文；0/200；GUI-only 主设置 |

结论：`NO_MATCHING_PUBLISHED_RUN`。没有找到 DSH + 候选模型 + 对应 benchmark 的明确公开组合；CADWorld 的 Flash EXT 不是已验证的 DSH 成绩。CAD Bench 优先引用榜单前三；CADWorld 优先引用 Opus 5.5、GPT-6-Astra、DeepSeek-V4.1-Flash EXT。不同版本、模型、Harness、effort 和输出协议不能合并排名。
