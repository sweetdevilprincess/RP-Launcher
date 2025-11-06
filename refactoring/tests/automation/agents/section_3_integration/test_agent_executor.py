"""Integration tests for AgentExecutor - Concurrent execution with retry and timeout.

Tests the agent executor's integration with thread pools, retry policies, and timeout enforcement.
"""

import pytest
import time
from unittest.mock import Mock
from refactoring.src.automation.services.agent_executor import AgentExecutor
from refactoring.src.automation.contracts import AgentExecutionResult


class MockSuccessAgent:
    """Mock agent that succeeds immediately."""

    def __init__(self, agent_id: str, content: str = "success"):
        self.agent_id = agent_id
        self.content = content
        self.executed = False

    def get_agent_id(self) -> str:
        return self.agent_id

    def execute(self, *args, **kwargs) -> str:
        self.executed = True
        return self.content


class MockSlowAgent:
    """Mock agent that takes time to execute."""

    def __init__(self, agent_id: str, delay: float = 0.1):
        self.agent_id = agent_id
        self.delay = delay
        self.executed = False

    def get_agent_id(self) -> str:
        return self.agent_id

    def execute(self, *args, **kwargs) -> str:
        self.executed = True
        time.sleep(self.delay)
        return f"result after {self.delay}s"


class MockFailingAgent:
    """Mock agent that always fails."""

    def __init__(self, agent_id: str, error_message: str = "Agent failed"):
        self.agent_id = agent_id
        self.error_message = error_message
        self.executed = False

    def get_agent_id(self) -> str:
        return self.agent_id

    def execute(self, *args, **kwargs) -> str:
        self.executed = True
        raise RuntimeError(self.error_message)


@pytest.mark.integration
def test_executor_runs_single_agent_successfully(stub_logger):
    """Test that executor successfully runs a single agent."""
    executor = AgentExecutor(logger=stub_logger, immediate_workers=1)

    agent = MockSuccessAgent("test_agent", "test_result")
    context = {"message": "test"}

    results = executor.run_immediate_agents([agent], context, timeout=5.0)

    assert len(results) == 1
    assert results[0].success is True
    assert results[0].agent_id == "test_agent"
    assert results[0].content == "test_result"
    assert agent.executed


@pytest.mark.integration
def test_executor_runs_multiple_agents_concurrently(stub_logger):
    """Test that executor runs multiple agents in parallel."""
    executor = AgentExecutor(logger=stub_logger, immediate_workers=4)

    agents = [
        MockSuccessAgent("agent1", "result1"),
        MockSuccessAgent("agent2", "result2"),
        MockSuccessAgent("agent3", "result3"),
    ]
    context = {"message": "test"}

    start_time = time.perf_counter()
    results = executor.run_immediate_agents(agents, context, timeout=5.0)
    duration = time.perf_counter() - start_time

    # All agents should complete
    assert len(results) == 3
    assert all(r.success for r in results)
    assert all(agent.executed for agent in agents)

    # Should be fast (concurrent, not sequential)
    assert duration < 1.0


@pytest.mark.integration
def test_executor_handles_agent_failure_gracefully(stub_logger):
    """Test that executor continues when one agent fails."""
    executor = AgentExecutor(logger=stub_logger, immediate_workers=2)

    agents = [
        MockSuccessAgent("good_agent", "success"),
        MockFailingAgent("bad_agent", "Failure"),
    ]
    context = {"message": "test"}

    results = executor.run_immediate_agents(agents, context, timeout=5.0)

    assert len(results) == 2

    # Find results by agent_id
    good_result = next(r for r in results if r.agent_id == "good_agent")
    bad_result = next(r for r in results if r.agent_id == "bad_agent")

    assert good_result.success is True
    assert good_result.content == "success"

    assert bad_result.success is False
    assert "Failure" in bad_result.error


@pytest.mark.integration
def test_executor_enforces_global_timeout(stub_logger):
    """Test that executor enforces global timeout for all agents."""
    executor = AgentExecutor(logger=stub_logger, immediate_workers=2)

    # Create agents that take longer than timeout
    agents = [
        MockSlowAgent("slow1", delay=2.0),
        MockSlowAgent("slow2", delay=2.0),
    ]
    context = {"message": "test"}

    results = executor.run_immediate_agents(agents, context, timeout=0.5)

    # Should timeout and return partial/error results
    assert len(results) == 2

    # At least some should have timeout errors
    timeout_results = [r for r in results if not r.success and "timeout" in r.error.lower()]
    assert len(timeout_results) > 0


@pytest.mark.integration
def test_executor_tracks_timing_metrics(stub_logger):
    """Test that executor tracks duration metrics for each agent."""
    executor = AgentExecutor(logger=stub_logger, immediate_workers=1)

    agent = MockSuccessAgent("test_agent")
    context = {"message": "test"}

    results = executor.run_immediate_agents([agent], context, timeout=5.0)

    assert len(results) == 1
    assert results[0].duration_ms is not None
    assert results[0].duration_ms >= 0


@pytest.mark.integration
def test_executor_with_empty_agent_list(stub_logger):
    """Test that executor handles empty agent list gracefully."""
    executor = AgentExecutor(logger=stub_logger, immediate_workers=1)

    results = executor.run_immediate_agents([], {"message": "test"}, timeout=5.0)

    assert len(results) == 0


@pytest.mark.integration
def test_executor_runs_background_agents(stub_logger):
    """Test that executor can run background agents with different pool."""
    executor = AgentExecutor(logger=stub_logger, background_workers=4)

    agents = [
        MockSuccessAgent("bg_agent1", "bg_result1"),
        MockSuccessAgent("bg_agent2", "bg_result2"),
    ]
    context = {"response_text": "test response", "response_number": 1}

    results = executor.run_background_agents(agents, context, timeout=10.0)

    assert len(results) == 2
    assert all(r.success for r in results)


@pytest.mark.integration
def test_executor_logs_execution_events(stub_logger):
    """Test that executor logs start and complete events."""
    executor = AgentExecutor(logger=stub_logger, immediate_workers=1)

    agent = MockSuccessAgent("test_agent")
    executor.run_immediate_agents([agent], {"message": "test"}, timeout=5.0)

    # Check logged events
    logged_messages = [msg[1] if len(msg) > 1 else str(msg) for msg in stub_logger.messages]
    assert any("start" in msg for msg in logged_messages)
    assert any("complete" in msg for msg in logged_messages)


@pytest.mark.integration
def test_executor_string_representation(stub_logger):
    """Test executor string representation."""
    executor = AgentExecutor(
        logger=stub_logger,
        immediate_workers=4,
        background_workers=6
    )

    repr_str = repr(executor)

    assert "AgentExecutor" in repr_str
    assert "immediate_workers=4" in repr_str
    assert "background_workers=6" in repr_str
