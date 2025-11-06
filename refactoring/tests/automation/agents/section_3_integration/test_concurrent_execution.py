"""Integration tests for concurrent agent execution.

Tests thread safety, resource contention, and proper cleanup during concurrent execution.
"""

import pytest
import time
import threading
from unittest.mock import Mock
from refactoring.src.automation.services.agent_executor import AgentExecutor


class ThreadSafeCounter:
    """Thread-safe counter for tracking concurrent execution."""

    def __init__(self):
        self.count = 0
        self.max_concurrent = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.count += 1
            self.max_concurrent = max(self.max_concurrent, self.count)

    def decrement(self):
        with self.lock:
            self.count -= 1

    def get_max_concurrent(self):
        with self.lock:
            return self.max_concurrent


class ConcurrentAgent:
    """Agent that tracks concurrent execution."""

    counter = ThreadSafeCounter()

    def __init__(self, agent_id: str, delay: float = 0.1):
        self.agent_id = agent_id
        self.delay = delay
        self.executed = False

    def get_agent_id(self) -> str:
        return self.agent_id

    def execute(self, *args, **kwargs) -> str:
        self.executed = True
        ConcurrentAgent.counter.increment()
        try:
            time.sleep(self.delay)
            return f"result_{self.agent_id}"
        finally:
            ConcurrentAgent.counter.decrement()


@pytest.mark.integration
def test_multiple_agents_execute_concurrently(stub_logger):
    """Test that multiple agents actually run concurrently."""
    # Reset counter
    ConcurrentAgent.counter = ThreadSafeCounter()

    executor = AgentExecutor(logger=stub_logger, immediate_workers=4)

    # Create 4 agents that take 0.2s each
    agents = [ConcurrentAgent(f"agent{i}", delay=0.2) for i in range(4)]
    context = {"message": "test"}

    start_time = time.perf_counter()
    results = executor.run_immediate_agents(agents, context, timeout=5.0)
    duration = time.perf_counter() - start_time

    # All should complete
    assert len(results) == 4
    assert all(r.success for r in results)

    # Should take ~0.2s (concurrent), not ~0.8s (sequential)
    assert duration < 0.5

    # Should have had multiple agents running at once
    assert ConcurrentAgent.counter.get_max_concurrent() >= 2


@pytest.mark.integration
def test_executor_respects_worker_pool_size(stub_logger):
    """Test that executor doesn't exceed worker pool size."""
    # Reset counter
    ConcurrentAgent.counter = ThreadSafeCounter()

    executor = AgentExecutor(logger=stub_logger, immediate_workers=2)

    # Create 4 agents with delay
    agents = [ConcurrentAgent(f"agent{i}", delay=0.1) for i in range(4)]
    context = {"message": "test"}

    results = executor.run_immediate_agents(agents, context, timeout=5.0)

    assert len(results) == 4
    # With 2 workers, should never have more than 2 running concurrently
    assert ConcurrentAgent.counter.get_max_concurrent() <= 2


@pytest.mark.integration
def test_concurrent_execution_with_mixed_success_and_failure(stub_logger):
    """Test concurrent execution handles mixed results correctly."""

    class MixedAgent:
        def __init__(self, agent_id: str, should_fail: bool):
            self.agent_id = agent_id
            self.should_fail = should_fail

        def get_agent_id(self) -> str:
            return self.agent_id

        def execute(self, *args, **kwargs) -> str:
            time.sleep(0.05)
            if self.should_fail:
                raise RuntimeError(f"{self.agent_id} failed")
            return f"success_{self.agent_id}"

    executor = AgentExecutor(logger=stub_logger, immediate_workers=4)

    agents = [
        MixedAgent("success1", should_fail=False),
        MixedAgent("failure1", should_fail=True),
        MixedAgent("success2", should_fail=False),
        MixedAgent("failure2", should_fail=True),
    ]

    results = executor.run_immediate_agents(agents, {"message": "test"}, timeout=5.0)

    assert len(results) == 4

    # Check each result
    success_results = [r for r in results if r.success]
    failure_results = [r for r in results if not r.success]

    assert len(success_results) == 2
    assert len(failure_results) == 2


