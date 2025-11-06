"""Branchable Message Widget - Chat message with hover actions for branching.

This widget displays a chat message with interactive hover actions that allow
users to branch from that specific point in the conversation timeline.
"""

from __future__ import annotations

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Static


class BranchableMessage(Vertical):
    """A chat message with hover actions for branching and bookmarking.

    Features:
    - Displays message with sender-based styling
    - Shows action buttons on hover (Branch, Bookmark, More)
    - Posts messages when actions are triggered
    - Maintains message index for branch creation
    """

    DEFAULT_CSS = """
    BranchableMessage {
        height: auto;
        padding: 0 1;
    }

    BranchableMessage .message-bubble {
        height: auto;
        width: 100%;
    }

    BranchableMessage .message-actions {
        height: auto;
        layout: horizontal;
        align: center middle;
        padding: 1 1 0 1;
        display: none;
    }

    BranchableMessage:hover .message-bubble {
        border: solid $accent;
    }

    BranchableMessage .action-btn {
        margin: 0 1 0 0;
        min-width: 12;
    }

    /* Sender-specific alignments */
    BranchableMessage.msg-you .message-bubble {
        dock: right;
    }

    BranchableMessage.msg-system .message-bubble {
        align: center middle;
    }

    BranchableMessage.msg-dm .message-bubble {
        dock: left;
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

    def __init__(
        self,
        sender: str,
        content: str,
        message_index: int,
        **kwargs
    ):
        """Initialize branchable message.

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
        self._actions_visible = False

    def compose(self) -> ComposeResult:
        """Compose the branchable message widget."""
        # Create the message bubble
        yield Static(
            self._create_message_bubble(),
            classes="message-bubble"
        )

        # Create action buttons (hidden by default)
        with Horizontal(classes="message-actions", id=f"actions-{self.message_index}"):
            yield Button("🌿 Branch", variant="primary", classes="action-btn", id=f"branch-{self.message_index}")
            yield Button("📍 Bookmark", classes="action-btn", id=f"bookmark-{self.message_index}")
            yield Button("⋯ More", classes="action-btn", id=f"more-{self.message_index}")

    def on_mount(self) -> None:
        """Set up the widget after mounting."""
        # Add sender-specific class for styling
        sender_key = self.sender.lower()
        if sender_key in ("you", "system", "claude"):
            self.add_class(f"msg-{sender_key if sender_key != 'claude' else 'dm'}")

    def append_content(self, chunk: str) -> None:
        """Append content chunk to message (for streaming).

        This method appends new content and debounces UI updates to avoid
        excessive redraws during rapid streaming. Updates are batched and
        applied every 100ms.

        Args:
            chunk: Text chunk to append

        Note:
            This method is thread-safe when called via UpdateMessageRequest.
            The actual UI update is debounced and runs on the UI thread.
        """
        if not self.is_mounted:
            # Widget has been removed, ignore update
            return

        # Append chunk to content
        self.content += chunk

        # Debounce UI updates: only update every 100ms
        if not hasattr(self, '_pending_update') or not self._pending_update:
            self._pending_update = True
            self.set_timer(0.1, self._do_update)

    def _do_update(self) -> None:
        """Perform the actual UI update (called after debounce delay)."""
        self._pending_update = False

        if not self.is_mounted:
            return

        try:
            # Update the message bubble with new content
            bubble_static = self.query_one(".message-bubble", Static)
            bubble_static.update(self._create_message_bubble())
        except Exception as e:
            # Log error but don't crash
            self.app.log(f"Error updating message bubble: {e}")

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

        # Map sender to display style
        style_map = {
            "you": ("You", "cyan", Style(bgcolor="rgb(30,40,50)")),
            "system": ("System", "yellow", Style(bgcolor="rgb(40,40,30)")),
            "claude": ("DM", "magenta", Style(bgcolor="rgb(40,30,40)")),
        }
        label, border, panel_style = style_map.get(
            sender_key,
            (sender_key or "DM", "magenta", Style(bgcolor="rgb(40,30,40)"))
        )

        # Create message bubble
        return Panel(
            body_text,
            title=f"[b]{label}[/]",
            border_style=border,
            box=box.ROUNDED,
            padding=(0, 1),
            style=panel_style,
        )

    def on_enter(self, event: events.Enter) -> None:
        """Show actions when mouse enters the message.

        Args:
            event: Enter event
        """
        # Show the actions container
        actions = self.query_one(".message-actions")
        actions.styles.display = "block"
        self._actions_visible = True

    def on_leave(self, event: events.Leave) -> None:
        """Hide actions when mouse leaves the message.

        Args:
            event: Leave event
        """
        # Hide the actions container
        actions = self.query_one(".message-actions")
        actions.styles.display = "none"
        self._actions_visible = False

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
        elif button_id.startswith("more-"):
            # Show more options menu (TODO: implement)
            self.app.notify(f"More options for message #{self.message_index}", severity="information")


__all__ = ["BranchableMessage"]
