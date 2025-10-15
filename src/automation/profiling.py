#!/usr/bin/env python3
"""
Performance Profiling Module

Tracks precise timing of automation operations to identify bottlenecks.
"""

import time
from typing import Dict, Optional
from contextlib import contextmanager


class PerformanceProfiler:
    """Track timing of automation operations"""

    def __init__(self):
        """Initialize profiler"""
        self.timings: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}
        self._operation_stack = []

    def start(self, operation: str) -> None:
        """Start timing an operation

        Args:
            operation: Name of operation to time
        """
        self._start_times[operation] = time.perf_counter()
        self._operation_stack.append(operation)

    def end(self, operation: str) -> float:
        """End timing an operation

        Args:
            operation: Name of operation

        Returns:
            Elapsed time in seconds
        """
        if operation not in self._start_times:
            return 0.0

        elapsed = time.perf_counter() - self._start_times[operation]
        self.timings[operation] = elapsed

        # Remove from stack
        if self._operation_stack and self._operation_stack[-1] == operation:
            self._operation_stack.pop()

        return elapsed

    @contextmanager
    def measure(self, operation: str):
        """Context manager for timing operations

        Usage:
            with profiler.measure("file_loading"):
                load_files()

        Args:
            operation: Name of operation
        """
        self.start(operation)
        try:
            yield
        finally:
            self.end(operation)

    def get_timing(self, operation: str) -> Optional[float]:
        """Get timing for an operation

        Args:
            operation: Operation name

        Returns:
            Elapsed time in seconds, or None if not found
        """
        return self.timings.get(operation)

    def report(self, title: str = "Performance Profile") -> str:
        """Generate formatted timing report

        Args:
            title: Report title

        Returns:
            Formatted report string
        """
        if not self.timings:
            return f"\n📊 {title}: No timings recorded"

        total = sum(self.timings.values())
        lines = [f"\n📊 {title}:"]
        lines.append("─" * 60)

        # Sort by time (descending)
        sorted_timings = sorted(self.timings.items(), key=lambda x: x[1], reverse=True)

        for operation, elapsed in sorted_timings:
            pct = (elapsed / total * 100) if total > 0 else 0
            ms = elapsed * 1000
            lines.append(f"  {operation:35s}: {ms:7.1f}ms ({pct:5.1f}%)")

        lines.append("─" * 60)
        lines.append(f"  {'TOTAL':35s}: {total*1000:7.1f}ms")

        return '\n'.join(lines)

    def get_summary(self) -> Dict[str, float]:
        """Get timing summary as dict

        Returns:
            Dict of {operation: elapsed_seconds}
        """
        return self.timings.copy()

    def reset(self) -> None:
        """Reset all timings"""
        self.timings.clear()
        self._start_times.clear()
        self._operation_stack.clear()


# Thread-local profiler instance
import threading
_thread_local = threading.local()


def get_profiler() -> PerformanceProfiler:
    """Get thread-local profiler instance

    Returns:
        PerformanceProfiler instance for current thread
    """
    if not hasattr(_thread_local, 'profiler'):
        _thread_local.profiler = PerformanceProfiler()
    return _thread_local.profiler


def reset_profiler() -> None:
    """Reset thread-local profiler"""
    if hasattr(_thread_local, 'profiler'):
        _thread_local.profiler.reset()
