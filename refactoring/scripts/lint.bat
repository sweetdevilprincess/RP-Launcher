@echo off
REM Run ruff linting on the codebase
REM Usage: scripts\lint.bat [--fix]

cd /d "%~dp0\.."

if "%1"=="--fix" (
    echo Running ruff with auto-fix...
    python -m ruff check src tests --fix
) else (
    echo Running ruff linting...
    python -m ruff check src tests
)

exit /b %ERRORLEVEL%
