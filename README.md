# GeoTree

A task-grounded verification and safe-repair harness for autonomous parametric CAD agents, built with FreeCAD and Harbor.

[简体中文](README.zh-CN.md) · [Windows / WSL2 setup](docs/windows-setup.md) · [Architecture](docs/GeoTree_Architecture_v0.1.md) · [Research status](experiments/summaries/research-status.md)

A model proposes a bounded action. GeoTree validates it and Harbor runs the permitted CAD action in a task container using FreeCAD/OCC. The next observation receives execution feedback and, in enhanced mode, eligible public-evidence geometry checks. ATIF and raw events preserve the decision trail. Independent scoring is terminal-only and never used as model feedback.

## What works and what does not

- NoSearch (one proposal per turn), validated actions, shared step/deadline/CAD budgets, MockProvider, ATIF and traces.
- Legacy Harbor entries, paired raw/geometry entry, and paired text entry with evidence-gated deterministic checks. Missing or ambiguous mapping is UNKNOWN, not FAIL.
- Host-side Windows Codex relay with schema, mailbox IDs, deadlines and supervised processes. The default smoke path uses no account and never launches Codex.
- Experimental FreeCAD copy-only planar-pocket repair contract and restricted isolated pad length repair with reopen, regression and BRep checks. The latter is driven by the offline API; the live L comparison reports existing verification, not an automatic repair success. An FCStd edit is not an answer.py replay.
- No MCTS, no general drawing interpretation, no claimed cross-task performance lift, no official leaderboard results. Development rewards are not causal evidence. Latest E02-L3 had an infrastructure failure: zero model requests, reward null, not zero.

## Quick start in Ubuntu / WSL2

Install uv and enable a Linux Docker daemon first. From the repository root:

```bash
bash scripts/setup-linux.sh
bash scripts/smoke-python.sh
docker build -f docker/smoke.Dockerfile -t geotree-smoke:freecad-1.1 .
bash scripts/smoke-linux.sh
bash scripts/smoke-harbor.sh
```

The first smoke is Python and MockProvider only. The second adds a synthetic FreeCAD observation and copy-only repair. The third runs the real Harbor EnhancedAgent against a synthetic task, with verification disabled and a local mock relay. No dataset, model or score is needed. An existing compatible conda/FreeCAD image can be used instead of building; see the setup guide.

## Agent and research map

- `src/geotree/nosearch.py`, `paired_agent.py`: ModelProvider, validator, executor, runtime, recorder, budgets.
- `src/geotree/enhanced_agent_l.py`: Harbor L entry for both raw and enhanced text modes; `harbor_agent.py`: no-model legacy entry.
- `geometry_reader.py`, `geometry_observer.py`, `geometry_feedback.py`, `task_geometry.py`: artifact inspection, binding and deterministic queries.
- `constraint_candidates.py`, `evidence_gate.py`, `verification_harness.py`, `k_worker.py`: public-constraint discovery, conservative verification and fixed worker.
- `safe_repair.py`, `experiments/methods/`: isolated pad repair and historical multi-view/pocket research code. Historical scripts require their original public inputs/snapshots to reproduce study-specific cases.
- `bridge/windows/`, `scripts/`, `tests/`, `examples/`: relay, entry points, regression tests and synthetic examples.
- `configs/`, `experiments/manifests/`, `docs/`: methods, freezes and reports. Historic paths there identify evidence on the source host, not setup dependencies.

For your own account and a complete authorized Harbor trial, use the [explicit opt-in workflow](docs/windows-setup.md#optional-authorized-harbor-task). A different provider can implement the ModelProvider/JSON transport contract; do not send account files into the container. Benchmark tasks, verifier payloads, model credentials, Docker layers and raw historical job directories are not part of this repository. No redistribution license is asserted.
