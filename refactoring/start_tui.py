"""Simple TUI Starter."""

from pathlib import Path
from src.presentation.tui.app import RPClientApp

if __name__ == "__main__":
    rp_dir = Path("test_rps_output/Test Adventure")

    print("=" * 60)
    print("Starting TUI")
    print("=" * 60)
    print(f"RP Directory: {rp_dir.absolute()}")
    print("Connecting to Bridge at 127.0.0.1:5555")
    print()

    app = RPClientApp(rp_dir=rp_dir, bridge_host="127.0.0.1", bridge_port=5555)
    app.run()
