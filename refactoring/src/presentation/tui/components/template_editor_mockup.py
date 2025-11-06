"""
Template Editor UI Mockup

Standalone mockup demonstrating the template editor interface with:
- Template list management
- Template content editor with variable support
- Category organization
- Preview functionality
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import (
    Button,
    Header,
    Footer,
    Static,
    Input,
    TextArea,
    Label,
    Select,
    TabbedContent,
    TabPane,
)
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown

# Sample template data
SAMPLE_TEMPLATES = {
    "System Prompt": {
        "category": "System",
        "content": """You are roleplaying as {{character_name}}.

Character Details:
{{character_details}}

Instructions:
- Stay in character at all times
- Reference character background and personality
- Respond naturally to the conversation""",
        "variables": ["character_name", "character_details"],
        "description": "Main system prompt for character roleplay",
    },
    "Scene Introduction": {
        "category": "Story",
        "content": """Setting: {{location}}
Time: {{time_of_day}}
Mood: {{mood}}

{{scene_description}}

What happens next?""",
        "variables": ["location", "time_of_day", "mood", "scene_description"],
        "description": "Template for introducing new scenes",
    },
    "Character Backstory": {
        "category": "Character",
        "content": """# {{character_name}}'s Background

## Early Life
{{early_life}}

## Key Events
{{key_events}}

## Current Situation
{{current_situation}}

## Motivations
{{motivations}}""",
        "variables": ["character_name", "early_life", "key_events", "current_situation", "motivations"],
        "description": "Structured character backstory template",
    },
    "Response Format": {
        "category": "System",
        "content": """Format your response as follows:

**Action**: {{character_action}}
**Dialogue**: "{{character_dialogue}}"
**Thought**: *{{internal_thought}}*""",
        "variables": ["character_action", "character_dialogue", "internal_thought"],
        "description": "Structured response format for character actions",
    },
}


class TemplateButton(Button):
    """Button representing a template."""

    def __init__(self, template_name: str, category: str, **kwargs):
        self.template_name = template_name
        self.category = category
        label = f"{template_name}\n[{category}]"
        super().__init__(label, **kwargs)


class TemplateList(Container):
    """List of available templates organized by category."""

    selected_template = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.templates = {}
        self.template_buttons = []

    def compose(self) -> ComposeResult:
        yield Static("📝 Templates", classes="template-list-header")
        with Vertical(id="template-list-scroll", classes="template-scroll"):
            yield Static("", id="template-container")

    def on_mount(self) -> None:
        """Load templates on mount."""
        self.load_templates(SAMPLE_TEMPLATES)

    def load_templates(self, templates: dict) -> None:
        """Load and display templates."""
        self.templates = templates
        self.template_buttons.clear()

        # Group by category
        categories = {}
        for name, data in templates.items():
            cat = data["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)

        # Build template list grouped by category
        scroll = self.query_one("#template-list-scroll", Vertical)
        scroll.remove_children()

        for category, names in sorted(categories.items()):
            # Category header
            scroll.mount(Static(f"▼ {category}", classes="category-header"))

            # Templates in this category
            for name in sorted(names):
                btn = Button(
                    name,
                    id=f"template-btn-{len(self.template_buttons)}",
                    classes="template-item"
                )
                self.template_buttons.append((name, btn))
                scroll.mount(btn)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle template button click."""
        if event.button.id and event.button.id.startswith("template-btn-"):
            # Find template name from button
            for name, btn in self.template_buttons:
                if btn == event.button:
                    self.selected_template = name

                    # Update button styles
                    for _, b in self.template_buttons:
                        if b == btn:
                            b.variant = "primary"
                        else:
                            b.variant = "default"

                    # Post message to parent
                    self.post_message(self.TemplateSelected(name))
                    break

    class TemplateSelected(Message):
        """Message sent when a template is selected."""

        def __init__(self, template_name: str):
            super().__init__()
            self.template_name = template_name


class TemplatePreview(Container):
    """Preview of selected template with metadata."""

    current_template = reactive(None)

    def compose(self) -> ComposeResult:
        yield Static("📄 Preview", classes="preview-header")
        with Vertical(classes="preview-content"):
            yield Static("", id="template-preview-content")

    def update_preview(self, template_name: str, template_data: dict) -> None:
        """Update preview with template information."""
        self.current_template = template_name

        # Build preview content
        content = f"# {template_name}\n\n"
        content += f"**Category**: {template_data['category']}\n\n"
        content += f"**Description**: {template_data['description']}\n\n"

        if template_data.get("variables"):
            content += "**Variables**:\n"
            for var in template_data["variables"]:
                content += f"  - `{{{{{var}}}}}`\n"
            content += "\n"

        content += "---\n\n"
        content += "**Template Content**:\n\n"
        content += f"```\n{template_data['content']}\n```"

        # Update preview
        preview = self.query_one("#template-preview-content", Static)
        preview.update(Markdown(content))


