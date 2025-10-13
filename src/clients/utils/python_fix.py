"""Python path fix utility - detects and fixes wrong conda Python paths.

This module handles the case where Windows file associations point to the
conda package cache Python instead of the environment Python, which causes
import errors for installed packages.

Also detects if running from a PyInstaller bundle (.exe) and skips the fix.
"""

import sys
import subprocess
from pathlib import Path


def fix_python_path() -> None:
    """Check if we're using the wrong Python and relaunch with correct one.

    This function:
    1. Checks if running from PyInstaller bundle - if yes, skip (no fix needed)
    2. Checks if using conda pkgs cache Python (wrong one)
    3. Finds the correct environment Python
    4. Relaunches the script with correct Python
    5. Exits current process

    Called at the top of launcher scripts before any imports that might fail.
    """
    # Skip if running from PyInstaller bundle (.exe)
    if getattr(sys, 'frozen', False):
        return  # Running from .exe, Python is bundled correctly

    current_python = Path(sys.executable)

    # Check if we're using the pkgs cache Python (wrong)
    if "\\pkgs\\" not in str(current_python) and "/pkgs/" not in str(current_python):
        return  # Using correct Python, no fix needed

    # Find the correct Python in the conda environment
    # Go up from pkgs/python-X.Y.Z-.../python.exe to miniconda3/python.exe
    conda_root = None
    for parent in current_python.parents:
        if parent.name in ["miniconda3", "anaconda3", "miniforge3"]:
            conda_root = parent
            break

    if not conda_root:
        return  # Can't find conda root, continue anyway

    correct_python = conda_root / "python.exe"
    if not correct_python.exists():
        return  # Correct Python not found, continue anyway

    # Relaunch with correct Python silently
    result = subprocess.run(
        [str(correct_python), sys.argv[0]] + sys.argv[1:],
        cwd=str(Path.cwd())
    )
    sys.exit(result.returncode)
