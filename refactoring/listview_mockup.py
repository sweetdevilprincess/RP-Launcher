"""ListView Mockup - Demo to visualize how ListView would work with BranchableMessage.

This is a standalone demo you can run to see how ListView looks and behaves.

Run with: python listview_mockup.py
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Button
from textual.containers import Horizontal

from src.presentation.tui.components.simple_message import SimpleMessage


class ListViewMockup(App):
    """Demo app to show ListView with BranchableMessage widgets."""

    CSS = """
    Screen {
        background: $surface;
    }

    #chat-area {
        height: 1fr;
        border: solid $primary;
        margin: 1 2;
    }

    #controls {
        height: auto;
        dock: bottom;
        padding: 1 2;
        background: $panel;
    }

    #controls Button {
        margin: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.message_counter = 0

    def compose(self) -> ComposeResult:
        """Compose the demo app."""
        yield Header()

        # The ListView - this is what would replace ScrollableContainer
        yield ListView(id="chat-area")

        # Control buttons at the bottom
        with Horizontal(id="controls"):
            yield Button("Add User Message", id="add-user", variant="primary")
            yield Button("Add System Message", id="add-system", variant="success")
            yield Button("Add DM Message", id="add-dm", variant="warning")
            yield Button("Simulate Streaming", id="simulate-stream")

        yield Footer()

    async def on_mount(self) -> None:
        """Add some initial messages to demonstrate."""
        # Add a system message
        await self._add_message("system", "Welcome to the ListView mockup! This demonstrates how your chat would look using ListView instead of ScrollableContainer.")

        # Add a user message
        await self._add_message("you", "Hello! This is my message.")

        # Add a DM response
        await self._add_message("claude", "Hello! I'm the DM. This is my response. Notice how these messages are interactive - hover over them to see the action buttons!")

    async def _add_message(self, sender: str, content: str) -> SimpleMessage:
        """Add a message to the ListView.

        This is the equivalent of your add_message method in ChatDisplay.
        """
        # Get the ListView
        list_view = self.query_one("#chat-area", ListView)

        self.log(f"ListView found: {list_view}")
        self.log(f"Current ListView length: {len(list_view)}")

        # TEST: Use SimpleMessage with Rich Align (no CSS dock)
        message_widget = SimpleMessage(
            sender=sender,
            content=content,
            message_index=self.message_counter,
            id=f"msg-{self.message_counter}"
        )

        self.log(f"Created SimpleMessage widget: {message_widget}")

        self.message_counter += 1

        # Wrap it in a ListItem and append to ListView
        list_item = ListItem(message_widget)
        self.log(f"Created ListItem: {list_item}")

        await list_view.append(list_item)
        self.log(f"Appended to ListView, new length: {len(list_view)}")

        # Auto-scroll to bottom
        list_view.index = len(list_view) - 1
        self.log(f"Scrolled to index: {list_view.index}")

        # Show notification
        self.notify(f"Added message #{self.message_counter - 1}: {sender}", severity="information")

        return message_widget

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id

        if button_id == "add-user":
            await self._add_message("you", f"This is user message #{self.message_counter}")

        elif button_id == "add-system":
            await self._add_message("system", f"This is system message #{self.message_counter}")

        elif button_id == "add-dm":
            await self._add_message("claude", f"This is DM message #{self.message_counter}")

        elif button_id == "simulate-stream":
            # Simulate streaming like LLM responses
            import asyncio
            message_widget = await self._add_message("claude", "")

            # Simulate chunks arriving
            chunks = [
                "This is ",
                "a simulated ",
                "streaming ",
                "response. ",
                "Notice how ",
                "the content ",
                "updates ",
                "in real-time! "
            ]

            for chunk in chunks:
                message_widget.append_content(chunk)
                await asyncio.sleep(0.1)  # Simulate network delay

    def on_simple_message_branch_requested(self, message: SimpleMessage.BranchRequested) -> None:
        """Handle branch button clicks."""
        self.notify(
            f"Branch requested from message #{message.message_index}: {message.sender}",
            severity="information",
            title="Branch Action"
        )

    def on_simple_message_bookmark_requested(self, message: SimpleMessage.BookmarkRequested) -> None:
        """Handle bookmark button clicks."""
        self.notify(
            f"Bookmark requested for message #{message.message_index}",
            severity="warning",
            title="Bookmark (Not Implemented)"
        )

    def on_simple_message_edit_requested(self, message: SimpleMessage.EditRequested) -> None:
        """Handle edit button clicks."""
        self.notify(
            f"Edit requested for message #{message.message_index}: {message.sender}",
            severity="warning",
            title="Edit (Not Implemented)"
        )

    def on_simple_message_more_requested(self, message: SimpleMessage.MoreRequested) -> None:
        """Handle more button clicks."""
        self.notify(
            f"More options for message #{message.message_index}",
            severity="warning",
            title="More (Not Implemented)"
        )


if __name__ == "__main__":
    app = ListViewMockup()
    app.run()
