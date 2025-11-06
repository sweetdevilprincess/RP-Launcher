"""Retry policy and backoff strategies for transient failure handling.

This module provides configurable retry logic with multiple backoff strategies.
Used throughout the system for handling transient network failures, timeouts,
and rate limiting.

Example:
    policy = RetryPolicy(
        max_attempts=3,
        backoff_strategy=BackoffStrategy.EXPONENTIAL,
        initial_delay_seconds=1.0,
        max_delay_seconds=30.0
    )
    executor = RetryExecutor(policy, logger=my_logger)

    result = executor.execute(
        my_function,
        args=(arg1, arg2),
        exceptions_to_retry=(TimeoutError, ConnectionError)
    )
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ...shared.interfaces import LoggingService


class BackoffStrategy(Enum):
    """Backoff strategy for retry delays."""

    EXPONENTIAL = "exponential"  # delay = initial * (2 ** attempt)
    LINEAR = "linear"  # delay = initial + (increment * attempt)
    FIXED = "fixed"  # delay = constant


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of attempts (including first try)
        backoff_strategy: Strategy for calculating delays between retries
        initial_delay_seconds: Initial delay before first retry
        max_delay_seconds: Maximum delay cap for exponential backoff
        backoff_multiplier: Multiplier for exponential strategy (default 2.0)
        linear_increment_seconds: Increment for linear strategy
        jitter: Add randomness to delays (0.0 = no jitter, 1.0 = 100% jitter)
    """

    max_attempts: int = 3
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    linear_increment_seconds: float = 1.0
    jitter: float = 0.1

    def __post_init__(self) -> None:
        """Validate retry policy configuration."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds must be >= 0")
        if self.max_delay_seconds < self.initial_delay_seconds:
            raise ValueError("max_delay_seconds must be >= initial_delay_seconds")
        if self.backoff_multiplier <= 0:
            raise ValueError("backoff_multiplier must be > 0")
        if self.jitter < 0 or self.jitter > 1:
            raise ValueError("jitter must be between 0 and 1")


@dataclass
class RetryResult:
    """Result of a retry execution.

    Attributes:
        success: Whether the operation succeeded
        result: The result value if successful
        attempts: Number of attempts made
        total_delay_seconds: Total time spent in delays
        last_exception: The last exception encountered (if failed)
    """

    success: bool
    result: Any = None
    attempts: int = 0
    total_delay_seconds: float = 0.0
    last_exception: Exception | None = None


class RetryExecutor:
    """Executes functions with configurable retry logic.

    This class handles retry execution with exponential/linear/fixed backoff,
    jitter, and exception filtering. Logs retry attempts for debugging.

    Example:
        executor = RetryExecutor(policy, logger=my_logger)

        def risky_operation():
            response = requests.get(url, timeout=10)
            return response.json()

        result = executor.execute(
            risky_operation,
            exceptions_to_retry=(requests.Timeout, requests.ConnectionError)
        )
    """

    def __init__(self, policy: RetryPolicy, logger: LoggingService | None = None) -> None:
        """Initialize retry executor.

        Args:
            policy: Retry policy configuration
            logger: Optional logging service for retry events
        """
        self.policy = policy
        self.logger = logger

    def execute(
        self,
        func: Callable[..., Any],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        exceptions_to_retry: tuple[type[Exception], ...] = (Exception,),
    ) -> RetryResult:
        """Execute function with retry logic.

        Args:
            func: Function to execute
            args: Positional arguments for function
            kwargs: Keyword arguments for function
            exceptions_to_retry: Tuple of exception types that trigger retries

        Returns:
            RetryResult with success status and result/exception
        """
        if kwargs is None:
            kwargs = {}

        attempts = 0
        total_delay = 0.0
        last_exception = None

        for attempt in range(1, self.policy.max_attempts + 1):
            attempts = attempt

            try:
                # Log attempt
                if self.logger and attempt > 1:
                    self.logger.debug(
                        "retry_executor.attempt",
                        context={
                            "attempt": attempt,
                            "max_attempts": self.policy.max_attempts,
                            "function": func.__name__,
                        },
                    )

                # Execute function
                result = func(*args, **kwargs)

                # Success - log and return
                if self.logger and attempt > 1:
                    self.logger.info(
                        "retry_executor.success",
                        context={
                            "attempts": attempts,
                            "total_delay_seconds": round(total_delay, 2),
                            "function": func.__name__,
                        },
                    )

                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_delay_seconds=total_delay,
                )

            except exceptions_to_retry as exc:
                last_exception = exc

                # Check if we should retry
                if attempt < self.policy.max_attempts:
                    # Calculate delay
                    delay = self._calculate_delay(attempt)
                    total_delay += delay

                    # Log retry decision
                    if self.logger:
                        self.logger.warning(
                            "retry_executor.retry",
                            context={
                                "attempt": attempt,
                                "max_attempts": self.policy.max_attempts,
                                "exception": str(exc),
                                "exception_type": type(exc).__name__,
                                "delay_seconds": round(delay, 2),
                                "function": func.__name__,
                            },
                        )

                    # Sleep before next attempt
                    time.sleep(delay)
                # Final attempt failed - log and return failure
                elif self.logger:
                    self.logger.error(
                        "retry_executor.failed",
                        context={
                            "attempts": attempts,
                            "total_delay_seconds": round(total_delay, 2),
                            "final_exception": str(exc),
                            "exception_type": type(exc).__name__,
                            "function": func.__name__,
                        },
                    )

            except Exception as exc:
                # Non-retryable exception - immediate failure
                if self.logger:
                    self.logger.error(
                        "retry_executor.non_retryable_exception",
                        context={
                            "attempts": attempts,
                            "exception": str(exc),
                            "exception_type": type(exc).__name__,
                            "function": func.__name__,
                        },
                    )

                return RetryResult(
                    success=False,
                    attempts=attempts,
                    total_delay_seconds=total_delay,
                    last_exception=exc,
                )

        # All attempts exhausted
        return RetryResult(
            success=False,
            attempts=attempts,
            total_delay_seconds=total_delay,
            last_exception=last_exception,
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds (with jitter applied)
        """
        import random

        # Calculate base delay based on strategy
        if self.policy.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            # Exponential: delay = initial * (multiplier ** (attempt - 1))
            delay = self.policy.initial_delay_seconds * (
                self.policy.backoff_multiplier ** (attempt - 1)
            )
            # Cap at max delay
            delay = min(delay, self.policy.max_delay_seconds)

        elif self.policy.backoff_strategy == BackoffStrategy.LINEAR:
            # Linear: delay = initial + (increment * (attempt - 1))
            delay = self.policy.initial_delay_seconds + (
                self.policy.linear_increment_seconds * (attempt - 1)
            )
            # Cap at max delay
            delay = min(delay, self.policy.max_delay_seconds)

        else:  # FIXED
            delay = self.policy.initial_delay_seconds

        # Apply jitter: randomize delay by ±jitter%
        if self.policy.jitter > 0:
            jitter_range = delay * self.policy.jitter
            delay += random.uniform(-jitter_range, jitter_range)
            # Ensure delay is non-negative
            delay = max(0.0, delay)

        return delay


# Common retry policies for reuse

DEFAULT_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    initial_delay_seconds=1.0,
    max_delay_seconds=30.0,
    jitter=0.1,
)

AGENT_RETRY_POLICY = RetryPolicy(
    max_attempts=2,  # Quick retries for agents (user-facing latency)
    backoff_strategy=BackoffStrategy.FIXED,
    initial_delay_seconds=0.5,
    max_delay_seconds=0.5,
    jitter=0.0,  # No jitter for predictable timing
)

BACKGROUND_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    initial_delay_seconds=2.0,
    max_delay_seconds=60.0,
    backoff_multiplier=2.0,
    jitter=0.2,  # More jitter for background tasks
)
