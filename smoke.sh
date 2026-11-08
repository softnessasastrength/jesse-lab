#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
[ "$(uname -s)" = Darwin ] || { echo 'Apple Silicon macOS required.' >&2; exit 1; }
[ "$(uname -m)" = arm64 ] || { echo 'Apple Silicon required.' >&2; exit 1; }
: "${MODEL:?Set MODEL to a compatible MLX checkpoint path or Hugging Face identifier}"
[ -x .venv/bin/python ] || { echo 'Run ./setup.sh first.' >&2; exit 1; }
mkdir -p runs
run="runs/smoke-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 "$run"
.venv/bin/python prepare.py data/synthetic.jsonl "$run/data"
.venv/bin/python -m pip freeze > "$run/versions.txt"
uname -a > "$run/system.txt"
echo "Running one-step experiment; output: $run"
set +e
.venv/bin/python -m mlx_lm lora --model "$MODEL" --train --data "$run/data" --iters 1 --batch-size 1 --max-seq-length 256 --adapter-path "$run/adapter" 2>&1 | tee "$run/train.log"
status=${PIPESTATUS[0]}
set -e
echo "$status" > "$run/exit-status.txt"
[ "$status" -eq 0 ] || { echo 'Smoke test failed; inspect train.log.' >&2; exit "$status"; }
echo 'Command completed. Inspect log and adapter before claiming training success.'
