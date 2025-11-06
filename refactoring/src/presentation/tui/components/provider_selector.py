"""Provider selector widget for switching LLM providers.

This module provides a dropdown/select widget that allows users to
switch between different LLM providers at runtime.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Select, Static
from textual.message import Message

from ....infrastructure.ipc import IPCMessageType, SocketClient


class ProviderSelector(Container):
    """Widget for selecting and switching LLM providers.

    This widget displays:
    - Current provider name
    - Dropdown to select different provider
    - Apply button to switch providers

    It communicates with the Bridge via IPC to get available providers
    and switch to the selected one.
    """

    class ProviderChanged(Message, bubble=True):
        """Message posted when provider is changed.

        Attributes:
            provider_name: Name of the new provider
        """

        def __init__(self, provider_name: str) -> None:
            super().__init__()
            self.provider_name = provider_name

    def __init__(self, ipc_client: SocketClient | None = None, **kwargs):
        """Initialize provider selector.

        Args:
            ipc_client: Optional socket client for IPC communication
            **kwargs: Additional arguments passed to Container
        """
        super().__init__(**kwargs)
        self.ipc_client = ipc_client
        self.current_provider: str | None = None
        self.providers: list[tuple[str, str]] = []  # [(name, display_name), ...]

    def compose(self) -> ComposeResult:
        """Compose the provider selector widget.

        Yields:
            Widgets composing the provider selector
        """
        with Horizontal(id="provider-selector-container"):
            yield Static("LLM Provider:", classes="provider-label")
            # Start with placeholder option - will be updated in on_mount
            options = [(name, display) for name, display in self.providers]
            if not options:
                options = [("loading", "Loading...")]
            yield Select(
                options=options,
                prompt="Select provider...",
                id="provider-select",
                value="loading",
                allow_blank=False,
            )
            yield Button("Switch", id="switch-provider-btn", variant="primary")

    def on_mount(self) -> None:
        """Widget mounted - providers will be loaded by parent after IPC connection."""
        pass

    def load_providers(self) -> None:
        """Load available providers from bridge."""
        if not self.ipc_client:
            self.notify("IPC client not connected", severity="warning")
            return

        try:
            response = self.ipc_client.send_request(
                IPCMessageType.GET_PROVIDERS,
                timeout=5.0
            )

            if response.success:
                providers_data = response.data.get("providers", [])
                self.current_provider = response.data.get("current_provider")

                # Format providers for select widget
                self.providers = [
                    (p["name"], p.get("display_name", p["name"]))
                    for p in providers_data
                ]

                # Update select widget options
                select_widget = self.query_one("#provider-select", Select)

                # Clear existing options and add new ones
                try:
                    # Use set_options if available (newer Textual versions)
                    select_widget.set_options(self.providers)
                except AttributeError:
                    # Fallback: clear and repopulate
                    select_widget.clear()
                    for value, prompt in self.providers:
                        select_widget.add_option((value, prompt))

                # Set current selection
                if self.current_provider:
                    try:
                        select_widget.value = self.current_provider
                    except Exception:
                        pass  # Current provider not in list

                self.notify(f"Loaded {len(self.providers)} providers", severity="information")
            else:
                self.notify(f"Failed to load providers: {response.error_message}", severity="error")

        except Exception as e:
            self.notify(f"Error loading providers: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle switch button press.

        Args:
            event: Button pressed event
        """
        if event.button.id == "switch-provider-btn":
            self.switch_provider()

    def switch_provider(self) -> None:
        """Switch to selected provider."""
        if not self.ipc_client:
            self.notify("IPC client not connected", severity="warning")
            return

        # Get selected provider
        select_widget = self.query_one("#provider-select", Select)
        selected_provider = select_widget.value

        if not selected_provider:
            self.notify("Please select a provider", severity="warning")
            return

        if selected_provider == self.current_provider:
            self.notify("Already using this provider", severity="information")
            return

        try:
            response = self.ipc_client.send_request(
                IPCMessageType.SET_PROVIDER,
                timeout=5.0,
                provider=selected_provider
            )

            if response.success:
                self.current_provider = selected_provider
                message = response.data.get("message", f"Switched to {selected_provider}")
                self.notify(message, severity="information")

                # Post provider changed message
                self.post_message(self.ProviderChanged(selected_provider))
            else:
                self.notify(f"Failed to switch provider: {response.error_message}", severity="error")

        except Exception as e:
            self.notify(f"Error switching provider: {e}", severity="error")


__all__ = ["ProviderSelector"]
