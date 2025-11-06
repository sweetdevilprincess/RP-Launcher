"""EntityManager Widget - A transparent overlay widget for managing entities.

This widget provides a list view and edit drawer for managing game entities
(characters, locations, organizations). It's designed to overlay transparently
over other content and connects to the Bridge service via IPC for real entity data.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll, ScrollableContainer
from textual.widgets import Input, OptionList, Label, Button, Collapsible, Static, TextArea
from textual.widgets.option_list import Option
from textual.message import Message

from ....infrastructure.ipc import IPCMessageType


class EntityManager(Horizontal):
    """A transparent overlay widget for managing entities.

    Features:
    - Searchable entity list with filtering by type
    - Expandable edit drawer for entity details
    - Transparent background to overlay content
    - Dynamic width (25% collapsed, 58% expanded)
    - IPC integration for loading/saving entities

    Usage:
        # In your app's compose():
        self.entity_manager = EntityManager(id="entity-manager")
        yield self.entity_manager

        # To show/hide:
        self.entity_manager.styles.display = "block"  # show
        self.entity_manager.styles.display = "none"   # hide
    """

    DEFAULT_CSS = """
    EntityManager {
        display: none;
        layer: overlay;
        width: 25%;
        height: 100%;
        dock: left;
        background: transparent;
        layout: horizontal;
    }

    EntityManager.drawer-open {
        width: 58%;
    }

    EntityManager #entity-list {
        width: 100%;
        height: 100%;
        margin-top: 2;
        background: $panel;
    }

    EntityManager.drawer-open #entity-list {
        width: 43%;
    }

    EntityManager #filter-buttons {
        width: 100%;
        height: auto;
        margin: 1 2 0 2;
        layout: horizontal;
    }

    EntityManager #filter-buttons Button {
        width: auto;
        min-width: 3;
        height: 3;
        margin: 0;
        padding: 0;
        background: $panel;
        color: $text;
        border: none;
    }

    EntityManager #filter-buttons Button.active {
        background: $panel;
        color: $text;
    }

    EntityManager #filter-buttons Button:hover {
        background: $surface;
    }

    EntityManager #entity-list Input {
        width: 1fr;
        margin: 1 2;
        background: $surface;
        color: $text;
        border: round $primary;
    }

    EntityManager #entity-list Input:focus {
        border: round $accent;
    }

    EntityManager #entity-list OptionList {
        width: 1fr;
        height: auto;
        border: none;
        background: $panel;
    }

    EntityManager #entity-list OptionList:focus {
        border: none;
    }

    EntityManager #entity-list OptionList:focus > .option-list--option-highlighted {
        background: $surface;
        color: $text;
    }

    EntityManager #entity-list OptionList > .option-list--option {
        color: $text;
        background: $panel;
        width: 100%;
    }

    EntityManager #entity-list OptionList > .option-list--option-highlighted {
        background: $surface;
        color: $text;
        width: 100%;
    }

    EntityManager #entity-edit-drawer {
        width: 0;
        height: 100%;
        background: $panel;
        border-left: solid $accent;
        padding: 0;
        overflow-y: auto;
    }

    EntityManager #entity-edit-drawer.visible {
        width: 57%;
        padding: 1 2;
    }

    EntityManager #entity-edit-drawer Collapsible {
        border: none;
        background: $panel;
        padding: 0;
    }

    EntityManager #entity-edit-drawer Collapsible > Contents {
        padding: 0;
    }

    EntityManager #entity-edit-drawer Input {
        width: 100%;
        margin: 0 0 1 0;
        background: $surface;
        color: $text;
        border: round $primary;
    }

    EntityManager #entity-edit-drawer Input:focus {
        border: round $accent;
    }

    EntityManager #entity-edit-drawer Label {
        color: $accent;
        margin-top: 1;
        text-style: bold;
    }

    EntityManager #entity-edit-drawer Button {
        margin: 1 0;
        width: 100%;
    }

    EntityManager #entity-edit-drawer TextArea {
        width: 100%;
        height: auto;
        min-height: 8;
        margin: 0 0 2 0;
        background: $surface;
        color: $text;
        border: round $primary;
    }

    EntityManager #entity-edit-drawer TextArea:focus {
        border: round $accent;
    }
    """

    class EntitySelected(Message, bubble=True):
        """Posted when an entity is selected for editing."""
        def __init__(self, entity_id: str) -> None:
            super().__init__()
            self.entity_id = entity_id

    class EntitySaved(Message, bubble=True):
        """Posted when an entity is saved."""
        def __init__(self, entity_id: str, entity_data: dict) -> None:
            super().__init__()
            self.entity_id = entity_id
            self.entity_data = entity_data

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_filter = "All"
        self.current_entity_id: str | None = None
        self.entities: dict[str, dict] = {}

    def compose(self) -> ComposeResult:
        """Compose the entity manager with list and drawer."""
        yield _EntityList(id="entity-list")
        yield _EntityEditDrawer(id="entity-edit-drawer")

    def on_mount(self) -> None:
        """Load entities from Bridge when mounted."""
        self.load_entities()

    def load_entities(self) -> None:
        """Load entities from Bridge via IPC."""
        if not self.app.ipc_client or not self.app.connected:
            self.app.notify("Not connected to Bridge", severity="warning")
            self.entities = {}
            return

        try:
            response = self.app.ipc_client.send_request(
                IPCMessageType.GET_ENTITIES,
                timeout=5.0
            )

            if response.success:
                self.entities = response.data.get("entities", {})
                self.app.notify(f"Loaded {len(self.entities)} entities", severity="information")
            else:
                self.app.notify(f"Failed to load entities: {response.error_message}", severity="error")
                self.entities = {}

        except Exception as e:
            self.app.notify(f"Error loading entities: {e}", severity="error")
            self.entities = {}

        # Refresh the list display
        entity_list = self.query_one("#entity-list", _EntityList)
        entity_list.entities = self.entities
        entity_list.refresh_list()

    def save_entity(self, entity_id: str, entity_data: dict) -> None:
        """Save entity to Bridge via IPC.

        TODO: Connect to Bridge IPC:
            response = await self.app.ipc_client.send_request(
                IPCMessageType.UPDATE_ENTITY,
                entity_id=entity_id,
                entity_data=entity_data
            )
        """
        # For now, just update local data
        self.entities[entity_id] = entity_data

        # Post message that entity was saved
        self.post_message(self.EntitySaved(entity_id, entity_data))

        # Refresh the list
        entity_list = self.query_one("#entity-list", _EntityList)
        entity_list.entities = self.entities
        entity_list.refresh_list()

    def hide_drawer(self) -> None:
        """Hide the drawer and collapse the container."""
        drawer = self.query_one("#entity-edit-drawer", _EntityEditDrawer)
        drawer.remove_class("visible")
        self.remove_class("drawer-open")


class _EntityList(VerticalScroll):
    """Internal widget for displaying and filtering the entity list."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_filter = "All"
        self.entities: dict[str, dict] = {}

    def compose(self) -> ComposeResult:
        # Filter buttons
        with Horizontal(id="filter-buttons"):
            yield Button("✨", id="filter-all", classes="filter-btn active")
            yield Button("👤", id="filter-character", classes="filter-btn")
            yield Button("📍", id="filter-location", classes="filter-btn")
            yield Button("🏛️", id="filter-organization", classes="filter-btn")

        yield Input(placeholder="Search: ⌕", id="entity-search")
        yield OptionList(id="entity-option-list")

    def on_mount(self) -> None:
        """Initialize the list."""
        self.refresh_list()

    def refresh_list(self) -> None:
        """Refresh the entity list display."""
        option_list = self.query_one("#entity-option-list", OptionList)
        option_list.clear_options()

        # Add entities
        for entity_id, entity in self.entities.items():
            option_list.add_option(Option(entity['name'], id=entity_id))

        # Add "new entity" option
        option_list.add_option(Option("+ New Entity", id="new-entity"))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter the entity list based on search input."""
        if event.input.id == "entity-search":
            search_term = event.value.lower()
            self._filter_entities(search_term)

    def _filter_entities(self, search_term: str = "") -> None:
        """Filter entities based on current filter and search term."""
        option_list = self.query_one("#entity-option-list", OptionList)
        option_list.clear_options()

        # Filter entities
        for entity_id, entity in self.entities.items():
            # Check type filter
            if self.current_filter != "All":
                # Match filter to type (e.g., "Characters" -> "Character")
                filter_type = self.current_filter.rstrip('s')  # Remove trailing 's'
                if entity['type'] != filter_type:
                    continue

            # Check search term in name or tags
            if search_term:
                name_match = search_term in entity['name'].lower()
                tags_match = any(search_term in tag.lower() for tag in entity.get('tags', []))
                if not (name_match or tags_match):
                    continue

            option_list.add_option(Option(entity['name'], id=entity_id))

        option_list.add_option(Option("+ New Entity", id="new-entity"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle filter button clicks."""
        if event.button.classes and "filter-btn" in event.button.classes:
            # Update current filter based on button ID
            filter_map = {
                "filter-all": "All",
                "filter-character": "Characters",
                "filter-location": "Locations",
                "filter-organization": "Organizations"
            }
            self.current_filter = filter_map.get(event.button.id, "All")

            # Update button active states
            for btn_id in filter_map.keys():
                try:
                    btn = self.query_one(f"#{btn_id}", Button)
                    if btn.id == event.button.id:
                        btn.add_class("active")
                    else:
                        btn.remove_class("active")
                except:
                    pass

            # Refresh the entity list with current search term
            search_input = self.query_one("#entity-search", Input)
            self._filter_entities(search_input.value.lower())

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle entity selection - show drawer."""
        if event.option_id and event.option_id != "new-entity":
            # Find the EntityManager parent and show drawer
            manager = self.parent
            if manager and isinstance(manager, EntityManager):
                drawer = manager.query_one("#entity-edit-drawer", _EntityEditDrawer)
                drawer.show_entity(event.option_id, manager.entities.get(event.option_id, {}))


class _EntityEditDrawer(ScrollableContainer):
    """Internal collapsible drawer for editing entity details."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_entity_id: str | None = None

    def compose(self) -> ComposeResult:
        with Collapsible(title="Select an entity", collapsed=False, id="entity-collapsible"):
            # Name input
            yield Label("Name:")
            yield Input(placeholder="Entity name", id="edit-name")

            # Type input
            yield Label("Type:")
            yield Input(placeholder="Character, Location, or Organization", id="edit-type")

            # Triggers text area
            yield Label("Triggers:")
            yield TextArea("", id="edit-triggers")

            # Information text area
            yield Label("Information:")
            yield TextArea("", id="edit-information")

            yield Button("Save Changes", id="save-entity-button", variant="success")

    def show_entity(self, entity_id: str, entity_data: dict):
        """Show the drawer and load entity data."""
        self.current_entity_id = entity_id

        # Update collapsible title
        title = entity_data.get('name', 'New Entity')

        collapsible = self.query_one("#entity-collapsible", Collapsible)
        collapsible.title = title
        collapsible.collapsed = False

        # Populate fields
        self.query_one("#edit-name", Input).value = entity_data.get("name", "")
        self.query_one("#edit-type", Input).value = entity_data.get("type", "")

        triggers_text = "\n".join(entity_data.get("triggers", []))
        self.query_one("#edit-triggers", TextArea).text = triggers_text

        info_text = f"""Archetype: {entity_data.get('archetype', '')}
Role: {entity_data.get('role', '')}
Tags: {', '.join(entity_data.get('tags', []))}

Summary:
{entity_data.get('summary', '')}"""
        self.query_one("#edit-information", TextArea).text = info_text

        # Show the drawer and expand container
        self.add_class("visible")
        manager = self.parent
        if manager:
            manager.add_class("drawer-open")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save button."""
        if event.button.id == "save-entity-button" and self.current_entity_id:
            # Collect updated data
            entity_data = {
                "name": self.query_one("#edit-name", Input).value,
                "type": self.query_one("#edit-type", Input).value,
                "triggers": [
                    t.strip()
                    for t in self.query_one("#edit-triggers", TextArea).text.split("\n")
                    if t.strip()
                ],
            }

            # Save via parent EntityManager
            manager = self.parent
            if manager and isinstance(manager, EntityManager):
                manager.save_entity(self.current_entity_id, entity_data)
                self.app.notify(f"Saved {entity_data['name']}", severity="information")


__all__ = ["EntityManager"]
