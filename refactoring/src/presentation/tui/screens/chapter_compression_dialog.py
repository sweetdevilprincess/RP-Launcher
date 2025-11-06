"""Chapter Compression Dialog - Modal screen for compressing a chapter.

This dialog allows users to compress the current chapter into a summary,
providing fields for chapter title and tags.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class ChapterCompressionDialog(ModalScreen[dict[str, str] | None]):
    """Modal dialog for compressing a chapter into a summary.

    This screen displays a form where users can:
    - See current chapter information (number, message range)
    - Enter a chapter title (optional)
    - Add optional tags for categorization
    - Confirm compression
    """

    DEFAULT_CSS = """
    ChapterCompressionDialog {
        align: center middle;
    }

    ChapterCompressionDialog > Container {
        width: 70;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 2;
    }

    ChapterCompressionDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    ChapterCompressionDialog .section-label {
        margin-top: 1;
        margin-bottom: 1;
        color: $text-muted;
    }

    ChapterCompressionDialog .chapter-info {
        background: $surface;
        border: round $primary;
        padding: 1;
        margin-bottom: 1;
        color: $text;
    }

    ChapterCompressionDialog .info-text {
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    ChapterCompressionDialog Input {
        width: 100%;
        margin-bottom: 1;
    }

    ChapterCompressionDialog .button-row {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    ChapterCompressionDialog Button {
        margin: 0 1;
        min-width: 16;
    }
    """

    def __init__(
        self,
        chapter_number: int,
        message_count: int,
        word_count: int | None = None,
        **kwargs
    ):
        """Initialize chapter compression dialog.

        Args:
            chapter_number: Current chapter number
            message_count: Number of messages in current chapter
            word_count: Optional total word count
            **kwargs: Additional arguments for ModalScreen
        """
        super().__init__(**kwargs)
        self.chapter_number = chapter_number
        self.message_count = message_count
        self.word_count = word_count

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Container():
            yield Static(
                f"Compress Chapter {self.chapter_number}",
                classes="dialog-title"
            )

            # Show chapter info
            yield Static("Current chapter:", classes="section-label")

            word_info = f" (~{self.word_count:,} words)" if self.word_count else ""
            yield Static(
                f"Chapter {self.chapter_number} - {self.message_count} messages{word_info}",
                classes="chapter-info"
            )

            yield Static(
                f"ℹ️ This will create a ~3,000 word summary and advance to Chapter {self.chapter_number + 1}",
                classes="info-text"
            )

            # Chapter title input (optional)
            yield Label("Chapter title (optional):", classes="section-label")
            yield Input(
                placeholder="e.g., The Tavern Incident, First Contact",
                id="chapter-title-input"
            )

            # Tags input (optional)
            yield Label("Tags (comma-separated, optional):", classes="section-label")
            yield Input(
                placeholder="e.g., combat, mystery, character-development",
                id="chapter-tags-input"
            )

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Compress Chapter", variant="primary", id="compress-btn")

    def on_mount(self) -> None:
        """Focus the chapter title input when dialog opens."""
        self.query_one("#chapter-title-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button pressed event
        """
        if event.button.id == "cancel-btn":
            # Dismiss without compressing
            self.dismiss(None)

        elif event.button.id == "compress-btn":
            # Gather form data
            result = {
                "chapter_number": str(self.chapter_number),
                "chapter_title": self.query_one("#chapter-title-input", Input).value.strip(),
                "tags": self.query_one("#chapter-tags-input", Input).value.strip(),
            }

            # Dismiss with result
            self.dismiss(result)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields - act as if Compress was clicked.

        Args:
            event: Input submitted event
        """
        # Trigger the compress button
        compress_btn = self.query_one("#compress-btn", Button)
        self.on_button_pressed(Button.Pressed(compress_btn))


__all__ = ["ChapterCompressionDialog"]
