"""LLM Settings Page - Configuration for primary and secondary LLM providers.

This page allows users to configure:
- Primary LLM provider (for actual roleplay)
- Secondary LLM provider (for automation tasks)
- API keys and model settings
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.widgets import Static, Label, Input, Select, Switch, Button
from textual.message import Message

from ....infrastructure.ipc import IPCMessageType
from .testing_mode_toggle import TestingModeToggle


class LLMSettingsPage(Container):
    """LLM Settings page with API configuration.

    Features:
    - Primary LLM provider selection (OpenAI, Anthropic, Google, Ollama)
    - API key input with password masking
    - Secondary LLM configuration for automation
    - Model name and parameter settings
    - Connects to Bridge IPC for saving/loading settings
    """

    DEFAULT_CSS = """
    LLMSettingsPage {
        width: 100%;
        height: 100%;
        background: $panel;
        padding: 0;
        layer: overlay;
        layout: vertical;
    }

    LLMSettingsPage > Container {
        width: 100%;
        height: 100%;
        background: $panel;
        border: none;
        padding: 0;
        layout: vertical;
    }

    LLMSettingsPage .overlay-title {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 1 2;
        dock: top;
        border-bottom: solid $primary;
    }

    LLMSettingsPage .button-container {
        width: 100%;
        height: auto;
        padding: 1 2;
        background: $panel;
        border-bottom: solid $primary;
    }

    LLMSettingsPage .save-button {
        width: 100%;
        height: 3;
        margin: 0;
    }

    LLMSettingsPage .overlay-content {
        width: 100%;
        height: 1fr;
        max-height: 100%;
        padding: 1 2;
        background: $panel;
        overflow-y: scroll;
        overflow-x: hidden;
    }

    LLMSettingsPage .overlay-footer {
        text-style: dim;
        text-align: center;
        padding: 1 2;
        dock: bottom;
        background: $surface;
        border-top: solid $primary;
        color: $text-muted;
    }

    LLMSettingsPage .section-title {
        color: $accent;
        text-style: bold;
        margin-top: 2;
        margin-bottom: 1;
    }

    LLMSettingsPage .section-divider {
        color: $primary;
        margin: 2 0;
    }

    LLMSettingsPage .section-description {
        color: $text-muted;
        margin-bottom: 2;
        text-style: italic;
    }

    LLMSettingsPage Label {
        color: $text;
        margin-top: 1;
        margin-bottom: 0;
    }

    LLMSettingsPage Input {
        width: 100%;
        margin: 0 0 2 0;
        background: $surface;
        color: $text;
        border: round $primary;
    }

    LLMSettingsPage Input:focus {
        border: round $accent;
    }

    LLMSettingsPage Select {
        width: 100%;
        margin: 0 0 2 0;
        background: $surface;
        color: $text;
        border: solid $primary;
        padding: 1;
    }

    LLMSettingsPage Select:focus {
        border: solid $accent;
    }

    #primary-provider {
        background: $surface;
        color: $text;
    }
    """

    class SettingsChanged(Message, bubble=True):
        """Posted when settings are modified."""
        def __init__(self, field: str, value: str) -> None:
            super().__init__()
            self.field = field
            self.value = value

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        """Compose the settings overlay."""
        yield Static("⚙️ LLM Settings", classes="overlay-title")

        with Container(classes="button-container"):
            yield Button("💾 Save Settings", id="save-settings-btn", variant="primary", classes="save-button")

        with ScrollableContainer(classes="overlay-content"):
            # Testing Mode Toggle
            yield TestingModeToggle(id="testing-mode-toggle")
            yield Static("─" * 50, classes="section-divider")

            # Primary LLM Section
            yield Static("Primary LLM Provider", classes="section-title")
            yield Static("Used for main conversation and character interactions", classes="section-description")

            yield Label("API Provider:")
            yield Select(
                [
                    ("Anthropic Claude (API)", "claude_api_client"),
                    ("Anthropic Claude (SDK)", "claude_sdk_client"),
                    ("OpenAI", "openai_client"),
                    ("OpenRouter", "openrouter_client"),
                ],
                id="primary-provider",
                value="claude_sdk_client"
            )

            yield Label("API Key:")
            yield Input(
                placeholder="Enter your API key (not needed for SDK)",
                id="primary-api-key",
                password=True
            )

            # Divider
            yield Static("─" * 50, classes="section-divider")

            # Secondary LLM Section (for automation)
            yield Static("Secondary LLM (Optional)", classes="section-title")
            yield Static("Configure a separate provider for automation agents (cost optimization)", classes="section-description")

            yield Label("Use Secondary for Automation:")
            yield Switch(id="use-secondary-automation", value=False)
            yield Static("Route automation agents to secondary provider (leave off to use primary for everything)", classes="section-description")

            yield Label("Secondary Provider:")
            yield Select(
                [
                    ("(Use Primary)", ""),
                    ("Anthropic Claude (API)", "claude_api_client"),
                    ("Anthropic Claude (SDK)", "claude_sdk_client"),
                    ("OpenAI", "openai_client"),
                    ("OpenRouter", "openrouter_client"),
                ],
                id="secondary-provider",
                value=""
            )

            yield Label("Secondary API Key:")
            yield Input(
                placeholder="Enter API key for secondary provider (optional)",
                id="secondary-api-key",
                password=True
            )

            # Additional Settings
            yield Static("Additional Settings (Coming Soon)", classes="section-title")
            yield Label("Temperature:")
            yield Input(placeholder="0.0 - 1.0", id="temperature")

            yield Label("Max Tokens:")
            yield Input(placeholder="e.g., 2048", id="max-tokens")

            yield Label("System Prompt:")
            yield Input(placeholder="Default system prompt", id="system-prompt")

            yield Label("Context Window:")
            yield Input(placeholder="e.g., 8192", id="context-window")

            yield Label("Response Format:")
            yield Select([("Text", "text"), ("JSON", "json")], id="response-format", value="text")

    def on_mount(self) -> None:
        """Load settings from Bridge when mounted."""
        # Set IPC client for testing mode toggle
        try:
            toggle = self.query_one("#testing-mode-toggle", TestingModeToggle)
            toggle.ipc_client = self.app.ipc_client
        except Exception:
            pass  # Toggle might not be mounted yet

        self.load_settings()

    def load_settings(self) -> None:
        """Load settings from Bridge via IPC."""
        if not self.app.ipc_client or not self.app.connected:
            self.app.notify("Not connected to Bridge", severity="warning")
            self.settings = {}
            return

        try:
            response = self.app.ipc_client.send_request(
                IPCMessageType.GET_SETTINGS,
                timeout=5.0
            )

            if response.success:
                self.settings = response.data.get("settings", {})
                self.app.notify("Settings loaded", severity="information")
                self.apply_settings()
            else:
                self.app.notify(f"Failed to load settings: {response.error_message}", severity="error")
                # Use defaults
                self.settings = {
                    "model": "claude-3-5-sonnet-20241022",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "use_prompt_caching": True,
                    "use_sdk": False,
                }
                self.apply_settings()

        except Exception as e:
            self.app.notify(f"Error loading settings: {e}", severity="error")
            self.settings = {}

    def apply_settings(self) -> None:
        """Apply loaded settings to UI widgets."""
        try:
            # Primary provider
            primary_provider = self.query_one("#primary-provider", Select)
            primary_provider.value = self.settings.get("primary_provider", "openai")

            # Primary API key
            primary_key = self.query_one("#primary-api-key", Input)
            primary_key.value = self.settings.get("primary_api_key", "")

            # Secondary API key
            secondary_key = self.query_one("#secondary-api-key", Input)
            secondary_key.value = self.settings.get("secondary_api_key", "")

            # Secondary model
            secondary_model = self.query_one("#secondary-model", Input)
            secondary_model.value = self.settings.get("secondary_model", "")

            # Temperature
            temperature = self.query_one("#temperature", Input)
            temperature.value = str(self.settings.get("temperature", "0.7"))

            # Max tokens
            max_tokens = self.query_one("#max-tokens", Input)
            max_tokens.value = str(self.settings.get("max_tokens", "2048"))

            # System prompt
            system_prompt = self.query_one("#system-prompt", Input)
            system_prompt.value = self.settings.get("system_prompt", "")

            # Context window
            context_window = self.query_one("#context-window", Input)
            context_window.value = self.settings.get("context_window", "8192")

            # Response format
            response_format = self.query_one("#response-format", Select)
            response_format.value = self.settings.get("response_format", "text")

            # SDK toggle
            use_sdk_switch = self.query_one("#use-sdk", Switch)
            use_sdk_switch.value = self.settings.get("use_sdk", False)

        except Exception as e:
            # If widgets not ready yet, ignore
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes and post message."""
        field_id = event.input.id
        if field_id:
            # Map input IDs to settings keys
            field_map = {
                "primary-api-key": "primary_api_key",
                "secondary-api-key": "secondary_api_key",
                "secondary-model": "secondary_model",
                "temperature": "temperature",
                "max-tokens": "max_tokens",
                "system-prompt": "system_prompt",
                "context-window": "context_window",
            }

            field_name = field_map.get(field_id)
            if field_name:
                self.settings[field_name] = event.value
                self.post_message(self.SettingsChanged(field_name, event.value))
                # TODO: Auto-save to Bridge
                # await self.save_settings()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select dropdown changes and post message."""
        select_id = event.select.id
        if select_id:
            # Map select IDs to settings keys
            field_map = {
                "primary-provider": "primary_provider",
                "response-format": "response_format",
            }

            field_name = field_map.get(select_id)
            if field_name:
                self.settings[field_name] = str(event.value)
                self.post_message(self.SettingsChanged(field_name, str(event.value)))
                # TODO: Auto-save to Bridge
                # await self.save_settings()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggle changes."""
        switch_id = event.switch.id
        if switch_id == "use-sdk":
            self.settings["use_sdk"] = event.value
            self.post_message(self.SettingsChanged("use_sdk", str(event.value)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-settings-btn":
            self.save_all_settings()

    def save_all_settings(self) -> None:
        """Collect all settings from UI and save to Bridge."""
        # Collect all settings from widgets
        try:
            provider_select = self.query_one("#primary-provider", Select)
            provider = str(provider_select.value)  # This is now the actual provider name

            use_sdk_switch = self.query_one("#use-sdk", Switch)
            primary_key = self.query_one("#primary-api-key", Input)
            secondary_key = self.query_one("#secondary-api-key", Input)
            secondary_model = self.query_one("#secondary-model", Input)
            temperature = self.query_one("#temperature", Input)
            max_tokens = self.query_one("#max-tokens", Input)
            system_prompt = self.query_one("#system-prompt", Input)
            context_window = self.query_one("#context-window", Input)
            response_format = self.query_one("#response-format", Select)

            self.settings = {
                "provider": provider,  # Send actual provider name to bridge
                "use_sdk": use_sdk_switch.value,
                "primary_api_key": primary_key.value,
                "secondary_api_key": secondary_key.value,
                "secondary_model": secondary_model.value,
                "temperature": temperature.value,
                "max_tokens": max_tokens.value,
                "system_prompt": system_prompt.value,
                "context_window": context_window.value,
                "response_format": str(response_format.value),
            }

            self.save_settings()

        except Exception as e:
            self.app.notify(f"Error collecting settings: {e}", severity="error")

    def save_settings(self) -> None:
        """Save settings to Bridge via IPC."""
        if not self.app.ipc_client or not self.app.connected:
            self.app.notify("Not connected to Bridge", severity="warning")
            return

        try:
            response = self.app.ipc_client.send_request(
                IPCMessageType.UPDATE_SETTINGS,
                timeout=5.0,
                settings=self.settings
            )

            if response.success:
                message = response.data.get("message", "Settings saved")
                self.app.notify(message, severity="information")
            else:
                self.app.notify(f"Failed to save settings: {response.error_message}", severity="error")

        except Exception as e:
            self.app.notify(f"Error saving settings: {e}", severity="error")


__all__ = ["LLMSettingsPage"]
