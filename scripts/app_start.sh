#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Error: Python 3 is required to run scripts/check_docker.py." >&2
  exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/check_docker.py"