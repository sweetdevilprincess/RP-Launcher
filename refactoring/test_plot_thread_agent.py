"""Simple verification script for PlotThreadDetectionAgent.

This script verifies that:
1. The agent can be imported
2. The agent can be instantiated
3. The agent has the required methods
4. The agent can generate thread IDs
"""

from pathlib import Path
import sys
import os

# Set PYTHONPATH to include src directory
project_root = Path(__file__).parent
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))
os.chdir(project_root)

def test_agent_import():
    """Test that the agent can be imported."""
    print("Testing agent import...")
    try:
        from src.automation.agents.implementations.plot_thread_detection_agent import PlotThreadDetectionAgent
        print("[PASS] PlotThreadDetectionAgent imported successfully")
        return PlotThreadDetectionAgent
    except ImportError as e:
        print(f"[FAIL] Failed to import PlotThreadDetectionAgent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_agent_instantiation(agent_class):
    """Test that the agent can be instantiated."""
    print("\nTesting agent instantiation...")
    try:
        # Create mock RP directory
        rp_dir = Path(__file__).parent / "test_rp"

        # Instantiate agent (without bridge for now)
        agent = agent_class(rp_dir=rp_dir, bridge=None)
        print("[PASS] PlotThreadDetectionAgent instantiated successfully")
        return agent
    except Exception as e:
        print(f"[FAIL] Failed to instantiate PlotThreadDetectionAgent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_agent_methods(agent):
    """Test that the agent has required methods."""
    print("\nTesting agent methods...")
    required_methods = [
        "get_agent_id",
        "execute",
        "_build_plot_thread_prompt",
        "_load_existing_threads",
        "_generate_thread_id",
        "_create_new_thread",
        "_update_existing_thread",
        "_resolve_thread",
        "_save_threads",
    ]

    missing_methods = []
    for method_name in required_methods:
        if not hasattr(agent, method_name):
            missing_methods.append(method_name)

    if missing_methods:
        print(f"[FAIL] Missing methods: {', '.join(missing_methods)}")
        sys.exit(1)

    print(f"[PASS] All {len(required_methods)} required methods present")

def test_agent_id(agent):
    """Test that get_agent_id returns correct value."""
    print("\nTesting agent ID...")
    agent_id = agent.get_agent_id()

    if agent_id != "plot_thread_detection":
        print(f"[FAIL] Expected agent_id='plot_thread_detection', got '{agent_id}'")
        sys.exit(1)

    print(f"[PASS] Agent ID correct: '{agent_id}'")

def test_thread_id_generation(agent):
    """Test that thread ID generation works."""
    print("\nTesting thread ID generation...")

    # Generate 5 thread IDs
    thread_ids = [agent._generate_thread_id() for _ in range(5)]

    # Check format
    for thread_id in thread_ids:
        if not thread_id.startswith("thread_"):
            print(f"[FAIL] Thread ID '{thread_id}' doesn't start with 'thread_'")
            sys.exit(1)

        if len(thread_id) != 15:  # "thread_" + 8 hex chars
            print(f"[FAIL] Thread ID '{thread_id}' has incorrect length: {len(thread_id)} (expected 15)")
            sys.exit(1)

    # Check uniqueness
    if len(set(thread_ids)) != len(thread_ids):
        print("[FAIL] Thread IDs are not unique")
        sys.exit(1)

    print(f"[PASS] Thread ID generation works correctly")
    print(f"  Sample IDs: {thread_ids[:3]}")

def test_background_strategy_import():
    """Test that the agent is properly integrated into BackgroundAgentStrategy."""
    print("\nTesting BackgroundAgentStrategy integration...")
    try:
        from src.automation.agents.background_agent_strategy import (
            BackgroundAgentStrategy,
            PLOT_THREAD_DETECTION_AVAILABLE,
            PlotThreadDetectionAgent
        )

        if not PLOT_THREAD_DETECTION_AVAILABLE:
            print("[FAIL] PLOT_THREAD_DETECTION_AVAILABLE is False")
            sys.exit(1)

        print("[PASS] PlotThreadDetectionAgent is properly integrated")
        print(f"  PLOT_THREAD_DETECTION_AVAILABLE = {PLOT_THREAD_DETECTION_AVAILABLE}")

    except ImportError as e:
        print(f"[FAIL] Failed to import from background_agent_strategy: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Run all verification tests."""
    print("="*60)
    print("PlotThreadDetectionAgent Verification Script")
    print("="*60)

    # Test 1: Import
    agent_class = test_agent_import()

    # Test 2: Instantiation
    agent = test_agent_instantiation(agent_class)

    # Test 3: Methods
    test_agent_methods(agent)

    # Test 4: Agent ID
    test_agent_id(agent)

    # Test 5: Thread ID generation
    test_thread_id_generation(agent)

    # Test 6: Integration
    test_background_strategy_import()

    print("\n" + "="*60)
    print("[PASS] All verification tests passed!")
    print("="*60)

if __name__ == "__main__":
    main()
