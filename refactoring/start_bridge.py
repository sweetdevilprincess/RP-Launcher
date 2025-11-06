"""Simple Bridge Starter - No module import issues."""

from pathlib import Path
from src.presentation.bridge.bridge_service import BridgeService

if __name__ == "__main__":
    rp_dir = Path("test_rps_output/Test Adventure")

    print("=" * 60)
    print("Starting Bridge Service")
    print("=" * 60)
    print(f"RP Directory: {rp_dir.absolute()}")
    print()

    bridge = BridgeService(rp_dir=rp_dir, host="127.0.0.1", port=5555)

    try:
        bridge.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        bridge.stop()
