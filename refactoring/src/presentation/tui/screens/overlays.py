#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Overlay screens for the RP Client TUI.

This module contains modal overlay screens that display on top of the main
application for quick access to information and actions.

Overlays:
- Character Sheet: View character memory, info, and relationships
- Story Overview: View story arc and genome with tab switching
- Settings: Application settings and preferences
- Help: Keyboard shortcuts and usage guide
"""

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.widgets import Static, Label, Select, Switch, Input, Button
from textual.screen import ModalScreen
from rich.markdown import Markdown

from ....infrastructure.ipc import IPCMessageType


# =============================================================================
# BASE OVERLAY
# =============================================================================

class BaseOverlay(ModalScreen):
    """Base class for overlay screens."""

    BINDINGS = [("escape", "dismiss", "Close")]

    def _create_overlay(self, title: str, content: str, footer: str = "[ESC to close]") -> ComposeResult:
        """Helper to create standard overlay layout.

        Args:
            title: Overlay title text
            content: Markdown content to display
            footer: Footer text (default: "[ESC to close]")

        Yields:
            Widgets for the overlay layout
        """
        with Container(id="overlay-container"):
            yield Static(title, id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static(footer, id="overlay-footer")


# =============================================================================
# CHARACTER SHEET OVERLAY
# =============================================================================

class CharacterSheetOverlay(BaseOverlay):
    """Character sheet overlay with mock data."""

    def compose(self) -> ComposeResult:
        """Compose the character sheet overlay."""
        content = """# Character Sheet

## 📖 Memory
- Known for quick wit and resourcefulness
- Has a mysterious past
- Skilled in negotiation

## 👤 Character Info
**Name**: Your Character
**Class**: Adventurer
**Level**: 5

## 💕 Relationships
- **Companion A**: Friend (75/100)
- **Companion B**: Ally (60/100)
"""
        yield from self._create_overlay("👤 Character Sheet", content)


# =============================================================================
# STORY OVERVIEW OVERLAY
# =============================================================================

class StoryOverviewOverlay(ModalScreen):
    """Story overview with tabs (mock data)."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("1", "show_arc", "Arc"),
        ("2", "show_genome", "Genome")
    ]

    def __init__(self):
        """Initialize story overview overlay."""
        super().__init__()
        self.current_tab = "arc"

    def compose(self) -> ComposeResult:
        """Compose the story overview overlay."""
        with Container(id="overlay-container"):
            yield Static("📖 Story Overview", id="overlay-title")
            yield Static("[1] Arc  [2] Genome", id="tab-selector")
            yield ScrollableContainer(
                Static("", id="story-content"),
                id="overlay-content"
            )
            yield Static("[ESC to close | 1/2 to switch tabs]", id="overlay-footer")

    def on_mount(self) -> None:
        """Show arc content on mount."""
        self.show_arc_content()

    def action_show_arc(self) -> None:
        """Show the story arc tab."""
        self.current_tab = "arc"
        self.show_arc_content()

    def action_show_genome(self) -> None:
        """Show the story genome tab."""
        self.current_tab = "genome"
        self.show_genome_content()

    def show_arc_content(self) -> None:
        """Display story arc content."""
        content = """# Story Arc

## Current Chapter: The Beginning

### Plot Points
- Introduction to the world
- Meeting key characters
- First major conflict

### Next Steps
- Resolve the conflict
- Discover new information
"""
        story_widget = self.query_one("#story-content", Static)
        story_widget.update(Markdown(content))

        tab_selector = self.query_one("#tab-selector", Static)
        tab_selector.update("[bold cyan][1] Arc[/]  [dim][2] Genome[/]")

    def show_genome_content(self) -> None:
        """Display story genome content."""
        content = """# Story Genome

## Themes
- Adventure and discovery
- Friendship and loyalty
- Mystery and intrigue

## Setting
A fantasy world with magic and wonder

## Tone
Lighthearted with moments of drama
"""
        story_widget = self.query_one("#story-content", Static)
        story_widget.update(Markdown(content))

        tab_selector = self.query_one("#tab-selector", Static)
        tab_selector.update("[dim][1] Arc[/]  [bold cyan][2] Genome[/]")


