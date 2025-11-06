"""Unit tests for AgentRunner - Strategy execution coordinator.

Tests the agent runner's logic for executing strategies and accumulating results.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from refactoring.src.automation.contracts import AutomationContext, AgentContext, AutomationResult
from refactoring.src.automation.services.agent_runner import AgentRunner


class MockStrategy:
    """Mock strategy for testing."""

    def __init__(self, name: str, success: bool = True, enhanced_prompt: str | None = None, cached_context: str | None = None, error: str | None = None):
        self.name = name
        self.success = success
        self.enhanced_prompt_value = enhanced_prompt
        self.cached_context_value = cached_context
        self.error_value = error
        self.create_context_called = False
        self.execute_called = False

    def create_context(self, context: AutomationContext) -> AgentContext:
        """Create agent context from automation context."""
        self.create_context_called = True
        return AgentContext(
            message=context.message,
            response_number=context.response_count,
            loaded_entities=context.loaded_entities,
            characters_in_scene=context.loaded_entities,
        )

    def execute(self, agent_context: AgentContext, prompt: str, automation_context: AutomationContext) -> AutomationResult:
        """Execute strategy and return result."""
        self.execute_called = True
        return AutomationResult(
            success=self.success,
            enhanced_prompt=self.enhanced_prompt_value or prompt,
            cached_context=self.cached_context_value,
            error=self.error_value,
        )


@pytest.mark.unit
def test_runner_with_no_strategies_returns_original_prompt(stub_logger):
    """Test that runner returns original prompt when no strategies."""
    runner = AgentRunner(logger=stub_logger, strategies=[])

    context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    result = runner.run(context, "Original prompt")

    assert result.success is True
    assert result.enhanced_prompt == "Original prompt"


@pytest.mark.unit
def test_runner_executes_single_strategy(stub_logger):
    """Test that runner executes a single strategy."""
    strategy = MockStrategy("test_strategy", enhanced_prompt="Enhanced prompt")
    runner = AgentRunner(logger=stub_logger, strategies=[strategy])

    context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    result = runner.run(context, "Original prompt")

    assert strategy.create_context_called
    assert strategy.execute_called
    assert result.success is True
    assert result.enhanced_prompt == "Enhanced prompt"


@pytest.mark.unit
def test_runner_executes_strategies_in_order(stub_logger):
    """Test that runner executes strategies in order and accumulates results."""
    strategy1 = MockStrategy("strategy1", enhanced_prompt="Prompt 1")
    strategy2 = MockStrategy("strategy2", enhanced_prompt="Prompt 2")

    runner = AgentRunner(logger=stub_logger, strategies=[strategy1, strategy2])

    context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    result = runner.run(context, "Original prompt")

    # Both should be called
    assert strategy1.execute_called
    assert strategy2.execute_called

    # Final prompt should be from strategy2 (last to run)
    assert result.enhanced_prompt == "Prompt 2"


@pytest.mark.unit
def test_runner_accumulates_cached_context(stub_logger):
    """Test that runner accumulates cached context from all strategies."""
    strategy1 = MockStrategy("strategy1", cached_context="Context 1")
    strategy2 = MockStrategy("strategy2", cached_context="Context 2")

    runner = AgentRunner(logger=stub_logger, strategies=[strategy1, strategy2])

    context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    result = runner.run(context, "Original prompt")

    # Should accumulate cached context from both strategies
    assert result.cached_context == "Context 1Context 2"


@pytest.mark.unit
def test_runner_continues_on_strategy_failure(stub_logger):
    """Test that runner continues executing strategies after one fails."""
    strategy1 = MockStrategy("strategy1", success=False, error="Strategy 1 failed")
    strategy2 = MockStrategy("strategy2", success=True, enhanced_prompt="Success")

    runner = AgentRunner(logger=stub_logger, strategies=[strategy1, strategy2])

    context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    result = runner.run(context, "Original prompt")

    # Both should be executed
    assert strategy1.execute_called
    assert strategy2.execute_called

    # Should report success since strategy2 succeeded
    assert result.success is True
    assert result.enhanced_prompt == "Success"


@pytest.mark.unit
def test_runner_continues_on_strategy_exception(stub_logger):
    """Test that runner continues executing strategies when one raises exception."""
    class ExceptionStrategy:
        def create_context(self, context):
            return AgentContext(message=context.message, response_number=1)

        def execute(self, agent_context, prompt, automation_context):
            raise ValueError("Strategy exploded")

    exception_strategy = ExceptionStrategy()
    success_strategy = MockStrategy("success", enhanced_prompt="Success")

    runner = AgentRunner(logger=stub_logger, strategies=[exception_strategy, success_strategy])

    context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    result = runner.run(context, "Original prompt")

    # Should continue to success_strategy
    assert success_strategy.execute_called
    assert result.success is True
    assert result.enhanced_prompt == "Success"


@pytest.mark.unit
def test_runner_reports_failure_when_all_strategies_fail(stub_logger):
    """Test that runner reports failure when all strategies fail."""
    strategy1 = MockStrategy("strategy1", success=False, error="Error 1")
    strategy2 = MockStrategy("strategy2", success=False, error="Error 2")

    runner = AgentRunner(logger=stub_logger, strategies=[strategy1, strategy2])

    context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    result = runner.run(context, "Original prompt")

    assert result.success is False
    assert result.error == "Error 2"  # Last error


@pytest.mark.unit
def test_runner_logs_strategy_execution(stub_logger):
    """Test that runner logs strategy execution events."""
    strategy = MockStrategy("test_strategy", enhanced_prompt="Enhanced")

    runner = AgentRunner(logger=stub_logger, strategies=[strategy])

    context = AutomationContext(
        message="Test message",
        rp_dir=Path("/test/rp"),
        response_count=1,
    )

    runner.run(context, "Original prompt")

    # Should log start, success, and complete
    logged_messages = [msg[1] if len(msg) > 1 else str(msg) for msg in stub_logger.messages]
    assert any("start" in message for message in logged_messages)
    assert any("success" in message for message in logged_messages)
    assert any("complete" in message for message in logged_messages)
