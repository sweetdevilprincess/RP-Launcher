@echo off
REM Start both Bridge and TUI together (default)

echo ========================================
echo RP Client Launcher
echo ========================================
echo.

python launch.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Launcher exited with error code %ERRORLEVEL%
    pause
)
