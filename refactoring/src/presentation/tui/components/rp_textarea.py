"""Custom text area widget with enhanced input controls.

This module provides a custom TextArea that supports:
- Ctrl+Enter to submit messages
- Enter for new lines
"""

from __future__ import annotations

from textual.message import Message
from textual.widgets import TextArea


class RPTextArea(TextArea):
    """Custom TextArea with Ctrl+Enter to send messages.

    Key bindings:
    - Ctrl+Enter: Submit message (posts Submitted message)
    - Enter: New line (works naturally)

    The submitted message bubbles up to parent components
    for handling.
    """

    class Submitted(Message, bubble=True):
        """Message posted when Ctrl+Enter is pressed.

        This message bubbles up to parent components when the user
        presses Ctrl+Enter, allowing them to handle the submission.
        """

        def __init__(self, text_area: "RPTextArea") -> None:
            """Initialize submitted message.

            Args:
                text_area: The text area that posted this message
            """
            super().__init__()
            self.text_area = text_area

    # Note: The actual Ctrl+Enter binding is typically handled by the
    # parent app or screen, which listens for ctrl+enter and posts
    # the Submitted message when detected.


__all__ = ["RPTextArea"]
