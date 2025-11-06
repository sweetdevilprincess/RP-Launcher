@echo off
REM Run mypy type checking
REM Usage: scripts\typecheck.bat [module_path]

cd /d "%~dp0\.."

if "%1"=="" (
    echo Running mypy type checking on configured modules...
    python -m mypy
) else (
    echo Running mypy on %1...
    python -m mypy %1
)

exit /b %ERRORLEVEL%
