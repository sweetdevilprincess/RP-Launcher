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
import os
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
            print("⚠️  Detected pkgs cache Python - relaunching with correct interpreter...")
            # Clean up any existing bridge processes before relaunching
            # (This prevents orphaned bridge processes)
            try:
                import psutil
                current_pid = os.getpid()
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'tui_bridge.py' in ' '.join(proc.info['cmdline'] or []):
                            print(f"Cleaning up bridge process: {proc.info['pid']}")
                            proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except ImportError:
                # psutil not available, skip cleanup
                pass

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
import json

# Force console window if launched with pythonw.exe on Windows
if sys.platform == 'win32' and not sys.stdout:
    print("⚠️  Detected pythonw.exe - relaunching with python.exe for console window...")
    # Clean up any existing bridge processes before relaunching
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'tui_bridge.py' in ' '.join(proc.info['cmdline'] or []):
                    print(f"Cleaning up bridge process: {proc.info['pid']}")
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        # psutil not available, skip cleanup
        pass

    # Relaunch with python.exe to get a console window
    python_exe = sys.executable.replace('pythonw.exe', 'python.exe')
    subprocess.Popen([python_exe] + sys.argv)
    sys.exit()

from src.rp_client_tui import RPClientApp
from src.update_checker import check_for_updates
from src.version import get_current_version, is_semantic_version
from src.initialize_rp import RPInitializer
import shutil


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


def restart_bridge() -> None:
    """Restart the bridge process.

    This function is called from the TUI when the user presses F10.
    """
    global _bridge_process
    if _bridge_process:
        print("\n🔄 Restarting bridge...")
        stop_bridge(_bridge_process)
        time.sleep(0.5)  # Brief pause to ensure clean shutdown

        # Get the RP directory from the bridge process arguments
        # The bridge was started with the rp_dir.name, we need to reconstruct it
        base_dir = Path(__file__).parent
        rps_dir = base_dir / "RPs"
        # We'll need to find the rp_dir - let's search for tui_active.flag in RPs directory
        for item in rps_dir.iterdir():
            if item.is_dir():
                tui_flag = item / "state" / "tui_active.flag"
                if tui_flag.exists():
                    rp_dir = item
                    _bridge_process = start_bridge(rp_dir, background=False)
                    print("✅ Bridge restarted")
                    return

        raise Exception("Could not find active RP directory")


def cleanup_bridge() -> None:
    """Cleanup function called on exit."""
    global _bridge_process
    if _bridge_process:
        # First, try to signal bridge to shutdown gracefully by removing flag
        try:
            # Find and remove tui_active.flag to signal bridge to stop
            base_dir = Path(__file__).parent
            rps_dir = base_dir / "RPs"
            for item in rps_dir.iterdir():
                if item.is_dir():
                    tui_flag = item / "state" / "tui_active.flag"
                    if tui_flag.exists():
                        tui_flag.unlink(missing_ok=True)
                        print("Removed TUI active flag")
                        # Give bridge a moment to see the flag is gone
                        import time
                        time.sleep(1)
                        break
        except Exception as e:
            print(f"Warning: Could not remove TUI flag: {e}")

        # Then terminate the process if it's still running
        stop_bridge(_bridge_process)


def find_rp_folders(base_dir):
    """Find all valid RP folders (those with a state/ subdirectory)."""
    rp_folders = []
    for item in base_dir.iterdir():
        if item.is_dir() and (item / "state").exists():
            rp_folders.append(item)
    return rp_folders


def select_rp_folder(rp_folders, base_dir):
    """Prompt user to select an RP folder from a list or create a new one.

    Args:
        rp_folders: List of existing RP folders
        base_dir: Base directory where RPs are stored

    Returns:
        Path to selected RP folder, or None if user cancelled
    """
    print("\nAvailable RP folders:")
    for i, folder in enumerate(rp_folders, 1):
        print(f"  {i}. {folder.name}")

    print(f"  {len(rp_folders) + 1}. ➕ Create new RP")

    while True:
        try:
            choice = input("\nSelect an RP folder (enter number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(rp_folders):
                return rp_folders[idx]
            elif idx == len(rp_folders):
                # Create new RP
                return create_new_rp(base_dir)
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(rp_folders) + 1}.")
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)


