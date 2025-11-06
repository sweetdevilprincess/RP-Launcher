"""Performance profiling and timing utilities.

Provides timing context managers and decorators that integrate with
the LoggingService for consistent performance tracking across the codebase.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

from ...shared.interfaces import LoggingService

F = TypeVar("F", bound=Callable[..., Any])


class PerformanceTimer:
    """Timer for measuring operation duration.

    Integrates with LoggingService to emit structured timing events.

    Example:
        >>> logger = get_logger(__name__)
        >>> timer = PerformanceTimer("file_loading", logger)
        >>> timer.start()
        >>> # ... do work ...
        >>> timer.stop()  # Logs performance event
    """

    def __init__(
        self,
        operation_name: str,
        logger: LoggingService,
        *,
        log_level: str = "info",
    ) -> None:
        """Initialize performance timer.

        Args:
            operation_name: Name of the operation being timed
            logger: Logger instance for emitting events
            log_level: Log level to use (debug, info, warning, error)
        """
        self.operation_name = operation_name
        self.logger = logger
        self.log_level = log_level
        self._start_time: float | None = None
        self._end_time: float | None = None

    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.time()
        self._log(
            "debug",
            f"performance.{self.operation_name}.started",
            context={"operation": self.operation_name},
        )

    def stop(self, context: dict | None = None) -> float:
        """Stop the timer and log the duration.

        Args:
            context: Additional context to include in log

        Returns:
            Duration in milliseconds
        """
        self._end_time = time.time()

        if self._start_time is None:
            self.logger.warning(
                f"performance.{self.operation_name}.stopped_without_start",
                context={"operation": self.operation_name},
            )
            return 0.0

        duration_ms = (self._end_time - self._start_time) * 1000

        log_context = {
            "operation": self.operation_name,
            "duration_ms": round(duration_ms, 2),
        }
        if context:
            log_context.update(context)

        self._log(
            self.log_level,
            f"performance.{self.operation_name}.completed",
            context=log_context,
        )

        return duration_ms

    def _log(self, level: str, message: str, *, context: dict | None = None) -> None:
        """Log message at specified level.

        Args:
            level: Log level (debug, info, warning, error)
            message: Log message
            context: Optional context
        """
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message, context=context)


@contextmanager
def timed_operation(
    operation_name: str,
    logger: LoggingService,
    *,
    log_level: str = "info",
    context: dict | None = None,
) -> Generator[PerformanceTimer, None, None]:
    """Context manager for timing operations.

    Automatically starts timer on entry and stops on exit.
    Logs performance event with duration.

    Args:
        operation_name: Name of the operation
        logger: Logger instance
        log_level: Log level for completion event
        context: Additional context to include

    Yields:
        PerformanceTimer instance

    Example:
        >>> logger = get_logger(__name__)
        >>> with timed_operation("entity_loading", logger) as timer:
        ...     # ... load entities ...
        ...     pass  # Automatically logs duration on exit
    """
    timer = PerformanceTimer(operation_name, logger, log_level=log_level)
    timer.start()
    try:
        yield timer
    finally:
        timer.stop(context=context)


def timed(
    operation_name: str | None = None,
    *,
    log_level: str = "info",
) -> Callable[[F], F]:
    """Decorator for timing function execution.

    Requires the decorated function to have a 'logger' parameter
    (either as positional or keyword argument).

    Args:
        operation_name: Name of operation (defaults to function name)
        log_level: Log level for timing event

    Returns:
        Decorated function

    Example:
        >>> @timed("user_validation")
        ... def validate_user(user_id: str, logger: LoggingService) -> bool:
        ...     # ... validation logic ...
        ...     return True

        >>> @timed()  # Uses function name
        ... def process_data(data: dict, logger: LoggingService) -> None:
        ...     # ... processing ...
        ...     pass
    """

    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try to find logger in args/kwargs
            logger = kwargs.get("logger")
            if logger is None:
                # Check if 'self' or first arg has logger attribute
                if args and hasattr(args[0], "logger"):
                    logger = args[0].logger
                elif args and hasattr(args[0], "_logger"):
                    logger = args[0]._logger

            if logger is None:
                # Can't time without logger, just execute
                return func(*args, **kwargs)

            with timed_operation(op_name, logger, log_level=log_level):
                return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


class PerformanceProfiler:
    """Aggregated performance profiling across multiple operations.

    Collects timing data for multiple operations and can emit
    summary statistics.

    Example:
        >>> logger = get_logger(__name__)
        >>> profiler = PerformanceProfiler(logger)
        >>>
        >>> with profiler.time("file_load"):
        ...     # ... load files ...
        ...     pass
        >>>
        >>> with profiler.time("parse_entities"):
        ...     # ... parse ...
        ...     pass
        >>>
        >>> profiler.log_summary()  # Logs summary of all operations
    """

    def __init__(self, logger: LoggingService) -> None:
        """Initialize profiler.

        Args:
            logger: Logger for emitting events
        """
        self.logger = logger
        self._timings: dict[str, list[float]] = {}

    @contextmanager
    def time(self, operation_name: str) -> Generator[None, None, None]:
        """Time an operation and record the duration.

        Args:
            operation_name: Name of the operation

        Yields:
            None

        Example:
            >>> with profiler.time("database_query"):
            ...     # ... query ...
            ...     pass
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            if operation_name not in self._timings:
                self._timings[operation_name] = []
            self._timings[operation_name].append(duration_ms)

    def get_stats(self, operation_name: str) -> dict[str, float]:
        """Get statistics for a specific operation.

        Args:
            operation_name: Name of the operation

        Returns:
            Dict with count, total_ms, avg_ms, min_ms, max_ms

        Example:
            >>> stats = profiler.get_stats("file_load")
            >>> print(f"Average: {stats['avg_ms']}ms")
        """
        timings = self._timings.get(operation_name, [])
        if not timings:
            return {
                "count": 0,
                "total_ms": 0.0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
            }

        return {
            "count": len(timings),
            "total_ms": round(sum(timings), 2),
            "avg_ms": round(sum(timings) / len(timings), 2),
            "min_ms": round(min(timings), 2),
            "max_ms": round(max(timings), 2),
        }

    def log_summary(self, *, log_level: str = "info") -> None:
        """Log summary of all recorded timings.

        Args:
            log_level: Log level to use

        Example:
            >>> profiler.log_summary()  # Logs summary at info level
        """
        if not self._timings:
            self.logger.info("performance.summary.empty", context={})
            return

        summary = {}
        for op_name in sorted(self._timings.keys()):
            summary[op_name] = self.get_stats(op_name)

        log_method = getattr(self.logger, log_level, self.logger.info)
        log_method(
            "performance.summary",
            context={
                "operations": summary,
                "total_operations": len(self._timings),
            },
        )

    def clear(self) -> None:
        """Clear all recorded timings.

        Example:
            >>> profiler.clear()  # Reset profiler
        """
        self._timings.clear()
        self.logger.debug("performance.profiler.cleared", context={})
