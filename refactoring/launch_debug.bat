@echo off
cd /d "%~dp0"
echo Running launcher with error capture...
echo.
python launch.py "test_rp" --tui-only 2> error_log.txt
echo.
echo Exit code: %ERRORLEVEL%
echo.
if %ERRORLEVEL% NEQ 0 (
    echo ERROR DETECTED! Check error_log.txt for details
    type error_log.txt
) else (
    echo No errors detected
)
echo.
pause
