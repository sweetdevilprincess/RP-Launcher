"""Unit tests for BackgroundAgentStrategy - Post-response analysis.

Tests the background agent strategy logic.
Note: Full agent execution tests require legacy agents to be refactored.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from refactoring.src.automation.contracts import AutomationContext, AgentContext
from refactoring.src.automation.agents.background_agent_strategy import BackgroundAgentStrategy


@pytest.mark.unit
def test_create_context_transforms_automation_to_agent_context(stub_logger):
    """Test that create_context transforms AutomationContext to AgentContext."""
    strategy = BackgroundAgentStrategy(
        logger=stub_logger,
        enabled_agents={},
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
    # Background agents extract characters from response, not message
    assert agent_context.characters_in_scene == []


@pytest.mark.unit
def test_execute_with_agents_unavailable_returns_original_prompt(stub_logger):
    """Test that execution returns original prompt when legacy agents unavailable."""
    with patch('refactoring.src.automation.agents.background_agent_strategy.AGENTS_AVAILABLE', False):
        strategy = BackgroundAgentStrategy(
            logger=stub_logger,
            enabled_agents={"response_analyzer": True},
        )

        agent_context = AgentContext(
            message="Test message",
            response_number=1,
            loaded_entities=[],
            characters_in_scene=[],
        )

        result = strategy.execute(
            agent_context=agent_context,
            prompt="Original prompt",
            automation_context=None,
        )

        assert result.success is True
        assert result.enhanced_prompt == "Original prompt"
        assert "not available" in result.error


@pytest.mark.unit
def test_strategy_initialization_with_custom_config(stub_logger):
    """Test strategy initialization with custom configuration."""
    enabled_agents = {
        "response_analyzer": True,
        "memory_creation": True,
        "relationship_analysis": False,
    }

    strategy = BackgroundAgentStrategy(
        logger=stub_logger,
        max_workers=8,
        enabled_agents=enabled_agents,
    )

    assert strategy._max_workers == 8
    assert strategy._enabled_agents == enabled_agents
    assert strategy._logger == stub_logger


@pytest.mark.unit
def test_prepare_agent_tasks_returns_empty_when_agents_unavailable(stub_logger):
    """Test that _prepare_agent_tasks returns empty list when agents unavailable."""
    strategy = BackgroundAgentStrategy(
        logger=stub_logger,
        enabled_agents={
            "response_analyzer": True,
        },
    )

    agent_context = AgentContext(
        message="Test",
        response_number=1,
        loaded_entities=["Alice"],
        characters_in_scene=["Alice"],
    )

    # When AGENTS_AVAILABLE=False (default in test env), should return empty list
    tasks = strategy._prepare_agent_tasks(agent_context)

    assert len(tasks) == 0
    assert tasks == []


@pytest.mark.unit
def test_background_agents_do_not_modify_prompt(stub_logger, tmp_path):
    """Test that background agents return the original prompt unchanged."""
    # Background agents run post-response and don't modify the prompt
    strategy = BackgroundAgentStrategy(
        logger=stub_logger,
        enabled_agents={},  # No agents enabled
    )

    auto_context = AutomationContext(
        message="Test message",
        rp_dir=tmp_path,
        response_count=1,
        loaded_entities=["Alice"],
    )

    agent_context = strategy.create_context(auto_context)

    result = strategy.execute(
        agent_context=agent_context,
        prompt="Original prompt",
        automation_context=auto_context,
    )

    assert result.success is True
    # Background agents should NOT modify the prompt
    assert result.enhanced_prompt == "Original prompt"


@pytest.mark.unit
def test_execute_logs_info_when_agents_unavailable(stub_logger):
    """Test that appropriate log messages are generated."""
    with patch('refactoring.src.automation.agents.background_agent_strategy.AGENTS_AVAILABLE', False):
        strategy = BackgroundAgentStrategy(
            logger=stub_logger,
            enabled_agents={"response_analyzer": True},
        )

        agent_context = AgentContext(
            message="Test",
            response_number=1,
            loaded_entities=[],
            characters_in_scene=[],
        )

        strategy.execute(
            agent_context=agent_context,
            prompt="Test prompt",
            automation_context=None,
        )

        # Should log warning about unavailable agents
        logged_messages = [msg[1] if len(msg) > 1 else str(msg) for msg in stub_logger.messages]
        assert any("unavailable" in message for message in logged_messages)


@pytest.mark.unit
def test_strategy_returns_success_when_no_agents_enabled(stub_logger, tmp_path):
    """Test that strategy returns success even when no agents are enabled."""
    strategy = BackgroundAgentStrategy(
        logger=stub_logger,
        enabled_agents={},  # No agents enabled
    )

    auto_context = AutomationContext(
        message="Test message",
        rp_dir=tmp_path,
        response_count=1,
        loaded_entities=["Alice"],
    )

    agent_context = strategy.create_context(auto_context)

    result = strategy.execute(
        agent_context=agent_context,
        prompt="Original prompt",
        automation_context=auto_context,
    )

    assert result.success is True
    assert result.enhanced_prompt == "Original prompt"
