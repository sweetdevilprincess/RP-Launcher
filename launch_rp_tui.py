#!/usr/bin/env python3
"""Launcher for the RP Client TUI with folder selection and bridge."""

# ============================================================================
# ⚠️  CRITICAL: DO NOT MOVE THIS CODE BELOW - MUST BE FIRST! ⚠️
# ============================================================================
# This Python path fix MUST be the very first code that runs, before ANY
# other imports. If you move this down or import anything before it, you'll
# get Unicode encoding errors (emojis failing) which indicates the wrong
# Python (conda pkgs cache) is being used.
#
# This code detects if we're using the wrong Python and relaunches with the
# correct one BEFORE any imports that would fail.
# ============================================================================

import sys
from pathlib import Path

# Check if we're using the wrong Python (pkgs cache) and relaunch if needed
current_python = Path(sys.executable)
if "\\pkgs\\" in str(current_python) or "/pkgs/" in str(current_python):
    # We're using pkgs cache Python - find the correct one
    import subprocess
    conda_root = None
    for parent in current_python.parents:
        if parent.name in ["miniconda3", "anaconda3", "miniforge3"]:
            conda_root = parent
            break

    if conda_root:
        correct_python = conda_root / "python.exe"
        if correct_python.exists():
            # Relaunch with correct Python
            result = subprocess.run(
                [str(correct_python), sys.argv[0]] + sys.argv[1:],
                cwd=str(Path.cwd())
            )
            sys.exit(result.returncode)

# Now add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now safe to import everything else
import os
import subprocess
import time
import atexit

# Force console window if launched with pythonw.exe on Windows
if sys.platform == 'win32' and not sys.stdout:
    # Relaunch with python.exe to get a console window
    python_exe = sys.executable.replace('pythonw.exe', 'python.exe')
    subprocess.Popen([python_exe] + sys.argv)
    sys.exit()

from src.rp_client_tui import RPClientApp


# Global bridge process tracker
_bridge_process = None


def start_bridge(rp_dir: Path, background: bool = False) -> subprocess.Popen:
    """Start the bridge in a separate process.

    Args:
        rp_dir: RP directory to monitor
        background: If True, run hidden. If False, show terminal window (for debugging)

    Returns:
        Bridge process handle
    """
    base_dir = Path(__file__).parent
    bridge_script = base_dir / "src" / "tui_bridge.py"
    python_exe = sys.executable

    print(f"Starting bridge for: {rp_dir.name}")

    if background:
        # Background mode - no window (for future use)
        if sys.platform == 'win32':
            # On Windows, use DETACHED_PROCESS to run without window
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            creationflags = 0

        process = subprocess.Popen(
            [python_exe, str(bridge_script), rp_dir.name],
            cwd=str(base_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags if sys.platform == 'win32' else 0
        )
        print("Bridge started in background (hidden)")
    else:
        # Debug mode - new visible terminal window
        if sys.platform == 'win32':
            # On Windows, create a new console window
            process = subprocess.Popen(
                [python_exe, str(bridge_script), rp_dir.name],
                cwd=str(base_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            print("Bridge started in new terminal window (visible for debugging)")
        else:
            # On Unix-like systems, try to open in new terminal
            # This is a fallback - may not work on all systems
            process = subprocess.Popen(
                [python_exe, str(bridge_script), rp_dir.name],
                cwd=str(base_dir)
            )
            print("Bridge started")

    # Give bridge a moment to start up
    time.sleep(0.1)

    return process


def stop_bridge(process: subprocess.Popen) -> None:
    """Stop the bridge process gracefully.

    Args:
        process: Bridge process handle
    """
    if process and process.poll() is None:  # If process is still running
        print("\nStopping bridge...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Bridge didn't stop gracefully, forcing...")
            process.kill()
        except Exception as e:
            print(f"Error stopping bridge: {e}")


def cleanup_bridge() -> None:
    """Cleanup function called on exit."""
    global _bridge_process
    if _bridge_process:
        stop_bridge(_bridge_process)


def find_rp_folders(base_dir):
    """Find all valid RP folders (those with a state/ subdirectory)."""
    rp_folders = []
    for item in base_dir.iterdir():
        if item.is_dir() and (item / "state").exists():
            rp_folders.append(item)
    return rp_folders


def select_rp_folder(rp_folders):
    """Prompt user to select an RP folder from a list."""
    print("\nAvailable RP folders:")
    for i, folder in enumerate(rp_folders, 1):
        print(f"  {i}. {folder.name}")

    while True:
        try:
            choice = input("\nSelect an RP folder (enter number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(rp_folders):
                return rp_folders[idx]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(rp_folders)}.")
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)


def main():
    """Main entry point with automatic folder detection."""
    global _bridge_process

    try:
        base_dir = Path(__file__).parent

        # Check for --background flag
        background_mode = "--background" in sys.argv
        if background_mode:
            sys.argv.remove("--background")

        # If folder specified on command line, use it
        if len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
            rp_folder = sys.argv[1]
            rp_dir = base_dir / rp_folder

            if not rp_dir.exists():
                print(f"Error: RP folder not found: {rp_dir}")
                input("\nPress Enter to exit...")
                sys.exit(1)

            if not (rp_dir / "state").exists():
                print(f"Error: Not a valid RP folder (no state/ directory): {rp_dir}")
                input("\nPress Enter to exit...")
                sys.exit(1)
        else:
            # Scan for available RP folders
            rp_folders = find_rp_folders(base_dir)

            if not rp_folders:
                print("Error: No RP folders found.")
                print("RP folders must contain a 'state/' subdirectory.")
                input("\nPress Enter to exit...")
                sys.exit(1)

            if len(rp_folders) == 1:
                # Auto-select if only one folder
                rp_dir = rp_folders[0]
                print(f"Auto-selected RP folder: {rp_dir.name}")
            else:
                # Let user choose
                rp_dir = select_rp_folder(rp_folders)
                print(f"Selected: {rp_dir.name}")

        # Register cleanup function
        atexit.register(cleanup_bridge)

        # Start the bridge
        print("\n" + "=" * 50)
        _bridge_process = start_bridge(rp_dir, background=background_mode)
        print("=" * 50)

        # Run the TUI
        print(f"\nLaunching RP Client TUI for: {rp_dir.name}")
        print("=" * 50)
        app = RPClientApp(rp_dir)
        app.run()

        # If we get here, the app exited normally
        print("\n" + "=" * 50)
        print("RP Client closed.")

        # Stop bridge before exiting
        stop_bridge(_bridge_process)

        input("\nPress Enter to exit...")

    except KeyboardInterrupt:
        print("\n\nExiting...")
        stop_bridge(_bridge_process)
        input("\nPress Enter to exit...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        stop_bridge(_bridge_process)
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    # Add a small delay to ensure console is visible
    time.sleep(0.1)

    try:
        main()
    except SystemExit:
        # Let system exits happen naturally
        raise
    except:
        # Catch any uncaught exceptions
        import traceback
        print("\n" + "=" * 50)
        print("UNCAUGHT EXCEPTION:")
        traceback.print_exc()
        print("=" * 50)
        stop_bridge(_bridge_process)
        input("\nPress Enter to exit...")
        raise
