@echo off
REM Comprehensive check script for RP Launcher Refactored
REM Runs linting, formatting check, type checking, and tests
REM Usage: scripts\check-all.bat

echo ========================================
echo RP Launcher - Running All Checks
echo ========================================
echo.

REM Change to project root
cd /d "%~dp0\.."

set FAILED=0

REM 1. Linting with ruff
echo [1/4] Running ruff linting...
python -m ruff check src tests
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Ruff linting found issues
    set FAILED=1
) else (
    echo [PASS] Ruff linting passed
)
echo.

REM 2. Formatting check with black
echo [2/4] Checking code formatting with black...
python -m black --check src tests
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Code needs formatting (run scripts\format.bat to fix)
    set FAILED=1
) else (
    echo [PASS] Code formatting is correct
)
echo.

REM 3. Type checking with mypy
echo [3/4] Running type checking with mypy...
python -m mypy
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Type checking found issues
    set FAILED=1
) else (
    echo [PASS] Type checking passed
)
echo.

REM 4. Tests with pytest and coverage
echo [4/4] Running tests with coverage...
python -m pytest tests --cov=src --cov-report=term-missing --cov-report=html
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Tests failed
    set FAILED=1
) else (
    echo [PASS] All tests passed
)
echo.

echo ========================================
if %FAILED% EQU 0 (
    echo ALL CHECKS PASSED!
    echo ========================================
    exit /b 0
) else (
    echo SOME CHECKS FAILED - See above for details
    echo ========================================
    exit /b 1
)