# =============================================================================
# SETTINGS OVERLAY
# =============================================================================

class SettingsOverlay(ModalScreen):
    """Settings overlay with LLM routing configuration."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("ctrl+s", "save_settings", "Save")
    ]

    def __init__(self):
        """Initialize settings overlay."""
        super().__init__()
        self.settings = {}

    def compose(self) -> ComposeResult:
        """Compose the settings overlay with interactive controls."""
        with Container(id="overlay-container"):
            yield Static("⚙️ LLM Settings", id="overlay-title")

            with ScrollableContainer(id="overlay-content"):
                with Vertical(id="settings-form"):
                    # Primary Provider Section
                    yield Static("Primary LLM Provider", classes="section-title")
                    yield Static("Used for main conversation", classes="help-text")

                    yield Label("Provider:")
                    yield Select(
                        [
                            ("Anthropic Claude (SDK)", "claude_sdk_client"),
                            ("Anthropic Claude (API)", "claude_api_client"),
                            ("OpenAI", "openai_client"),
                            ("OpenRouter", "openrouter_client"),
                        ],
                        id="primary-provider",
                        value="claude_sdk_client"
                    )

                    yield Label("Temperature:")
                    yield Input(
                        placeholder="0.0 - 2.0 (Claude: 0.0-1.0)",
                        id="primary-temperature",
                        value="1.0"
                    )

                    yield Static("")  # Spacer

                    # Secondary Provider Section
                    yield Static("Secondary LLM (Optional)", classes="section-title")
                    yield Static("For automation agents (cost optimization)", classes="help-text")

                    yield Label("Use Secondary for Automation:")
                    yield Switch(id="use-secondary-automation", value=False)

                    yield Label("Secondary Provider:")
                    yield Select(
                        [
                            ("(Use Primary)", ""),
                            ("Anthropic Claude (SDK)", "claude_sdk_client"),
                            ("Anthropic Claude (API)", "claude_api_client"),
                            ("OpenAI", "openai_client"),
                            ("OpenRouter", "openrouter_client"),
                        ],
                        id="secondary-provider",
                        value=""
                    )

                    yield Label("Temperature:")
                    yield Input(
                        placeholder="0.0 - 2.0 (Claude: 0.0-1.0)",
                        id="secondary-temperature",
                        value="1.0"
                    )

                    yield Static("")  # Spacer
                    yield Button("Save Settings", id="save-button", variant="primary")

            yield Static("[ESC] Close  •  [Ctrl+S] Save", id="overlay-footer")

    def on_mount(self) -> None:
        """Load settings when mounted."""
        self.load_settings()

    def load_settings(self) -> None:
        """Load settings from Bridge via IPC."""
        if not self.app.ipc_client or not self.app.connected:
            return

        try:
            response = self.app.ipc_client.send_request(
                IPCMessageType.GET_SETTINGS,
                timeout=5.0
            )

            if response.success:
                self.settings = response.data.get("settings", {})
                self.apply_settings()
        except Exception as e:
            self.app.notify(f"Error loading settings: {e}", severity="error")

    def apply_settings(self) -> None:
        """Apply loaded settings to UI widgets."""
        try:
            # Primary provider
            primary_provider = self.query_one("#primary-provider", Select)
            primary_value = self.settings.get("primary_provider", "claude_sdk_client")
            print(f"[SETTINGS] Applying primary_provider: {primary_value}")
            primary_provider.value = primary_value

            # Secondary provider
            secondary_provider = self.query_one("#secondary-provider", Select)
            secondary_value = self.settings.get("secondary_provider", "")
            print(f"[SETTINGS] Applying secondary_provider: {secondary_value}")
            secondary_provider.value = secondary_value

            # Use secondary toggle
            use_secondary = self.query_one("#use-secondary-automation", Switch)
            use_secondary_value = self.settings.get("use_secondary_for_automation", False)
            print(f"[SETTINGS] Applying use_secondary_for_automation: {use_secondary_value}")
            use_secondary.value = use_secondary_value

            # Primary temperature
            primary_temp = self.query_one("#primary-temperature", Input)
            primary_temp_value = self.settings.get("primary_temperature", 1.0)
            print(f"[SETTINGS] Applying primary_temperature: {primary_temp_value}")
            primary_temp.value = str(primary_temp_value)

            # Secondary temperature
            secondary_temp = self.query_one("#secondary-temperature", Input)
            secondary_temp_value = self.settings.get("secondary_temperature", 1.0)
            print(f"[SETTINGS] Applying secondary_temperature: {secondary_temp_value}")
            secondary_temp.value = str(secondary_temp_value)
        except Exception as e:
            print(f"[SETTINGS] Error applying settings: {e}")
            import traceback
            traceback.print_exc()

    def action_save_settings(self) -> None:
        """Save settings action (Ctrl+S)."""
        self.save_settings()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "save-button":
            self.save_settings()

    def save_settings(self) -> None:
        """Save settings to Bridge via IPC."""
        if not self.app.ipc_client or not self.app.connected:
            self.app.notify("Not connected to Bridge", severity="warning")
            return

        try:
            # Collect settings from widgets
            primary_provider = self.query_one("#primary-provider", Select).value
            secondary_provider = self.query_one("#secondary-provider", Select).value
            use_secondary = self.query_one("#use-secondary-automation", Switch).value

            # Get temperature values and convert to float
            primary_temp_str = self.query_one("#primary-temperature", Input).value
            secondary_temp_str = self.query_one("#secondary-temperature", Input).value

            # Parse temperature values with validation
            try:
                primary_temp = float(primary_temp_str) if primary_temp_str else 1.0
                primary_temp = max(0.0, min(2.0, primary_temp))  # Clamp to 0-2 range
            except ValueError:
                primary_temp = 1.0

            try:
                secondary_temp = float(secondary_temp_str) if secondary_temp_str else 1.0
                secondary_temp = max(0.0, min(2.0, secondary_temp))  # Clamp to 0-2 range
            except ValueError:
                secondary_temp = 1.0

            print(f"[SETTINGS] Saving - primary: {primary_provider} (temp: {primary_temp}), secondary: {secondary_provider} (temp: {secondary_temp}), use_secondary: {use_secondary}")

            settings = {
                "primary_provider": primary_provider,
                "secondary_provider": secondary_provider,
                "use_secondary_for_automation": use_secondary,
                "primary_temperature": primary_temp,
                "secondary_temperature": secondary_temp,
            }

            # Send to bridge
            response = self.app.ipc_client.send_request(
                IPCMessageType.UPDATE_SETTINGS,
                data={"settings": settings},
                timeout=10.0
            )

            if response.success:
                self.app.notify("Settings saved successfully", severity="information")
                self.dismiss()
            else:
                self.app.notify(f"Failed to save: {response.error_message}", severity="error")

        except Exception as e:
            self.app.notify(f"Error saving settings: {e}", severity="error")
            print(f"[SETTINGS] Save error: {e}")
            import traceback
            traceback.print_exc()


# =============================================================================
# HELP OVERLAY
# =============================================================================

class HelpOverlay(BaseOverlay):
    """Help overlay."""

    def compose(self) -> ComposeResult:
        """Compose the help overlay."""
        help_text = """# Keyboard Shortcuts & Controls

## Main Controls
- **Ctrl+Enter** - Send message
- **Enter** - New line in message
- **Ctrl+Q** - Quit application
- **Ctrl+T** - Cycle through themes
- **F1** - Show this help

## Quick Access Overlays (F-keys)
- **F2** - Character Sheet
- **F3** - Story Overview (Arc + Genome)
- **F4** - Status
- **F8** - Settings

## In Overlays
- **ESC** - Close overlay
- **↑/↓ or PgUp/PgDn** - Scroll content
- **Number keys** - Switch tabs (in tabbed overlays)

## Layout Guide
- **Left Panel**: Context information
- **Main Area**: Chat display
- **Bottom**: Message input area

## Writing Tips
- Type naturally - Enter adds new lines
- Multi-line messages supported
- Press Ctrl+Enter when ready to send

## Available Themes
Press **Ctrl+T** to cycle through themes
"""
        yield from self._create_overlay("❓ Help", help_text)


__all__ = [
    "BaseOverlay",
    "CharacterSheetOverlay",
    "StoryOverviewOverlay",
    "SettingsOverlay",
    "HelpOverlay",
]
