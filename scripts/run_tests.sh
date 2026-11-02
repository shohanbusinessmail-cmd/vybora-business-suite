#!/usr/bin/env bash
# Run the full test suite. On the Linux sandbox, offscreen Qt needs the dev-only
# stub libs in .sandbox-libs (never shipped). On Windows/CI these are unnecessary.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname)" == "Linux" && -d ".sandbox-libs" ]]; then
  export LD_LIBRARY_PATH="$PWD/.sandbox-libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  export QT_QPA_PLATFORM=offscreen
fi
PY=".venv/bin/python"; [[ -x "$PY" ]] || PY="python"
exec "$PY" -m pytest "$@"
