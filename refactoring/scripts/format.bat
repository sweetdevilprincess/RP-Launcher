@echo off
REM Run black code formatting
REM Usage: scripts\format.bat [--check]

cd /d "%~dp0\.."

if "%1"=="--check" (
    echo Checking code formatting (no changes)...
    python -m black --check src tests
) else (
    echo Formatting code with black...
    python -m black src tests
)

exit /b %ERRORLEVEL%
