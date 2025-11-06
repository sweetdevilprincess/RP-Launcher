@echo off
REM Start TUI only (Bridge must be running separately)

echo ========================================
echo RP Client - TUI Only
echo ========================================
echo.
echo WARNING: Make sure Bridge is running!
echo.

python launch.py --tui-only %*
