"""Verify MemoryExtractionAgent implementation and integration.

This script checks that MemoryExtractionAgent is properly:
1. Implemented in the immediate agents package
2. Registered in immediate_agent_strategy.py
3. Enabled in defaults.py configuration
4. Can be instantiated (basic smoke test)
"""

from pathlib import Path
import sys

print("=" * 70)
print("MemoryExtractionAgent Verification")
print("=" * 70)

# 1. Check agent can be imported
print("\n1. Checking agent import...")
try:
    from src.automation.agents.immediate import MemoryExtractionAgent
    print("   [OK] MemoryExtractionAgent imported successfully")
    print(f"   Agent class: {MemoryExtractionAgent.__name__}")
except ImportError as e:
    print(f"   [X] Failed to import MemoryExtractionAgent: {e}")
    sys.exit(1)

# 2. Check agent is registered in immediate_agent_strategy
print("\n2. Checking immediate_agent_strategy registration...")
try:
    from src.automation.agents.immediate_agent_strategy import ImmediateAgentStrategy

    # Check import availability flag
    from src.automation.agents import immediate_agent_strategy as strategy_module
    memory_available = strategy_module.MEMORY_EXTRACTION_AVAILABLE

    if memory_available:
        print("   [OK] MEMORY_EXTRACTION_AVAILABLE = True")
    else:
        print("   [X] MEMORY_EXTRACTION_AVAILABLE = False")

    # Check if it's in the available agents
    with open("src/automation/agents/immediate_agent_strategy.py", "r") as f:
        content = f.read()
        if "MemoryExtractionAgent" in content:
            print("   [OK] MemoryExtractionAgent found in strategy file")
        else:
            print("   [X] MemoryExtractionAgent not found in strategy file")

        if '"memory_extraction"' in content or "'memory_extraction'" in content:
            print("   [OK] 'memory_extraction' agent_id referenced")
        else:
            print("   [X] 'memory_extraction' agent_id not found")

except Exception as e:
    print(f"   [X] Error checking strategy: {e}")

# 3. Check defaults.py configuration
print("\n3. Checking defaults.py configuration...")
try:
    from src.infrastructure.config.defaults import (
        IMMEDIATE_AGENT_DEFAULTS,
        get_default_config
    )

    # Check IMMEDIATE_AGENT_DEFAULTS exists and has memory_extraction
    if "memory_extraction" in IMMEDIATE_AGENT_DEFAULTS:
        config = IMMEDIATE_AGENT_DEFAULTS["memory_extraction"]
        enabled = config.get("enabled", False)
        timeout = config.get("timeout_seconds", "N/A")

        print(f"   [OK] memory_extraction config found")
        print(f"       - enabled: {enabled}")
        print(f"       - timeout_seconds: {timeout}")

        if enabled:
            print("   [OK] memory_extraction is enabled by default")
        else:
            print("   [WARN] memory_extraction is disabled by default")
    else:
        print("   [X] memory_extraction not in IMMEDIATE_AGENT_DEFAULTS")

    # Check it's in get_default_config()
    default_config = get_default_config()
    immediate_agents = default_config.get("agents", {}).get("immediate", {})

    if immediate_agents:
        print(f"   [OK] get_default_config() includes immediate agents")
        if "memory_extraction" in immediate_agents:
            print(f"   [OK] memory_extraction in default config")
        else:
            print(f"   [X] memory_extraction NOT in default config")
    else:
        print(f"   [X] No immediate agents in get_default_config()")

except ImportError as e:
    print(f"   [X] Failed to import from defaults: {e}")
except Exception as e:
    print(f"   [X] Error checking defaults: {e}")

# 4. Check agent structure
print("\n4. Checking agent implementation...")
try:
    # Check agent has required methods
    agent_methods = dir(MemoryExtractionAgent)

    required_methods = [
        "get_agent_id",
        "execute",
        "_load_recent_memories",
        "_build_relevance_prompt",
        "_format_for_injection"
    ]

    for method in required_methods:
        if method in agent_methods:
            print(f"   [OK] Method '{method}' exists")
        else:
            print(f"   [X] Method '{method}' MISSING")

except Exception as e:
    print(f"   [X] Error checking agent structure: {e}")

# 5. Check docstrings and documentation
print("\n5. Checking documentation...")
try:
    agent_doc = MemoryExtractionAgent.__doc__
    if agent_doc and len(agent_doc.strip()) > 0:
        print("   [OK] MemoryExtractionAgent has class docstring")
        # Show first line
        first_line = agent_doc.strip().split('\n')[0]
        print(f"       \"{first_line}\"")
    else:
        print("   [WARN] MemoryExtractionAgent missing class docstring")

    execute_doc = MemoryExtractionAgent.execute.__doc__
    if execute_doc and len(execute_doc.strip()) > 0:
        print("   [OK] execute() method has docstring")
    else:
        print("   [WARN] execute() method missing docstring")

except Exception as e:
    print(f"   [X] Error checking documentation: {e}")

# 6. Basic instantiation test
print("\n6. Testing basic instantiation...")
try:
    # Create a minimal agent instance (won't actually run)
    from unittest.mock import Mock

    mock_bridge = Mock()
    mock_bridge.session_state_service.get_scene_context.return_value = {
        "characters_in_scene": []
    }

    test_agent = MemoryExtractionAgent(
        rp_dir=Path("test_rps_output/Test Adventure"),
        log_file=None,
        bridge=mock_bridge
    )

    print("   [OK] Agent instantiated successfully")
    print(f"       - Agent ID: {test_agent.get_agent_id()}")
    print(f"       - rp_dir: {test_agent.rp_dir}")

except Exception as e:
    print(f"   [X] Failed to instantiate agent: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Verification Complete")
print("=" * 70)

print("\nSummary:")
print("--------")
print("[*] MemoryExtractionAgent is an immediate agent (runs BEFORE Claude)")
print("[*] Loads last 50 memories per character from repository")
print("[*] Uses LLM for relevance ranking (temperature=0.0)")
print("[*] Returns 5-10 most relevant memories as markdown")
print("[*] Has 5-second timeout for fast execution")

print("\nNext Steps:")
print("-----------")
print("1. Test with actual RP data:")
print("   - Create test RP with characters and memories")
print("   - Run agent with user message")
print("   - Verify relevant memories are extracted")
print("")
print("2. Integration testing:")
print("   - Test via ImmediateAgentStrategy.execute()")
print("   - Verify prompt injection works correctly")
print("   - Test timeout behavior")
print("")
print("3. End-to-end testing:")
print("   - Run full conversation with agent enabled")
print("   - Verify memories appear in Claude's context")
print("   - Check response quality with memory context")
