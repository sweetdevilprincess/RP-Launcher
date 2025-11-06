"""Unit tests for ImmediateAgentStrategy - Pre-response context gathering.

Tests the immediate agent strategy logic.
Note: Full agent execution tests require legacy agents to be refactored.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from refactoring.src.automation.contracts import AutomationContext, AgentContext
from refactoring.src.automation.agents.immediate_agent_strategy import ImmediateAgentStrategy


@pytest.mark.unit
def test_create_context_transforms_automation_to_agent_context(stub_logger):
    """Test that create_context transforms AutomationContext to AgentContext."""
    strategy = ImmediateAgentStrategy(
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
    assert agent_context.characters_in_scene == ["Alice", "Bob"]  # Uses loaded_entities


@pytest.mark.unit
def test_execute_with_agents_unavailable_returns_original_prompt(stub_logger):
    """Test that execution returns original prompt when legacy agents unavailable."""
    # When AGENTS_AVAILABLE is False (default in test env), should return original prompt
    with patch('refactoring.src.automation.agents.immediate_agent_strategy.AGENTS_AVAILABLE', False):
        strategy = ImmediateAgentStrategy(
            logger=stub_logger,
            enabled_agents={"quick_entity_analysis": {"enabled": True}},
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
        "quick_entity_analysis": {"enabled": True, "timeout_seconds": 3},
        "fact_extraction": {"enabled": True, "timeout_seconds": 5},
        "memory_extraction": {"enabled": False},
    }

    strategy = ImmediateAgentStrategy(
        logger=stub_logger,
        max_workers=8,
        enabled_agents=enabled_agents,
        default_timeout=10,
    )

    assert strategy._max_workers == 8
    assert strategy._default_timeout == 10
    assert strategy._enabled_agents == enabled_agents
    assert strategy._logger == stub_logger


@pytest.mark.unit
def test_prepare_agent_tasks_returns_empty_when_agents_unavailable(stub_logger):
    """Test that _prepare_agent_tasks returns empty list when agents unavailable."""
    strategy = ImmediateAgentStrategy(
        logger=stub_logger,
        enabled_agents={
            "quick_entity_analysis": {"enabled": True},
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
def test_format_agent_results_with_successful_results(stub_logger):
    """Test formatting successful agent results."""
    strategy = ImmediateAgentStrategy(
        logger=stub_logger,
        enabled_agents={},
    )

    results = {
        "agent1": {
            "success": True,
            "content": '{"entities": ["Alice", "Bob"]}',
        },
        "agent2": {
            "success": True,
            "content": '{"facts": ["tall", "brave"]}',
        },
    }

    formatted = strategy._format_agent_results(results)

    assert "<!-- agent1 -->" in formatted
    assert '{"entities": ["Alice", "Bob"]}' in formatted
    assert "<!-- agent2 -->" in formatted
    assert '{"facts": ["tall", "brave"]}' in formatted


@pytest.mark.unit
def test_format_agent_results_skips_failed_results(stub_logger):
    """Test that failed results are excluded from formatted output."""
    strategy = ImmediateAgentStrategy(
        logger=stub_logger,
        enabled_agents={},
    )

    results = {
        "agent1": {
            "success": True,
            "content": '{"data": "good"}',
        },
        "agent2": {
            "success": False,
            "error": "Agent failed",
        },
    }

    formatted = strategy._format_agent_results(results)

    assert "<!-- agent1 -->" in formatted
    assert '{"data": "good"}' in formatted
    assert "agent2" not in formatted
    assert "Agent failed" not in formatted


@pytest.mark.unit
def test_format_agent_results_skips_empty_content(stub_logger):
    """Test that results with no content are excluded."""
    strategy = ImmediateAgentStrategy(
        logger=stub_logger,
        enabled_agents={},
    )

    results = {
        "agent1": {
            "success": True,
            "content": '{"data": "exists"}',
        },
        "agent2": {
            "success": True,
            "content": "",  # Empty content
        },
    }

    formatted = strategy._format_agent_results(results)

    assert "<!-- agent1 -->" in formatted
    assert "agent2" not in formatted


@pytest.mark.unit
def test_format_agent_results_with_empty_dict_returns_empty_string(stub_logger):
    """Test that empty results dict returns empty string."""
    strategy = ImmediateAgentStrategy(
        logger=stub_logger,
        enabled_agents={},
    )

    formatted = strategy._format_agent_results({})

    assert formatted == ""


@pytest.mark.unit
def test_inject_agent_context_with_user_message_marker(stub_logger):
    """Test that agent context is injected before USER MESSAGE marker."""
    strategy = ImmediateAgentStrategy(
        logger=stub_logger,
        enabled_agents={},
    )

    prompt = """Some context here...

========== USER MESSAGE ==========
User's message here
"""

    agent_context = "Agent analysis results"

    enhanced = strategy._inject_agent_context(prompt, agent_context)

    # Agent context should be before USER MESSAGE marker
    marker_pos = enhanced.find("========== USER MESSAGE ==========")
    context_pos = enhanced.find("IMMEDIATE AGENT CONTEXT")
    assert context_pos < marker_pos
    assert "Agent analysis results" in enhanced


@pytest.mark.unit
def test_inject_agent_context_without_marker_appends_at_end(stub_logger):
    """Test that agent context is appended when no USER MESSAGE marker."""
    strategy = ImmediateAgentStrategy(
        logger=stub_logger,
        enabled_agents={},
    )

    prompt = "Just a simple prompt without markers"
    agent_context = "Agent analysis results"

    enhanced = strategy._inject_agent_context(prompt, agent_context)

    # Should append at end
    assert enhanced.startswith("Just a simple prompt")
    assert "IMMEDIATE AGENT CONTEXT" in enhanced
    assert "Agent analysis results" in enhanced


@pytest.mark.unit
def test_execute_logs_warning_when_agents_unavailable(stub_logger):
    """Test that appropriate log messages are generated."""
    with patch('refactoring.src.automation.agents.immediate_agent_strategy.AGENTS_AVAILABLE', False):
        strategy = ImmediateAgentStrategy(
            logger=stub_logger,
            enabled_agents={"quick_entity_analysis": {"enabled": True}},
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
        # stub_logger.messages is a list of tuples (level, message, context)
        logged_messages = [msg[1] if len(msg) > 1 else str(msg) for msg in stub_logger.messages]
        assert any("unavailable" in message for message in logged_messages)


@pytest.mark.unit
def test_strategy_returns_original_prompt_when_no_agents_enabled(stub_logger, tmp_path):
    """Test that original prompt is returned when no agents are enabled."""
    # Even when agents are unavailable, should return original prompt gracefully
    strategy = ImmediateAgentStrategy(
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
    assert result.cached_context == ""
