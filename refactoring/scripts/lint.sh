#!/usr/bin/env bash
# Run ruff linting on the codebase
# Usage: ./scripts/lint.sh [--fix]

cd "$(dirname "$0")/.."

if [ "$1" == "--fix" ]; then
    echo "Running ruff with auto-fix..."
    python -m ruff check src tests --fix
else
    echo "Running ruff linting..."
    python -m ruff check src tests
fi

exit $?
