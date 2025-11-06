@echo off
REM RP Claude Code Setup Script (Windows)
REM This script installs all Python and Node.js dependencies

setlocal

echo ===========================================
echo     RP Claude Code - Setup
echo ===========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%
echo.

REM Check Node.js
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo Found Node.js %NODE_VERSION%
echo.

REM Install Python dependencies
echo Installing Python dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)
echo Python dependencies installed
echo.

REM Install Node.js dependencies for SDK
echo Installing Node.js SDK dependencies...
cd src\infrastructure\llm
call npm install
if errorlevel 1 (
    cd ..\..\..
    echo Error: Failed to install Node.js dependencies
    pause
    exit /b 1
)
cd ..\..\..
echo Node.js SDK dependencies installed
echo.

echo ===========================================
echo Setup complete!
echo ===========================================
echo.
echo To launch RP Claude Code:
echo   python launch.py
echo.
echo For help:
echo   python launch.py --help
echo.
pause