def check_and_display_updates(config: dict) -> None:
    """Check for updates and display notification if available.

    Args:
        config: Configuration dict with update check settings
    """
    # Check if update checking is enabled
    if not config.get("check_for_updates", True):
        return

    try:
        # Get cache duration from config (default 24 hours)
        cache_duration = config.get("update_check_interval", 86400)

        # Check for updates (with 3 second timeout)
        result = check_for_updates(use_cache=True, cache_duration=cache_duration, timeout=3)

        if result.available:
            # Format version display
            current_display = result.current if result.current else 'unknown'
            latest_display = result.latest if result.latest else 'unknown'

            # Show prominent update notification
            print("\n" + "=" * 70)
            print(" " * 20 + "UPDATE AVAILABLE" + " " * 34)
            print("=" * 70)
            print(f"  Current version:  {current_display}")
            print(f"  Latest version:   {latest_display}")

            # Show release info if it's a semantic version
            if is_semantic_version(latest_display):
                print(f"  New release available!")

            print()
            print("  To update, run:")
            print("    git pull")
            print("=" * 70)

            # Pause so user can see the notification
            input("\nPress Enter to continue...")
            print()
        elif not result.error:
            # Silently succeed if up to date
            pass
        # Silently ignore errors (don't want to block startup)
    except Exception:
        # Don't let update check failures block the launcher
        pass


def copy_template(template_name: str, dest_dir: Path, rp_name: str) -> bool:
    """Copy template files from starter pack to destination.

    Args:
        template_name: Name of template (e.g., 'minimal')
        dest_dir: Destination RP directory
        rp_name: Name of the RP (for renaming RP_NAME.md)

    Returns:
        True if template was copied, False if not found
    """
    base_dir = Path(__file__).parent
    template_dir = base_dir / "setup" / "templates" / "starter_packs" / template_name

    if not template_dir.exists():
        return False

    print(f"📦 Using template: {template_name}")
    print(f"   Copying from: {template_dir}")
    print()

    # Create destination if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy all template files and directories
    copied_count = 0
    for item in template_dir.iterdir():
        # Skip README.md from template (it's template documentation)
        if item.name == "README.md":
            continue

        dest_item = dest_dir / item.name

        # Handle RP_NAME.md renaming
        if item.name == "RP_NAME.md":
            dest_item = dest_dir / f"{rp_name}.md"

        try:
            if item.is_file():
                shutil.copy2(item, dest_item)
                print(f"  ✓ Copied: {item.name}")
                copied_count += 1
            elif item.is_dir():
                shutil.copytree(item, dest_item, dirs_exist_ok=True)
                print(f"  ✓ Copied directory: {item.name}/")
                copied_count += 1
        except Exception as e:
            print(f"  ⚠️  Warning: Could not copy {item.name}: {e}")

    print(f"\n  📄 Copied {copied_count} items from template")
    print()
    return True


def print_success_message(rp_dir: Path, rp_name: str):
    """Print success message with next steps."""
    print()
    print("=" * 70)
    print(" " * 24 + "SUCCESS!" + " " * 39)
    print("=" * 70)
    print()
    print(f"✅ RP Created: {rp_name}")
    print(f"📁 Location: {rp_dir}")
    print()
    print("Next steps:")
    print()
    print("  1. (Optional) Customize your RP:")
    print(f"     - Edit: {rp_dir}/AUTHOR'S_NOTES.md")
    print(f"     - Edit: {rp_dir}/STORY_GENOME.md")
    print(f"     - Edit: {rp_dir}/characters/{{{{user}}}}.md")
    print()
    print("  2. Your new RP will launch next!")
    print()
    print("  3. Start writing!")
    print("     - Type your message")
    print("     - Press Ctrl+Enter to send")
    print("     - Get Claude's response")
    print("     - Continue your story!")
    print()
    print("=" * 70)
    print()


