"""System Handler - Handles system-level IPC requests.

This handler processes system-related requests including:
- TEST_MODE: Enable/disable testing mode and WIP mode
- PING: Health check endpoint
- SHUTDOWN: Graceful shutdown of bridge service
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from src.infrastructure.ipc import IPCMessageType, IPCRequest, create_error_response, create_response

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class SystemHandler(BaseHandler):
    """Handler for system-level operations.

    Handles testing mode, health checks, and shutdown operations.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route system request to appropriate handler method.

        Args:
            request: IPC request with system operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.TEST_MODE:
            return self._handle_test_mode(request)
        elif request_type == IPCMessageType.PING:
            return self._handle_ping(request)
        elif request_type == IPCMessageType.SHUTDOWN:
            return self._handle_shutdown(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown system request type: {request.type}"
            )

    def _handle_test_mode(self, request: IPCRequest) -> str:
        """Handle TEST_MODE request.

        Supports both legacy testing mode (mock LLM) and new WIP mode.

        Commands:
        - enabled=true: Enable mock LLM testing mode
        - wip_action="enable", wip_component="prompt_builder": Enable WIP mode for component
        - wip_action="disable", wip_component="prompt_builder": Disable WIP mode for component
        - wip_action="list": List available WIP modules
        - wip_action="status": Get WIP system status
        """
        # Legacy testing mode (mock LLM)
        if "enabled" in request.data:
            enabled = request.data.get("enabled", True)
            self.bridge.testing_mode = enabled
            self.bridge._initialize_llm_client()  # Reinitialize with mock or real client

            return create_response(
                request.request_id,
                testing_mode=self.bridge.testing_mode,
                message=f"Testing mode {'enabled' if enabled else 'disabled'}"
            )

        # WIP mode commands
        wip_action = request.data.get("wip_action")

        if wip_action == "enable":
            component_id = request.data.get("wip_component")
            if not component_id:
                return create_error_response(request.request_id, "Missing wip_component")

            success = self.bridge.wip_executor.enable(component_id)
            if not success:
                return create_error_response(
                    request.request_id,
                    f"WIP module not available for: {component_id}"
                )

            return create_response(
                request.request_id,
                wip_enabled=True,
                component=component_id,
                message=f"WIP mode enabled for {component_id}"
            )

        elif wip_action == "disable":
            component_id = request.data.get("wip_component")
            if not component_id:
                # Disable all if no component specified
                self.bridge.wip_executor.disable_all()
                return create_response(
                    request.request_id,
                    wip_enabled=False,
                    message="WIP mode disabled for all components"
                )

            self.bridge.wip_executor.disable(component_id)
            return create_response(
                request.request_id,
                wip_enabled=False,
                component=component_id,
                message=f"WIP mode disabled for {component_id}"
            )

        elif wip_action == "list":
            available = self.bridge.wip_executor.scanner.list_available()
            summary = self.bridge.wip_executor.scanner.get_summary()

            return create_response(
                request.request_id,
                available_wip_modules=available,
                summary=summary
            )

        elif wip_action == "status":
            status = self.bridge.wip_executor.get_status()
            return create_response(
                request.request_id,
                wip_status=status
            )

        elif wip_action == "reload":
            component_id = request.data.get("wip_component")
            if not component_id:
                return create_error_response(request.request_id, "Missing wip_component")

            success = self.bridge.wip_executor.reload_wip_module(component_id)
            if not success:
                return create_error_response(
                    request.request_id,
                    f"Failed to reload WIP module: {component_id}"
                )

            return create_response(
                request.request_id,
                reloaded=True,
                component=component_id,
                message=f"WIP module reloaded: {component_id}"
            )

        else:
            return create_error_response(
                request.request_id,
                f"Unknown wip_action: {wip_action}"
            )

    def _handle_ping(self, request: IPCRequest) -> str:
        """Handle PING request."""
        return create_response(
            request.request_id,
            pong=True,
            timestamp=Path(__file__).stat().st_mtime  # Just some data
        )

    def _handle_shutdown(self, request: IPCRequest) -> str:
        """Handle SHUTDOWN request."""
        response = create_response(
            request.request_id,
            message="Shutting down bridge"
        )

        # Schedule shutdown after sending response
        threading.Timer(0.5, self.bridge.stop).start()

        return response


__all__ = ["SystemHandler"]
