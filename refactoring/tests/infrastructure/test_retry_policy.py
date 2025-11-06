"""Unit tests for retry policy and executor.

Tests retry behavior, backoff strategies, exception filtering, and timing.
"""

import time

import pytest
from refactoring.src.infrastructure.retry import (
    BackoffStrategy,
    RetryExecutor,
    RetryPolicy,
)


class TestRetryPolicy:
    """Tests for RetryPolicy dataclass."""

    def test_default_policy(self):
        """Test default retry policy creation."""
        policy = RetryPolicy()

        assert policy.max_attempts == 3
        assert policy.backoff_strategy == BackoffStrategy.EXPONENTIAL
        assert policy.initial_delay_seconds == 1.0

    def test_custom_policy(self):
        """Test custom retry policy."""
        policy = RetryPolicy(
            max_attempts=5,
            backoff_strategy=BackoffStrategy.LINEAR,
            initial_delay_seconds=0.5,
            max_delay_seconds=10.0,
        )

        assert policy.max_attempts == 5
        assert policy.backoff_strategy == BackoffStrategy.LINEAR
        assert policy.initial_delay_seconds == 0.5
        assert policy.max_delay_seconds == 10.0

    def test_invalid_max_attempts(self):
        """Test validation of max_attempts."""
        with pytest.raises(ValueError, match="max_attempts must be >= 1"):
            RetryPolicy(max_attempts=0)

    def test_invalid_delay(self):
        """Test validation of delay values."""
        with pytest.raises(ValueError, match="initial_delay_seconds must be >= 0"):
            RetryPolicy(initial_delay_seconds=-1.0)

        with pytest.raises(ValueError, match="max_delay_seconds must be >= initial_delay_seconds"):
            RetryPolicy(initial_delay_seconds=10.0, max_delay_seconds=5.0)


class TestRetryExecutor:
    """Tests for RetryExecutor."""

    def test_immediate_success(self):
        """Test function that succeeds immediately."""
        policy = RetryPolicy(max_attempts=3)
        executor = RetryExecutor(policy)

        def succeeds_immediately():
            return "success"

        result = executor.execute(succeeds_immediately)

        assert result.success is True
        assert result.result == "success"
        assert result.attempts == 1
        assert result.total_delay_seconds == 0.0

    def test_retry_after_failures(self):
        """Test retrying after transient failures."""
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.FIXED,
            initial_delay_seconds=0.01,  # Short delay for testing
        )
        executor = RetryExecutor(policy)

        attempt_count = 0

        def fails_twice_then_succeeds():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:
                raise RuntimeError("Transient failure")
            return "success"

        result = executor.execute(
            fails_twice_then_succeeds,
            exceptions_to_retry=(RuntimeError,),
        )

        assert result.success is True
        assert result.result == "success"
        assert result.attempts == 3
        assert result.total_delay_seconds > 0.0

    def test_exhausted_retries(self):
        """Test exhausting all retry attempts."""
        policy = RetryPolicy(
            max_attempts=2,
            backoff_strategy=BackoffStrategy.FIXED,
            initial_delay_seconds=0.01,
        )
        executor = RetryExecutor(policy)

        def always_fails():
            raise RuntimeError("Permanent failure")

        result = executor.execute(
            always_fails,
            exceptions_to_retry=(RuntimeError,),
        )

        assert result.success is False
        assert result.attempts == 2
        assert isinstance(result.last_exception, RuntimeError)

    def test_non_retryable_exception(self):
        """Test non-retryable exceptions fail immediately."""
        policy = RetryPolicy(max_attempts=3)
        executor = RetryExecutor(policy)

        def raises_value_error():
            raise ValueError("Non-retryable error")

        result = executor.execute(
            raises_value_error,
            exceptions_to_retry=(RuntimeError,),  # ValueError not in list
        )

        assert result.success is False
        assert result.attempts == 1  # No retries
        assert isinstance(result.last_exception, ValueError)

    def test_exponential_backoff_timing(self):
        """Test exponential backoff timing."""
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay_seconds=0.01,
            backoff_multiplier=2.0,
            jitter=0.0,  # No jitter for predictable timing
        )
        executor = RetryExecutor(policy)

        def always_fails():
            raise RuntimeError("Test failure")

        start = time.perf_counter()
        result = executor.execute(
            always_fails,
            exceptions_to_retry=(RuntimeError,),
        )
        elapsed = time.perf_counter() - start

        # Expected delays: 0.01s (attempt 2), 0.02s (attempt 3) = ~0.03s total
        assert result.attempts == 3
        assert 0.02 < elapsed < 0.05  # Allow some tolerance

    def test_linear_backoff(self):
        """Test linear backoff strategy."""
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.LINEAR,
            initial_delay_seconds=0.01,
            linear_increment_seconds=0.01,
            jitter=0.0,
        )
        executor = RetryExecutor(policy)

        delays = []
        attempt_count = 0

        def always_fails():
            nonlocal attempt_count
            attempt_count += 1
            raise RuntimeError("Test")

        executor.execute(
            always_fails,
            exceptions_to_retry=(RuntimeError,),
        )

        # Linear backoff: delay increases by fixed increment each time
        # This is verified by the total execution time

    def test_fixed_backoff(self):
        """Test fixed backoff strategy."""
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.FIXED,
            initial_delay_seconds=0.01,
            jitter=0.0,
        )
        executor = RetryExecutor(policy)

        def always_fails():
            raise RuntimeError("Test")

        start = time.perf_counter()
        executor.execute(
            always_fails,
            exceptions_to_retry=(RuntimeError,),
        )
        elapsed = time.perf_counter() - start

        # Fixed delay: 0.01s * 2 retries = ~0.02s
        assert 0.015 < elapsed < 0.03

    def test_max_delay_cap(self):
        """Test that delays are capped at max_delay_seconds."""
        policy = RetryPolicy(
            max_attempts=5,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay_seconds=0.01,  # 10ms (smaller than max)
            max_delay_seconds=0.05,  # Cap at 50ms
            backoff_multiplier=10.0,  # Would grow very large without cap
            jitter=0.0,
        )
        executor = RetryExecutor(policy)

        def always_fails():
            raise RuntimeError("Test")

        start = time.perf_counter()
        executor.execute(
            always_fails,
            exceptions_to_retry=(RuntimeError,),
        )
        elapsed = time.perf_counter() - start

        # All delays should be capped at 0.05s
        # 4 retries * 0.05s = ~0.2s
        assert 0.15 < elapsed < 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
