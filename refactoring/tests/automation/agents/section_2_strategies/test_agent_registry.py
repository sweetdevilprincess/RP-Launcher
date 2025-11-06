"""Unit tests for AgentRegistry - Strategy creation and configuration.

Tests the agent registry's logic for creating and ordering strategies.
"""

import pytest
from refactoring.src.automation.agents.registry import AgentRegistry
from refactoring.src.automation.agents.immediate_agent_strategy import ImmediateAgentStrategy
from refactoring.src.automation.agents.background_agent_strategy import BackgroundAgentStrategy
from refactoring.src.automation.agents.fallback_trigger_strategy import FallbackTriggerStrategy


@pytest.mark.unit
def test_registry_creates_immediate_strategy_when_enabled(stub_logger):
    """Test that immediate strategy is created when agents are enabled."""
    from tests.automation.agents.conftest import MockConfigService

    config = MockConfigService({
        "agents": {
            "immediate": {
                "quick_entity_analysis": {"enabled": True, "timeout_seconds": 3}
            }
        },
        "fallback": {
            "use_trigger_system": True,
            "trigger_system_primary": False
        }
    })

    registry = AgentRegistry(config=config, logger=stub_logger)
    strategies = registry.create_strategies()

    assert len(strategies) == 1
    assert isinstance(strategies[0], ImmediateAgentStrategy)


@pytest.mark.unit
def test_registry_creates_background_strategy_when_enabled(stub_logger):
    """Test that background strategy is created when agents are enabled."""
    from tests.automation.agents.conftest import MockConfigService

    config = MockConfigService({
        "agents": {
            "background": {
                "response_analyzer": {"enabled": True}
            }
        },
        "fallback": {
            "use_trigger_system": True,
            "trigger_system_primary": False
        }
    })

    registry = AgentRegistry(config=config, logger=stub_logger)
    strategies = registry.create_strategies()

    assert len(strategies) == 1
    assert isinstance(strategies[0], BackgroundAgentStrategy)


@pytest.mark.unit
def test_registry_creates_both_strategies_when_enabled(stub_logger):
    """Test that both immediate and background strategies are created."""
    from tests.automation.agents.conftest import MockConfigService

    config = MockConfigService({
        "agents": {
            "immediate": {
                "quick_entity_analysis": {"enabled": True}
            },
            "background": {
                "response_analyzer": {"enabled": True}
            }
        },
        "fallback": {
            "use_trigger_system": True,
            "trigger_system_primary": False
        }
    })

    registry = AgentRegistry(config=config, logger=stub_logger)
    strategies = registry.create_strategies()

    # Should have both strategies
    assert len(strategies) == 2
    assert isinstance(strategies[0], ImmediateAgentStrategy)
    assert isinstance(strategies[1], BackgroundAgentStrategy)


@pytest.mark.unit
def test_registry_creates_fallback_when_trigger_system_primary(stub_logger):
    """Test that fallback trigger strategy is used when configured as primary."""
    from tests.automation.agents.conftest import MockConfigService

    config = MockConfigService({
        "agents": {
            "immediate": {
                "quick_entity_analysis": {"enabled": True}
            }
        },
        "fallback": {
            "use_trigger_system": True,
            "trigger_system_primary": True  # Force trigger system
        }
    })

    registry = AgentRegistry(config=config, logger=stub_logger)
    strategies = registry.create_strategies()

    # Should use trigger fallback, not agent strategies
    assert len(strategies) == 1
    assert isinstance(strategies[0], FallbackTriggerStrategy)


@pytest.mark.unit
def test_registry_creates_fallback_when_no_agents_enabled(stub_logger):
    """Test that fallback is used when no agents are enabled."""
    from tests.automation.agents.conftest import MockConfigService

    config = MockConfigService({
        "agents": {
            "immediate": {
                "quick_entity_analysis": {"enabled": False}  # Disabled
            }
        },
        "fallback": {
            "use_trigger_system": True,
            "trigger_system_primary": False
        }
    })

    registry = AgentRegistry(config=config, logger=stub_logger)
    strategies = registry.create_strategies()

    # Should use trigger fallback when no agents enabled
    assert len(strategies) == 1
    assert isinstance(strategies[0], FallbackTriggerStrategy)


@pytest.mark.unit
def test_registry_returns_empty_when_all_disabled(stub_logger):
    """Test that empty list is returned when everything is disabled."""
    from tests.automation.agents.conftest import MockConfigService

    config = MockConfigService({
        "agents": {
            "immediate": {
                "quick_entity_analysis": {"enabled": False}
            }
        },
        "fallback": {
            "use_trigger_system": False,  # Trigger system disabled too
            "trigger_system_primary": False
        }
    })

    registry = AgentRegistry(config=config, logger=stub_logger)
    strategies = registry.create_strategies()

    # No strategies should be created
    assert len(strategies) == 0


@pytest.mark.unit
def test_registry_skips_immediate_when_no_agents_enabled(stub_logger):
    """Test that immediate strategy is not created when all agents disabled."""
    from tests.automation.agents.conftest import MockConfigService

    config = MockConfigService({
        "agents": {
            "immediate": {
                "quick_entity_analysis": {"enabled": False},
                "fact_extraction": {"enabled": False}
            },
            "background": {
                "response_analyzer": {"enabled": True}
            }
        },
        "fallback": {
            "use_trigger_system": True,
            "trigger_system_primary": False
        }
    })

    registry = AgentRegistry(config=config, logger=stub_logger)
    strategies = registry.create_strategies()

    # Should only create background strategy
    assert len(strategies) == 1
    assert isinstance(strategies[0], BackgroundAgentStrategy)


@pytest.mark.unit
def test_registry_logs_strategy_creation(stub_logger):
    """Test that registry logs strategy creation events."""
    from tests.automation.agents.conftest import MockConfigService

    config = MockConfigService({
        "agents": {
            "immediate": {
                "quick_entity_analysis": {"enabled": True}
            }
        },
        "fallback": {
            "use_trigger_system": True,
            "trigger_system_primary": False
        }
    })

    registry = AgentRegistry(config=config, logger=stub_logger)
    registry.create_strategies()

    # Should log start, registration, and complete
    logged_messages = [msg[1] if len(msg) > 1 else str(msg) for msg in stub_logger.messages]
    assert any("start" in message for message in logged_messages)
    assert any("complete" in message for message in logged_messages)
