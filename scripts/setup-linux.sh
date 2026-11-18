#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { echo 'Install uv in WSL first.' >&2; exit 2; }
uv venv --allow-existing --python 3.12
uv pip sync --require-hashes requirements.lock
uv pip install --no-deps -e .
