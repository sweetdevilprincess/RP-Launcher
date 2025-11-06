"""Protocol definitions for logging across layers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class LoggingService(Protocol):
    """Minimal contract for structured logging."""

    def debug(self, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        """Emit diagnostic information for developers."""

    def info(self, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        """Emit general operational information."""

    def warning(self, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        """Flag recoverable issues for follow-up."""

    def error(self, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        """Record unexpected failures or user-visible errors."""

    def exception(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
        exc: BaseException | None = None,
    ) -> None:
        """Capture an exception stack with optional structured context."""