def create_new_rp(base_dir: Path) -> Path:
    """Create a new RP through interactive setup.

    Args:
        base_dir: Base directory where RPs folder is located

    Returns:
        Path to the newly created RP
    """
    rps_dir = base_dir / "RPs"

    # Print setup banner
    print("\n" + "=" * 70)
    print(" " * 20 + "CREATE NEW RP" + " " * 38)
    print("=" * 70)
    print()

    # Get RP name
    while True:
        rp_name = input("Enter name for your new RP: ").strip()
        if rp_name:
            break
        print("Please enter a valid name.")

    rp_dir = rps_dir / rp_name

    # Check if RP already exists
    if rp_dir.exists():
        print(f"\n⚠️  RP folder already exists: {rp_dir}")
        print("\nOptions:")
        print(f"  1. Use a different name")
        print(f"  2. Delete the existing folder")
        print()
        response = input("Continue with different name? (y/n): ").strip().lower()
        if response == 'y':
            return create_new_rp(base_dir)
        else:
            print("Setup cancelled.")
            return None

    # Select template
    print("\nAvailable templates:")
    templates = ["minimal", "fantasy_adventure"]
    for i, template in enumerate(templates, 1):
        print(f"  {i}. {template}")

    while True:
        try:
            choice = input("\nSelect template (enter number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(templates):
                selected_template = templates[idx]
                break
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(templates)}.")
        except ValueError:
            print("Please enter a valid number.")

    print(f"\nCreating RP: {rp_name}")
    print(f"Location: {rp_dir}")
    print()

    # Step 1: Initialize directory structure
    try:
        initializer = RPInitializer(rp_dir)
        initializer.initialize(rp_name=rp_name, skip_existing=True)
    except Exception as e:
        print(f"❌ Error initializing RP: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Step 2: Copy template files
    try:
        template_found = copy_template(selected_template, rp_dir, rp_name)
        if not template_found:
            print(f"⚠️  Template not found: {selected_template}")
            print(f"   Using basic structure instead.")
            print()
    except Exception as e:
        print(f"⚠️  Warning: Could not copy template: {e}")

    # Print success message
    print_success_message(rp_dir, rp_name)

    return rp_dir


def main():
    """Main entry point with automatic folder detection."""
    global _bridge_process

    try:
        base_dir = Path(__file__).parent
        rps_dir = base_dir / "RPs"

        # Check for --background flag
        background_mode = "--background" in sys.argv
        if background_mode:
            sys.argv.remove("--background")

        # Check for --skip-update-check flag
        skip_update_check = "--skip-update-check" in sys.argv
        if skip_update_check:
            sys.argv.remove("--skip-update-check")

        # Load config for update check settings
        config_file = base_dir / "config.json"
        config = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception:
                pass

        # Check for updates (unless skipped)
        if not skip_update_check:
            check_and_display_updates(config)

        # Ensure RPs directory exists
        if not rps_dir.exists():
            print(f"Creating RPs directory...")
            rps_dir.mkdir(parents=True, exist_ok=True)

        # If folder specified on command line, use it
        if len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
            rp_folder = sys.argv[1]
            rp_dir = rps_dir / rp_folder

            if not rp_dir.exists():
                print(f"Error: RP folder not found: {rp_dir}")
                input("\nPress Enter to exit...")
                sys.exit(1)

            if not (rp_dir / "state").exists():
                print(f"Error: Not a valid RP folder (no state/ directory): {rp_dir}")
                input("\nPress Enter to exit...")
                sys.exit(1)
        else:
            # Scan for available RP folders in RPs directory
            rp_folders = find_rp_folders(rps_dir)

            if not rp_folders:
                print("Error: No RP folders found.")
                print()
                print("Would you like to create a new RP?")
                response = input("Create new RP? (y/n): ").strip().lower()
                if response == 'y':
                    rp_dir = create_new_rp(base_dir)
                    if not rp_dir:
                        print("Error: Could not create RP.")
                        input("\nPress Enter to exit...")
                        sys.exit(1)
                else:
                    print("No RP folders found and no new RP created.")
                    input("\nPress Enter to exit...")
                    sys.exit(1)
            elif len(rp_folders) == 1:
                # Auto-select if only one folder
                rp_dir = rp_folders[0]
                print(f"Auto-selected RP folder: {rp_dir.name}")
            else:
                # Let user choose
                rp_dir = select_rp_folder(rp_folders, base_dir)
                if not rp_dir:
                    print("Error: Could not create or select RP.")
                    input("\nPress Enter to exit...")
                    sys.exit(1)
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
        app = RPClientApp(rp_dir, bridge_restart_callback=restart_bridge)
        print("[LAUNCHER] Starting app.run()...")
        app.run()

        # If we get here, the app exited normally
        print("[LAUNCHER] app.run() returned")
        print("\n" + "=" * 50)
        print("RP Client closed.")

        # Stop bridge before exiting
        print("[LAUNCHER] Stopping bridge...")
        stop_bridge(_bridge_process)
        print("[LAUNCHER] Bridge stopped")

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
