"""Agent execution contracts and data models.

This module defines minimal contracts for agent execution in Workstream E.
These contracts will be expanded after Workstream D finalizes AutomationContext.

NOTE: This is a minimal version for Workstream E implementation. Coordinate
with Workstream D before making significant changes to these contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AgentType(Enum):
    """Agent execution type classification."""

    IMMEDIATE = "immediate"  # Pre-response context gathering (~3s latency)
    BACKGROUND = "background"  # Post-response analysis (hidden from user)


@dataclass(frozen=True)
class AgentMetadata:
    """Metadata describing an agent's configuration and behavior.

    Used by AgentRegistry for discovery and AgentRunner for execution planning.

    Attributes:
        agent_id: Unique identifier (e.g., 'quick_entity_analysis')
        description: Human-readable description
        agent_type: IMMEDIATE or BACKGROUND
        priority: Execution priority (lower = higher priority, 1-10)
        timeout_seconds: Maximum execution time before timeout
        enabled: Whether agent is active in current configuration
    """

    agent_id: str
    description: str
    agent_type: AgentType
    priority: int = 5
    timeout_seconds: float = 10.0
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate metadata fields."""
        if not self.agent_id:
            raise ValueError("agent_id cannot be empty")
        if self.priority < 1 or self.priority > 10:
            raise ValueError("priority must be between 1 and 10")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")


@dataclass(frozen=True)
class AgentExecutionRequest:
    """Request to execute an agent with specific context.

    This is the input to AgentRunner for executing a single agent.

    Attributes:
        agent_id: ID of agent to execute
        rp_dir: RP directory path
        log_file: Log file path
        args: Positional arguments for agent.execute()
        kwargs: Keyword arguments for agent.execute()
    """

    agent_id: str
    rp_dir: Path
    log_file: Path
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentExecutionResult:
    """Result from executing an agent.

    Contains success/failure status, output content, timing, and error info.

    Attributes:
        agent_id: ID of executed agent
        success: Whether execution succeeded
        content: Output content (JSON string for background, text for immediate)
        duration_ms: Execution time in milliseconds
        error: Error message if failed
        is_balance_error: Whether failure was due to insufficient API balance
        attempts: Number of retry attempts made
    """

    agent_id: str
    success: bool
    content: str | None = None
    duration_ms: int = 0
    error: str | None = None
    is_balance_error: bool = False
    attempts: int = 1

    @property
    def is_timeout(self) -> bool:
        """Check if failure was due to timeout."""
        return self.error is not None and "timeout" in self.error.lower()

    @property
    def is_retryable(self) -> bool:
        """Check if failure is retryable (not balance error or timeout)."""
        return not self.is_balance_error and not self.is_timeout


@dataclass(frozen=True)
class AgentExecutionStats:
    """Statistics from batch agent execution.

    Used by AgentCoordinator to track execution metrics.

    Attributes:
        agents_registered: Number of agents registered for execution
        agents_executed: Number of agents that completed (success or failure)
        agents_succeeded: Number of successful executions
        agents_failed: Number of failed executions
        balance_errors: Number of failures due to insufficient balance
        total_duration_ms: Total execution time across all agents
        max_duration_ms: Duration of slowest agent
        avg_duration_ms: Average execution time
    """

    agents_registered: int
    agents_executed: int
    agents_succeeded: int
    agents_failed: int
    balance_errors: int = 0
    total_duration_ms: int = 0
    max_duration_ms: int = 0
    avg_duration_ms: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage (0.0-1.0)."""
        if self.agents_executed == 0:
            return 0.0
        return self.agents_succeeded / self.agents_executed

    @property
    def has_balance_errors(self) -> bool:
        """Check if any balance errors occurred."""
        return self.balance_errors > 0


# Type aliases for clarity
AgentID = str
AgentClass = type  # Type of BaseAgent subclass
