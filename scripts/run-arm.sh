#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
check=0
if [[ ${1:-} == --check-only ]]; then check=1; shift; fi
[[ $# == 3 ]] || { echo 'Expected: [--check-only] TRIAL_ID UNIX_DEADLINE authorized-task-directory' >&2; exit 65; }
id=$1; deadline=$2; task=$(realpath -e "$3")
[[ $id =~ ^l-[0-9a-f]{16}-l[01]$ ]] || { echo 'Invalid L trial ID' >&2; exit 65; }
[[ $deadline =~ ^[1-9][0-9]{0,9}$ ]] || { echo 'Invalid deadline' >&2; exit 66; }
export LITELLM_LOCAL_MODEL_COST_MAP=True
left=$((deadline-$(date +%s)))
((left > 0 && left <= 1200)) || { echo 'Deadline outside budget' >&2; exit 66; }
py=${GEOTREE_PYTHON:-.venv/bin/python}
public="$task/instruction.md"
sha=$(sha256sum "$public"); sha=${sha%% *}
[[ $sha == "${GEOTREE_INSTRUCTION_SHA256:?Set expected public instruction SHA256}" ]] || { echo 'Public instruction hash mismatch' >&2; exit 66; }
# Read only orchestration metadata; never inspect verifier code or artifacts.
"$py" - "$task/task.toml" <<'PY'
import sys, tomllib
with open(sys.argv[1], "rb") as stream:
    env = tomllib.load(stream)["environment"]
if (env.get("cpus"), env.get("memory_mb"), env.get("gpus", 0)) != (2, 4096, 0):
    raise SystemExit("Require task limits CPU 2 / RAM 4096 MiB / GPU 0")
PY
"$py" tests/test_harbor_agent_abi.py
if ((check)); then echo 'CHECK_PASS (ABI and public inputs; no trial)'; exit 0; fi
[[ ${GEOTREE_L_RUN_APPROVED:-} == EXPLICIT_PAIR_APPROVAL ]] || { echo 'NOT_RUN: awaiting explicit approval of the live pair' >&2; exit 64; }
[[ ${GEOTREE_SEPARATE_VERIFIER_CONFIRMED:-} == YES ]] || { echo 'Require separate verifier and network/mount preflight' >&2; exit 64; }
export GEOTREE_RUN_ROOT="$(realpath -m "${GEOTREE_RUN_ROOT:-$PWD/.geotree}")"
export GEOTREE_L_TRIAL=$id GEOTREE_L_DEADLINE=$deadline GEOTREE_PUBLIC_INSTRUCTION=$public
base="$GEOTREE_RUN_ROOT/l"
mkdir -p "$base"
exec 8>"$base/real.lock"; flock -n 8
arm=${id##*-}
[[ ! -e "$base/live-$arm.id" ]] || { echo 'Attempt already reserved; no retry' >&2; exit 65; }
if [[ $arm == l1 ]]; then
  prior=$(cat "$base/live-l0.id")
  [[ $prior == "${id%1}0" ]]
  "$py" scripts/result_gate.py "$base/$prior" --live
  [[ $(cat "$base/$prior/public.sha256") == "$sha" ]]
fi
d="$base/$id"; mkdir "$d"
printf '%s\n' "$sha" > "$d/public.sha256"
printf '%s\n' "$deadline" > "$d/deadline"
left=$((deadline-$(date +%s))); ((left > 0 && left <= 1200))
printf '%s\n' "$id" > "$base/live-$arm.id"
rc=0
timeout --signal=INT --kill-after=3s "${left}s" "$(dirname "$py")/harbor" run -p "$task" -e docker \
  -a geotree.enhanced_agent_l:EnhancedAgent --n-concurrent 1 --n-attempts 1 --max-retries 0 \
  --jobs-dir "$d/jobs" --job-name "$id" >"$d/harbor.stdout" 2>"$d/harbor.stderr" || rc=$?
printf '%s\n' "$rc" > "$d/exit"
((rc == 0)) || exit "$rc"
"$py" scripts/result_gate.py "$d" --live
