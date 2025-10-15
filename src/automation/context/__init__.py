"""
Automation Context Module

Provides immutable context objects for passing data through the automation pipeline.
Replaces parameter sprawl with clean, typed context objects.
"""

from src.automation.context.automation_context import (
    AutomationContext,
    AutomationResult,
    LoadingContext,
    AgentContext
)

__all__ = [
    'AutomationContext',
    'AutomationResult',
    'LoadingContext',
    'AgentContext'
]