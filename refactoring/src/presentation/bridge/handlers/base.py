"""Base Handler - Abstract base class for all IPC message handlers.

This module defines the handler pattern used throughout the Bridge service.
Each handler is responsible for processing specific types of IPC messages
and delegating to appropriate bridge services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.infrastructure.ipc import IPCRequest

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class BaseHandler(ABC):
    """Abstract base class for IPC message handlers.

    Handler Pattern:
    ---------------
    Each handler class processes one or more related IPC message types.
    Handlers have access to the BridgeService instance and can delegate
    to any of its services (entity_service, config_loader, etc.).

    Usage:
    ------
    ```python
    class MyHandler(BaseHandler):
        def handle(self, request: IPCRequest) -> str:
            # Access bridge services
            data = self.bridge.entity_service.get_data()

            # Return JSON response
            return create_response(request.request_id, data=data)
    ```

    Attributes:
        bridge: Reference to the BridgeService instance with all initialized services
    """

    def __init__(self, bridge: BridgeService):
        """Initialize handler with bridge reference.

        Args:
            bridge: BridgeService instance providing access to all services
        """
        self.bridge = bridge

    @abstractmethod
    def handle(self, request: IPCRequest) -> str:
        """Handle an IPC request and return JSON response.

        This method must be implemented by all handler subclasses.
        It should:
        1. Extract data from request.data
        2. Validate required fields
        3. Delegate to appropriate bridge services
        4. Return JSON response using create_response() or create_error_response()

        Args:
            request: IPC request containing message type and data

        Returns:
            JSON string response (success or error)

        Example:
            ```python
            def handle(self, request: IPCRequest) -> str:
                try:
                    data = self.bridge.some_service.get_data()
                    return create_response(request.request_id, data=data)
                except Exception as e:
                    return create_error_response(request.request_id, str(e))
            ```
        """
        raise NotImplementedError("Handler must implement handle() method")


__all__ = ["BaseHandler"]
