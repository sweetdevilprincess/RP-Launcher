"""Provider Handler - Handles LLM provider management IPC requests.

This handler processes provider-related requests including:
- GET_PROVIDERS: List all available LLM providers
- SET_PROVIDER: Switch to a different LLM provider
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.infrastructure.ipc import IPCMessageType, IPCRequest, create_error_response, create_response
from src.infrastructure.llm.registry import list_providers

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class ProviderHandler(BaseHandler):
    """Handler for LLM provider management operations.

    Delegates to bridge._initialize_llm_client for provider switching.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route provider request to appropriate handler method.

        Args:
            request: IPC request with provider operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.GET_PROVIDERS:
            return self._handle_get_providers(request)
        elif request_type == IPCMessageType.SET_PROVIDER:
            return self._handle_set_provider(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown provider request type: {request.type}"
            )

    def _handle_get_providers(self, request: IPCRequest) -> str:
        """Handle GET_PROVIDERS request."""
        providers = list_providers()

        provider_list = [
            {
                "name": spec.provider_id,
                "display_name": spec.label,
                "description": spec.description
            }
            for spec in providers.values()
        ]

        return create_response(
            request.request_id,
            providers=provider_list,
            current_provider=self.bridge.current_provider
        )

    def _handle_set_provider(self, request: IPCRequest) -> str:
        """Handle SET_PROVIDER request."""
        provider_name = request.data.get("provider")
        if not provider_name:
            return create_error_response(request.request_id, "Missing provider name")

        try:
            self.bridge._initialize_llm_client(provider_name)
            return create_response(
                request.request_id,
                provider=self.bridge.current_provider,
                message=f"Switched to {provider_name}"
            )
        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to switch provider: {str(e)}"
            )


__all__ = ["ProviderHandler"]
