@echo off
REM Start Bridge only (for testing or when running TUI separately)

echo ========================================
echo RP Client - Bridge Only
echo ========================================
echo.

python launch.py --bridge-only %*
