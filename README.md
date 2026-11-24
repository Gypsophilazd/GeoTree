# GeoTree Studio · E06

GeoTree turns text into a parametric FreeCAD design and exposes its script, real feature meshes, and geometry checks. It combines a loopback Studio with a research harness for task-grounded verification and bounded repair.

## Quick start — Ubuntu or Windows with WSL2 Ubuntu

Requirements: Python 3.12, uv, Docker Linux containers (Docker Desktop WSL integration if using Windows). From the clone in Ubuntu:

```bash
bash scripts/setup-linux.sh
docker build -f docker/smoke.Dockerfile -t geotree/freecad:1.1.0 .
bash scripts/studio-smoke.sh
bash scripts/studio-start.sh
```

Open <http://127.0.0.1:8765/>. For remote Linux, forward a loopback port: `ssh -N -L 127.0.0.1:18765:127.0.0.1:8765 YOUR_SSH_HOST`. Keep Studio private; it is not a multi-user service. To reuse a compatible local FreeCAD 1.1 image set `GEOTREE_FREECAD_IMAGE` to its local ID or tag. See [Windows setup](docs/windows-setup.md).

Mock tests transport and persistence, not CAD. For genuine model-free CAD use **检查合成件右三角** and **运行 E05 限定修复**; the bundled source is built, measured, edited in isolation and independently replayed. Preview before/after. No historical CAD files are required.

## Providers and replay

- **Codex:** verify your own Windows ChatGPT CLI login with `codex login status`. Set `GEOTREE_STUDIO_URL` to the Studio loopback URL (the relay default is port 18765), then run `py -3.13 bridge/windows/studio_bridge.py`. The tested model is GPT-6.2 Sol/high; entitlement and CLI options depend on your install. Credentials stay on the host.
- **DeepSeek:** configure the backend with your own `DEEPSEEK_API_KEY` and set `GEOTREE_DEEPSEEK_APPROVED=1` only when authorized. The adapter uses Responses SSE and `deepseek-flash`; otherwise it reports NOT_CONFIGURED.
- **LIVE** records actual model and FreeCAD events. **REPLAY** uses a saved local artifact without a model request. “Feature reconstruction” exports actual intermediate FreeCAD features after building; it is not a live modeling feed. Fresh installations have no historical sessions.

## Architecture

FastAPI and WebGL Studio live in studio/. Agent execution, OCC queries, evidence gates, budgets and Harbor adapters are under src/geotree/. The bounded repair edits one allowed numeric AST slot, checks the constraint and geometry outside the intended area, then independently replays. It is not general automatic CAD repair. See [architecture](docs/presentation/architecture.svg) and the [editable deck](docs/presentation/GeoTree_Contest_Draft.pptx).

## Historical E06 development scores

| Task | B0 native Codex | B1 raw | B2 passive evidence-gated |
|---|---|---:|---:|
| Hinge leaf | NOT_RUN | 0.000000 | FAILED / reward=null |
| Power-strip housing | NOT_RUN | 0.000000 (same-artifact regrade) | 0.814775 |

[CSV](docs/presentation/benchmark_results.csv) and [acceptance](docs/E06_release_acceptance.md). Both power-strip artifacts replayed. B2 passed two basic checks, with no feedback-driven repair. This is not a causal comparison or a leaderboard result. B0 was not run because native subscription credential isolation was not verified.

References: [CAD-Assistant, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Mallis_CAD-Assistant_Tool-Augmented_VLLMs_as_Generic_CAD_Task_Solvers_ICCV_2025_paper.html), [SPADA, ICML 2026](https://proceedings.mlr.press/v306/zheng26q.html), [DeciCAD, arXiv preprint](https://arxiv.org/abs/2610.21755), [CAD Bench V3](https://cadbench.ai/benchmark).
