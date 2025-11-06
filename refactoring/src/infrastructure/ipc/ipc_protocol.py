"""IPC Protocol for TUI-Bridge Communication.

This module defines the message protocol for socket-based communication
between the TUI (client) and the Bridge (server).

Protocol Design:
- JSON-based messages
- Request/Response pattern
- Typed message enums
- Error handling
"""

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class IPCMessageType(Enum):
    """Message types for IPC communication."""

    # Client → Server (Requests)
    SEND_MESSAGE = "send_message"  # Send user message to LLM
    GET_STATE = "get_state"  # Get current session state
    GET_PROVIDERS = "get_providers"  # Get available LLM providers
    SET_PROVIDER = "set_provider"  # Switch LLM provider
    GET_TRIGGERS = "get_triggers"  # Get active triggers
    SET_TRIGGER = "set_trigger"  # Enable/disable trigger
    GET_TEMPLATES = "get_templates"  # Get available templates
    SET_TEMPLATE = "set_template"  # Switch narrative template
    TEST_MODE = "test_mode"  # Toggle testing mode
    PING = "ping"  # Health check
    SHUTDOWN = "shutdown"  # Graceful shutdown

    # Entity Management
    GET_ENTITIES = "get_entities"  # Get all entities
    CREATE_ENTITY = "create_entity"  # Create new entity
    UPDATE_ENTITY = "update_entity"  # Update existing entity
    DELETE_ENTITY = "delete_entity"  # Delete entity

    # Settings Management
    GET_SETTINGS = "get_settings"  # Get LLM settings
    UPDATE_SETTINGS = "update_settings"  # Update LLM settings

    # Module Management
    GET_MODULES = "get_modules"  # Get module states
    TOGGLE_MODULE = "toggle_module"  # Enable/disable module

    # Branch Management (SessionService)
    GET_BRANCHES = "get_branches"  # Get all branches
    CREATE_BRANCH = "create_branch"  # Create new branch
    SWITCH_BRANCH = "switch_branch"  # Switch to branch
    COMPARE_BRANCHES = "compare_branches"  # Compare two branches

    # Chapter Management
    COMPRESS_CHAPTER = "compress_chapter"  # Compress chapter into summary

    # Server → Client (Responses)
    RESPONSE = "response"  # Generic successful response
    ERROR = "error"  # Error response
    STREAMING_CHUNK = "streaming_chunk"  # Streaming response chunk
    STREAMING_DONE = "streaming_done"  # Streaming complete


@dataclass
class IPCMessage:
    """Base IPC message structure."""

    type: str  # Message type (from IPCMessageType)
    request_id: str  # Unique request ID for matching responses
    data: dict[str, Any]  # Message payload

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "IPCMessage":
        """Deserialize message from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class IPCRequest(IPCMessage):
    """Request message from TUI to Bridge."""

    @classmethod
    def create(cls, message_type: IPCMessageType, request_id: str, **kwargs) -> "IPCRequest":
        """Create a request message.

        Args:
            message_type: Type of request
            request_id: Unique ID for this request
            **kwargs: Request-specific data

        Returns:
            IPCRequest instance
        """
        return cls(type=message_type.value, request_id=request_id, data=kwargs)


@dataclass
class IPCResponse(IPCMessage):
    """Response message from Bridge to TUI."""

    success: bool = True  # Whether request succeeded
    error_message: str | None = None  # Error message if failed

    @classmethod
    def create(
        cls, request_id: str, success: bool = True, error_message: str | None = None, **kwargs
    ) -> "IPCResponse":
        """Create a response message.

        Args:
            request_id: ID of original request
            success: Whether request succeeded
            error_message: Error message if failed
            **kwargs: Response-specific data

        Returns:
            IPCResponse instance
        """
        return cls(
            type=IPCMessageType.RESPONSE.value,
            request_id=request_id,
            success=success,
            error_message=error_message,
            data=kwargs,
        )

    def to_json(self) -> str:
        """Serialize response to JSON string."""
        data_dict = asdict(self)
        return json.dumps(data_dict, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "IPCResponse":
        """Deserialize response from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


# =============================================================================
# Helper Functions
# =============================================================================


