#!/usr/bin/env python3
"""Launcher for RP Client - Starts Bridge and TUI together.

This script:
1. Scans for available RPs or creates new ones
2. Starts the Bridge service in a background process
3. Waits for Bridge to be ready
4. Launches the TUI application
5. Cleans up properly on exit
"""

from __future__ import annotations

import argparse
import multiprocessing
import shutil
import sys
import time
from pathlib import Path

# Add project root to path for package imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.presentation.bridge.bridge_service import BridgeService
from src.presentation.tui.app import RPClientApp
from src.presentation.tui.screens.rp_selection_screen import RPSelectionScreen
from textual.app import App


def run_bridge(rp_dir: Path, host: str = "127.0.0.1", port: int = 5555) -> None:
    """Run the Bridge service in a subprocess.

    Args:
        rp_dir: Path to RP directory
        host: Host to bind to
        port: Port to listen on
    """
    # Redirect stdout and stderr to log file to prevent glitching through TUI
    log_dir = rp_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "bridge.log"

    try:
        # Open log file for append
        with open(log_file, 'a', encoding='utf-8') as log:
            # Write header
            import datetime
            log.write(f"\n{'='*60}\n")
            log.write(f"Bridge started at {datetime.datetime.now()}\n")
            log.write(f"Host: {host}:{port}\n")
            log.write(f"RP: {rp_dir}\n")
            log.write(f"{'='*60}\n\n")
            log.flush()

            # Redirect stdout and stderr
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = log
            sys.stderr = log

            try:
                print(f"[Bridge Process] Starting Bridge on {host}:{port}...")
                bridge = BridgeService(rp_dir, host, port)
                bridge.run()  # Blocks until shutdown
            except KeyboardInterrupt:
                print("[Bridge Process] Interrupted")
            except Exception as e:
                print(f"[Bridge Process] Error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Restore original stdout/stderr
                sys.stdout = original_stdout
                sys.stderr = original_stderr
    except Exception as e:
        # If we can't even open the log file, fail silently
        # (the TUI is running and we don't want to mess up its display)
        pass


def wait_for_bridge(host: str, port: int, timeout: int = 10) -> bool:
    """Wait for Bridge to be ready and responding to requests.

    Args:
        host: Bridge host
        port: Bridge port
        timeout: Maximum time to wait in seconds

    Returns:
        True if Bridge is ready and responding, False if timeout
    """
    import socket
    from src.infrastructure.ipc import SocketClient, IPCMessageType

    start_time = time.time()

    # First, wait for socket to be available
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect((host, port))
            sock.close()
            break  # Socket is open
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    else:
        # Timeout waiting for socket
        return False

    # Give bridge a moment to finish initialization
    time.sleep(1.0)

    # Now verify bridge is actually responding to requests
    remaining_time = timeout - (time.time() - start_time)
    retry_end = time.time() + max(remaining_time, 3.0)  # At least 3 seconds for ping test

    while time.time() < retry_end:
        try:
            client = SocketClient(host, port)
            client.connect()
            response = client.send_request(IPCMessageType.PING, timeout=2.0)
            client.disconnect()

            if response and response.success:
                return True
        except Exception:
            time.sleep(0.5)

    return False


class RPLauncherApp(App):
    """Launcher app that shows RP selection screen.

    This app displays the RP selection screen and handles the RPSelected
    message by exiting and returning the selected RP path.
    """

    def __init__(self, base_dir: Path, host: str, port: int):
        """Initialize launcher app.

        Args:
            base_dir: Base directory containing RP folders
            host: Bridge host
            port: Bridge port
        """
        super().__init__()
        self.base_dir = base_dir
        self.host = host
        self.port = port
        self.selected_rp_path: Path | None = None

    def on_mount(self) -> None:
        """Mount the RP selection screen."""
        self.push_screen(RPSelectionScreen(self.base_dir), callback=self.handle_rp_selection)

    def handle_rp_selection(self, rp_path: Path | None) -> None:
        """Handle RP selection result from screen.

        Args:
            rp_path: Path to selected RP, or None if cancelled
        """
        print(f"[DEBUG] RPLauncherApp received selection result: {rp_path}")
        if rp_path:
            self.selected_rp_path = rp_path
            print(f"[DEBUG] Setting selected_rp_path and exiting launcher app")
        self.exit()


def find_rp_folders(base_dir: Path) -> list[Path]:
    """Find all valid RP folders (those with a state/ subdirectory).

    Args:
        base_dir: Base directory to search in

    Returns:
        List of RP folder paths
    """
    rp_folders = []
    for item in base_dir.iterdir():
        if item.is_dir() and (item / "state").exists():
            rp_folders.append(item)
    return sorted(rp_folders, key=lambda p: p.name.lower())


def select_rp_folder(rp_folders: list[Path], base_dir: Path) -> Path | None:
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

    print(f"  {len(rp_folders) + 1}. [+] Create new RP")

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
            return None


def create_new_rp(base_dir: Path) -> Path | None:
    """Create a new RP through interactive setup.

    Args:
        base_dir: Base directory where RPs folder is located

    Returns:
        Path to the newly created RP, or None if cancelled
    """
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

    rp_dir = base_dir / rp_name

    # Check if RP already exists
    if rp_dir.exists():
        print(f"\n[WARNING] RP folder already exists: {rp_dir}")
        print("\nOptions:")
        print(f"  1. Use a different name")
        print(f"  2. Cancel")
        print()
        response = input("Use different name? (y/n): ").strip().lower()
        if response == 'y':
            return create_new_rp(base_dir)
        else:
            print("Setup cancelled.")
            return None

    print(f"\nCreating RP: {rp_name}")
    print(f"Location: {rp_dir}")
    print()

    # Create basic directory structure
    try:
        # Create directories
        (rp_dir / "state").mkdir(parents=True, exist_ok=True)
        (rp_dir / "config").mkdir(parents=True, exist_ok=True)
        (rp_dir / "characters").mkdir(parents=True, exist_ok=True)
        (rp_dir / "entities").mkdir(parents=True, exist_ok=True)
        (rp_dir / "logs").mkdir(parents=True, exist_ok=True)

        # Create minimal config
        config_file = rp_dir / "config" / "config.json"
        config_file.write_text('{\n  "version": "2.0.0"\n}\n', encoding='utf-8')

        # Create minimal state files
        state_file = rp_dir / "state" / "current_state.md"
        state_file.write_text(
            f"# {rp_name}\n\n"
            f"**Current Chapter:** Chapter 1\n"
            f"**Current Timestamp:** Unknown\n"
            f"**Current Location:** Unknown\n\n"
            f"## Current Scene\n\n"
            f"[Your story begins here...]\n",
            encoding='utf-8'
        )

        # Create empty session triggers
        session_file = rp_dir / "state" / "session_triggers.json"
        session_file.write_text('[]', encoding='utf-8')

        # Create counter file (legacy - for backwards compatibility)
        counter_file = rp_dir / "state" / "response_counter.json"
        counter_file.write_text('{"count": 0}', encoding='utf-8')

        # Initialize proper session state using SessionStateService
        from src.infrastructure.sessions import SessionStateService
        from src.shared.logging_service import get_logger

        logger = get_logger("launcher")
        session_service = SessionStateService(logger=logger)
        session_service.initialize_session_state(
            rp_dir,
            rp_title=rp_name,
            session_id="main"
        )

        print("[OK] RP structure created successfully!")
        print("[OK] Session state initialized with all required fields!")
        print()
        print("=" * 70)
        print(" " * 24 + "SUCCESS!" + " " * 39)
        print("=" * 70)
        print()
        print(f"[OK] RP Created: {rp_name}")
        print(f"     Location: {rp_dir}")
        print()
        print("Your new RP will launch next!")
        print()
        print("=" * 70)
        print()

        return rp_dir

    except Exception as e:
        print(f"[ERROR] Error creating RP: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RP Client Launcher - Starts Bridge and TUI together"
    )
    parser.add_argument(
        "rp_dir",
        type=Path,
        nargs="?",
        help="Path to specific RP directory (optional - will show menu if not provided)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bridge host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5555,
        help="Bridge port (default: 5555)",
    )
    parser.add_argument(
        "--bridge-only",
        action="store_true",
        help="Start only the Bridge (no TUI)",
    )
    parser.add_argument(
        "--tui-only",
        action="store_true",
        help="Start only the TUI (Bridge must be running separately)",
    )

    args = parser.parse_args()

    # Determine RP directory
    if args.rp_dir:
        # Specific RP directory provided
        rp_dir = args.rp_dir.resolve()

        # Validate RP directory
        if not rp_dir.exists():
            print(f"[ERROR] RP directory does not exist: {rp_dir}")
            sys.exit(1)

        if not (rp_dir / "state").exists():
            print(f"[ERROR] Not a valid RP folder (no state/ directory): {rp_dir}")
            sys.exit(1)
    else:
        # No specific RP provided - show launcher screen
        base_dir = project_root / "RPs"

        # Ensure RPs directory exists
        if not base_dir.exists():
            print(f"Creating RPs directory: {base_dir}")
            base_dir.mkdir(parents=True, exist_ok=True)

        # Show RP selection screen
        print("\n[LAUNCHER] Starting RP Selection Screen...")
        print("[INFO] Use the TUI to browse and select your RP")
        print()

        launcher = RPLauncherApp(base_dir, args.host, args.port)
        launcher.run()

        # Get selected RP
        print(f"[DEBUG] Launcher exited, selected_rp_path = {launcher.selected_rp_path}")
        if launcher.selected_rp_path:
            rp_dir = launcher.selected_rp_path
            print(f"\n[OK] Selected RP: {rp_dir.name}")
        else:
            print("\n[INFO] No RP selected. Exiting.")
            sys.exit(0)

    # Set up launcher logging to file
    log_dir = rp_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    launcher_log_file = log_dir / "launcher.log"

    # Create log file handler
    import logging
    import datetime

    # Configure logging to both console and file
    class TeeLogger:
        """Logger that writes to both stdout and log file."""
        def __init__(self, log_file):
            self.terminal = sys.stdout
            self.log = open(log_file, 'a', encoding='utf-8')
            # Write header
            self.log.write(f"\n{'=' * 80}\n")
            self.log.write(f"Launcher started at {datetime.datetime.now()}\n")
            self.log.write(f"{'=' * 80}\n\n")
            self.log.flush()

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()

        def flush(self):
            self.terminal.flush()
            self.log.flush()

        def close(self):
            self.log.close()

    # Redirect stdout to tee logger
    original_stdout = sys.stdout
    sys.stdout = TeeLogger(launcher_log_file)

    print("\n" + "=" * 60)
    print("RP Client Launcher")
    print("=" * 60)
    print(f"RP Directory: {rp_dir.name}")
    print(f"Full Path: {rp_dir}")
    print(f"Bridge: {args.host}:{args.port}")
    print(f"Launcher Log: {launcher_log_file}")
    print("=" * 60)

    bridge_process = None

    try:
        # Option 1: Bridge only
        if args.bridge_only:
            print("\n[BRIDGE] Starting Bridge (Bridge-only mode)...")
            run_bridge(rp_dir, args.host, args.port)
            return

        # Option 2: TUI only (Bridge must be running)
        if args.tui_only:
            print("\n[TUI] Starting TUI (TUI-only mode)...")
            print("[WARNING] Make sure Bridge is running separately!")
            time.sleep(1)

            # Start TUI
            app = RPClientApp(rp_dir, args.host, args.port)
            app.run()
            return

        # Option 3: Start both (default)
        print("\n[START] Starting both Bridge and TUI...")

        # Start Bridge in background process
        print("\n[1] Starting Bridge process...")
        bridge_process = multiprocessing.Process(
            target=run_bridge,
            args=(rp_dir, args.host, args.port),
            daemon=True,
        )
        bridge_process.start()

        # Wait for Bridge to be ready
        print("[2] Waiting for Bridge to be ready...")
        if not wait_for_bridge(args.host, args.port, timeout=10):
            print("[ERROR] Bridge failed to start within 10 seconds")
            print("        Check if port is already in use or if there are errors above")
            sys.exit(1)

        print("[OK] Bridge is ready!")

        # Start TUI
        print("\n[3] Starting TUI...")
        time.sleep(0.5)  # Brief pause for user to see messages

        app = RPClientApp(rp_dir, args.host, args.port)
        app.run()

    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("\n[SHUTDOWN] Shutting down...")

        if bridge_process and bridge_process.is_alive():
            print("           Stopping Bridge process...")
            bridge_process.terminate()
            bridge_process.join(timeout=2)

            if bridge_process.is_alive():
                print("           Force killing Bridge process...")
                bridge_process.kill()

        print("[OK] Cleanup complete")

        # Close and restore stdout
        if isinstance(sys.stdout, TeeLogger):
            sys.stdout.close()
            sys.stdout = original_stdout


if __name__ == "__main__":
    # Required for multiprocessing on Windows
    multiprocessing.freeze_support()
    main()
