"""Telemetry and performance profiling infrastructure.

Provides timing utilities and performance profiling that integrate
with the LoggingService for consistent monitoring across the codebase.
"""

from .performance import (
    PerformanceProfiler,
    PerformanceTimer,
    timed,
    timed_operation,
)

__all__ = [
    "PerformanceProfiler",
    "PerformanceTimer",
    "timed",
    "timed_operation",
]
