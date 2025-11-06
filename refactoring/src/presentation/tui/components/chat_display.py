"""Chat display widget for showing RP conversation history.

This module provides the central chat panel that displays messages
with appropriate styling and alignment based on sender. Messages are
displayed as interactive widgets that support hover actions for branching.
"""

from __future__ import annotations

from typing import Dict, Deque
from collections import deque

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical

from .simple_message import SimpleMessage


class ChatDisplay(ScrollableContainer):
    """Center panel showing RP conversation history.

    This scrollable container displays chat messages as interactive widgets with:
    - Different styling per sender (You, System, DM)
    - Hover actions for branching and bookmarking
    - Real-time streaming support for LLM responses
    - Performance optimization (limits to last 100 messages)
    - Auto-scroll to bottom on new message

    Thread Safety:
    The public methods (add_message, append_chunk) are thread-safe and can be
    called from background IPC threads. They use app.call_from_thread to schedule
    UI operations on the UI thread.
    """

    DEFAULT_CSS = """
    ChatDisplay {
        height: 1fr;
        overflow-y: auto;
        background: $panel;
        padding: 0;
    }
    #messages-container {
        width: 100%;
        height: auto;
        padding: 0;
    }
    """

    def __init__(self, **kwargs):
        """Initialize chat display.

        Args:
            **kwargs: Additional arguments passed to ScrollableContainer
        """
        super().__init__(**kwargs)
        # Container for messages (set in on_mount)
        self._messages_container: Vertical | None = None
        # Track active messages by ID for updates
        self._by_id: Dict[str, SimpleMessage] = {}
        # Track message order for trimming
        self._order: Deque[str] = deque()
        # Message index counter for branch points
        self.message_count = 0
        # Maximum messages to keep
        self.max_display_messages = 100

        # Debug file logging
        self._debug_file = None
        self._setup_debug_logging()

    def _setup_debug_logging(self) -> None:
        """Set up debug logging to file."""
        try:
            from pathlib import Path
            import datetime

            # Try to find logs directory
            log_file = Path.cwd() / "RPs" / "test_rp" / "logs" / "chat_display_debug.log"
            if not log_file.parent.exists():
                # Try alternative path
                for possible_dir in Path.cwd().rglob("logs"):
                    if possible_dir.is_dir():
                        log_file = possible_dir / "chat_display_debug.log"
                        break

            if log_file.parent.exists():
                self._debug_file = open(log_file, 'a', encoding='utf-8')
                self._debug_file.write(f"\n{'='*80}\n")
                self._debug_file.write(f"ChatDisplay initialized at {datetime.datetime.now()}\n")
                self._debug_file.write(f"{'='*80}\n")
                self._debug_file.flush()
        except Exception:
            pass

    def _debug_log(self, message: str) -> None:
        """Write debug message to file."""
        try:
            if self._debug_file:
                import datetime
                timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
                self._debug_file.write(f"[{timestamp}] {message}\n")
                self._debug_file.flush()
        except Exception:
            pass

    def _schedule_ui(self, coroutine, *, exclusive: bool = False) -> None:
        """Ensure the coroutine runs on Textual's UI thread."""
        import threading
        current_thread = threading.get_ident()
        app_thread = getattr(self.app, '_thread_id', None)

        self._debug_log(f"_schedule_ui: current_thread={current_thread}, app_thread={app_thread}")

        if app_thread == current_thread:
            self._debug_log("Running on UI thread directly")
            self.run_worker(coroutine, thread=False, exclusive=exclusive)
        else:
            self._debug_log("Calling from background thread via call_from_thread")
            self.app.call_from_thread(
                self.run_worker,
                coroutine,
                thread=False,
                exclusive=exclusive,
            )

    def compose(self) -> ComposeResult:
        """Compose the chat display.

        Yields a stable Vertical container that messages will be mounted into.
        This is critical - we need a child container to mount widgets into,
        not mount directly to ScrollableContainer.

        Yields:
            Vertical container for messages
        """
        # Yield a stable container for messages
        yield Vertical(id="messages-container")

    def on_mount(self) -> None:
        """Cache the messages container after mounting."""
        self._messages_container = self.query_one("#messages-container", Vertical)

    # =========================================================================
    # UI-THREAD METHODS (must be called from UI thread)
    # =========================================================================

    async def _ui_add_message(
        self,
        sender: str,
        content: str,
        message_id: str,
        response_num: int | None = None
    ) -> None:
        """UI-thread: Create and mount a new message widget.

        This method MUST be called from the UI thread. Use add_message()
        from background threads.

        Args:
            sender: Message sender ("you", "system", "claude", or custom)
            content: Message content text
            message_id: Unique identifier for this message
            response_num: Optional response number from session (for accurate branch points)
        """
        self._debug_log(f"_ui_add_message: sender={sender}, id={message_id}, content_len={len(content)}")

        if not self._messages_container:
            self._debug_log("ERROR: messages container not ready!")
            return

        self._debug_log("Container exists, checking attachment...")

        # CRITICAL FIX: Wait for container to be fully attached before mounting
        # This prevents MountError when messages are added during initialization
        max_wait = 50  # Maximum 5 seconds (50 * 0.1s)
        wait_count = 0
        while not self._messages_container.is_attached and wait_count < max_wait:
            import asyncio
            await asyncio.sleep(0.1)  # Wait 100ms
            wait_count += 1

        if not self._messages_container.is_attached:
            self._debug_log(f"ERROR: Container failed to attach after {wait_count * 0.1}s")
            return

        self._debug_log("Container attached! Creating widget...")

        # Use response_num if provided, otherwise use display counter
        message_index = response_num if response_num is not None else self.message_count

        # Create widget
        widget = SimpleMessage(
            sender=sender,
            content=content,
            message_index=message_index,
            id=f"msg-{message_id}"
        )

        self._debug_log("Widget created, tracking it...")

        # Track widget
        self._by_id[message_id] = widget
        self._order.append(message_id)
        self.message_count += 1

        self._debug_log("Mounting widget to container...")

        # Mount to container (not to self!)
        await self._messages_container.mount(widget)

        self._debug_log(f"Widget mounted! Total messages: {self.message_count}")

        # Trim old messages if needed
        if len(self._order) > self.max_display_messages:
            await self._trim_old_messages()

        # Scroll to bottom (scroll_end is synchronous, not async)
        self.scroll_end(animate=False, force=True)

        self._debug_log("Message add complete, scrolled to bottom")

    async def _ui_append_chunk(self, message_id: str, chunk: str) -> None:
        """UI-thread: Append content chunk to existing message.

        This method MUST be called from the UI thread. Use append_chunk()
        from background threads.

        Args:
            message_id: ID of message to update
            chunk: Text chunk to append
        """
        self._debug_log(f"_ui_append_chunk: message_id={message_id}, chunk_len={len(chunk)}")

        # Find the message widget
        widget = self._by_id.get(message_id)

        self._debug_log(f"_ui_append_chunk: widget found = {widget is not None}")

        if widget is None:
            self._debug_log(f"_ui_append_chunk: Widget not found, creating empty message...")
            # Message not found - might be first chunk, create empty message
            # This will wait for container to be attached
            await self._ui_add_message("claude", "", message_id)
            widget = self._by_id.get(message_id)
            self._debug_log(f"_ui_append_chunk: After create, widget found = {widget is not None}")

        if widget:
            self._debug_log(f"_ui_append_chunk: Appending to widget...")
            # Append content to widget (debounced internally)
            widget.append_content(chunk)
            self._debug_log(f"_ui_append_chunk: Content appended, scrolling...")
            # Scroll to bottom (scroll_end is synchronous, not async)
            self.scroll_end(animate=False, force=True)
            self._debug_log(f"_ui_append_chunk: Complete!")
        else:
            self._debug_log(f"_ui_append_chunk: ERROR - widget is still None after create!")

    async def _trim_old_messages(self) -> None:
        """Remove oldest messages when limit is exceeded."""
        while len(self._order) > self.max_display_messages:
            # Get oldest message ID
            old_message_id = self._order.popleft()

            # Get widget
            widget = self._by_id.pop(old_message_id, None)

            # Remove from display
            if widget and widget.is_mounted:
                await widget.remove()

    # =========================================================================
    # THREAD-SAFE PUBLIC API (safe to call from ANY thread)
    # =========================================================================

    def add_message(
        self,
        sender: str,
        content: str,
        message_id: str,
        response_num: int | None = None
    ) -> None:
        """Thread-safe: Add a new message to chat display.

        This method is safe to call from ANY thread (UI or background).
        It schedules the UI operation on the UI thread.

        Args:
            sender: Message sender ("you", "system", "claude", or custom)
            content: Message content text
            message_id: Unique identifier for this message
            response_num: Optional response number from session (for accurate branch points)
        """
        self._debug_log(f"add_message called: sender={sender}, id={message_id}")
        self._schedule_ui(
            self._ui_add_message(sender, content, message_id, response_num),
            exclusive=False,
        )

    def append_chunk(self, message_id: str, chunk: str) -> None:
        """Thread-safe: Append content to existing message (for streaming).

        This method is safe to call from ANY thread (UI or background).
        It schedules the UI operation on the UI thread.

        Args:
            message_id: ID of message to update
            chunk: Text chunk to append
        """
        self._debug_log(f"append_chunk called: message_id={message_id}, chunk_len={len(chunk)}")
        self._schedule_ui(
            self._ui_append_chunk(message_id, chunk),
            exclusive=False,
        )

    def update_message_index(self, message_id: str, message_index: int) -> None:
        """Thread-safe: Update the message index for a specific message.

        This is used to fix the response_num for streaming messages after
        the response is complete.

        Args:
            message_id: ID of message to update
            message_index: New message index (response_num)
        """
        widget = self._by_id.get(message_id)
        if widget and hasattr(widget, 'update_message_index'):
            widget.update_message_index(message_index)

    def clear_messages(self) -> None:
        """Clear all messages from chat display.

        Note: This is a synchronous method for compatibility, but removal
        happens asynchronously.
        """
        async def do_clear():
            """Async helper to clear messages."""
            # Remove all widgets
            for widget in self._by_id.values():
                if widget.is_mounted:
                    await widget.remove()

            # Clear tracking
            self._by_id.clear()
            self._order.clear()
            self.message_count = 0

        # Schedule async clear
        self._schedule_ui(do_clear(), exclusive=True)


__all__ = ["ChatDisplay"]
