"""Unit tests for FallbackTriggerStrategy - Legacy trigger system fallback.

Tests the fallback trigger strategy that provides legacy compatibility.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from refactoring.src.automation.contracts import AutomationContext, AgentContext
from refactoring.src.automation.agents.fallback_trigger_strategy import FallbackTriggerStrategy


@pytest.mark.unit
def test_create_context_transforms_automation_to_agent_context(stub_logger, mock_config_service):
    """Test that create_context transforms AutomationContext to AgentContext."""
    strategy = FallbackTriggerStrategy(
        logger=stub_logger,
        config_service=mock_config_service,
        use_trigger_system=True,
    )

    auto_context = AutomationContext(
        message="Alice walks through the forest",
        rp_dir=Path("/test/rp"),
        response_count=5,
        loaded_entities=["Alice", "Bob"],
    )

    agent_context = strategy.create_context(auto_context)

    assert isinstance(agent_context, AgentContext)
    assert agent_context.message == "Alice walks through the forest"
    assert agent_context.response_number == 5
    assert agent_context.loaded_entities == ["Alice", "Bob"]
    # Triggers don't need characters_in_scene
    assert agent_context.characters_in_scene == []


@pytest.mark.unit
def test_execute_with_trigger_system_disabled_returns_original_prompt(stub_logger, mock_config_service):
    """Test that execution returns original prompt when trigger system disabled."""
    strategy = FallbackTriggerStrategy(
        logger=stub_logger,
        config_service=mock_config_service,
        use_trigger_system=False,  # Disabled
    )

    agent_context = AgentContext(
        message="Test message",
        response_number=1,
        loaded_entities=[],
        characters_in_scene=[],
    )

    auto_context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    result = strategy.execute(
        agent_context=agent_context,
        prompt="Original prompt",
        automation_context=auto_context,
    )

    assert result.success is True
    assert result.enhanced_prompt == "Original prompt"


@pytest.mark.unit
def test_strategy_initialization_with_trigger_system_enabled(stub_logger, mock_config_service):
    """Test strategy initialization with trigger system enabled."""
    strategy = FallbackTriggerStrategy(
        logger=stub_logger,
        config_service=mock_config_service,
        use_trigger_system=True,
    )

    assert strategy._use_trigger_system is True
    assert strategy._logger == stub_logger
    assert strategy._config == mock_config_service
    # When enabled, trigger components should be initialized
    assert strategy._pattern_loader is not None
    assert strategy._trigger_coordinator is not None


@pytest.mark.unit
def test_strategy_initialization_with_trigger_system_disabled(stub_logger, mock_config_service):
    """Test strategy initialization with trigger system disabled."""
    strategy = FallbackTriggerStrategy(
        logger=stub_logger,
        config_service=mock_config_service,
        use_trigger_system=False,
    )

    assert strategy._use_trigger_system is False
    # When disabled, trigger components should be None
    assert strategy._pattern_loader is None
    assert strategy._trigger_coordinator is None


@pytest.mark.unit
def test_format_triggered_results_with_no_results(stub_logger, mock_config_service):
    """Test formatting empty trigger results."""
    strategy = FallbackTriggerStrategy(
        logger=stub_logger,
        config_service=mock_config_service,
        use_trigger_system=True,
    )

    formatted = strategy._format_triggered_results([])

    assert formatted == ""


@pytest.mark.unit
def test_inject_triggered_context_with_user_message_marker(stub_logger, mock_config_service):
    """Test that triggered context is injected before USER MESSAGE marker."""
    strategy = FallbackTriggerStrategy(
        logger=stub_logger,
        config_service=mock_config_service,
        use_trigger_system=True,
    )

    prompt = """Some context here...

========== USER MESSAGE ==========
User's message here
"""

    triggered_context = "<!-- Triggered entity: Alice -->"

    enhanced = strategy._inject_triggered_context(prompt, triggered_context)

    # Triggered context should be before USER MESSAGE marker
    marker_pos = enhanced.find("========== USER MESSAGE ==========")
    context_pos = enhanced.find("TRIGGERED CONTEXT")
    assert context_pos < marker_pos
    assert "Alice" in enhanced


@pytest.mark.unit
def test_inject_triggered_context_without_marker_appends_at_end(stub_logger, mock_config_service):
    """Test that triggered context is appended when no USER MESSAGE marker."""
    strategy = FallbackTriggerStrategy(
        logger=stub_logger,
        config_service=mock_config_service,
        use_trigger_system=True,
    )

    prompt = "Just a simple prompt without markers"
    triggered_context = "<!-- Triggered entity: Alice -->"

    enhanced = strategy._inject_triggered_context(prompt, triggered_context)

    # Should append at end
    assert enhanced.startswith("Just a simple prompt")
    assert "TRIGGERED CONTEXT" in enhanced
    assert "Alice" in enhanced


@pytest.mark.unit
def test_execute_logs_debug_when_trigger_system_disabled(stub_logger, mock_config_service):
    """Test that appropriate log messages are generated."""
    strategy = FallbackTriggerStrategy(
        logger=stub_logger,
        config_service=mock_config_service,
        use_trigger_system=False,
    )

    agent_context = AgentContext(
        message="Test",
        response_number=1,
        loaded_entities=[],
        characters_in_scene=[],
    )

    auto_context = AutomationContext(
        message="Test",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    strategy.execute(
        agent_context=agent_context,
        prompt="Test prompt",
        automation_context=auto_context,
    )

    # Should log debug about disabled trigger system
    logged_messages = [msg[1] if len(msg) > 1 else str(msg) for msg in stub_logger.messages]
    assert any("disabled" in message for message in logged_messages)
