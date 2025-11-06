"""Integration tests for retry configuration with AgentExecutor.

Tests that retry policies are properly configured in the executor.
Note: Full retry behavior requires network exceptions (TimeoutError, ConnectionError).
"""

import pytest
from refactoring.src.automation.services.agent_executor import AgentExecutor
from refactoring.src.infrastructure.retry import RetryPolicy


@pytest.mark.integration
def test_executor_initializes_with_retry_policy(stub_logger):
    """Test that executor can be initialized with a retry policy."""
    retry_policy = RetryPolicy(
        max_attempts=3,
        initial_delay_seconds=0.01,
        max_delay_seconds=0.1,
    )

    executor = AgentExecutor(
        logger=stub_logger,
        retry_policy=retry_policy,
        immediate_workers=1,
    )

    assert executor.retry_policy is not None
    assert executor.retry_executor is not None
    assert executor.retry_policy.max_attempts == 3


@pytest.mark.integration
def test_executor_initializes_without_retry_policy(stub_logger):
    """Test that executor can be initialized without a retry policy."""
    executor = AgentExecutor(
        logger=stub_logger,
        retry_policy=None,
        immediate_workers=1,
    )

    assert executor.retry_policy is None
    assert executor.retry_executor is None


@pytest.mark.integration
def test_executor_uses_different_retry_policies_for_immediate_and_background(stub_logger):
    """Test that different executors can have different retry policies."""
    immediate_policy = RetryPolicy(
        max_attempts=2,
        initial_delay_seconds=0.5,
    )

    background_policy = RetryPolicy(
        max_attempts=5,
        initial_delay_seconds=2.0,
    )

    immediate_executor = AgentExecutor(
        logger=stub_logger,
        retry_policy=immediate_policy,
        immediate_workers=4,
    )

    background_executor = AgentExecutor(
        logger=stub_logger,
        retry_policy=background_policy,
        background_workers=6,
    )

    assert immediate_executor.retry_policy.max_attempts == 2
    assert background_executor.retry_policy.max_attempts == 5


@pytest.mark.integration
def test_executor_repr_shows_retry_status(stub_logger):
    """Test that executor repr shows retry configuration status."""
    # With retry
    executor_with_retry = AgentExecutor(
        logger=stub_logger,
        retry_policy=RetryPolicy(max_attempts=3),
        immediate_workers=1,
    )

    repr_with = repr(executor_with_retry)
    assert "retry=True" in repr_with

    # Without retry
    executor_without_retry = AgentExecutor(
        logger=stub_logger,
        retry_policy=None,
        immediate_workers=1,
    )

    repr_without = repr(executor_without_retry)
    assert "retry=False" in repr_without
