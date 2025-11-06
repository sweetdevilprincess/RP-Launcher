"""Trigger Handler - Handles automation trigger management IPC requests.

This handler processes trigger-related requests including:
- GET_TRIGGERS: Get automation trigger configuration
- SET_TRIGGER: Update automation trigger settings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.infrastructure.ipc import IPCMessageType, IPCRequest, create_error_response, create_response

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class TriggerHandler(BaseHandler):
    """Handler for automation trigger management operations.

    Delegates to bridge.config_loader for trigger configuration.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route trigger request to appropriate handler method.

        Args:
            request: IPC request with trigger operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.GET_TRIGGERS:
            return self._handle_get_triggers(request)
        elif request_type == IPCMessageType.SET_TRIGGER:
            return self._handle_set_trigger(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown trigger request type: {request.type}"
            )

    def _handle_get_triggers(self, request: IPCRequest) -> str:
        """Handle GET_TRIGGERS request."""
        # Get trigger configuration from config loader
        use_triggers = self.bridge.config_loader.get("modules.automation_orchestrator.config.use_triggers", True)
        fallback_enabled = self.bridge.config_loader.get("modules.automation_orchestrator.config.fallback_enabled", True)

        # Return trigger configuration
        return create_response(
            request.request_id,
            triggers={
                "use_triggers": use_triggers,
                "fallback_enabled": fallback_enabled,
            }
        )

    def _handle_set_trigger(self, request: IPCRequest) -> str:
        """Handle SET_TRIGGER request."""
        trigger_id = request.data.get("trigger_id")
        enabled = request.data.get("enabled", True)

        if not trigger_id:
            return create_error_response(request.request_id, "Missing trigger_id")

        # Map trigger_id to config key
        trigger_config_map = {
            "use_triggers": "modules.automation_orchestrator.config.use_triggers",
            "fallback_enabled": "modules.automation_orchestrator.config.fallback_enabled",
        }

        config_key = trigger_config_map.get(trigger_id)
        if not config_key:
            return create_error_response(
                request.request_id,
                f"Unknown trigger_id: {trigger_id}. Valid options: {', '.join(trigger_config_map.keys())}"
            )

        try:
            # Update configuration
            self.bridge.config_loader.set(config_key, enabled)

            # Persist to file
            self.bridge.config_loader.save()

            return create_response(
                request.request_id,
                trigger_id=trigger_id,
                enabled=enabled,
                message=f"Trigger '{trigger_id}' {'enabled' if enabled else 'disabled'}"
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to update trigger: {str(e)}"
            )


__all__ = ["TriggerHandler"]
