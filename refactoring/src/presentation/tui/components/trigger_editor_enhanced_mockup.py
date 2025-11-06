"""Enhanced Trigger Editor UI Mockup - Tabbed with Two-Column Character Grid

This mockup features:
- TabbedContent for organized navigation (works with existing TUI tabs)
- Two-column character grid for compact selection
- OptionList-based trigger editing (click to select, edit, remove)
- Character sheet content viewer to help write better triggers
- Adaptive sizing based on window dimensions

Run with: python trigger_editor_enhanced_mockup.py
"""

from __future__ import annotations

from rich.markdown import Markdown
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Label, Static, TabbedContent, TabPane
from textual.widgets import OptionList
from textual.widgets.option_list import Option


# Sample character data for mockup
SAMPLE_CHARACTERS = {
    "Silas": {
        "triggers": ["Silas", "him", "he", "boyfriend"],
        "sheet": """# Silas Mercer

## Overview
- **Age**: 28
- **Role**: Boyfriend, Detective
- **Personality**: Protective, analytical, slightly jealous

## Physical Description
Tall with dark hair, sharp green eyes, athletic build from police training.

## Background
Homicide detective who met {{user}} during a case investigation.
Has trust issues from previous relationships but is trying to open up.

## Relationships
- {{user}}: Current romantic partner (6 months)
- Marcus: Best friend and partner on the force
- Emma: {{user}}'s sister (cautious relationship)

## Traits
- Workaholic tendencies
- Coffee addict (black, no sugar)
- Plays guitar to de-stress
- Secretly writes poetry

## Speech Patterns
Direct and confident at work, softer and more vulnerable with {{user}}.
Uses "darling" as a term of endearment.
"""
    },
    "Emma": {
        "triggers": ["Emma", "she", "her", "sister"],
        "sheet": """# Emma Rodriguez

## Overview
- **Age**: 24
- **Role**: Sister, Artist
- **Personality**: Free-spirited, protective, rebellious

## Physical Description
Petite with curly brown hair, often dyed with colorful streaks.
Multiple piercings and tattoos.

## Background
{{user}}'s younger sister who moved to the city to pursue her art career.
Runs a small studio and teaches art classes to kids.

## Relationships
- {{user}}: Older sibling (very close, protective)
- Silas: Wary of him, thinks he's too controlling
- Marcus: Mutual respect, occasional collaborator on art projects

## Traits
- Night owl, often paints until dawn
- Vegetarian
- Advocates for local community causes
- Has a pet ferret named Picasso

## Speech Patterns
Uses slang and art terminology. Calls {{user}} "hermana/hermano".
Tends to be blunt and honest, sometimes too honest.
"""
    },
    "Marcus": {
        "triggers": ["Marcus", "he", "him", "best friend"],
        "sheet": """# Marcus Chen

## Overview
- **Age**: 29
- **Role**: Best friend, Detective partner
- **Personality**: Laid-back, humorous, loyal

## Physical Description
Medium height, athletic Asian man with short black hair and warm brown eyes.
Always impeccably dressed even in casual clothes.

## Background
Silas's partner on the police force for 5 years. Known for defusing
tense situations with humor. Comes from a large family.

## Relationships
- Silas: Best friend and work partner since academy
- {{user}}: Friendly, considers them family
- Emma: Occasional art collaborator, appreciates her perspective

## Traits
- Mediator between Silas and Emma
- Foodie who knows every good restaurant in town
- Practices martial arts (Muay Thai)
- Takes care of his grandmother

## Speech Patterns
Casual and friendly, uses food metaphors frequently.
Code-switches between formal work talk and relaxed friend mode.
Occasional Mandarin phrases when excited or stressed.
"""
    },
}


class CharacterButton(Button):
    """Button representing a character in the grid."""

    def __init__(self, character_name: str, trigger_count: int, **kwargs):
        self.character_name = character_name
        self.trigger_count = trigger_count
        # Create label with name and count
        label = f"{character_name}\n({trigger_count} triggers)"
        super().__init__(label, **kwargs)


