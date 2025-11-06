#!/usr/bin/env bash
# Comprehensive check script for RP Launcher Refactored
# Runs linting, formatting check, type checking, and tests
# Usage: ./scripts/check-all.sh

set -e  # Exit on first error

echo "========================================"
echo "RP Launcher - Running All Checks"
echo "========================================"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

FAILED=0

# 1. Linting with ruff
echo "[1/4] Running ruff linting..."
if python -m ruff check src tests; then
    echo "[PASS] Ruff linting passed"
else
    echo "[FAIL] Ruff linting found issues"
    FAILED=1
fi
echo ""

# 2. Formatting check with black
echo "[2/4] Checking code formatting with black..."
if python -m black --check src tests; then
    echo "[PASS] Code formatting is correct"
else
    echo "[FAIL] Code needs formatting (run ./scripts/format.sh to fix)"
    FAILED=1
fi
echo ""

# 3. Type checking with mypy
echo "[3/4] Running type checking with mypy..."
if python -m mypy; then
    echo "[PASS] Type checking passed"
else
    echo "[FAIL] Type checking found issues"
    FAILED=1
fi
echo ""

# 4. Tests with pytest and coverage
echo "[4/4] Running tests with coverage..."
if python -m pytest tests --cov=src --cov-report=term-missing --cov-report=html; then
    echo "[PASS] All tests passed"
else
    echo "[FAIL] Tests failed"
    FAILED=1
fi
echo ""

echo "========================================"
if [ $FAILED -eq 0 ]; then
    echo "ALL CHECKS PASSED!"
    echo "========================================"
    exit 0
else
    echo "SOME CHECKS FAILED - See above for details"
    echo "========================================"
    exit 1
fi
