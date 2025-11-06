"""
Agent Logger Utilities

Standardized logging for agents with consistent prefixes and emoji.
Replaces inline logging assembly across AgentCoordinator and individual agents.
"""

import logging
from pathlib import Path
from typing import Optional, Union
from datetime import datetime


class AgentLogger:
    """Standardized logger for agent operations.

    Provides consistent logging format with emoji and timing info.

    Usage:
        logger = AgentLogger("fact_extraction")
        logger.started()
        # ... agent work ...
        logger.completed(duration_ms=1234.5)

    Or use context manager:
        with AgentLogger("fact_extraction") as logger:
            # ... agent work ...
            pass  # Automatically logs completion
    """

    def __init__(
        self,
        agent_id: str,
        log_file: Optional[Union[str, Path]] = None,
        console_logger: Optional[logging.Logger] = None
    ):
        """Initialize agent logger.

        Args:
            agent_id: Agent identifier
            log_file: Optional file to log to
            console_logger: Optional logger instance (creates one if not provided)
        """
        self.agent_id = agent_id
        self.log_file = Path(log_file) if log_file else None
        self.console_logger = console_logger or logging.getLogger(f"agent.{agent_id}")
        self._start_time: Optional[float] = None

    def _format_message(self, emoji: str, message: str) -> str:
        """Format message with agent ID and emoji.

        Args:
            emoji: Emoji prefix
            message: Message text

        Returns:
            Formatted message
        """
        return f"{emoji} [{self.agent_id}] {message}"

    def _log_to_file(self, message: str) -> None:
        """Log message to file if configured.

        Args:
            message: Message to log
        """
        if not self.log_file:
            return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            self.console_logger.error(f"Failed to write to log file: {e}")

    def started(self, message: str = "Starting...") -> None:
        """Log agent start.

        Args:
            message: Custom message (optional)
        """
        import time
        self._start_time = time.time()

        formatted = self._format_message("🔄", message)
        self.console_logger.info(formatted)
        self._log_to_file(formatted)

    def completed(
        self,
        duration_ms: Optional[float] = None,
        message: str = "Completed"
    ) -> None:
        """Log agent completion.

        Args:
            duration_ms: Duration in milliseconds (auto-calculated if not provided)
            message: Custom message (optional)
        """
        # Calculate duration if not provided
        if duration_ms is None and self._start_time is not None:
            import time
            duration_ms = (time.time() - self._start_time) * 1000

        # Format message with duration
        if duration_ms is not None:
            full_message = f"{message} ({duration_ms:.0f}ms)"
        else:
            full_message = message

        formatted = self._format_message("✓", full_message)
        self.console_logger.info(formatted)
        self._log_to_file(formatted)

    def failed(self, error: Union[str, Exception], message: str = "Failed") -> None:
        """Log agent failure.

        Args:
            error: Error message or exception
            message: Custom message (optional)
        """
        error_str = str(error)
        full_message = f"{message}: {error_str}"

        formatted = self._format_message("✗", full_message)
        self.console_logger.error(formatted)
        self._log_to_file(formatted)

    def warning(self, message: str) -> None:
        """Log warning.

        Args:
            message: Warning message
        """
        formatted = self._format_message("⚠️", message)
        self.console_logger.warning(formatted)
        self._log_to_file(formatted)

    def info(self, message: str, emoji: str = "ℹ️") -> None:
        """Log info message.

        Args:
            message: Info message
            emoji: Custom emoji (optional)
        """
        formatted = self._format_message(emoji, message)
        self.console_logger.info(formatted)
        self._log_to_file(formatted)

    def debug(self, message: str) -> None:
        """Log debug message.

        Args:
            message: Debug message
        """
        formatted = self._format_message("🔍", message)
        self.console_logger.debug(formatted)
        self._log_to_file(formatted)

    def cached(self, message: str = "Using cached result") -> None:
        """Log cache hit.

        Args:
            message: Custom message (optional)
        """
        formatted = self._format_message("💾", message)
        self.console_logger.info(formatted)
        self._log_to_file(formatted)

    def retrying(self, attempt: int, max_attempts: int, reason: str = "") -> None:
        """Log retry attempt.

        Args:
            attempt: Current attempt number
            max_attempts: Maximum attempts
            reason: Reason for retry (optional)
        """
        reason_str = f" ({reason})" if reason else ""
        message = f"Retry {attempt}/{max_attempts}{reason_str}"

        formatted = self._format_message("🔁", message)
        self.console_logger.warning(formatted)
        self._log_to_file(formatted)

    # Context manager support
    def __enter__(self) -> 'AgentLogger':
        """Enter context manager."""
        self.started()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context manager."""
        if exc_type is not None:
            self.failed(exc_val)
            return False
        else:
            self.completed()
            return True


def log_to_file(log_file: Union[str, Path], message: str) -> None:
    """Simple utility to log a message to a file.

    Args:
        log_file: Path to log file
        message: Message to log
    """
    try:
        log_path = Path(log_file)
        timestamp = datetime.now().strftime("%H:%M:%S")

        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    except Exception as e:
        logging.error(f"Failed to write to log file {log_file}: {e}")


class AgentCoordinatorLogger:
    """Specialized logger for AgentCoordinator operations.

    Handles multi-agent orchestration logging.
    """

    def __init__(
        self,
        log_file: Optional[Union[str, Path]] = None,
        console_logger: Optional[logging.Logger] = None
    ):
        """Initialize coordinator logger.

        Args:
            log_file: Optional file to log to
            console_logger: Optional logger instance
        """
        self.log_file = Path(log_file) if log_file else None
        self.console_logger = console_logger or logging.getLogger("agent.coordinator")

    def orchestration_start(self, agent_count: int) -> None:
        """Log start of multi-agent orchestration.

        Args:
            agent_count: Number of agents to run
        """
        message = f"🎭 Starting orchestration ({agent_count} agents)"
        self.console_logger.info(message)

        if self.log_file:
            log_to_file(self.log_file, message)

    def orchestration_complete(self, duration_ms: float, success_count: int, total_count: int) -> None:
        """Log completion of orchestration.

        Args:
            duration_ms: Total duration
            success_count: Number of successful agents
            total_count: Total number of agents
        """
        message = f"🎭 Orchestration complete ({success_count}/{total_count} successful, {duration_ms:.0f}ms)"
        self.console_logger.info(message)

        if self.log_file:
            log_to_file(self.log_file, message)

    def agent_queued(self, agent_id: str) -> None:
        """Log agent queued for execution.

        Args:
            agent_id: Agent identifier
        """
        message = f"📋 Queued: {agent_id}"
        self.console_logger.debug(message)

        if self.log_file:
            log_to_file(self.log_file, message)

    def background_task_queued(self, agent_id: str, task_id: str) -> None:
        """Log background task queued.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier
        """
        message = f"🔄 Background task queued: {agent_id} ({task_id})"
        self.console_logger.info(message)

        if self.log_file:
            log_to_file(self.log_file, message)
