#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src:$PWD"
exec .venv/bin/python -m uvicorn studio.backend.app:app --host 127.0.0.1 --port 8765
