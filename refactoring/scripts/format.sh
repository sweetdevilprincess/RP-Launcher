#!/usr/bin/env bash
# Run black code formatting
# Usage: ./scripts/format.sh [--check]

cd "$(dirname "$0")/.."

if [ "$1" == "--check" ]; then
    echo "Checking code formatting (no changes)..."
    python -m black --check src tests
else
    echo "Formatting code with black..."
    python -m black src tests
fi

exit $?
