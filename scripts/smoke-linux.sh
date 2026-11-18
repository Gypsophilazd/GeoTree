#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/smoke-python.sh
image=${GEOTREE_SMOKE_IMAGE:-geotree-smoke:freecad-1.1}
docker image inspect "$image" >/dev/null || { echo 'Build docker/smoke.Dockerfile or set GEOTREE_SMOKE_IMAGE to an existing compatible image.' >&2; exit 2; }
docker run --rm --pull never --network none --cpus 2 --memory 4g --user 65534:65534 \
  --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m,mode=1777 \
  --mount "type=bind,source=$PWD,target=/repo,readonly" -e HOME=/tmp -e PYTHONPATH=/repo/src \
  -e PYTHONDONTWRITEBYTECODE=1 -e OPENBLAS_NUM_THREADS=1 -e OMP_NUM_THREADS=1 \
  --entrypoint /opt/conda/bin/python "$image" /repo/examples/smoke_freecad.py
