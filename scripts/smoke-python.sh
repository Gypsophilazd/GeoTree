#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
export LITELLM_LOCAL_MODEL_COST_MAP=True
py=${GEOTREE_PYTHON:-.venv/bin/python}
"$py" -m unittest discover -s tests -v
"$py" tests/nosearch_regression.py
"$py" tests/budget_regression.py
"$py" tests/candidate_regression.py
