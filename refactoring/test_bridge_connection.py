"""Quick test script to verify Bridge IPC communication."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.ipc import SocketClient, IPCMessageType

def test_bridge():
    """Test bridge connection and basic operations."""
    print("=" * 60)
    print("Bridge Connection Test")
    print("=" * 60)

    # Connect to bridge
    client = SocketClient(host="127.0.0.1", port=5555)

    try:
        print("\n1. Connecting to bridge...")
        client.connect()
        print("   ✓ Connected")

        # Test PING
        print("\n2. Testing PING...")
        response = client.send_request(IPCMessageType.PING, timeout=5.0)
        if response.success:
            print(f"   ✓ PING successful: {response.data}")
        else:
            print(f"   ✗ PING failed: {response.error_message}")
            return

        # Test GET_MODULES
        print("\n3. Testing GET_MODULES...")
        response = client.send_request(IPCMessageType.GET_MODULES, timeout=5.0)
        if response.success:
            modules = response.data.get("modules", [])
            print(f"   ✓ GET_MODULES successful")
            print(f"   → Returned {len(modules)} modules")
            if modules:
                print("\n   Modules:")
                for module in modules[:5]:  # Show first 5
                    print(f"     - {module.get('name')}: {'✓' if module.get('enabled') else '✗'}")
            else:
                print("   ⚠ WARNING: No modules returned!")
        else:
            print(f"   ✗ GET_MODULES failed: {response.error_message}")

        # Test GET_SETTINGS
        print("\n4. Testing GET_SETTINGS...")
        response = client.send_request(IPCMessageType.GET_SETTINGS, timeout=5.0)
        if response.success:
            settings = response.data.get("settings", {})
            print(f"   ✓ GET_SETTINGS successful")
            print(f"   → Settings keys: {list(settings.keys())}")
            print(f"   → primary_provider: {settings.get('primary_provider')}")
            print(f"   → use_sdk: {settings.get('use_sdk')}")
        else:
            print(f"   ✗ GET_SETTINGS failed: {response.error_message}")

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()

if __name__ == "__main__":
    test_bridge()
