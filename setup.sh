#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
[ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] || { echo 'Requires Apple Silicon macOS.' >&2; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install 'mlx-lm[train]'
.venv/bin/python -m pip freeze > installed-versions.txt
echo 'Installed versions recorded in installed-versions.txt. Inspect before running training.'
