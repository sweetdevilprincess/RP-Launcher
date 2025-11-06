"""Custom message events for chat display.

This module defines message events used for thread-safe communication
between background threads (IPC callbacks) and the UI thread (widgets).
"""

from __future__ import annotations

import uuid
from textual.message import Message


class AddMessageRequest(Message):
    """Request to add a new message to chat display.

    This message is posted when a new chat message should be displayed.
    It's thread-safe and can be posted from background threads (e.g., IPC callbacks).

    Attributes:
        message_id: Unique identifier for this message (auto-generated if not provided)
        sender: Message sender ("you", "system", "claude", or custom)
        content: Initial message content
        response_num: Optional response number from session (for branch points)
    """

    def __init__(
        self,
        sender: str,
        content: str,
        message_id: str | None = None,
        response_num: int | None = None
    ) -> None:
        """Initialize add message request.

        Args:
            sender: Message sender identifier
            content: Message text content
            message_id: Optional message ID (auto-generated if None)
            response_num: Optional response number from session (for accurate branch points)
        """
        super().__init__()
        self.message_id = message_id or str(uuid.uuid4())
        self.sender = sender
        self.content = content
        self.response_num = response_num


class UpdateMessageRequest(Message):
    """Request to update an existing message (for streaming).

    This message is posted when new content should be appended to an existing
    message, typically during streaming responses from the LLM.

    Attributes:
        message_id: ID of the message to update
        chunk: Content chunk to append
    """

    def __init__(self, message_id: str, chunk: str) -> None:
        """Initialize update message request.

        Args:
            message_id: ID of message to update
            chunk: Text chunk to append to message
        """
        super().__init__()
        self.message_id = message_id
        self.chunk = chunk


__all__ = ["AddMessageRequest", "UpdateMessageRequest"]
