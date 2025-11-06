"""Logging utilities for refactored components.

Provides get_logger() function that returns LoggingService instances
backed by Python's logging module.
"""

from __future__ import annotations

import logging

from .interfaces import LoggingService


class SimpleLogger(LoggingService):
    """Simple no-op logging implementation for testing.

    This logger does nothing - useful for tests that don't need logging output.
    """

    def __init__(self, name: str) -> None:
        """Initialize logger with name.

        Args:
            name: Logger name (typically __name__)
        """
        self.name = name

    def debug(self, event: str, *, context: dict | None = None) -> None:
        """Log debug message."""

    def info(self, event: str, *, context: dict | None = None) -> None:
        """Log info message."""

    def warning(self, event: str, *, context: dict | None = None) -> None:
        """Log warning message."""

    def error(self, event: str, *, context: dict | None = None) -> None:
        """Log error message."""

    def exception(
        self,
        message: str,
        *,
        context: dict | None = None,
        exc: BaseException | None = None,
    ) -> None:
        """Capture exception (no-op)."""


class PythonLogger(LoggingService):
    """Production LoggingService backed by Python's logging module.

    Wraps logging.Logger with structured context support.
    Formats context as JSON for readability.
    """

    def __init__(self, name: str) -> None:
        """Initialize logger with name.

        Args:
            name: Logger name (typically __name__)
        """
        self._logger = logging.getLogger(name)

    def debug(self, message: str, *, context: dict | None = None) -> None:
        """Log debug message with optional context."""
        self._logger.debug(message + self._format_context(context))

    def info(self, message: str, *, context: dict | None = None) -> None:
        """Log info message with optional context."""
        self._logger.info(message + self._format_context(context))

    def warning(self, message: str, *, context: dict | None = None) -> None:
        """Log warning message with optional context."""
        self._logger.warning(message + self._format_context(context))

    def error(self, message: str, *, context: dict | None = None) -> None:
        """Log error message with optional context."""
        self._logger.error(message + self._format_context(context))

    def exception(
        self,
        message: str,
        *,
        context: dict | None = None,
        exc: BaseException | None = None,
    ) -> None:
        """Log exception with stack trace and optional context."""
        if exc is not None:
            self._logger.exception(message + self._format_context(context), exc_info=exc)
        else:
            self._logger.exception(message + self._format_context(context))

    def _format_context(self, context: dict | None) -> str:
        """Format context dict as JSON string.

        Args:
            context: Optional context dictionary

        Returns:
            Formatted context string or empty string
        """
        if not context:
            return ""
        try:
            import json

            serialized = json.dumps(context, ensure_ascii=False, sort_keys=True)
            return f" | context={serialized}"
        except (TypeError, ValueError):
            return f" | context={dict(context)}"


def get_logger(name: str) -> LoggingService:
    """Get a production logger instance for the given name.

    This function returns a PythonLogger backed by Python's logging module.
    The logger will respect the logging configuration set via logging.basicConfig()
    or configure_logging() from infrastructure.logging.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        LoggingService instance backed by Python's logging

    Example:
        >>> from shared.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("operation.started", context={"user": "alice"})
        >>> logger.error("operation.failed", context={"error": "timeout"})
    """
    return PythonLogger(name)


def get_silent_logger(name: str) -> LoggingService:
    """Get a no-op logger for testing.

    Returns a SimpleLogger that does nothing - useful for tests
    that don't need logging output.

    Args:
        name: Logger name (typically __name__)

    Returns:
        LoggingService instance that does nothing

    Example:
        >>> from shared.logging import get_silent_logger
        >>> logger = get_silent_logger(__name__)
        >>> logger.info("this won't output anything")
    """
    return SimpleLogger(name)