def create_request(message_type: IPCMessageType, request_id: str, **kwargs) -> str:
    """Create a request message and serialize to JSON.

    Args:
        message_type: Type of request
        request_id: Unique request ID
        **kwargs: Request data

    Returns:
        JSON string

    Example:
        >>> request = create_request(
        ...     IPCMessageType.SEND_MESSAGE,
        ...     "req_001",
        ...     user_message="Hello!",
        ...     session_id="session_123"
        ... )
    """
    req = IPCRequest.create(message_type, request_id, **kwargs)
    return req.to_json()


def create_response(request_id: str, success: bool = True, **kwargs) -> str:
    """Create a success response and serialize to JSON.

    Args:
        request_id: ID of original request
        success: Whether request succeeded
        **kwargs: Response data

    Returns:
        JSON string

    Example:
        >>> response = create_response(
        ...     "req_001",
        ...     llm_response="Hello! How can I help?",
        ...     metadata={"model": "claude-3-5-sonnet"}
        ... )
    """
    resp = IPCResponse.create(request_id, success=success, **kwargs)
    return resp.to_json()


def create_error_response(request_id: str, error_message: str, **kwargs) -> str:
    """Create an error response and serialize to JSON.

    Args:
        request_id: ID of original request
        error_message: Error description
        **kwargs: Additional error data

    Returns:
        JSON string

    Example:
        >>> error = create_error_response(
        ...     "req_001",
        ...     "Provider not available",
        ...     provider="gpt-4"
        ... )
    """
    resp = IPCResponse.create(request_id, success=False, error_message=error_message, **kwargs)
    return resp.to_json()


def create_streaming_chunk(request_id: str, chunk: str, **kwargs) -> str:
    """Create a streaming chunk message and serialize to JSON.

    Args:
        request_id: ID of original request
        chunk: Content chunk to stream
        **kwargs: Additional chunk data

    Returns:
        JSON string

    Example:
        >>> chunk_msg = create_streaming_chunk(
        ...     "req_001",
        ...     "Hello, ",
        ...     index=0
        ... )
    """
    message = IPCMessage(
        type=IPCMessageType.STREAMING_CHUNK.value,
        request_id=request_id,
        data={"chunk": chunk, **kwargs}
    )
    return message.to_json()


def create_streaming_done(request_id: str, **kwargs) -> str:
    """Create a streaming done message and serialize to JSON.

    Args:
        request_id: ID of original request
        **kwargs: Final metadata (usage stats, etc.)

    Returns:
        JSON string

    Example:
        >>> done_msg = create_streaming_done(
        ...     "req_001",
        ...     total_tokens=150,
        ...     input_tokens=50,
        ...     output_tokens=100
        ... )
    """
    message = IPCMessage(
        type=IPCMessageType.STREAMING_DONE.value,
        request_id=request_id,
        data=kwargs
    )
    return message.to_json()


def parse_message(json_str: str) -> IPCMessage:
    """Parse a JSON string into an IPC message.

    Args:
        json_str: JSON message string

    Returns:
        IPCMessage, IPCRequest, or IPCResponse

    Raises:
        json.JSONDecodeError: If invalid JSON
        ValueError: If invalid message structure
    """
    data = json.loads(json_str)

    # Determine message type
    if "success" in data:
        # Response message
        return IPCResponse.from_json(json_str)
    # Request message
    return IPCRequest.from_json(json_str)


# =============================================================================
# Message Validation
# =============================================================================


def validate_request(request: IPCRequest) -> bool:
    """Validate request message structure.

    Args:
        request: Request to validate

    Returns:
        True if valid

    Raises:
        ValueError: If invalid
    """
    if not request.type:
        raise ValueError("Request missing 'type' field")

    if not request.request_id:
        raise ValueError("Request missing 'request_id' field")

    # Validate message type
    try:
        IPCMessageType(request.type)
    except ValueError:
        raise ValueError(f"Invalid message type: {request.type}")

    return True


def validate_response(response: IPCResponse) -> bool:
    """Validate response message structure.

    Args:
        response: Response to validate

    Returns:
        True if valid

    Raises:
        ValueError: If invalid
    """
    if not response.request_id:
        raise ValueError("Response missing 'request_id' field")

    if not response.success and not response.error_message:
        raise ValueError("Error response missing 'error_message'")

    return True
