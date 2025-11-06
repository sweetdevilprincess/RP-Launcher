"""Trigger Editor UI Mockup - Standalone Preview

This is a mockup of the trigger editor UI that can be run independently
to preview the design and interaction patterns.

Run with: python trigger_editor_mockup.py
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, Footer, DataTable
from textual.message import Message


# Sample data for mockup
SAMPLE_TRIGGERS = {
    "Silas": ["Silas", "him", "he", "boyfriend"],
    "Emma": ["Emma", "she", "her", "sister"],
    "Marcus": ["Marcus", "he", "him", "best friend"],
}


class TriggerEditModal(ModalScreen):
    """Modal for adding or editing a character's triggers."""

    CSS = """
    TriggerEditModal {
        align: center middle;
    }

    #edit-dialog {
        width: 70;
        height: auto;
        background: #eaeada;
        border: thick #723d46;
        padding: 0;
    }

    #edit-header {
        width: 100%;
        height: auto;
        background: #723d46;
        color: #eaeada;
        padding: 1 2;
        text-align: center;
    }

    #edit-content {
        width: 100%;
        height: auto;
        padding: 2;
    }

    #edit-footer {
        width: 100%;
        height: auto;
        background: #dfe0c8;
        padding: 1 2;
    }

    .field-label {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        color: #472d30;
    }

    .field-input {
        width: 100%;
        height: auto;
        margin-bottom: 2;
    }

    .button-row {
        width: 100%;
        height: auto;
        align: right middle;
    }
    """

    def __init__(self, character_name: str = "", triggers: list[str] | None = None):
        super().__init__()
        self.character_name = character_name
        self.triggers = triggers or []
        self.is_new = not character_name

    def compose(self) -> ComposeResult:
        """Compose the edit modal."""
        with Container(id="edit-dialog"):
            yield Static(
                "Add Character" if self.is_new else f"Edit: {self.character_name}",
                id="edit-header"
            )

            with Vertical(id="edit-content"):
                yield Label("Character Name:", classes="field-label")
                yield Input(
                    value=self.character_name,
                    placeholder="e.g., Silas",
                    id="name-input",
                    classes="field-input"
                )

                yield Label("Trigger Words (comma-separated):", classes="field-label")
                yield Input(
                    value=", ".join(self.triggers),
                    placeholder="e.g., Silas, him, he, boyfriend",
                    id="triggers-input",
                    classes="field-input"
                )

                yield Static(
                    "💡 Tip: Include the character's name, pronouns, and relationship terms",
                    classes="field-label"
                )

            with Horizontal(id="edit-footer", classes="button-row"):
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Save", variant="primary", id="save-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "save-btn":
            self.save_trigger()

    def save_trigger(self) -> None:
        """Save the trigger data."""
        name_input = self.query_one("#name-input", Input)
        triggers_input = self.query_one("#triggers-input", Input)

        character_name = name_input.value.strip()
        triggers_text = triggers_input.value.strip()

        if not character_name:
            self.notify("Character name is required", severity="error")
            return

        if not triggers_text:
            self.notify("At least one trigger word is required", severity="error")
            return

        # Parse triggers
        triggers = [t.strip() for t in triggers_text.split(",") if t.strip()]

        # Return data to parent
        self.dismiss({
            "name": character_name,
            "triggers": triggers
        })


