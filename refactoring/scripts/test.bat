@echo off
REM Run pytest with coverage
REM Usage: scripts\test.bat [test_path] [extra_args...]

cd /d "%~dp0\.."

if "%1"=="" (
    echo Running all tests with coverage...
    python -m pytest tests --cov=src --cov-report=term-missing --cov-report=html -v
) else (
    echo Running tests: %*
    python -m pytest %*
)

exit /b %ERRORLEVEL%