class TemplateEditor(Container):
    """Editor for creating/modifying templates."""

    current_template = reactive(None)

    def compose(self) -> ComposeResult:
        yield Static("✏️ Editor", classes="editor-header")

        with Vertical(classes="editor-form"):
            # Template name
            yield Label("Template Name:")
            yield Input(
                placeholder="Enter template name...",
                id="template-name-input",
                classes="editor-input"
            )

            # Category selection
            yield Label("Category:")
            yield Select(
                options=[
                    ("System", "System"),
                    ("Story", "Story"),
                    ("Character", "Character"),
                    ("Scene", "Scene"),
                    ("Dialogue", "Dialogue"),
                ],
                id="template-category-select",
                classes="editor-select"
            )

            # Description
            yield Label("Description:")
            yield Input(
                placeholder="Brief description...",
                id="template-description-input",
                classes="editor-input"
            )

            # Template content
            yield Label("Template Content:")
            yield Static(
                "💡 Use {{variable_name}} for variables",
                classes="editor-hint"
            )
            yield TextArea(
                text="",
                id="template-content-area",
                classes="editor-textarea"
            )

            # Action buttons
            with Horizontal(classes="editor-actions"):
                yield Button("💾 Save", id="save-template-btn", variant="success")
                yield Button("🗑️ Delete", id="delete-template-btn", variant="error")
                yield Button("➕ New", id="new-template-btn", variant="primary")

    def load_template(self, template_name: str, template_data: dict) -> None:
        """Load template data into editor."""
        self.current_template = template_name

        # Update form fields
        name_input = self.query_one("#template-name-input", Input)
        name_input.value = template_name

        desc_input = self.query_one("#template-description-input", Input)
        desc_input.value = template_data.get("description", "")

        category_select = self.query_one("#template-category-select", Select)
        category_select.value = template_data.get("category", "System")

        content_area = self.query_one("#template-content-area", TextArea)
        content_area.text = template_data.get("content", "")

    def clear_form(self) -> None:
        """Clear all form fields."""
        self.current_template = None
        self.query_one("#template-name-input", Input).value = ""
        self.query_one("#template-description-input", Input).value = ""
        self.query_one("#template-category-select", Select).value = "System"
        self.query_one("#template-content-area", TextArea).text = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "new-template-btn":
            self.clear_form()
        elif event.button.id == "save-template-btn":
            # In real implementation, would save template
            pass
        elif event.button.id == "delete-template-btn":
            # In real implementation, would delete template
            pass


class TemplateEditorPanel(Container):
    """Main template editor panel with three-column layout."""

    def compose(self) -> ComposeResult:
        with Grid(classes="template-grid"):
            yield TemplateList(classes="template-list-panel")
            yield TemplatePreview(classes="template-preview-panel")
            yield TemplateEditor(classes="template-editor-panel")

    def on_mount(self) -> None:
        """Set up message handling."""
        pass

    def on_template_list_template_selected(
        self, message: TemplateList.TemplateSelected
    ) -> None:
        """Handle template selection."""
        template_name = message.template_name
        template_data = SAMPLE_TEMPLATES[template_name]

        # Update preview
        preview = self.query_one(TemplatePreview)
        preview.update_preview(template_name, template_data)

        # Load into editor
        editor = self.query_one(TemplateEditor)
        editor.load_template(template_name, template_data)


class TemplateEditorApp(App):
    """Template Editor application."""

    CSS = """
    Screen {
        background: $surface;
    }

    .template-grid {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 1.5fr 1.5fr;
        height: 100%;
        width: 100%;
        padding: 1;
    }

    /* Template List Panel */
    .template-list-panel {
        border: solid $primary;
        height: 100%;
        padding: 1;
    }

    .template-list-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    .template-scroll {
        width: 100%;
        height: auto;
        overflow-y: auto;
    }

    .category-header {
        text-style: bold;
        color: $secondary;
        margin: 1 0;
        padding: 0 1;
    }

    .template-item {
        width: 100%;
        margin: 0 0 1 1;
        text-align: left;
    }

    /* Preview Panel */
    .template-preview-panel {
        border: solid $primary;
        height: 100%;
        padding: 1;
    }

    .preview-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    .preview-content {
        width: 100%;
        height: auto;
        overflow-y: auto;
    }

    #template-preview-content {
        width: 100%;
        height: auto;
        padding: 1;
    }

    /* Editor Panel */
    .template-editor-panel {
        border: solid $primary;
        height: 100%;
        padding: 1;
    }

    .editor-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    .editor-form {
        width: 100%;
        height: auto;
        overflow-y: auto;
    }

    .editor-form Label {
        margin-top: 1;
        margin-bottom: 0;
        color: $text;
    }

    .editor-input {
        width: 100%;
        margin-bottom: 1;
    }

    .editor-select {
        width: 100%;
        margin-bottom: 1;
    }

    .editor-hint {
        color: $text-muted;
        margin-bottom: 1;
        text-style: italic;
    }

    .editor-textarea {
        width: 100%;
        height: 20;
        margin-bottom: 1;
        border: solid $primary;
    }

    .editor-actions {
        layout: horizontal;
        width: 100%;
        height: auto;
        margin-top: 1;
    }

    .editor-actions Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "save_all", "Save All"),
        ("ctrl+n", "new_template", "New Template"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with TabbedContent(initial="templates"):
            with TabPane("Templates", id="templates"):
                yield TemplateEditorPanel()

            with TabPane("Settings", id="settings"):
                yield Static("Template Settings\n(Coming soon...)", classes="tab-placeholder")

            with TabPane("Import/Export", id="import-export"):
                yield Static("Import/Export Templates\n(Coming soon...)", classes="tab-placeholder")

        yield Footer()

    def action_save_all(self) -> None:
        """Save all templates (mockup)."""
        self.notify("Templates saved (mockup)", severity="information")

    def action_new_template(self) -> None:
        """Create new template."""
        editor = self.query_one(TemplateEditor)
        editor.clear_form()
        self.notify("New template form cleared", severity="information")


def main():
    """Run the template editor mockup."""
    app = TemplateEditorApp()
    app.run()


if __name__ == "__main__":
    main()