class TriggerEditor(Container):
    """Main trigger editor widget."""

    CSS = """
    TriggerEditor {
        width: 100%;
        height: 100%;
        background: #eaeada;
        padding: 1;
    }

    #editor-header {
        width: 100%;
        height: auto;
        background: #723d46;
        color: #eaeada;
        padding: 1 2;
        margin-bottom: 1;
    }

    #editor-description {
        width: 100%;
        height: auto;
        padding: 1 2;
        margin-bottom: 1;
        background: #ffedcb;
        color: #472d30;
    }

    #trigger-table-container {
        width: 100%;
        height: 1fr;
        border: solid #723d46;
        margin-bottom: 1;
    }

    #trigger-table {
        width: 100%;
        height: 100%;
    }

    .button-bar {
        width: 100%;
        height: auto;
        align: right middle;
    }

    #add-btn {
        margin-right: 1;
    }

    #info-panel {
        width: 100%;
        height: auto;
        padding: 1 2;
        margin-top: 1;
        background: #dfe0c8;
        color: #472d30;
    }
    """

    class TriggersChanged(Message, bubble=True):
        """Posted when triggers are modified."""

        def __init__(self, triggers: dict[str, list[str]]) -> None:
            super().__init__()
            self.triggers = triggers

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.triggers: dict[str, list[str]] = SAMPLE_TRIGGERS.copy()
        self.selected_row: int | None = None

    def compose(self) -> ComposeResult:
        """Compose the trigger editor."""
        yield Static("✨ Character Trigger Editor", id="editor-header")

        yield Static(
            "📋 Manage character triggers that activate when mentioned in your messages.\n"
            "Each character can have multiple trigger words (name, pronouns, relationships).",
            id="editor-description"
        )

        with Container(id="trigger-table-container"):
            table = DataTable(id="trigger-table", cursor_type="row")
            table.add_column("Character", key="character")
            table.add_column("Trigger Words", key="triggers")
            table.add_column("Count", key="count", width=8)
            yield table

        with Horizontal(classes="button-bar"):
            yield Button("➕ Add Character", id="add-btn", variant="primary")
            yield Button("✏️  Edit", id="edit-btn", variant="default")
            yield Button("🗑️  Remove", id="remove-btn", variant="error")

        yield Static(
            "💡 Select a row and click Edit to modify, or Remove to delete.\n"
            "Triggers are case-insensitive and match whole words.",
            id="info-panel"
        )

    def on_mount(self) -> None:
        """Populate table on mount."""
        self.refresh_table()

    def refresh_table(self) -> None:
        """Refresh the table with current triggers."""
        table = self.query_one("#trigger-table", DataTable)
        table.clear()

        for character, triggers in sorted(self.triggers.items()):
            trigger_display = ", ".join(triggers)
            table.add_row(
                character,
                trigger_display,
                str(len(triggers)),
                key=character
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        self.selected_row = event.cursor_row
        self.notify(f"Selected: {event.row_key.value}", severity="information")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add-btn":
            self.add_character()
        elif event.button.id == "edit-btn":
            self.edit_character()
        elif event.button.id == "remove-btn":
            self.remove_character()

    def add_character(self) -> None:
        """Show modal to add a new character."""
        self.app.push_screen(TriggerEditModal(), self.handle_edit_result)

    def edit_character(self) -> None:
        """Show modal to edit selected character."""
        table = self.query_one("#trigger-table", DataTable)

        if self.selected_row is None:
            self.notify("Please select a character to edit", severity="warning")
            return

        # Get selected character
        row_key = table.get_row_at(self.selected_row)
        if not row_key:
            return

        character_name = str(row_key[0])
        triggers = self.triggers.get(character_name, [])

        self.app.push_screen(
            TriggerEditModal(character_name, triggers),
            self.handle_edit_result
        )

    def remove_character(self) -> None:
        """Remove selected character."""
        table = self.query_one("#trigger-table", DataTable)

        if self.selected_row is None:
            self.notify("Please select a character to remove", severity="warning")
            return

        # Get selected character
        row_key = table.get_row_at(self.selected_row)
        if not row_key:
            return

        character_name = str(row_key[0])

        # Remove from triggers
        if character_name in self.triggers:
            del self.triggers[character_name]
            self.notify(f"Removed {character_name}", severity="information")
            self.refresh_table()
            self.selected_row = None
            self.post_message(self.TriggersChanged(self.triggers))

    def handle_edit_result(self, result: dict | None) -> None:
        """Handle result from edit modal.

        Args:
            result: Dictionary with 'name' and 'triggers', or None if cancelled
        """
        if not result:
            return

        name = result["name"]
        triggers = result["triggers"]

        # Update triggers
        self.triggers[name] = triggers
        self.notify(f"Saved {name} with {len(triggers)} triggers", severity="information")
        self.refresh_table()
        self.post_message(self.TriggersChanged(self.triggers))


class TriggerEditorMockupApp(App):
    """Standalone app to preview the trigger editor UI."""

    CSS = """
    Screen {
        background: #eaeada;
    }

    #main-container {
        width: 100%;
        height: 100%;
        padding: 2;
    }

    #title {
        width: 100%;
        height: auto;
        text-align: center;
        padding: 1;
        background: #723d46;
        color: #eaeada;
        margin-bottom: 2;
    }

    Footer {
        background: #723d46;
        color: #eaeada;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app."""
        with Vertical(id="main-container"):
            yield Static("🎭 Trigger Editor UI Mockup", id="title")
            yield TriggerEditor()
        yield Footer()

    def on_trigger_editor_triggers_changed(self, event: TriggerEditor.TriggersChanged) -> None:
        """Handle triggers changed event."""
        self.notify(
            f"Triggers updated: {len(event.triggers)} characters",
            severity="information"
        )

    def action_save(self) -> None:
        """Simulate save action."""
        editor = self.query_one(TriggerEditor)
        self.notify(
            f"Would save {len(editor.triggers)} characters to file",
            severity="information"
        )


if __name__ == "__main__":
    app = TriggerEditorMockupApp()
    app.run()
