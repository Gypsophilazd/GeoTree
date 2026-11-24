# GeoTree repository guide

- src/geotree/: Harbor agents, decision validation, OCC evidence and repair contracts.
- studio/backend/ and studio/frontend/: loopback Studio, FreeCAD, API smoke and synthetic demo.
- bridge/windows/: host-only Codex CLI and process supervisor.
- examples/demo/: synthetic repair source and public dimensional contract.
- tests/, scripts/, docker/: setup, no-model regressions and FreeCAD image recipe.
- docs/presentation/: historical development summaries and vetted presentation assets.

Run bash scripts/setup-linux.sh, bash scripts/smoke-python.sh and bash scripts/studio-smoke.sh. Do not interpret Mock PASS as competition results. Do not run a real provider or Benchmark without authorization, copy credentials, read hidden scoring data, or tune against hidden rewards. Keep missing scores null. Fix and retest ordinary engineering faults before delivering.

Local state belongs under .geotree/ or an explicitly configured runtime path. Keep trials, event ledgers, caches, datasets and credentials out of Git.
