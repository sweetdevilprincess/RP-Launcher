"""Automation layer for the refactored RP Launcher."""

from .contracts.automation_context import (
    AgentContext,
    AutomationContext,
    AutomationResult,
    LoadingContext,
)
from .factory import create_automation_service

__all__ = [
    "AgentContext",
    "AutomationContext",
    "AutomationResult",
    "LoadingContext",
    "create_automation_service",
]
