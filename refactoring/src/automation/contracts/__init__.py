"""Data contracts shared across automation services."""

from .agent_contracts import (
    AgentClass,
    AgentExecutionResult,
    AgentExecutionStats,
    AgentID,
    AgentMetadata,
    AgentType,
)
from .automation_context import (
    AgentContext,
    AutomationContext,
    AutomationResult,
    LoadingContext,
)

__all__ = [
    "AgentClass",
    "AgentContext",
    "AgentExecutionResult",
    "AgentExecutionStats",
    "AgentID",
    "AgentMetadata",
    "AgentType",
    "AutomationContext",
    "AutomationResult",
    "LoadingContext",
]
