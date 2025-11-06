#!/usr/bin/env bash
# Run mypy type checking
# Usage: ./scripts/typecheck.sh [module_path]

cd "$(dirname "$0")/.."

if [ -z "$1" ]; then
    echo "Running mypy type checking on configured modules..."
    python -m mypy
else
    echo "Running mypy on $1..."
    python -m mypy "$1"
fi

exit $?
