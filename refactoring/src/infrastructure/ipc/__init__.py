"""Inter-process communication module for TUI-Bridge communication."""

# New socket-based IPC (TUI-Bridge)
from .ipc_protocol import (
    IPCMessage,
    IPCRequest,
    IPCResponse,
    IPCMessageType,
    create_request,
    create_response,
    create_error_response,
    create_streaming_chunk,
    create_streaming_done,
    parse_message,
)
from .socket_server import SocketServer
from .socket_client import SocketClient

# Legacy file-based IPC (Filesystem module)
from .ipc_channel import (
    IpcChannel,
    IpcInputPayload,
    IpcResponsePayload,
)

__all__ = [
    # New socket-based IPC
    "IPCMessage",
    "IPCRequest",
    "IPCResponse",
    "IPCMessageType",
    "create_request",
    "create_response",
    "create_error_response",
    "create_streaming_chunk",
    "create_streaming_done",
    "parse_message",
    "SocketServer",
    "SocketClient",
    # Legacy file-based IPC
    "IpcChannel",
    "IpcInputPayload",
    "IpcResponsePayload",
]
