#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RP Selection Screen - Choose from available RP sessions

A clean interface for browsing and selecting roleplay sessions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Button, Input, Label, OptionList
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.screen import Screen

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Group
from rich import box
from textwrap import dedent


# =============================================================================
# RP SELECTION SCREEN
# =============================================================================

class RPSelectionScreen(Screen):
    """Screen for selecting an RP session to load."""

    CSS = dedent(
        """
        RPSelectionScreen {
            background: $surface;
            color: $text;
            layers: base overlay;
        }

        #rp-header {
            dock: top;
            background: $primary;
            color: $surface;
            padding: 1 2;
            text-align: center;
            height: 3;
            text-style: bold;
        }

        #rp-container {
            layout: horizontal;
            height: 1fr;
            padding: 2;
        }

        #rp-list-panel {
            width: 35%;
            height: 100%;
            background: $panel;
            border: round $primary;
            padding: 1 2;
        }

        #rp-list-panel Input {
            width: 100%;
            margin: 0 0 1 0;
            background: $surface;
            color: $text;
            border: round $primary;
        }

        #rp-list-panel Input:focus {
            border: round $accent;
        }

        #rp-list-panel OptionList {
            width: 100%;
            height: 1fr;
            border: none;
            background: $panel;
            margin-top: 1;
        }

        #rp-list-panel OptionList:focus {
            border: none;
        }

        #rp-list-panel OptionList > .option-list--option {
            color: $text;
            background: $panel;
        }

        #rp-list-panel OptionList > .option-list--option-highlighted {
            background: $surface;
            color: $text;
        }

        #rp-details-panel {
            width: 65%;
            height: 100%;
            background: $panel;
            border: round $primary;
            padding: 2;
            margin-left: 2;
        }

        #rp-details-content {
            height: 1fr;
            color: $text;
            overflow-y: auto;
        }

        .detail-title {
            color: $accent;
            text-style: bold;
            margin-bottom: 1;
        }

        .detail-label {
            color: $text-muted;
            text-style: bold;
        }

        .detail-value {
            color: $text;
            margin-bottom: 1;
        }

        #action-buttons {
            layout: horizontal;
            height: auto;
            margin-top: 2;
            dock: bottom;
        }

        #action-buttons Button {
            margin: 0 1 0 0;
        }

        Button {
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
        """
    )

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("ctrl+n", "new_rp", "New RP"),
    ]

    def __init__(self, base_dir: Path):
        """Initialize RP selection screen.

        Args:
            base_dir: Base directory containing RP folders
        """
        super().__init__()
        self.base_dir = base_dir
        self.selected_rp_path: Optional[Path] = None
        self.rp_sessions: dict[str, dict] = {}

    def _load_rp_sessions(self) -> None:
        """Load RP sessions from filesystem."""
        self.rp_sessions = {}

        # Find all RP folders (those with a state/ subdirectory)
        if not self.base_dir.exists():
            return

        for item in self.base_dir.iterdir():
            if not item.is_dir():
                continue

            state_dir = item / "state"
            if not state_dir.exists():
                continue

            # Load metadata from rp_config.json
            config_file = item / "rp_config.json"
            metadata = self._load_rp_metadata(item, config_file)

            # Store with folder name as key
            self.rp_sessions[item.name] = {
                "path": item,
                "title": metadata.get("title", item.name),
                "genre": metadata.get("genre", "Unknown"),
                "characters": metadata.get("characters", []),
                "last_played": metadata.get("last_played", "Unknown"),
                "turns": metadata.get("turns", 0),
                "status": metadata.get("status", "Active"),
                "description": metadata.get("description", "No description available."),
            }

    def _load_rp_metadata(self, rp_dir: Path, config_file: Path) -> dict:
        """Load RP metadata from config file.

        Args:
            rp_dir: RP directory path
            config_file: Path to rp_config.json

        Returns:
            Metadata dictionary
        """
        metadata = {}

        # Try to load from rp_config.json
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    metadata["title"] = config.get("rp_name", rp_dir.name)
                    metadata["genre"] = config.get("genre", "Unknown")
                    metadata["description"] = config.get("description", "")
            except Exception:
                pass

        # Try to infer last played from state files
        state_dir = rp_dir / "state"
        if state_dir.exists():
            try:
                state_files = list(state_dir.glob("*.json"))
                if state_files:
                    # Get most recent state file
                    latest = max(state_files, key=lambda p: p.stat().st_mtime)
                    mtime = datetime.fromtimestamp(latest.stat().st_mtime)
                    metadata["last_played"] = mtime.strftime("%Y-%m-%d")

                    # Try to load character info from state
                    try:
                        with open(latest, "r", encoding="utf-8") as f:
                            state = json.load(f)
                            if "characters" in state:
                                metadata["characters"] = [
                                    char.get("name", "Unknown")
                                    for char in state["characters"]
                                ]
                            if "turn_count" in state:
                                metadata["turns"] = state["turn_count"]
                    except Exception:
                        pass
            except Exception:
                pass

        return metadata

    def compose(self) -> ComposeResult:
        """Create the RP selection layout."""
        yield Static("📚 Select Your Adventure", id="rp-header")

        with Container(id="rp-container"):
            # Left panel - RP list
            with Vertical(id="rp-list-panel"):
                yield Input(placeholder="Search RPs...", id="rp-search")
                yield OptionList(id="rp-option-list")

            # Right panel - RP details
            with Vertical(id="rp-details-panel"):
                with VerticalScroll(id="rp-details-content"):
                    yield Static("", id="rp-details-static")

                with Horizontal(id="action-buttons"):
                    yield Button("Load RP", id="load-btn", classes="primary")
                    yield Button("Delete", id="delete-btn")
                    yield Button("Export", id="export-btn")

    def on_mount(self) -> None:
        """Initialize with first RP selected."""
        # Load RP sessions from filesystem
        self._load_rp_sessions()

        # Populate option list
        self._populate_option_list()

        # Select first RP if available
        if len(self.rp_sessions) > 0:
            first_rp = list(self.rp_sessions.keys())[0]
            self.show_rp_details(first_rp)

    def _populate_option_list(self, filter_term: str = "") -> None:
        """Populate the RP option list.

        Args:
            filter_term: Optional search filter
        """
        option_list = self.query_one("#rp-option-list", OptionList)
        option_list.clear_options()

        # Add RP options
        for rp_id, rp in self.rp_sessions.items():
            # Apply filter if provided
            if filter_term:
                title_match = filter_term in rp['title'].lower()
                genre_match = filter_term in rp['genre'].lower()
                char_match = any(
                    filter_term in char.lower() for char in rp.get('characters', [])
                )
                if not (title_match or genre_match or char_match):
                    continue

            status_icon = "●" if rp['status'] == "Active" else "◐"
            label = f"{status_icon} {rp['title']}"
            option_list.add_option(Option(label, id=rp_id))

        # Add "Create New" option
        option_list.add_option(Option("+ Create New RP", id="new-rp"))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter RPs based on search input."""
        if event.input.id == "rp-search":
            search_term = event.value.lower()
            self._populate_option_list(search_term)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle RP selection."""
        if event.option_id == "new-rp":
            self.action_new_rp()
        elif event.option_id:
            self.show_rp_details(event.option_id)

    def show_rp_details(self, rp_id: str) -> None:
        """Display details for selected RP."""
        rp = self.rp_sessions.get(rp_id)
        if not rp:
            return

        # Store selected RP path
        self.selected_rp_path = rp['path']

        # Build details display
        details_widget = self.query_one("#rp-details-static", Static)

        # Create a rich display using Group to combine renderables
        content = []

        # Title
        title = Text(rp['title'], style="bold cyan")
        content.append(title)
        content.append(Text())  # blank line

        # Details table
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold dim")
        table.add_column(style="")

        table.add_row("Genre:", rp['genre'])
        table.add_row("Status:", rp['status'])
        table.add_row("Last Played:", rp['last_played'])
        table.add_row("Total Turns:", str(rp['turns']))

        # Handle characters list
        characters = rp.get('characters', [])
        char_str = ", ".join(characters) if characters else "No characters"
        table.add_row("Characters:", char_str)

        content.append(table)
        content.append(Text())  # blank line

        # Description
        content.append(Text("Description:", style="bold dim"))
        content.append(Text(rp['description'], style=""))

        # Use Group to combine all renderables, then wrap in Panel
        panel = Panel(
            Group(*content),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2)
        )

        details_widget.update(panel)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        print(f"[DEBUG] Button pressed: {event.button.id}")
        if event.button.id == "load-btn":
            self.action_load_rp()
        elif event.button.id == "delete-btn":
            self.action_delete_rp()
        elif event.button.id == "export-btn":
            self.action_export_rp()

    def action_load_rp(self) -> None:
        """Load the selected RP."""
        if self.selected_rp_path:
            print(f"[DEBUG] Dismissing screen with selected path: {self.selected_rp_path}")
            # Dismiss screen and return selected path
            self.dismiss(self.selected_rp_path)
        else:
            print("[DEBUG] No RP selected yet")
            self.app.notify("Please select an RP first", severity="warning")

    def action_delete_rp(self) -> None:
        """Delete the selected RP."""
        if self.selected_rp_path:
            self.app.notify("Delete functionality not yet implemented", severity="warning")
            # TODO: Implement delete with confirmation dialog
        else:
            self.app.notify("Please select an RP first", severity="warning")

    def action_export_rp(self) -> None:
        """Export the selected RP."""
        if self.selected_rp_path:
            self.app.notify("Export functionality not yet implemented", severity="warning")
            # TODO: Implement export functionality
        else:
            self.app.notify("Please select an RP first", severity="warning")

    def action_new_rp(self) -> None:
        """Create a new RP."""
        from .startup_wizard_screen import StartupWizardScreen
        self.app.notify("Opening startup wizard...", severity="information")
        # Push wizard screen - when it finishes, it will return to selection
        self.app.push_screen(StartupWizardScreen(base_rps_dir=self.base_dir))


# =============================================================================
# DEMO APP
# =============================================================================

class RPSelectionApp(App):
    """Demo app for RP selection screen."""

    def on_mount(self) -> None:
        """Push the RP selection screen on mount."""
        self.push_screen(RPSelectionScreen())


def main():
    """Main entry point."""
    app = RPSelectionApp()
    app.run()


if __name__ == "__main__":
    main()
