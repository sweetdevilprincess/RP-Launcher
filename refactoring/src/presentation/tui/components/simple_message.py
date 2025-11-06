"""Simple Message Widget - Chat message with hover support using Rich Align.

This is a simplified version that uses Rich's Align (like the backup) instead
of CSS dock property, to test if that fixes the rendering issue.
"""

from __future__ import annotations

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widgets import Static, Button


class SimpleMessage(Vertical):
    """A chat message with hover support.

    Uses Rich Align for positioning (like backup) instead of CSS dock.
    This should allow multiple messages to render properly.
    """

    DEFAULT_CSS = """
    SimpleMessage {
        height: auto;
        width: 100%;
        padding: 0 1;
    }

    SimpleMessage .message-content {
        height: auto;
        width: 100%;
    }

    SimpleMessage .message-actions {
        height: auto;
        width: 100%;
        layout: horizontal;
        padding: 0 1;
        display: none;
    }

    /* Align action buttons based on sender */
    SimpleMessage.msg-you .message-actions {
        align: right middle;
    }

    SimpleMessage.msg-system .message-actions {
        align: center middle;
    }

    SimpleMessage.msg-dm .message-actions {
        align: left middle;
    }

    SimpleMessage .action-btn {
        margin: 0 1;
        min-width: 3;
        width: auto;
        height: 3;
        padding: 0 1;
        background: transparent;
        border: none;
        color: $text;
    }

    SimpleMessage .action-btn:hover {
        background: $boost;
        text-style: bold;
    }
    """

    class BranchRequested(Message):
        """Posted when user clicks the Branch button."""
        def __init__(self, message_index: int, sender: str, content: str) -> None:
            super().__init__()
            self.message_index = message_index
            self.sender = sender
            self.content = content

    class BookmarkRequested(Message):
        """Posted when user clicks the Bookmark button."""
        def __init__(self, message_index: int) -> None:
            super().__init__()
            self.message_index = message_index

    class EditRequested(Message):
        """Posted when user clicks the Edit button."""
        def __init__(self, message_index: int, sender: str, content: str) -> None:
            super().__init__()
            self.message_index = message_index
            self.sender = sender
            self.content = content

    class CopyRequested(Message):
        """Posted when user clicks the Copy button."""
        def __init__(self, message_index: int, content: str) -> None:
            super().__init__()
            self.message_index = message_index
            self.content = content

    class MoreRequested(Message):
        """Posted when user clicks the More button."""
        def __init__(self, message_index: int) -> None:
            super().__init__()
            self.message_index = message_index

    def __init__(
        self,
        sender: str,
        content: str,
        message_index: int,
        **kwargs
    ):
        """Initialize simple message.

        Args:
            sender: Message sender ("you", "system", "claude", or custom)
            content: Message content text
            message_index: Index of this message in the conversation
            **kwargs: Additional arguments passed to Vertical
        """
        super().__init__(**kwargs)
        self.sender = sender
        self.content = content
        self.message_index = message_index
        self._hide_timer = None  # Timer for delayed button hiding

    def on_mount(self) -> None:
        """Set up the widget after mounting."""
        # Add sender-specific class for styling alignment
        sender_key = self.sender.lower()
        if sender_key in ("you", "system", "claude"):
            self.add_class(f"msg-{sender_key if sender_key != 'claude' else 'dm'}")

    def compose(self) -> ComposeResult:
        """Compose the message widget."""
        # Create the message bubble using Rich (like backup)
        bubble = self._create_message_bubble()

        # Align based on sender (like backup!)
        sender_key = self.sender.lower()
        if sender_key == "you":
            aligned = Align.right(bubble)
        elif sender_key == "system":
            aligned = Align.center(bubble)
        else:
            aligned = Align.left(bubble)

        # Yield Static containing the aligned panel
        yield Static(aligned, classes="message-content")

        # Yield action buttons (hidden by default, shown on hover)
        with Horizontal(classes="message-actions", id=f"actions-{self.message_index}"):
            yield Button("🌿", classes="action-btn", id=f"branch-{self.message_index}")
            yield Button("📍", classes="action-btn", id=f"bookmark-{self.message_index}")
            yield Button("✏️", classes="action-btn", id=f"edit-{self.message_index}")
            yield Button("📋", classes="action-btn", id=f"copy-{self.message_index}")
            yield Button("⋯", classes="action-btn", id=f"more-{self.message_index}")

    def _create_message_bubble(self) -> Panel:
        """Create the styled message panel.

        Returns:
            Rich Panel with appropriate styling for sender
        """
        sender_key = self.sender.lower()

        # System messages can include markup
        if sender_key == "system":
            body_text = Text.from_markup(self.content, justify="left")
        else:
            body_text = Text(self.content, justify="left")

        # Map sender to display style (same as backup)
        style_map = {
            "you": ("You", "cyan", Style(bgcolor="rgb(30,40,50)")),
            "system": ("System", "yellow", Style(bgcolor="rgb(40,40,30)")),
            "claude": ("DM", "magenta", Style(bgcolor="rgb(40,30,40)")),
        }
        label, border, panel_style = style_map.get(
            sender_key,
            (sender_key or "DM", "magenta", Style(bgcolor="rgb(40,30,40)"))
        )

        return Panel(
            body_text,
            title=f"[b]{label}[/]",
            border_style=border,
            box=box.ROUNDED,
            padding=(0, 1),
            style=panel_style,
        )

    def append_content(self, chunk: str) -> None:
        """Append content chunk to message (for streaming).

        Args:
            chunk: Text chunk to append
        """
        if not self.is_mounted:
            return

        # Append chunk to content
        self.content += chunk

        # Debounce UI updates: only update every 100ms
        if not hasattr(self, '_pending_update') or not self._pending_update:
            self._pending_update = True
            self.set_timer(0.1, self._do_update)

    def update_message_index(self, message_index: int) -> None:
        """Update the message index (for fixing streaming messages).

        Args:
            message_index: New message index to set
        """
        self.message_index = message_index

    def _do_update(self) -> None:
        """Perform the actual UI update (called after debounce delay)."""
        self._pending_update = False

        if not self.is_mounted:
            return

        try:
            # Recreate the bubble with new content
            bubble = self._create_message_bubble()

            # Re-align
            sender_key = self.sender.lower()
            if sender_key == "you":
                aligned = Align.right(bubble)
            elif sender_key == "system":
                aligned = Align.center(bubble)
            else:
                aligned = Align.left(bubble)

            # Update the Static widget
            content_static = self.query_one(".message-content", Static)
            content_static.update(aligned)
        except Exception as e:
            # Log error but don't crash
            if hasattr(self, 'app'):
                self.app.log(f"Error updating message bubble: {e}")

    def on_enter(self, event: events.Enter) -> None:
        """Handle mouse entering the message - show action buttons.

        Args:
            event: Enter event
        """
        # Cancel any pending hide timer
        if self._hide_timer is not None:
            self._hide_timer.stop()
            self._hide_timer = None

        # Show the actions container immediately
        try:
            actions = self.query_one(".message-actions")
            actions.styles.display = "block"
        except Exception:
            pass  # Actions might not be mounted yet

    def on_leave(self, event: events.Leave) -> None:
        """Handle mouse leaving the message - hide action buttons after delay.

        Args:
            event: Leave event
        """
        # Don't hide immediately - set a timer so user can move to buttons
        if self._hide_timer is not None:
            self._hide_timer.stop()

        self._hide_timer = self.set_timer(0.2, self._hide_actions)

    def _hide_actions(self) -> None:
        """Hide the action buttons (called after delay)."""
        try:
            actions = self.query_one(".message-actions")
            actions.styles.display = "none"
            self._hide_timer = None
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle action button clicks.

        Args:
            event: Button pressed event
        """
        button_id = event.button.id or ""

        if button_id.startswith("branch-"):
            # Post branch requested message
            self.post_message(
                self.BranchRequested(
                    self.message_index,
                    self.sender,
                    self.content
                )
            )
        elif button_id.startswith("bookmark-"):
            # Post bookmark requested message
            self.post_message(
                self.BookmarkRequested(self.message_index)
            )
        elif button_id.startswith("edit-"):
            # Post edit requested message
            self.post_message(
                self.EditRequested(
                    self.message_index,
                    self.sender,
                    self.content
                )
            )
        elif button_id.startswith("copy-"):
            # Post copy requested message
            self.post_message(
                self.CopyRequested(
                    self.message_index,
                    self.content
                )
            )
        elif button_id.startswith("more-"):
            # Post more options requested message
            self.post_message(
                self.MoreRequested(self.message_index)
            )


__all__ = ["SimpleMessage"]
