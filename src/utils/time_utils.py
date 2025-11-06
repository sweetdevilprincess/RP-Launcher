"""
Time Utilities

Common timestamp and timing utilities to eliminate duplication.
Every agent's gather_data adds datetime.now().strftime(...).
"""

from datetime import datetime, timedelta
from typing import Optional
import time


def now_iso() -> str:
    """Get current time in ISO format.

    Returns:
        ISO formatted timestamp

    Example:
        "2025-10-17T14:30:45.123456"
    """
    return datetime.now().isoformat()


def now_formatted(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Get current time in custom format.

    Args:
        fmt: strftime format string

    Returns:
        Formatted timestamp

    Example:
        now_formatted()  # "2025-10-17 14:30:45"
        now_formatted("%H:%M:%S")  # "14:30:45"
    """
    return datetime.now().strftime(fmt)


def now_timestamp() -> float:
    """Get current Unix timestamp.

    Returns:
        Unix timestamp (seconds since epoch)
    """
    return time.time()


def now_timestamp_ms() -> int:
    """Get current Unix timestamp in milliseconds.

    Returns:
        Unix timestamp in milliseconds
    """
    return int(time.time() * 1000)


def elapsed_ms(start_time: float) -> float:
    """Calculate elapsed time in milliseconds.

    Args:
        start_time: Start time from time.time()

    Returns:
        Elapsed time in milliseconds

    Example:
        start = time.time()
        # ... do work ...
        duration = elapsed_ms(start)
    """
    return (time.time() - start_time) * 1000


def parse_iso(iso_string: str) -> Optional[datetime]:
    """Parse ISO formatted timestamp.

    Args:
        iso_string: ISO timestamp string

    Returns:
        datetime object or None if invalid
    """
    try:
        return datetime.fromisoformat(iso_string)
    except (ValueError, TypeError):
        return None


def format_duration(duration_ms: float) -> str:
    """Format duration in human-readable form.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        Formatted duration string

    Example:
        format_duration(1234)  # "1.2s"
        format_duration(125)   # "125ms"
        format_duration(61000) # "1m 1s"
    """
    if duration_ms < 1000:
        return f"{duration_ms:.0f}ms"
    elif duration_ms < 60000:
        return f"{duration_ms / 1000:.1f}s"
    else:
        minutes = int(duration_ms / 60000)
        seconds = int((duration_ms % 60000) / 1000)
        return f"{minutes}m {seconds}s"


def time_ago(timestamp: float) -> str:
    """Get human-readable 'time ago' string.

    Args:
        timestamp: Unix timestamp

    Returns:
        Human-readable string

    Example:
        "5 seconds ago"
        "2 minutes ago"
        "1 hour ago"
    """
    now = time.time()
    diff = now - timestamp

    if diff < 60:
        return f"{int(diff)} seconds ago"
    elif diff < 3600:
        minutes = int(diff / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(diff / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def is_expired(timestamp: float, max_age_seconds: float) -> bool:
    """Check if timestamp is expired.

    Args:
        timestamp: Unix timestamp to check
        max_age_seconds: Maximum age in seconds

    Returns:
        True if expired

    Example:
        # Check if cache is older than 5 minutes
        if is_expired(cache_time, 300):
            refresh_cache()
    """
    return (time.time() - timestamp) > max_age_seconds


class Timer:
    """Simple timer for measuring execution time.

    Usage:
        timer = Timer()
        # ... do work ...
        elapsed = timer.elapsed_ms()

    Or use as context manager:
        with Timer() as t:
            # ... do work ...
        print(f"Took {t.elapsed_ms()}ms")
    """

    def __init__(self):
        """Initialize timer."""
        self.start_time = time.time()
        self.end_time: Optional[float] = None

    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds.

        Returns:
            Elapsed time in milliseconds
        """
        end = self.end_time if self.end_time is not None else time.time()
        return (end - self.start_time) * 1000

    def elapsed_s(self) -> float:
        """Get elapsed time in seconds.

        Returns:
            Elapsed time in seconds
        """
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

    def reset(self) -> None:
        """Reset timer to current time."""
        self.start_time = time.time()
        self.end_time = None

    def stop(self) -> float:
        """Stop timer and return elapsed time.

        Returns:
            Elapsed time in milliseconds
        """
        self.end_time = time.time()
        return self.elapsed_ms()

    def __enter__(self) -> 'Timer':
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context manager."""
        self.stop()
        return False

    def __repr__(self) -> str:
        """String representation."""
        return f"<Timer elapsed={format_duration(self.elapsed_ms())}>"
