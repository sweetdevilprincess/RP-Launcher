"""Settings Handler - Handles settings management IPC requests.

This handler processes settings-related requests including:
- GET_SETTINGS: Get current LLM settings from config
- UPDATE_SETTINGS: Update LLM settings in config
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.infrastructure.ipc import IPCMessageType, IPCRequest, create_error_response, create_response

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class SettingsHandler(BaseHandler):
    """Handler for settings management operations.

    Delegates to bridge.config_loader for settings operations.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route settings request to appropriate handler method.

        Args:
            request: IPC request with settings operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.GET_SETTINGS:
            return self._handle_get_settings(request)
        elif request_type == IPCMessageType.UPDATE_SETTINGS:
            return self._handle_update_settings(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown settings request type: {request.type}"
            )

    def _handle_get_settings(self, request: IPCRequest) -> str:
        """Handle GET_SETTINGS request - get LLM settings from config."""
        try:
            config = self.bridge.config_loader.load()

            # Get LLM routing config
            from src.infrastructure.config.defaults import LLM_ROUTING_DEFAULTS
            llm_config = config.get("llm", LLM_ROUTING_DEFAULTS)

            primary_provider = llm_config.get("primary_provider", "claude_api_client")
            secondary_provider = llm_config.get("secondary_provider", "")

            settings = {
                # LLM routing settings
                "primary_provider": primary_provider,
                "secondary_provider": secondary_provider,
                "use_secondary_for_automation": llm_config.get("use_secondary_for_automation", False),
            }

            # Get primary provider's settings
            primary_config = config.get("modules", {}).get(primary_provider, {}).get("config", {})
            settings["primary_api_key"] = primary_config.get("api_key", "")
            settings["primary_model"] = primary_config.get("model", "claude-3-5-sonnet-20241022")
            settings["primary_temperature"] = primary_config.get("temperature", 1.0)
            settings["primary_max_tokens"] = primary_config.get("max_tokens", 4096)
            settings["primary_prompt_caching"] = primary_config.get("use_prompt_caching", True)

            # Get secondary provider's settings (if enabled)
            settings["enable_secondary"] = bool(secondary_provider)
            if secondary_provider:
                secondary_config = config.get("modules", {}).get(secondary_provider, {}).get("config", {})
                settings["secondary_api_key"] = secondary_config.get("api_key", "")
                settings["secondary_model"] = secondary_config.get("model", "")
                settings["secondary_temperature"] = secondary_config.get("temperature", 1.0)

            # Get proxy settings
            proxy_config = config.get("modules", {}).get("proxy_client", {}).get("config", {})
            settings["use_proxy"] = proxy_config.get("use_proxy", False)
            settings["proxy_url"] = proxy_config.get("proxy_url", "")
            settings["proxy_username"] = proxy_config.get("proxy_username", "")
            settings["proxy_password"] = proxy_config.get("proxy_password", "")

            return create_response(
                request.request_id,
                settings=settings
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to get settings: {str(e)}"
            )

    def _handle_update_settings(self, request: IPCRequest) -> str:
        """Handle UPDATE_SETTINGS request - update LLM settings in config."""
        settings = request.data.get("settings", {})

        if not settings:
            return create_error_response(request.request_id, "Missing settings")

        try:
            print(f"[SETTINGS] Settings to update: {list(settings.keys())}")

            # LLM routing fields (go in "llm" section)
            routing_fields = {"primary_provider", "secondary_provider", "use_secondary_for_automation"}

            # Special fields that don't get saved directly
            excluded_fields = {"provider", "enable_secondary"}

            # Get provider names
            primary_provider = settings.get("primary_provider", self.bridge.current_provider or "claude_api_client")
            secondary_provider = settings.get("secondary_provider", "")

            # Handle enable_secondary toggle
            if "enable_secondary" in settings and not settings["enable_secondary"]:
                # User disabled secondary, clear the secondary_provider
                secondary_provider = ""
                settings["secondary_provider"] = ""

            # Update LLM routing settings
            for field in routing_fields:
                if field in settings:
                    config_key = f"llm.{field}"
                    value = settings[field]
                    print(f"[SETTINGS] Setting {config_key} = {value}")
                    self.bridge.config_loader.set(config_key, value)

            # Auto-enable primary provider module
            if primary_provider:
                print(f"[SETTINGS] Auto-enabling primary provider module: {primary_provider}")
                self.bridge.config_loader.set(f"modules.{primary_provider}.enabled", True)
                self.bridge.config_loader.set(f"modules.{primary_provider}.config.enabled", True)

            # Auto-enable secondary provider module
            if secondary_provider:
                print(f"[SETTINGS] Auto-enabling secondary provider module: {secondary_provider}")
                self.bridge.config_loader.set(f"modules.{secondary_provider}.enabled", True)
                self.bridge.config_loader.set(f"modules.{secondary_provider}.config.enabled", True)

            # Update primary provider settings (primary_* prefix)
            for key, value in settings.items():
                if key.startswith("primary_") and key not in excluded_fields:
                    field_name = key[8:]  # Remove "primary_" prefix
                    # Map field names to config names
                    if field_name == "prompt_caching":
                        field_name = "use_prompt_caching"

                    # Convert types for validation
                    if field_name in ("max_tokens", "thinking_budget_tokens"):
                        # Convert to int
                        try:
                            value = int(value) if value not in ("", None) else value
                        except (ValueError, TypeError):
                            print(f"[SETTINGS] Warning: Could not convert {field_name}={value} to int")
                    elif field_name == "temperature":
                        # Convert to float
                        try:
                            value = float(value) if value not in ("", None) else value
                        except (ValueError, TypeError):
                            print(f"[SETTINGS] Warning: Could not convert {field_name}={value} to float")

                    config_key = f"modules.{primary_provider}.config.{field_name}"
                    print(f"[SETTINGS] Setting {config_key} = {value}")
                    self.bridge.config_loader.set(config_key, value)

            # Update secondary provider settings (secondary_* prefix)
            if secondary_provider:
                for key, value in settings.items():
                    if key.startswith("secondary_") and key not in excluded_fields:
                        field_name = key[10:]  # Remove "secondary_" prefix

                        # Convert types for validation
                        if field_name in ("max_tokens", "thinking_budget_tokens"):
                            # Convert to int
                            try:
                                value = int(value) if value not in ("", None) else value
                            except (ValueError, TypeError):
                                print(f"[SETTINGS] Warning: Could not convert {field_name}={value} to int")
                        elif field_name == "temperature":
                            # Convert to float
                            try:
                                value = float(value) if value not in ("", None) else value
                            except (ValueError, TypeError):
                                print(f"[SETTINGS] Warning: Could not convert {field_name}={value} to float")

                        config_key = f"modules.{secondary_provider}.config.{field_name}"
                        print(f"[SETTINGS] Setting {config_key} = {value}")
                        self.bridge.config_loader.set(config_key, value)

            # Update proxy settings (proxy_* prefix or use_proxy)
            proxy_fields = {k: v for k, v in settings.items() if k.startswith("proxy_") or k == "use_proxy"}
            if proxy_fields:
                for key, value in proxy_fields.items():
                    # Remove "proxy_" prefix if present
                    field_name = key[6:] if key.startswith("proxy_") else key
                    config_key = f"modules.proxy_client.config.{field_name}"
                    print(f"[SETTINGS] Setting {config_key} = {value}")
                    self.bridge.config_loader.set(config_key, value)

            # Persist to file
            print(f"[SETTINGS] Saving configuration to file...")
            self.bridge.config_loader.save()

            # Reinitialize LLM clients (both primary and secondary)
            print(f"[SETTINGS] Reinitializing LLM clients...")
            self.bridge._initialize_llm_clients()

            return create_response(
                request.request_id,
                settings=settings,
                message=f"Settings updated successfully"
            )

        except Exception as e:
            import traceback
            traceback.print_exc()  # Print full stack trace
            return create_error_response(
                request.request_id,
                f"Failed to update settings: {str(e)}"
            )


__all__ = ["SettingsHandler"]
