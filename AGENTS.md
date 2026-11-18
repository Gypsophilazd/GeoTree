# Project Overview

GeoTree validates bounded actions proposed by CAD agents and checks public task constraints against FreeCAD artifacts. It supports k=1, conservative evidence verification and a small set of offline copy-only repair operations, not general drawing interpretation or validated tree search.

# Repository Map

- `src/geotree/nosearch.py`, `paired_agent.py`: ModelProvider, runtime, executor, action validator, budget and ATIF.
- `src/geotree/harbor_agent.py:GeoTreeNoModelAgent`, `nosearch_agent.py:GeoTreeNoSearchAgent`, `paired_agent.py:PairedAgent`, `enhanced_agent_l.py:EnhancedAgent`: Harbor entry points; all concrete entries are enumerated in the ABI test.
- `enhanced_agent_l.py` selects raw/evidence by L trial ID. The fixed container worker is `src/geotree/k_worker.py`. Preserve `environment=` on both async BaseAgent methods.
- Geometry: `geometry_reader.py`, `geometry_observer.py`, `task_geometry.py`; evidence: `constraint_candidates.py`, `evidence_gate.py`, `verification_harness.py`; repair: `safe_repair.py`, `experiments/methods/`.
- `bridge/windows/relay.py` and `action-schema.json`; `configs/`, `experiments/manifests/`, `tests/`, `examples/`, `docs/`.

# Development Commands

- WSL/Linux install: `bash scripts/setup-linux.sh`; unit and MockProvider: `bash scripts/smoke-python.sh`.
- ABI only: `.venv/bin/python tests/test_harbor_agent_abi.py`.
- Build local smoke image: `docker build -f docker/smoke.Dockerfile -t geotree-smoke:freecad-1.1 .`; execute `bash scripts/smoke-linux.sh` and optionally `bash scripts/smoke-harbor.sh`.
- On Windows, follow `docs/windows-setup.md`. Relay supervisor regression: `py -3.13 bridge/windows/test_relay.py`.

# Autonomous Execution

For an explicitly authorized work order, diagnose ordinary failures, apply a minimal fix, verify and continue to the real deliverable. Preserve original files and negative evidence. For experimental changes, freeze conditions and use the same infrastructure in both arms.

# Research Integrity

PASS means the named operation was actually verified; PARTIAL means incomplete evidence; BLOCKED means a prerequisite failed; NOT_RUN means it was not executed. Mock runs are not benchmark results. Never read hidden references/verifier internals, feed reward to the model, fabricate observations, retry for a better score or alter research conditions without authorization. UNKNOWN must remain unknown.

# Safety & Resource Boundaries

Default to no model requests, no paid/subscription calls and no Benchmark. Use authorized isolated containers only; do not copy credentials, use GPUs or modify other projects, training or Docker settings. Keep raw evidence under ignored run roots, and do not commit datasets and caches.

# Definition of Done

Deliver the requested artifacts and run the relevant gates from the delivered version. Preserve failures and report exact blockers or scope if a local check did not run. Passing only Mock does not mean a real trial completed.
