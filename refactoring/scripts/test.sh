#!/usr/bin/env bash
# Run pytest with coverage
# Usage: ./scripts/test.sh [test_path] [extra_args...]

cd "$(dirname "$0")/.."

if [ -z "$1" ]; then
    echo "Running all tests with coverage..."
    python -m pytest tests --cov=src --cov-report=term-missing --cov-report=html -v
else
    echo "Running tests: $@"
    python -m pytest "$@"
fi

exit $?