class CharacterGrid(Container):
    """Two-column grid of character selection buttons."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_character: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the two-column character grid."""
        with Horizontal(classes="character-grid"):
            for char_name in sorted(SAMPLE_CHARACTERS.keys()):
                triggers = SAMPLE_CHARACTERS[char_name]["triggers"]
                yield CharacterButton(
                    char_name,
                    len(triggers),
                    id=f"char-btn-{char_name}",
                    classes="character-btn"
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle character button press."""
        if isinstance(event.button, CharacterButton):
            self.selected_character = event.button.character_name
            # Post a custom message that parent can handle
            self.post_message(
                CharacterSelected(event.button.character_name)
            )


class CharacterSelected(Button.Pressed):
    """Custom message for character selection."""

    def __init__(self, character_name: str) -> None:
        super().__init__(Button())
        self.character_name = character_name


class CharacterSheetPreview(ScrollableContainer):
    """Panel showing character sheet content."""

    character_name: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Character Sheet"
        self.content_widget = Static("", expand=True)

    def compose(self) -> ComposeResult:
        """Compose the preview panel."""
        yield self.content_widget

    def watch_character_name(self, character_name: str | None) -> None:
        """Update preview when character changes."""
        if not character_name or character_name not in SAMPLE_CHARACTERS:
            self.content_widget.update(
                Markdown("*Select a character to view their sheet*")
            )
            self.border_title = "Character Sheet"
            return

        sheet_content = SAMPLE_CHARACTERS[character_name]["sheet"]
        self.content_widget.update(Markdown(sheet_content))
        self.border_title = f"Character Sheet - {character_name}"


class TriggerList(Container):
    """Interactive horizontal list of triggers."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Triggers"
        self.triggers: list[str] = []
        self.selected_index: int | None = None
        self.trigger_buttons: list[Button] = []

    def compose(self) -> ComposeResult:
        """Compose the horizontal trigger list."""
        with Horizontal(id="trigger-list-scroll", classes="trigger-scroll"):
            yield Static("", id="trigger-container")

    def load_triggers(self, triggers: list[str]) -> None:
        """Load triggers into the list.

        Args:
            triggers: List of trigger words
        """
        self.triggers = triggers.copy()
        self.selected_index = None

        # Clear and rebuild trigger buttons
        container = self.query_one("#trigger-container", Static)

        if not self.triggers:
            container.update("[dim italic]No triggers yet...[/]")
            return

        # Build horizontal list of trigger buttons
        self.trigger_buttons.clear()
        for i, trigger in enumerate(self.triggers):
            btn = Button(f"• {trigger}", id=f"trigger-btn-{i}", classes="trigger-chip")
            self.trigger_buttons.append(btn)

        # Mount new buttons
        scroll = self.query_one("#trigger-list-scroll", Horizontal)
        scroll.remove_children()
        for btn in self.trigger_buttons:
            scroll.mount(btn)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle trigger button click."""
        if event.button.id and event.button.id.startswith("trigger-btn-"):
            index = int(event.button.id.split("-")[-1])
            self.selected_index = index
            # Highlight selected button
            for i, btn in enumerate(self.trigger_buttons):
                if i == index:
                    btn.variant = "primary"
                else:
                    btn.variant = "default"

    def get_selected_trigger_index(self) -> int | None:
        """Get index of currently selected trigger.

        Returns:
            Index of selected trigger or None
        """
        return self.selected_index

    def remove_selected_trigger(self) -> bool:
        """Remove the currently selected trigger.

        Returns:
            True if removed, False if nothing selected
        """
        index = self.get_selected_trigger_index()
        if index is not None and 0 <= index < len(self.triggers):
            self.triggers.pop(index)
            self.load_triggers(self.triggers)
            return True
        return False

    def update_trigger(self, index: int, new_value: str) -> None:
        """Update a trigger at given index.

        Args:
            index: Index of trigger to update
            new_value: New trigger text
        """
        if 0 <= index < len(self.triggers):
            self.triggers[index] = new_value
            self.load_triggers(self.triggers)

    def add_trigger(self, trigger: str) -> None:
        """Add a new trigger.

        Args:
            trigger: Trigger text to add
        """
        if trigger.strip():
            self.triggers.append(trigger.strip())
            self.load_triggers(self.triggers)


class TriggerEditorPanel(Vertical):
    """Right panel for editing triggers with OptionList interaction."""

    character_name: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trigger_list: TriggerList | None = None
        self.edit_input: Input | None = None
        self.editing_index: int | None = None

    def compose(self) -> ComposeResult:
        """Compose the editor panel."""
        # Static header section (stays at top)
        with Container(classes="trigger-header"):
            with Container(classes="info-section"):
                yield Label("Selected Character:", classes="section-label")
                yield Static(
                    "No character selected",
                    id="selected-character",
                    classes="character-name"
                )
            yield Label("Trigger Words:", classes="section-label")
            yield Static(
                "Click a trigger to edit, or use the buttons below",
                classes="tip-text"
            )

        # Scrollable trigger list
        self.trigger_list = TriggerList()
        yield self.trigger_list

        # Edit section (initially hidden)
        with Container(id="edit-section", classes="hidden"):
            yield Label("Edit Trigger:", classes="section-label")
            self.edit_input = Input(placeholder="Enter trigger word", id="trigger-edit-input")
            yield self.edit_input
            with Horizontal(classes="edit-buttons"):
                yield Button("Cancel", id="cancel-edit-btn", variant="default")
                yield Button("Update", id="update-trigger-btn", variant="primary")

        # Action buttons
        with Horizontal(classes="action-buttons"):
            yield Button("+ Add", id="add-trigger-btn", variant="success")
            yield Button("Edit", id="edit-selected-btn", variant="default")
            yield Button("Remove", id="remove-trigger-btn", variant="error")
            yield Button("Save All", id="save-btn", variant="primary")

    def watch_character_name(self, character_name: str | None) -> None:
        """Update editor when character changes."""
        name_widget = self.query_one("#selected-character", Static)

        if not character_name or character_name not in SAMPLE_CHARACTERS:
            name_widget.update("No character selected")
            if self.trigger_list:
                self.trigger_list.load_triggers([])
            return

        # Update character name display
        name_widget.update(f"[bold #e26d5c]{character_name}[/]")

        # Load triggers
        if self.trigger_list:
            triggers = SAMPLE_CHARACTERS[character_name]["triggers"]
            self.trigger_list.load_triggers(triggers)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        # First check if it's from trigger list (trigger chip clicked)
        if event.button.id and event.button.id.startswith("trigger-btn-"):
            # Trigger button clicked - start editing it
            self.start_edit_selected()
            return

        # Then handle editor panel buttons
        if event.button.id == "add-trigger-btn":
            self.start_add_trigger()
        elif event.button.id == "edit-selected-btn":
            self.start_edit_selected()
        elif event.button.id == "remove-trigger-btn":
            self.remove_selected_trigger()
        elif event.button.id == "save-btn":
            self.save_triggers()
        elif event.button.id == "cancel-edit-btn":
            self.cancel_edit()
        elif event.button.id == "update-trigger-btn":
            self.update_trigger()

    def start_add_trigger(self) -> None:
        """Start adding a new trigger."""
        if not self.character_name:
            self.notify("Please select a character first", severity="warning")
            return

        self.editing_index = None
        if self.edit_input:
            self.edit_input.value = ""
            self.edit_input.placeholder = "Enter new trigger word"

        # Show edit section
        edit_section = self.query_one("#edit-section")
        edit_section.remove_class("hidden")
        if self.edit_input:
            self.edit_input.focus()

    def start_edit_selected(self) -> None:
        """Start editing the selected trigger."""
        if not self.trigger_list:
            return

        index = self.trigger_list.get_selected_trigger_index()
        if index is None:
            self.notify("Please select a trigger to edit", severity="warning")
            return

        self.editing_index = index
        current_value = self.trigger_list.triggers[index]

        if self.edit_input:
            self.edit_input.value = current_value
            self.edit_input.placeholder = "Edit trigger word"

        # Show edit section
        edit_section = self.query_one("#edit-section")
        edit_section.remove_class("hidden")
        if self.edit_input:
            self.edit_input.focus()

    def cancel_edit(self) -> None:
        """Cancel editing."""
        edit_section = self.query_one("#edit-section")
        edit_section.add_class("hidden")
        self.editing_index = None
        if self.edit_input:
            self.edit_input.value = ""

    def update_trigger(self) -> None:
        """Save the edited trigger."""
        if not self.edit_input or not self.trigger_list:
            return

        new_value = self.edit_input.value.strip()
        if not new_value:
            self.notify("Trigger cannot be empty", severity="error")
            return

        if self.editing_index is not None:
            # Update existing
            self.trigger_list.update_trigger(self.editing_index, new_value)
            self.notify(f"Updated trigger to '{new_value}'", severity="information")
        else:
            # Add new
            self.trigger_list.add_trigger(new_value)
            self.notify(f"Added trigger '{new_value}'", severity="information")

        self.cancel_edit()

    def remove_selected_trigger(self) -> None:
        """Remove the selected trigger."""
        if not self.trigger_list:
            return

        if self.trigger_list.remove_selected_trigger():
            self.notify("Trigger removed", severity="information")
        else:
            self.notify("Please select a trigger to remove", severity="warning")

    def save_triggers(self) -> None:
        """Save all triggers."""
        if not self.character_name or not self.trigger_list:
            self.notify("No character selected", severity="warning")
            return

        triggers = self.trigger_list.triggers
        if not triggers:
            self.notify("Please add at least one trigger", severity="error")
            return

        # Update mock data
        SAMPLE_CHARACTERS[self.character_name]["triggers"] = triggers
        self.notify(
            f"Saved {len(triggers)} triggers for {self.character_name}",
            severity="information"
        )


class TriggerEditorTab(Container):
    """Main trigger editor organized in tab."""

    CSS = """
    TriggerEditorTab {
        width: 100%;
        height: 100%;
        padding: 0;
    }

    .tab-layout {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: auto 1fr;
        width: 100%;
        height: 100%;
        padding: 1;
    }

    .character-selection {
        column-span: 2;
        width: 100%;
        height: 8;
        padding: 1;
        margin-bottom: 1;
        border: solid $primary;
    }

    .character-grid {
        layout: horizontal;
        width: 100%;
        height: 100%;
    }

    .character-btn {
        width: 1fr;
        height: 100%;
        min-width: 15;
        border: solid $border;
        margin: 0 1;
    }

    .character-btn:hover {
        background: $boost;
    }

    CharacterSheetPreview {
        width: 100%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    TriggerEditorPanel {
        width: 100%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    .trigger-header {
        width: 100%;
        height: auto;
        dock: top;
    }

    .info-section {
        width: 100%;
        height: auto;
        padding: 1;
        margin-bottom: 1;
        background: $boost;
        border: solid $primary;
    }

    .section-label {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        color: $text;
    }

    .character-name {
        width: 100%;
        height: auto;
        padding: 1;
    }

    TriggerList {
        width: 100%;
        height: auto;
        border: solid $primary;
        margin-bottom: 1;
        padding: 1;
    }

    .trigger-scroll {
        width: 100%;
        height: auto;
        overflow-x: auto;
        overflow-y: hidden;
    }

    .trigger-chip {
        height: 3;
        min-width: 10;
        margin: 0 1;
        padding: 0 2;
    }

    .tip-text {
        width: 100%;
        height: auto;
        padding: 1;
        margin-bottom: 1;
        background: $boost;
        color: $text;
    }

    #edit-section {
        width: 100%;
        height: auto;
        padding: 1;
        margin-bottom: 1;
        border: solid $accent;
        background: $panel;
    }

    #edit-section.hidden {
        display: none;
    }

    .edit-buttons {
        width: 100%;
        height: auto;
        align: right middle;
        margin-top: 1;
    }

    .action-buttons {
        width: 100%;
        height: auto;
        align: right middle;
    }

    .action-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.character_grid: CharacterGrid | None = None
        self.sheet_preview: CharacterSheetPreview | None = None
        self.editor_panel: TriggerEditorPanel | None = None

    def compose(self) -> ComposeResult:
        """Compose the tabbed layout."""
        with Container(classes="tab-layout"):
            # Character selection at top (spans 2 columns)
            with Container(classes="character-selection"):
                yield Label("Select Character:", classes="section-label")
                self.character_grid = CharacterGrid()
                yield self.character_grid

            # Sheet preview (bottom left)
            self.sheet_preview = CharacterSheetPreview()
            yield self.sheet_preview

            # Trigger editor (bottom right)
            self.editor_panel = TriggerEditorPanel()
            yield self.editor_panel

    def on_character_selected(self, event: CharacterSelected) -> None:
        """Handle character selection from grid."""
        character_name = event.character_name

        # Update both preview and editor
        if self.sheet_preview:
            self.sheet_preview.character_name = character_name
        if self.editor_panel:
            self.editor_panel.character_name = character_name

        self.notify(f"Selected: {character_name}", severity="information")


class EnhancedTriggerEditorApp(App):
    """Standalone app with tabbed interface."""

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $primary;
        color: $surface;
    }

    Footer {
        background: $primary;
        color: $surface;
    }

    TabbedContent {
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "save_all", "Save All"),
        Binding("ctrl+a", "add_trigger", "Add Trigger"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app with tabs."""
        yield Header()

        with TabbedContent(initial="triggers"):
            with TabPane("Triggers", id="triggers"):
                yield TriggerEditorTab()

            with TabPane("Settings", id="settings"):
                yield Static("Settings tab placeholder\n\nThis is where other settings would go (provider selection, testing mode, etc.)")

            with TabPane("Templates", id="templates"):
                yield Static("Templates tab placeholder\n\nThis is where template editor would go")

        yield Footer()

    def action_save_all(self) -> None:
        """Save all trigger changes."""
        self.notify(
            f"Would save triggers for {len(SAMPLE_CHARACTERS)} characters",
            severity="information"
        )

    def action_add_trigger(self) -> None:
        """Shortcut to add trigger."""
        try:
            editor = self.query_one(TriggerEditorPanel)
            if editor:
                editor.start_add_trigger()
        except Exception:
            pass


if __name__ == "__main__":
    app = EnhancedTriggerEditorApp()
    app.run()
