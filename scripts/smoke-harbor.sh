#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export LITELLM_LOCAL_MODEL_COST_MAP=True
py=${GEOTREE_PYTHON:-.venv/bin/python}
image=${GEOTREE_HARBOR_SMOKE_IMAGE:-geotree-smoke:freecad-1.1}
docker image inspect "$image" >/dev/null
"$py" tests/test_harbor_agent_abi.py
export GEOTREE_RUN_ROOT
GEOTREE_RUN_ROOT=$(mktemp -d)
id=l-$("$py" -c 'import secrets; print(secrets.token_hex(8))')-l1
d="$GEOTREE_RUN_ROOT/l/$id"
task="$GEOTREE_RUN_ROOT/harbor-smoke"
mkdir -p "$d" "$task"
cp -r examples/harbor-smoke/. "$task/"
export GEOTREE_L_TRIAL=$id GEOTREE_L_DEADLINE=$(($(date +%s)+100))
export GEOTREE_PUBLIC_INSTRUCTION="$task/instruction.md"
sha=$(sha256sum "$GEOTREE_PUBLIC_INSTRUCTION")
export GEOTREE_INSTRUCTION_SHA256=${sha%% *}
"$py" - "$task/task.toml" "$image" <<'PY'
from pathlib import Path
import re,sys
if not re.fullmatch(r"[a-z0-9][a-zA-Z0-9_./:@-]+", sys.argv[2]):
    raise SystemExit("Invalid local image name")
Path(sys.argv[1]).write_text(f"""version = "1.0"
[agent]
timeout_sec = 90
[environment]
docker_image = "{sys.argv[2]}"
cpus = 2
memory_mb = 4096
gpus = 0
""")
PY
printf 'Local no-model Harbor smoke evidence: %s\n' "$d"
timeout --signal=INT --kill-after=3s 100s "$(dirname "$py")/harbor" run -p "$task" \
  -a geotree.enhanced_agent_l:EnhancedAgent -e docker --disable-verification \
  --n-concurrent 1 --n-attempts 1 --max-retries 0 --jobs-dir "$d/jobs" --job-name "$id" \
  >"$d/harbor.stdout" 2>"$d/harbor.stderr" & runner=$!
relay_rc=0
"$py" examples/mock_mailbox.py "$d/mailbox" || relay_rc=$?
rc=0; wait "$runner" || rc=$?
printf '%s\n' "$rc" > "$d/exit"
((relay_rc == 0 && rc == 0)) || { cat "$d/harbor.stderr"; exit 1; }
"$py" scripts/result_gate.py "$d"
