#!/usr/bin/env bash
# Bootstrap Poetry environment (POSIX shell)

set -euo pipefail

runtime_only=0
if [[ "${1:-}" == "--runtime-only" ]]; then
    runtime_only=1
fi

if ! command -v poetry >/dev/null 2>&1; then
    echo "Poetry is not installed or not on PATH. Install from https://python-poetry.org/docs/#installation" >&2
    exit 1
fi

# Keep the virtualenv inside the project folder for simplicity.
export POETRY_VIRTUALENVS_IN_PROJECT="${POETRY_VIRTUALENVS_IN_PROJECT:-1}"

install_args=(install --no-interaction --sync)
if [[ $runtime_only -eq 0 ]]; then
    install_args+=(--with dev)
fi

echo "Installing dependencies via Poetry..."
poetry "${install_args[@]}"

echo "Checking PySide6 WebEngine availability..."
poetry run python - <<'PY'
from PySide6.QtWebEngineQuick import QtWebEngineQuick
QtWebEngineQuick.initialize()
print("Qt WebEngine ready")
PY

echo
echo "Environment is ready."
echo "Run GUI: poetry run python -m fire_uav.main"
