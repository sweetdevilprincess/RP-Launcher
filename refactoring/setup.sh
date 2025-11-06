#!/bin/bash
# RP Claude Code Setup Script (Linux/Mac)
# This script installs all Python and Node.js dependencies

set -e  # Exit on error

echo "==========================================="
echo "    RP Claude Code - Setup"
echo "==========================================="
echo ""

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.10 or higher from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Check Node.js
echo "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Found Node.js $NODE_VERSION"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

# Install Node.js dependencies for SDK
echo "Installing Node.js SDK dependencies..."
cd src/infrastructure/llm
npm install
cd ../../..
echo "✓ Node.js SDK dependencies installed"
echo ""

echo "==========================================="
echo "✅ Setup complete!"
echo "==========================================="
echo ""
echo "To launch RP Claude Code:"
echo "  python3 launch.py"
echo ""
echo "For help:"
echo "  python3 launch.py --help"
echo ""
