"""Branch Creation Dialog - Modal screen for creating a new timeline branch.

This dialog allows users to create a new branch from a specific message,
providing fields for branch name, description, and tags.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Static


class BranchCreationDialog(ModalScreen[dict[str, str | bool] | None]):
    """Modal dialog for creating a new branch from a message.

    This screen displays a form where users can:
    - See which message they're branching from
    - Enter a branch name (required)
    - Enter an optional description
    - Add optional tags
    - Choose whether to switch to the new branch immediately
    """

    DEFAULT_CSS = """
    BranchCreationDialog {
        align: center middle;
    }

    BranchCreationDialog > Container {
        width: 70;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 2;
    }

    BranchCreationDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    BranchCreationDialog .section-label {
        margin-top: 1;
        margin-bottom: 1;
        color: $text-muted;
    }

    BranchCreationDialog .branch-from-info {
        background: $surface;
        border: round $primary;
        padding: 1;
        margin-bottom: 1;
        color: $text;
    }

    BranchCreationDialog .info-text {
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    BranchCreationDialog Input {
        width: 100%;
        margin-bottom: 1;
    }

    BranchCreationDialog .button-row {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    BranchCreationDialog Button {
        margin: 0 1;
        min-width: 16;
    }

    BranchCreationDialog Checkbox {
        margin-top: 1;
    }
    """

    def __init__(
        self,
        message_index: int,
        message_sender: str,
        message_content: str,
        **kwargs
    ):
        """Initialize branch creation dialog.

        Args:
            message_index: Index of the message to branch from
            message_sender: Sender of the message
            message_content: Content of the message
            **kwargs: Additional arguments for ModalScreen
        """
        super().__init__(**kwargs)
        self.message_index = message_index
        self.message_sender = message_sender
        self.message_content = message_content

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Container():
            yield Static(
                f"Create Branch from Message #{self.message_index}",
                classes="dialog-title"
            )

            # Show which message we're branching from
            yield Static("Branching from:", classes="section-label")
            yield Static(
                f"#{self.message_index} - {self.message_sender}: \"{self._truncate_content(self.message_content, 80)}\"",
                classes="branch-from-info"
            )

            yield Static(
                f"ℹ️ This will create a new timeline including messages 1-{self.message_index}",
                classes="info-text"
            )

            # Branch name input (required)
            yield Label("Branch name:", classes="section-label")
            yield Input(
                placeholder="e.g., tavern-explore, friendly-path",
                id="branch-name-input"
            )

            # Description input (optional)
            yield Label("Description (optional):", classes="section-label")
            yield Input(
                placeholder="Brief description of this branch",
                id="branch-description-input"
            )

            # Tags input (optional)
            yield Label("Tags (comma-separated, optional):", classes="section-label")
            yield Input(
                placeholder="e.g., social, combat, exploration",
                id="branch-tags-input"
            )

            # Switch immediately checkbox
            yield Checkbox(
                "Switch to new branch immediately",
                value=True,
                id="switch-immediately-checkbox"
            )

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Create Branch", variant="primary", id="create-btn")

    def on_mount(self) -> None:
        """Focus the branch name input when dialog opens."""
        self.query_one("#branch-name-input", Input).focus()

    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content to max_length with ellipsis.

        Args:
            content: Content to truncate
            max_length: Maximum length

        Returns:
            Truncated string
        """
        if len(content) <= max_length:
            return content
        return content[:max_length].strip() + "..."

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button pressed event
        """
        if event.button.id == "cancel-btn":
            # Dismiss without creating branch
            self.dismiss(None)

        elif event.button.id == "create-btn":
            # Validate and gather form data
            branch_name = self.query_one("#branch-name-input", Input).value.strip()

            if not branch_name:
                self.app.notify("Branch name is required", severity="warning")
                self.query_one("#branch-name-input", Input).focus()
                return

            # Gather all form data
            result = {
                "branch_name": branch_name,
                "description": self.query_one("#branch-description-input", Input).value.strip(),
                "tags": self.query_one("#branch-tags-input", Input).value.strip(),
                "switch_immediately": self.query_one("#switch-immediately-checkbox", Checkbox).value,
                "branch_point": self.message_index,
            }

            # Dismiss with result
            self.dismiss(result)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields - act as if Create was clicked.

        Args:
            event: Input submitted event
        """
        # Trigger the create button
        create_btn = self.query_one("#create-btn", Button)
        self.on_button_pressed(Button.Pressed(create_btn))


__all__ = ["BranchCreationDialog"]
