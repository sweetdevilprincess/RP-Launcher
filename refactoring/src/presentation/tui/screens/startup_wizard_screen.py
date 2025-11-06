#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Startup Wizard Screen - Guide new users through RP setup

A 2-pane wizard for creating a new RP session with navigation sidebar.
"""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Button, Input, Label, Select, TextArea
from textual.binding import Binding
from textual.screen import Screen

from rich.text import Text
from rich.console import Group
from textwrap import dedent

from ....infrastructure.rp_initialization import RPCreator, RPCreationError


# =============================================================================
# WIZARD PAGES
# =============================================================================

WIZARD_PAGES = [
    {
        "id": "welcome",
        "title": "Welcome",
        "icon": "🎉",
    },
    {
        "id": "template_select",
        "title": "Template",
        "icon": "📦",
    },
    {
        "id": "basic_info",
        "title": "Basic Info",
        "icon": "📝",
    },
    {
        "id": "story_rules",
        "title": "Story Rules",
        "icon": "📋",
    },
    {
        "id": "world_setting",
        "title": "World & Setting",
        "icon": "🌍",
    },
    {
        "id": "naming",
        "title": "Naming",
        "icon": "✍️",
    },
    {
        "id": "scene_setup",
        "title": "Scene Setup",
        "icon": "🎬",
    },
    {
        "id": "player_character",
        "title": "Your Character",
        "icon": "👤",
    },
    {
        "id": "main_npc",
        "title": "Main NPC",
        "icon": "👥",
    },
    {
        "id": "llm_config",
        "title": "LLM Config",
        "icon": "⚙️",
    },
    {
        "id": "review",
        "title": "Review",
        "icon": "✓",
    },
]


# =============================================================================
# STARTUP WIZARD SCREEN
# =============================================================================

class StartupWizardScreen(Screen):
    """2-pane wizard for creating a new RP session."""

    CSS = dedent(
        """
        StartupWizardScreen {
            background: $surface;
            color: $text;
            layers: base overlay top;
        }

        #wizard-header {
            dock: top;
            layer: top;
            background: $primary;
            color: $surface;
            padding: 1 2;
            text-align: center;
            height: 3;
            text-style: bold;
        }

        #wizard-main {
            layout: horizontal;
            height: 1fr;
        }

        /* Left Navigation Pane */
        #nav-pane {
            width: 30%;
            height: 100%;
            background: $panel;
            border-right: solid $primary;
        }

        #nav-scroll {
            height: 1fr;
            width: 100%;
            padding: 2;
        }

        .nav-title {
            color: $accent;
            text-style: bold;
            text-align: center;
            margin-bottom: 2;
        }

        #nav-scroll Button {
            width: 1fr;
            height: 3;
            min-height: 3;
            max-height: 3;
            margin: 0 0 1 0;
            padding: 0 1;
            text-align: left;
            border: none;
        }

        #nav-scroll Button.active {
            background: $accent;
            color: $text;
            text-style: bold;
        }

        /* Right Content Pane */
        #content-pane {
            width: 70%;
            height: 100%;
            background: $surface;
            padding: 3;
        }

        .page-title {
            color: $accent;
            text-style: bold;
            margin-bottom: 1;
        }

        .page-description {
            color: $text-muted;
            margin-bottom: 2;
            text-style: italic;
        }

        .section-title {
            color: $accent;
            text-style: bold;
            margin-top: 2;
            margin-bottom: 1;
        }

        .section-description {
            color: $text-muted;
            margin-bottom: 2;
            text-style: italic;
        }

        .section-divider {
            color: $primary;
            margin: 2 0;
        }

        #page-content {
            height: 1fr;
            width: 100%;
            overflow-y: auto;
        }

        #page-content > Static {
            width: 100%;
            height: auto;
        }

        #page-content > Vertical {
            width: 100%;
            height: auto;
        }

        /* Form Elements */
        Label {
            color: $text-muted;
            text-style: bold;
            margin-top: 1;
            margin-bottom: 0;
        }

        Input {
            width: 100%;
            margin: 0 0 2 0;
            background: $surface;
            color: $text;
            border: round $primary;
        }

        Input:focus {
            border: round $accent;
        }

        TextArea {
            width: 100%;
            height: 10;
            min-height: 10;
            margin: 0 0 2 0;
            background: $surface;
            color: $text;
            border: round $primary;
        }

        TextArea:focus {
            border: round $accent;
        }

        Select {
            width: 100%;
            margin: 0 0 2 0;
            background: $surface;
            color: $text;
            border: solid $primary;
        }

        Select:focus {
            border: solid $accent;
        }

        /* Bottom Navigation */
        #bottom-nav {
            dock: bottom;
            layer: top;
            layout: horizontal;
            height: auto;
            min-height: 5;
            background: $panel;
            padding: 1 2;
            border-top: solid $primary;
        }

        #nav-left {
            width: 1fr;
            height: auto;
            align: left middle;
        }

        #nav-right {
            width: 1fr;
            height: auto;
            align: right middle;
        }

        /* Buttons */
        Button {
            margin: 0 1;
            background: $surface;
            color: $text;
            border: round $primary;
        }

        Button:hover {
            background: $primary;
            text-style: bold;
        }

        Button.primary {
            background: $accent;
            color: $text;
            border: round $accent;
        }

        Button.primary:hover {
            background: $warning;
            text-style: bold;
        }

        Button:disabled {
            opacity: 0.5;
        }

        .section-spacer {
            height: 1;
        }
        """
    )

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel"),
        Binding("ctrl+n", "next_page", "Next"),
        Binding("ctrl+p", "prev_page", "Previous"),
    ]

    def __init__(self, base_rps_dir: Optional[Path] = None):
        super().__init__()
        self.current_page = 0
        self.wizard_data = {}
        self.base_rps_dir = base_rps_dir or Path("RPs")

    def compose(self) -> ComposeResult:
        """Create the 2-pane wizard layout."""
        yield Static("🧙 RP Creation Wizard", id="wizard-header")

        with Horizontal(id="wizard-main"):
            # Left Navigation Pane
            with Vertical(id="nav-pane"):
                with VerticalScroll(id="nav-scroll"):
                    yield Static("Navigation", classes="nav-title")

                    # Create navigation buttons for each page
                    for i, page in enumerate(WIZARD_PAGES):
                        btn_id = f"nav-btn-{i}"
                        btn_label = f"{page['icon']} {page['title']}"
                        classes = "nav-button active" if i == 0 else "nav-button"
                        yield Button(btn_label, id=btn_id, classes=classes)

            # Right Content Pane
            with Vertical(id="content-pane"):
                yield VerticalScroll(id="page-content")

        # Bottom Navigation
        with Horizontal(id="bottom-nav"):
            with Horizontal(id="nav-left"):
                yield Button("← Back", id="back-btn")
            with Horizontal(id="nav-right"):
                yield Button("Next →", id="next-btn", variant="primary")
                yield Button("Finish", id="finish-btn", variant="primary")

    def on_mount(self) -> None:
        """Initialize wizard with first page."""
        self.show_page(0)
        self.update_navigation()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        btn_id = event.button.id

        # Navigation buttons (sidebar)
        if btn_id and btn_id.startswith("nav-btn-"):
            page_index = int(btn_id.split("-")[-1])
            self.show_page(page_index)

        # Bottom navigation
        elif btn_id == "back-btn":
            self.action_prev_page()
        elif btn_id == "next-btn":
            self.action_next_page()
        elif btn_id == "finish-btn":
            self.action_finish()

    def update_navigation(self) -> None:
        """Update navigation button states."""
        # Update sidebar button active states
        for i, page in enumerate(WIZARD_PAGES):
            btn = self.query_one(f"#nav-btn-{i}", Button)
            if i == self.current_page:
                btn.add_class("active")
            else:
                btn.remove_class("active")

        # Update bottom navigation
        back_btn = self.query_one("#back-btn", Button)
        next_btn = self.query_one("#next-btn", Button)
        finish_btn = self.query_one("#finish-btn", Button)

        back_btn.disabled = (self.current_page == 0)

        is_last_page = (self.current_page == len(WIZARD_PAGES) - 1)
        next_btn.display = not is_last_page
        finish_btn.display = is_last_page

    def show_page(self, page_index: int) -> None:
        """Display a specific wizard page."""
        if page_index < 0 or page_index >= len(WIZARD_PAGES):
            return

        self.current_page = page_index
        page = WIZARD_PAGES[page_index]

        # Get content scroll container and clear it
        content_scroll = self.query_one("#page-content", VerticalScroll)
        content_scroll.remove_children()

        # Build page content based on page ID
        if page['id'] == "welcome":
            content_scroll.mount(Static(self._build_welcome_page()))
        elif page['id'] == "template_select":
            content_scroll.mount(self._build_template_select_page())
        elif page['id'] == "basic_info":
            content_scroll.mount(self._build_basic_info_page())
        elif page['id'] == "story_rules":
            content_scroll.mount(self._build_story_rules_page())
        elif page['id'] == "world_setting":
            content_scroll.mount(self._build_world_setting_page())
        elif page['id'] == "naming":
            content_scroll.mount(self._build_naming_page())
        elif page['id'] == "scene_setup":
            content_scroll.mount(self._build_scene_setup_page())
        elif page['id'] == "player_character":
            content_scroll.mount(self._build_player_character_page())
        elif page['id'] == "main_npc":
            content_scroll.mount(self._build_main_npc_page())
        elif page['id'] == "llm_config":
            content_scroll.mount(self._build_llm_config_page())
        elif page['id'] == "review":
            content_scroll.mount(Static(self._build_review_page()))

        self.update_navigation()

    # =============================================================================
    # PAGE BUILDERS
    # =============================================================================

    def _build_welcome_page(self) -> Group:
        """Build the welcome page content."""
        title = Text("Welcome to RP Creator!", style="bold cyan")

        content = Text.assemble(
            ("Let's create your new roleplay adventure!\n\n", ""),
            ("This wizard will guide you through:\n\n", ""),
            ("  📦 ", "cyan"), ("Template - Choose a starting template\n", ""),
            ("  📝 ", "cyan"), ("Basic Info - RP name, genre, and premise\n", ""),
            ("  📋 ", "cyan"), ("Story Rules - Define your story constraints\n", ""),
            ("  🌍 ", "cyan"), ("World & Setting - Build your world\n", ""),
            ("  ✍️  ", "cyan"), ("Naming - Set naming conventions\n", ""),
            ("  🎬 ", "cyan"), ("Scene Setup - Configure starting scene\n", ""),
            ("  👤 ", "cyan"), ("Your Character - Create player character\n", ""),
            ("  👥 ", "cyan"), ("Main NPC - Create the main NPC\n", ""),
            ("  ⚙️  ", "cyan"), ("LLM Config - Configure your AI\n", ""),
            ("  ✓  ", "cyan"), ("Review - Final check before creation\n\n", ""),
            ("Click 'Next' or select a page from the left to begin!", "italic dim"),
        )

        return Group(title, Text(), content)

    def _build_template_select_page(self) -> Vertical:
        """Build the template selection page."""
        container = Vertical()

        container.compose_add_child(Static("Choose a Template", classes="page-title"))
        container.compose_add_child(Static("Select a starting template for your RP.", classes="page-description"))

        container.compose_add_child(Label("Template:"))
        container.compose_add_child(Select(
            [
                ("Custom (Start from scratch)", "custom"),
                ("Minimal (Basic structure only)", "minimal"),
                ("Fantasy Adventure (Pre-filled fantasy template)", "fantasy_adventure"),
            ],
            id="wizard-template",
            value="minimal"
        ))

        # Template descriptions
        container.compose_add_child(Static("", classes="section-spacer"))
        container.compose_add_child(Static("Template Descriptions:", classes="section-title"))

        desc_text = Text.assemble(
            ("Custom", "bold cyan"), (" - Start from scratch with minimal boilerplate.\n", ""),
            ("  Good for: ", "bold dim"), ("Experienced users who want full control\n\n", ""),

            ("Minimal", "bold cyan"), (" - Basic structure with helpful placeholders.\n", ""),
            ("  Good for: ", "bold dim"), ("Quick setup, you'll fill in details later\n\n", ""),

            ("Fantasy Adventure", "bold cyan"), (" - Rich template with fantasy examples.\n", ""),
            ("  Good for: ", "bold dim"), ("Beginners or fantasy settings\n", ""),
            ("  Includes: ", "bold dim"), ("Pre-written guidance, magic system notes, character prompts\n", ""),
        )

        container.compose_add_child(Static(desc_text))

        return container

    def _build_basic_info_page(self) -> Vertical:
        """Build the basic info page with form fields."""
        container = Vertical()

        container.compose_add_child(Static("Basic Information", classes="page-title"))
        container.compose_add_child(Static("Give your RP a name, genre, and premise.", classes="page-description"))

        # RP Name
        container.compose_add_child(Label("RP Name (Required):"))
        container.compose_add_child(Input(
            placeholder="Enter a memorable name for your RP",
            id="wizard-rp-name"
        ))

        # Genre
        container.compose_add_child(Label("Genre:"))
        container.compose_add_child(Select(
            [
                ("Fantasy", "fantasy"),
                ("Sci-Fi", "scifi"),
                ("Horror", "horror"),
                ("Romance", "romance"),
                ("Mystery", "mystery"),
                ("Adventure", "adventure"),
                ("Drama", "drama"),
                ("Comedy", "comedy"),
                ("Custom Mix", "custom"),
            ],
            id="wizard-genre",
            value="fantasy"
        ))

        # Setting
        container.compose_add_child(Label("Setting (brief description):"))
        container.compose_add_child(Input(
            placeholder="e.g., Medieval fantasy kingdom, Modern cyberpunk city",
            id="wizard-setting"
        ))

        # Premise
        container.compose_add_child(Label("Premise (2-3 sentences):"))
        container.compose_add_child(TextArea("", id="wizard-premise"))

        # Content Rating
        container.compose_add_child(Label("Content Rating:"))
        container.compose_add_child(Select(
            [
                ("PG - Family Friendly", "PG"),
                ("PG-13 - Mild themes", "PG-13"),
                ("R - Mature themes", "R"),
            ],
            id="wizard-content-rating",
            value="PG-13"
        ))

        return container

    def _build_setting_page(self) -> Group:
        """Build the setting page content."""
        title = Text("World & Setting", style="bold cyan")
        desc = Text("Describe the world where your story takes place.", style="italic dim")

        content = Text.assemble(
            ("Build Your World\n", "bold dim"),
            ("Describe the setting for your roleplay. Consider:\n\n", ""),

            ("Time & Technology\n", "bold dim"),
            ("When does your story take place? What tech level exists?\n\n", ""),

            ("Geography\n", "bold dim"),
            ("What are the key locations? Continents, cities, landmarks?\n\n", ""),

            ("Magic & Rules\n", "bold dim"),
            ("Are there magical systems? Special rules of your world?\n\n", ""),

            ("Society\n", "bold dim"),
            ("What's the political/social structure? Any current conflicts?\n\n", ""),

            ("You can always add more details later!", "italic dim"),
        )

        return Group(title, desc, Text(), content)

    def _build_characters_page(self) -> Group:
        """Build the characters page content."""
        title = Text("Characters", style="bold cyan")
        desc = Text("Add the main characters for your roleplay.", style="italic dim")

        content = Text.assemble(
            ("Main Characters\n", "bold dim"),
            ("Define the key characters in your story. For each:\n\n", ""),

            ("  • ", "cyan"), ("Name & Role - Who are they?\n", ""),
            ("  • ", "cyan"), ("Personality - What are they like?\n", ""),
            ("  • ", "cyan"), ("Background - Where did they come from?\n", ""),
            ("  • ", "cyan"), ("Motivations - What drives them?\n", ""),
            ("  • ", "cyan"), ("Relationships - Connections to others\n", ""),
            ("  • ", "cyan"), ("Abilities - Special skills or powers\n\n", ""),

            ("Tip: ", "bold cyan"),
            ("Start with 1-2 main characters. You can add more anytime!", "italic dim"),
        )

        return Group(title, desc, Text(), content)

    def _build_tone_style_page(self) -> Group:
        """Build the tone & style page content."""
        title = Text("Tone & Style", style="bold cyan")
        desc = Text("Define the narrative style and mood.", style="italic dim")

        content = Text.assemble(
            ("Narrative Tone\n", "bold dim"),
            ("What's the overall mood of your story?\n\n", ""),
            ("  • Serious & Dramatic - Heavy themes, emotional depth\n", ""),
            ("  • Light & Comedic - Humor, fun, lighthearted\n", ""),
            ("  • Dark & Gritty - Harsh reality, difficult choices\n", ""),
            ("  • Epic & Heroic - Grand scale, legendary deeds\n", ""),
            ("  • Mysterious & Suspenseful - Tension, unknown threats\n\n", ""),

            ("Writing Style\n", "bold dim"),
            ("How should the story be told?\n\n", ""),
            ("  • Descriptive & Literary - Rich prose, detailed\n", ""),
            ("  • Fast-Paced Action - Quick, exciting, dynamic\n", ""),
            ("  • Character-Focused - Dialogue and relationships\n", ""),
            ("  • Mixed/Balanced - Combination of approaches\n", ""),
        )

        return Group(title, desc, Text(), content)

    def _build_llm_config_page(self) -> Vertical:
        """Build the LLM configuration page content with actual form fields."""
        container = Vertical()

        # Page title and description
        container.compose_add_child(Static("LLM Configuration", classes="page-title"))
        container.compose_add_child(Static("Configure your language model settings.", classes="page-description"))

        # Primary LLM Section
        container.compose_add_child(Static("Primary LLM Provider", classes="section-title"))
        container.compose_add_child(Static("Used for roleplaying and character interactions", classes="section-description"))

        container.compose_add_child(Label("API Provider:"))
        container.compose_add_child(Select(
            [
                ("OpenAI (GPT-4, GPT-3.5)", "openai"),
                ("Anthropic (Claude 3)", "anthropic"),
                ("Google (Gemini)", "google"),
                ("Ollama (Local)", "ollama"),
            ],
            id="wizard-primary-provider",
            value="openai"
        ))

        container.compose_add_child(Label("API Key:"))
        container.compose_add_child(Input(
            placeholder="Enter your API key",
            id="wizard-primary-api-key",
            password=True
        ))

        # Divider
        container.compose_add_child(Static("─" * 60, classes="section-divider"))

        # Model Settings
        container.compose_add_child(Static("Model Settings", classes="section-title"))

        container.compose_add_child(Label("Temperature (0.0 - 1.0):"))
        container.compose_add_child(Input(placeholder="0.7", id="wizard-temperature"))

        container.compose_add_child(Label("Max Tokens:"))
        container.compose_add_child(Input(placeholder="2048", id="wizard-max-tokens"))

        container.compose_add_child(Label("System Prompt:"))
        container.compose_add_child(TextArea("", id="wizard-system-prompt"))

        # Divider
        container.compose_add_child(Static("─" * 60, classes="section-divider"))

        # Secondary LLM (Optional)
        container.compose_add_child(Static("Secondary LLM (Optional)", classes="section-title"))
        container.compose_add_child(Static("Used for automation tasks (summaries, etc.)", classes="section-description"))

        container.compose_add_child(Label("API Provider:"))
        container.compose_add_child(Select(
            [
                ("Same as Primary", "same"),
                ("OpenAI", "openai"),
                ("Anthropic", "anthropic"),
                ("Ollama (Local)", "ollama"),
            ],
            id="wizard-secondary-provider",
            value="same"
        ))

        container.compose_add_child(Label("API Key:"))
        container.compose_add_child(Input(
            placeholder="Leave empty to use primary key",
            id="wizard-secondary-api-key",
            password=True
        ))

        return container

    def _build_story_rules_page(self) -> Vertical:
        """Build the story rules page (AUTHOR'S_NOTES data)."""
        container = Vertical()

        container.compose_add_child(Static("Story Rules", classes="page-title"))
        container.compose_add_child(Static("Define constraints and preferences for your story.", classes="page-description"))

        container.compose_add_child(Label("Tone:"))
        container.compose_add_child(Input(placeholder="e.g., Serious, Light-hearted, Dark", id="wizard-tone"))

        container.compose_add_child(Label("Writing Style:"))
        container.compose_add_child(Input(placeholder="e.g., Descriptive, Fast-paced, Character-focused", id="wizard-writing-style"))

        container.compose_add_child(Static("Fields below are optional - can be filled later", classes="section-description"))

        return container

    def _build_world_setting_page(self) -> Vertical:
        """Build the world setting page (STORY_GENOME data)."""
        container = Vertical()

        container.compose_add_child(Static("World & Setting", classes="page-title"))
        container.compose_add_child(Static("Describe your world and story structure.", classes="page-description"))

        container.compose_add_child(Label("Time Period:"))
        container.compose_add_child(Input(placeholder="e.g., Medieval, Modern, Far Future", id="wizard-time-period"))

        container.compose_add_child(Label("World Notes (optional):"))
        container.compose_add_child(TextArea("", id="wizard-world-notes"))

        return container

    def _build_naming_page(self) -> Vertical:
        """Build the naming conventions page."""
        container = Vertical()

        container.compose_add_child(Static("Naming Conventions", classes="page-title"))
        container.compose_add_child(Static("Set naming patterns for consistency.", classes="page-description"))

        container.compose_add_child(Label("Primary Culture:"))
        container.compose_add_child(Input(placeholder="e.g., Celtic, Japanese, Futuristic", id="wizard-primary-culture"))

        container.compose_add_child(Static("Other fields can be customized later in NAMING_CONVENTIONS.md", classes="section-description"))

        return container

    def _build_scene_setup_page(self) -> Vertical:
        """Build the scene setup page (SCENE_NOTES data)."""
        container = Vertical()

        container.compose_add_child(Static("Scene Setup", classes="page-title"))
        container.compose_add_child(Static("Configure the starting scene.", classes="page-description"))

        container.compose_add_child(Label("Starting Location:"))
        container.compose_add_child(Input(placeholder="Where does the story begin?", id="wizard-starting-location"))

        container.compose_add_child(Label("Starting Time:"))
        container.compose_add_child(Input(placeholder="Time of day/season", id="wizard-starting-time"))

        container.compose_add_child(Label("Atmosphere:"))
        container.compose_add_child(Input(placeholder="Mood of the opening scene", id="wizard-starting-atmosphere"))

        return container

    def _build_player_character_page(self) -> Vertical:
        """Build the player character page."""
        container = Vertical()

        container.compose_add_child(Static("Your Character", classes="page-title"))
        container.compose_add_child(Static("Create the player character ({{user}}).", classes="page-description"))

        container.compose_add_child(Label("Name:"))
        container.compose_add_child(Input(placeholder="Character name", id="wizard-user-name"))

        container.compose_add_child(Label("Age:"))
        container.compose_add_child(Input(placeholder="Age", id="wizard-user-age"))

        container.compose_add_child(Label("Gender:"))
        container.compose_add_child(Input(placeholder="Gender", id="wizard-user-gender"))

        container.compose_add_child(Label("Appearance (brief):"))
        container.compose_add_child(TextArea("", id="wizard-user-appearance"))

        container.compose_add_child(Label("Personality (brief):"))
        container.compose_add_child(TextArea("", id="wizard-user-personality"))

        container.compose_add_child(Static("More details can be added later in the character sheet", classes="section-description"))

        return container

    def _build_main_npc_page(self) -> Vertical:
        """Build the main NPC page."""
        container = Vertical()

        container.compose_add_child(Static("Main NPC", classes="page-title"))
        container.compose_add_child(Static("Create the main NPC ({{char}}) - Optional, can skip.", classes="page-description"))

        container.compose_add_child(Label("Name (optional):"))
        container.compose_add_child(Input(placeholder="NPC name (leave empty to skip)", id="wizard-npc-name"))

        container.compose_add_child(Label("Age:"))
        container.compose_add_child(Input(placeholder="Age", id="wizard-npc-age"))

        container.compose_add_child(Label("Gender:"))
        container.compose_add_child(Input(placeholder="Gender", id="wizard-npc-gender"))

        container.compose_add_child(Label("Appearance (brief):"))
        container.compose_add_child(TextArea("", id="wizard-npc-appearance"))

        container.compose_add_child(Label("Personality (brief):"))
        container.compose_add_child(TextArea("", id="wizard-npc-personality"))

        return container

    def _build_review_page(self) -> Group:
        """Build the review page content."""
        title = Text("Review & Create", style="bold cyan")
        desc = Text("Review your settings and create the RP.", style="italic dim")

        content = Text.assemble(
            ("Your RP Configuration\n\n", "bold"),

            ("✓ ", "cyan"), ("Basic Information - Set\n", ""),
            ("✓ ", "cyan"), ("Story Rules - Configured\n", ""),
            ("✓ ", "cyan"), ("World & Setting - Defined\n", ""),
            ("✓ ", "cyan"), ("Naming Conventions - Set\n", ""),
            ("✓ ", "cyan"), ("Scene Setup - Configured\n", ""),
            ("✓ ", "cyan"), ("Characters - Created\n", ""),
            ("✓ ", "cyan"), ("LLM Configuration - Ready\n\n", ""),

            ("Everything looks good!\n\n", "bold"),

            ("Click ", "dim"),
            ("'Finish'", "bold cyan"),
            (" to create your RP and start your adventure!\n\n", "dim"),

            ("Note: ", "bold yellow"),
            ("You can always edit these settings later from the RP menu.", "italic dim"),
        )

        return Group(title, desc, Text(), content)

    # =============================================================================
    # DATA COLLECTION
    # =============================================================================

    def _collect_wizard_data(self) -> dict:
        """Collect all data from wizard form fields."""
        data = {}

        # Helper to safely get widget values
        def get_input(widget_id: str, default: str = "") -> str:
            try:
                widget = self.query_one(f"#{widget_id}", Input)
                return widget.value.strip()
            except:
                return default

        def get_textarea(widget_id: str, default: str = "") -> str:
            try:
                widget = self.query_one(f"#{widget_id}", TextArea)
                return widget.text.strip()
            except:
                return default

        def get_select(widget_id: str, default: str = "") -> str:
            try:
                widget = self.query_one(f"#{widget_id}", Select)
                return str(widget.value) if widget.value else default
            except:
                return default

        # Template Selection
        data["template"] = get_select("wizard-template", "minimal")

        # Basic Info
        data["rp_name"] = get_input("wizard-rp-name")
        data["genre"] = get_select("wizard-genre")
        data["setting"] = get_input("wizard-setting")
        data["premise"] = get_textarea("wizard-premise")
        data["content_rating"] = get_select("wizard-content-rating")

        # Story Rules
        data["tone"] = get_input("wizard-tone")
        data["writing_style"] = get_input("wizard-writing-style")

        # World Setting
        data["time_period"] = get_input("wizard-time-period")
        data["world_notes"] = get_textarea("wizard-world-notes")

        # Naming
        data["primary_culture"] = get_input("wizard-primary-culture")

        # Scene Setup
        data["starting_location"] = get_input("wizard-starting-location")
        data["starting_time"] = get_input("wizard-starting-time")
        data["starting_atmosphere"] = get_input("wizard-starting-atmosphere")

        # Player Character
        data["user_char_name"] = get_input("wizard-user-name")
        data["user_age"] = get_input("wizard-user-age")
        data["user_gender"] = get_input("wizard-user-gender")
        data["user_appearance"] = get_textarea("wizard-user-appearance")
        data["user_personality"] = get_textarea("wizard-user-personality")

        # Main NPC
        data["main_npc_name"] = get_input("wizard-npc-name")
        data["npc_age"] = get_input("wizard-npc-age")
        data["npc_gender"] = get_input("wizard-npc-gender")
        data["npc_appearance"] = get_textarea("wizard-npc-appearance")
        data["npc_personality"] = get_textarea("wizard-npc-personality")

        # LLM Config
        data["primary_provider"] = get_select("wizard-primary-provider")
        data["primary_api_key"] = get_input("wizard-primary-api-key")
        data["temperature"] = get_input("wizard-temperature", "0.7")
        data["max_tokens"] = get_input("wizard-max-tokens", "2048")
        data["system_prompt"] = get_textarea("wizard-system-prompt")
        data["secondary_provider"] = get_select("wizard-secondary-provider")
        data["secondary_api_key"] = get_input("wizard-secondary-api-key")

        return data

    # =============================================================================
    # NAVIGATION ACTIONS
    # =============================================================================

    def action_next_page(self) -> None:
        """Go to next page."""
        if self.current_page < len(WIZARD_PAGES) - 1:
            self.show_page(self.current_page + 1)

    def action_prev_page(self) -> None:
        """Go to previous page."""
        if self.current_page > 0:
            self.show_page(self.current_page - 1)

    def action_finish(self) -> None:
        """Finish wizard and create RP."""
        try:
            # Collect all wizard data
            wizard_data = self._collect_wizard_data()

            # Validate required fields
            if not wizard_data.get("rp_name"):
                self.app.notify("Please enter an RP name", severity="error")
                return

            # Create RP using RPCreator
            self.app.notify("Creating your RP...", severity="information")
            creator = RPCreator(self.base_rps_dir)
            rp_dir = creator.create_rp(wizard_data)

            # Success!
            self.app.notify(f"RP '{wizard_data['rp_name']}' created successfully!", severity="success")
            self.app.pop_screen()

        except RPCreationError as e:
            self.app.notify(f"Failed to create RP: {e}", severity="error")
        except Exception as e:
            self.app.notify(f"Unexpected error: {e}", severity="error")
