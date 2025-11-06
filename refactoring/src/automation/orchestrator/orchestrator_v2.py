"""Thin façade around the automation service."""

from __future__ import annotations

from ..contracts import AutomationContext, AutomationResult
from ..services import AutomationService


class AutomationOrchestrator:
    """Public entry point for the automation pipeline."""

    def __init__(self, service: AutomationService) -> None:
        self._service = service

    def execute(self, context: AutomationContext) -> AutomationResult:
        """Execute automation for the provided context."""

        return self._service.run(context)