@pytest.mark.integration
def test_concurrent_immediate_and_background_execution(stub_logger):
    """Test that immediate and background executors can run concurrently."""

    class SlowAgent:
        def __init__(self, agent_id: str):
            self.agent_id = agent_id
            self.executed = False

        def get_agent_id(self) -> str:
            return self.agent_id

        def execute(self, *args, **kwargs) -> str:
            self.executed = True
            time.sleep(0.1)
            return f"result_{self.agent_id}"

    immediate_executor = AgentExecutor(logger=stub_logger, immediate_workers=2)
    background_executor = AgentExecutor(logger=stub_logger, background_workers=2)

    immediate_agents = [SlowAgent(f"immediate{i}") for i in range(2)]
    background_agents = [SlowAgent(f"background{i}") for i in range(2)]

    # Run both types concurrently
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        immediate_future = pool.submit(
            immediate_executor.run_immediate_agents,
            immediate_agents,
            {"message": "test"},
            5.0
        )
        background_future = pool.submit(
            background_executor.run_background_agents,
            background_agents,
            {"response_text": "test", "response_number": 1},
            10.0
        )

        immediate_results = immediate_future.result()
        background_results = background_future.result()

    # All agents should complete
    assert len(immediate_results) == 2
    assert len(background_results) == 2
    assert all(r.success for r in immediate_results)
    assert all(r.success for r in background_results)
    assert all(agent.executed for agent in immediate_agents)
    assert all(agent.executed for agent in background_agents)


@pytest.mark.integration
def test_executor_cleanup_after_concurrent_execution(stub_logger):
    """Test that executor properly cleans up resources after concurrent execution."""

    class ResourceAgent:
        active_count = 0
        lock = threading.Lock()

        def __init__(self, agent_id: str):
            self.agent_id = agent_id

        def get_agent_id(self) -> str:
            return self.agent_id

        def execute(self, *args, **kwargs) -> str:
            with ResourceAgent.lock:
                ResourceAgent.active_count += 1
            try:
                time.sleep(0.05)
                return f"result_{self.agent_id}"
            finally:
                with ResourceAgent.lock:
                    ResourceAgent.active_count -= 1

    ResourceAgent.active_count = 0

    executor = AgentExecutor(logger=stub_logger, immediate_workers=4)

    agents = [ResourceAgent(f"agent{i}") for i in range(4)]
    results = executor.run_immediate_agents(agents, {"message": "test"}, timeout=5.0)

    # All should complete
    assert len(results) == 4

    # After completion, all resources should be released
    assert ResourceAgent.active_count == 0


@pytest.mark.integration
def test_executor_handles_high_concurrency_load(stub_logger):
    """Test executor handles many agents concurrently."""

    class QuickAgent:
        def __init__(self, agent_id: str):
            self.agent_id = agent_id

        def get_agent_id(self) -> str:
            return self.agent_id

        def execute(self, *args, **kwargs) -> str:
            return f"result_{self.agent_id}"

    executor = AgentExecutor(logger=stub_logger, immediate_workers=8)

    # Create many agents
    agents = [QuickAgent(f"agent{i}") for i in range(20)]

    start_time = time.perf_counter()
    results = executor.run_immediate_agents(agents, {"message": "test"}, timeout=10.0)
    duration = time.perf_counter() - start_time

    # All should complete successfully
    assert len(results) == 20
    assert all(r.success for r in results)

    # Should complete quickly with concurrency
    assert duration < 2.0


@pytest.mark.integration
def test_concurrent_execution_preserves_agent_results(stub_logger):
    """Test that results from concurrent agents are not corrupted."""

    class UniqueResultAgent:
        def __init__(self, agent_id: str, value: int):
            self.agent_id = agent_id
            self.value = value

        def get_agent_id(self) -> str:
            return self.agent_id

        def execute(self, *args, **kwargs) -> str:
            # Simulate work
            time.sleep(0.05)
            # Return unique value
            return f"value_{self.value}"

    executor = AgentExecutor(logger=stub_logger, immediate_workers=4)

    agents = [UniqueResultAgent(f"agent{i}", i) for i in range(10)]
    results = executor.run_immediate_agents(agents, {"message": "test"}, timeout=5.0)

    assert len(results) == 10

    # Each result should have unique content
    contents = [r.content for r in results if r.success]
    assert len(contents) == 10
    assert len(set(contents)) == 10  # All unique

    # Check that each value appears exactly once
    for i in range(10):
        matching = [r for r in results if r.content == f"value_{i}"]
        assert len(matching) == 1
