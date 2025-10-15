#!/usr/bin/env python3
"""
Profiling Decorator

Replaces conditional profiling code with clean decorator pattern.
Eliminates 11 instances of repetitive profiling boilerplate.
"""

import time
from functools import wraps
from typing import Any, Callable, Optional, Dict
from pathlib import Path
from contextlib import contextmanager


class ProfileContext:
    """Context manager for profiling operations."""

    def __init__(self, name: str, profiler: Optional[Any] = None,
                 enabled: bool = True, log_file: Optional[Path] = None):
        """
        Initialize profiling context.

        Args:
            name: Name of the operation being profiled
            profiler: Optional profiler instance
            enabled: Whether profiling is enabled
            log_file: Optional log file for profiling output
        """
        self.name = name
        self.profiler = profiler
        self.enabled = enabled and profiler is not None
        self.log_file = log_file
        self.start_time = None

    def __enter__(self):
        """Start profiling."""
        if self.enabled:
            self.start_time = time.time()
            if hasattr(self.profiler, 'start'):
                self.profiler.start(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop profiling and log results."""
        if self.enabled and self.start_time:
            duration = time.time() - self.start_time

            if hasattr(self.profiler, 'stop'):
                self.profiler.stop(self.name, duration)

            if self.log_file:
                from src.automation.core import log_to_file
                log_to_file(self.log_file,
                           f"[Profiler] {self.name}: {duration:.2f}s")
        return False


def profile(name: Optional[str] = None, log: bool = True):
    """
    Decorator for profiling methods.

    Replaces this pattern:
    ```python
    if self.profiler:
        self.profiler.start("operation")
    # ... do work ...
    if self.profiler:
        self.profiler.stop("operation", duration)
    ```

    With:
    ```python
    @profile("operation")
    def method(self, ...):
        # ... do work ...
    ```

    Args:
        name: Name for profiling (defaults to method name)
        log: Whether to log profiling results

    Returns:
        Decorated function with automatic profiling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get self if this is a method
            self_arg = args[0] if args and hasattr(args[0], '__class__') else None

            # Determine profiling settings
            profiler = getattr(self_arg, 'profiler', None) if self_arg else None
            profiling_enabled = getattr(self_arg, 'profiling_enabled', True) if self_arg else True
            log_file = getattr(self_arg, 'log_file', None) if self_arg else None

            # Use provided name or function name
            profile_name = name or func.__name__

            # Skip profiling if disabled
            if not profiler or not profiling_enabled:
                return func(*args, **kwargs)

            # Profile the operation
            with ProfileContext(profile_name, profiler, profiling_enabled,
                              log_file if log else None):
                return func(*args, **kwargs)

        return wrapper
    return decorator


@contextmanager
def profile_block(name: str, profiler: Optional[Any] = None,
                  enabled: bool = True, log_file: Optional[Path] = None):
    """
    Context manager for profiling code blocks.

    Usage:
    ```python
    with profile_block("loading_files", self.profiler, self.profiling_enabled):
        # ... code to profile ...
    ```

    Args:
        name: Name of the operation
        profiler: Profiler instance
        enabled: Whether profiling is enabled
        log_file: Optional log file

    Yields:
        ProfileContext instance
    """
    ctx = ProfileContext(name, profiler, enabled, log_file)
    try:
        ctx.__enter__()
        yield ctx
    finally:
        ctx.__exit__(None, None, None)


class MethodProfiler:
    """
    Mixin class that provides profiling capabilities.

    Classes can inherit from this to get automatic profiling support.
    """

    def __init__(self, profiler: Optional[Any] = None,
                 profiling_enabled: bool = True,
                 log_file: Optional[Path] = None):
        """
        Initialize profiler mixin.

        Args:
            profiler: Profiler instance
            profiling_enabled: Whether to enable profiling
            log_file: Log file for profiling output
        """
        self.profiler = profiler
        self.profiling_enabled = profiling_enabled
        self.log_file = log_file

    def profile_operation(self, name: str) -> ProfileContext:
        """
        Create a profiling context for an operation.

        Args:
            name: Name of the operation

        Returns:
            ProfileContext for the operation
        """
        return ProfileContext(name, self.profiler,
                            self.profiling_enabled, self.log_file)


# Specialized decorators for common operations
def profile_file_operation(name: Optional[str] = None):
    """Profile file I/O operations."""
    return profile(name or "file_operation", log=True)


def profile_agent_execution(agent_name: Optional[str] = None):
    """Profile agent execution."""
    def decorator(func):
        actual_name = agent_name or f"agent_{func.__name__}"
        return profile(actual_name, log=True)(func)
    return decorator


def profile_api_call(service: str = "api"):
    """Profile external API calls."""
    return profile(f"{service}_call", log=True)


def profile_cache_operation(operation: str = "cache"):
    """Profile cache operations."""
    return profile(f"cache_{operation}", log=True)