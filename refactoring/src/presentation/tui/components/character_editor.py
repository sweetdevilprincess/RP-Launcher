from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual.widgets import Static, Input, OptionList, Button, Collapsible, Label, TextArea
from textual.widgets.option_list import Option
from rich.text import Text


class CharacterList(VerticalScroll):
    """Widget for displaying and filtering the character list."""

    DEFAULT_CSS = """
    CharacterList {
        width: 25%;
        border-right: solid $primary;
    }

    CharacterList .list-title {
        width: 100%;
        text-align: center;
        background: $primary;
        color: $text;
        padding: 1;
        text-style: bold;
    }

    CharacterList Input {
        margin: 1 2;
    }

    CharacterList OptionList {
        height: auto;
        border: none;
    }
    """

    def __init__(self):
        super().__init__()
        self.characters_data = [
            {"name": "Lilith Ravenshade", "id": "lilith"},
            {"name": "Dante Valeon", "id": "dante"},
            {"name": "Seraphine Aster", "id": "seraphine"},
        ]

    def compose(self) -> ComposeResult:
        yield Static("CHARACTERS", classes="list-title")
        yield Input(placeholder="Search: ⌕", id="character-search")
        yield OptionList(
            *[Option(f"• {char['name']}", id=char['id']) for char in self.characters_data],
            Option("+ New Character", id="new-character"),
            id="character-list"
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter the character list based on search input."""
        if event.input.id == "character-search":
            search_term = event.value.lower()
            option_list = self.query_one("#character-list", OptionList)
            option_list.clear_options()

            filtered = [
                char for char in self.characters_data
                if search_term in char['name'].lower()
            ]

            for char in filtered:
                option_list.add_option(Option(f"• {char['name']}", id=char['id']))
            option_list.add_option(Option("+ New Character", id="new-character"))


class CharacterDetail(Container):
    """Widget for displaying character details."""

    DEFAULT_CSS = """
    CharacterDetail {
        width: 75%;
        height: 100%;
        layers: base overlay;
        background: #1a1a2e;
    }

    CharacterDetail #detail-content {
        layer: base;
        width: 100%;
        height: 100%;
        padding: 2;
        color: $text-muted;
    }

    CharacterDetail #edit-drawer {
        layer: overlay;
        width: 33%;
        max-height: 90%;
        border: solid $accent;
        background: $panel;
        display: none;
        overflow-y: auto;
    }

    CharacterDetail #edit-drawer.visible {
        display: block;
    }

    CharacterDetail Collapsible Input {
        margin: 0 0 1 0;
    }

    CharacterDetail Collapsible Label {
        color: $accent;
        margin-top: 1;
        text-style: bold;
    }

    CharacterDetail Collapsible Button {
        margin: 1 0;
    }

    CharacterDetail Collapsible TextArea {
        height: auto;
        min-height: 8;
        margin: 0 0 2 0;
    }

    CharacterDetail #trigger-display {
        margin: 1 0;
        padding: 1;
        border: solid $warning;
        background: $surface;
        color: $warning;
    }

    CharacterDetail .trigger-item {
        margin-left: 2;
        color: $warning;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_character = None
        self.character_details = {
            "lilith": {
                "name": "Lilith Ravenshade",
                "archetype": "Anti-heroine",
                "role": "FMC / Hexblade",
                "tags": ["fae", "cursed", "romance"],
                "summary": '"A razor-tongued survivor with a pact-scarred soul."',
                "triggers": [
                    "On Greeting → greet_back",
                    "When Strahd Appears → inject:lilith_stance"
                ]
            },
            "dante": {
                "name": "Dante Valeon",
                "archetype": "Dark Knight",
                "role": "MMC / Paladin",
                "tags": ["brooding", "duty-bound", "tragic"],
                "summary": '"A fallen paladin seeking redemption through blood."',
                "triggers": [
                    "On Combat → activate:battle_stance",
                    "When Honor Questioned → inject:dante_defense"
                ]
            },
            "seraphine": {
                "name": "Seraphine Aster",
                "archetype": "Oracle",
                "role": "Support / Seer",
                "tags": ["mystical", "enigmatic", "prophetic"],
                "summary": '"She sees all futures, yet cannot change her own."',
                "triggers": [
                    "On Vision → trigger:prophecy",
                    "When Danger Near → inject:warning"
                ]
            }
        }

    def compose(self) -> ComposeResult:
        # Base layer - empty background
        yield Static("", id="detail-content")

        # Overlay layer - the edit drawer that pops over when a character is selected
        with Collapsible(title="✏️ Character Overview", collapsed=False, id="edit-drawer"):
            # Static trigger display at the top
            yield Static("", id="trigger-display")

            # Name input
            yield Label("Name:")
            yield Input(placeholder="Character name", id="edit-name")

            # Triggers text area
            yield Label("Triggers:")
            yield TextArea("", id="edit-triggers")

            # Information text area
            yield Label("Information:")
            yield TextArea("", id="edit-information")

            yield Button("💾 Save Changes", id="save-button", variant="success")

    def update_character(self, character_id: str) -> None:
        """Update the displayed character details."""
        if character_id == "new-character":
            self.show_new_character_form()
            return

        char = self.character_details.get(character_id)
        if not char:
            return

        self.current_character = character_id

        # Show the edit drawer
        drawer = self.query_one("#edit-drawer", Collapsible)
        drawer.add_class("visible")
        drawer.collapsed = False

        # Update static trigger display at the top
        trigger_content = Text()
        trigger_content.append("Active Triggers:\n", style="bold yellow")
        for trigger in char['triggers']:
            trigger_content.append(f" • {trigger}\n", style="yellow")

        trigger_display = self.query_one("#trigger-display", Static)
        trigger_display.update(trigger_content)

        # Populate the name
        self.query_one("#edit-name", Input).value = char["name"]

        # Populate triggers textarea
        triggers_text = "\n".join(char["triggers"])
        self.query_one("#edit-triggers", TextArea).text = triggers_text

        # Populate information textarea with all other details
        info_text = f"""Archetype: {char['archetype']}
Role: {char['role']}
Tags: {', '.join(char['tags'])}

Summary:
{char['summary']}"""

        self.query_one("#edit-information", TextArea).text = info_text

    def show_new_character_form(self) -> None:
        """Show form for creating a new character."""
        # Show the drawer
        drawer = self.query_one("#edit-drawer", Collapsible)
        drawer.add_class("visible")
        drawer.collapsed = False

        # Clear the trigger display
        trigger_display = self.query_one("#trigger-display", Static)
        trigger_display.update("No triggers set")

        # Clear the form
        self.query_one("#edit-name", Input).value = ""
        self.query_one("#edit-triggers", TextArea).text = ""
        self.query_one("#edit-information", TextArea).text = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-button":
            # Save the edited character data
            if self.current_character:
                char = self.character_details.get(self.current_character)
                if char:
                    # Update name
                    char["name"] = self.query_one("#edit-name", Input).value

                    # Update triggers from textarea (split by newlines, filter empty)
                    triggers_text = self.query_one("#edit-triggers", TextArea).text
                    char["triggers"] = [t.strip() for t in triggers_text.split("\n") if t.strip()]

                    # Parse information textarea
                    info_text = self.query_one("#edit-information", TextArea).text
                    lines = info_text.split("\n")

                    # Simple parsing - look for key patterns
                    for line in lines:
                        if line.startswith("Archetype:"):
                            char["archetype"] = line.replace("Archetype:", "").strip()
                        elif line.startswith("Role:"):
                            char["role"] = line.replace("Role:", "").strip()
                        elif line.startswith("Tags:"):
                            tags_str = line.replace("Tags:", "").strip()
                            char["tags"] = [tag.strip() for tag in tags_str.split(",")]
                        elif line.startswith("Summary:"):
                            # Get everything after "Summary:" line
                            summary_idx = lines.index(line)
                            char["summary"] = "\n".join(lines[summary_idx + 1:]).strip()
                            break

                    # Refresh the display
                    self.update_character(self.current_character)

                    # The drawer stays open so user can continue editing or manually close it


class CharacterManager(Static):
    """Main character management widget with split pane layout."""

    DEFAULT_CSS = """
    CharacterManager {
        layout: horizontal;
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield CharacterList()
        yield CharacterDetail()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle character selection from the list."""
        character_detail = self.query_one(CharacterDetail)
        character_detail.update_character(event.option_id)
