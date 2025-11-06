"""Module Handler - Handles module management IPC requests.

This handler processes module-related requests including:
- GET_MODULES: List all available modules and their states
- TOGGLE_MODULE: Enable/disable a module
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.infrastructure.ipc import IPCMessageType, IPCRequest, create_error_response, create_response

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class ModuleHandler(BaseHandler):
    """Handler for module management operations.

    Delegates to bridge.config_loader for module configuration.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route module request to appropriate handler method.

        Args:
            request: IPC request with module operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.GET_MODULES:
            return self._handle_get_modules(request)
        elif request_type == IPCMessageType.TOGGLE_MODULE:
            return self._handle_toggle_module(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown module request type: {request.type}"
            )

    def _handle_get_modules(self, request: IPCRequest) -> str:
        """Handle GET_MODULES request - get module states from config."""
        try:
            config = self.bridge.config_loader.load()
            modules_config = config.get("modules", {})

            # Build dict keyed by module_id for UI compatibility
            modules = {}
            for module_id, module_data in modules_config.items():
                modules[module_id] = {
                    "enabled": module_data.get("enabled", False),
                    "status": "running" if module_data.get("enabled", False) else "disabled",
                    "config": module_data.get("config", {})
                }

            return create_response(
                request.request_id,
                modules=modules
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to get modules: {str(e)}"
            )

    def _handle_toggle_module(self, request: IPCRequest) -> str:
        """Handle TOGGLE_MODULE request - enable/disable module."""
        module_id = request.data.get("module_id")
        enabled = request.data.get("enabled", True)

        if not module_id:
            return create_error_response(request.request_id, "Missing module_id")

        try:
            # Load config to validate module exists
            config = self.bridge.config_loader.load()
            modules_config = config.get("modules", {})

            # Validation 1: Check if module exists
            if module_id not in modules_config:
                return create_error_response(
                    request.request_id,
                    f"Unknown module: {module_id}"
                )

            # Validation 2: Prevent disabling active LLM provider
            llm_providers = [
                "claude_sdk_client",
                "claude_api_client",
                "openai_client",
                "openrouter_client"
            ]
            if not enabled and module_id in llm_providers:
                # Check if this is the current provider
                current_provider = self.bridge.current_provider
                if module_id == current_provider:
                    return create_error_response(
                        request.request_id,
                        f"Cannot disable active LLM provider '{module_id}'. Switch to a different provider first."
                    )

            # Update configuration
            config_key = f"modules.{module_id}.enabled"
            self.bridge.config_loader.set(config_key, enabled)

            # Persist to file
            self.bridge.config_loader.save()

            display_name = self._format_module_name(module_id)

            # Build response message with restart notification if needed
            message = f"Module '{display_name}' {'enabled' if enabled else 'disabled'}"

            # Modules that require restart to take effect
            requires_restart = [
                "agent_coordinator",
                "automation_orchestrator",
                "entity_manager",
                "session_manager",
                "file_manager"
            ]
            if module_id in requires_restart:
                message += " (restart required for changes to take effect)"

            return create_response(
                request.request_id,
                module_id=module_id,
                enabled=enabled,
                message=message
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to toggle module: {str(e)}"
            )

    def _format_module_name(self, module_id: str) -> str:
        """Format module ID for display."""
        # Convert snake_case to Title Case
        return module_id.replace("_", " ").title()

    def _get_module_description(self, module_id: str) -> str:
        """Get description for a module."""
        descriptions = {
            "file_manager": "Manages file operations and backups",
            "claude_sdk_client": "Anthropic Claude SDK (high-performance Node bridge)",
            "claude_api_client": "Anthropic Claude API (with prompt caching)",
            "openai_client": "OpenAI API (GPT-4.1 / GPT-4o)",
            "openrouter_client": "OpenRouter API (multi-model gateway)",
            "proxy_client": "HTTP proxy configuration",
            "session_manager": "Manages session state and checkpoints",
            "entity_manager": "Analyzes and tracks entity mentions",
            "automation_orchestrator": "Orchestrates automation triggers",
            "agent_coordinator": "Manages background agent execution",
            "fs_write_queue": "Async file write queue",
            "background_task_queue": "Background task execution queue",
            "update_checker": "Checks for system updates",
            "time_tracking": "Tracks in-world time passage and activity durations",
            "memory_creation": "Extracts memorable moments and saves to character memory logs",
        }
        return descriptions.get(module_id, "Module configuration")


__all__ = ["ModuleHandler"]
