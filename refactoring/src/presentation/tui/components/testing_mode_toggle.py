"""Testing mode toggle widget.

This module provides a switch/toggle widget that enables/disables
testing mode, which uses the mock LLM client instead of real API calls.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Switch
from textual.message import Message

from ....infrastructure.ipc import IPCMessageType, SocketClient


class TestingModeToggle(Horizontal):
    """Widget for toggling testing mode on/off.

    This widget displays:
    - Label indicating testing mode
    - Switch to enable/disable
    - Status indicator

    When enabled, the Bridge uses MockLLMClient for all requests.
    """

    class TestingModeChanged(Message, bubble=True):
        """Message posted when testing mode is toggled.

        Attributes:
            enabled: True if testing mode is now enabled
        """

        def __init__(self, enabled: bool) -> None:
            super().__init__()
            self.enabled = enabled

    def __init__(self, ipc_client: SocketClient | None = None, **kwargs):
        """Initialize testing mode toggle.

        Args:
            ipc_client: Optional socket client for IPC communication
            **kwargs: Additional arguments passed to Horizontal
        """
        super().__init__(**kwargs)
        self.ipc_client = ipc_client
        self.testing_mode_enabled = False

    def compose(self) -> ComposeResult:
        """Compose the testing mode toggle widget.

        Yields:
            Widgets composing the toggle
        """
        yield Static("[TEST] Testing Mode:", classes="toggle-label")
        yield Switch(id="testing-mode-switch", value=self.testing_mode_enabled)
        yield Static(
            "Disabled" if not self.testing_mode_enabled else "Enabled",
            id="testing-mode-status",
            classes="status-text"
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggle.

        Args:
            event: Switch changed event
        """
        if event.switch.id == "testing-mode-switch":
            self.toggle_testing_mode(event.value)

    def toggle_testing_mode(self, enabled: bool) -> None:
        """Toggle testing mode on/off.

        Args:
            enabled: True to enable testing mode, False to disable
        """
        if not self.ipc_client:
            self.notify("IPC client not connected", severity="warning")
            # Reset switch
            switch = self.query_one("#testing-mode-switch", Switch)
            switch.value = self.testing_mode_enabled
            return

        try:
            response = self.ipc_client.send_request(
                IPCMessageType.TEST_MODE,
                timeout=5.0,
                enabled=enabled
            )

            if response.success:
                self.testing_mode_enabled = enabled

                # Update status text
                status_widget = self.query_one("#testing-mode-status", Static)
                status_widget.update("Enabled" if enabled else "Disabled")

                # Notify user
                message = response.data.get(
                    "message",
                    f"Testing mode {'enabled' if enabled else 'disabled'}"
                )
                self.notify(message, severity="information")

                # Post message
                self.post_message(self.TestingModeChanged(enabled))
            else:
                # Failed - reset switch
                self.notify(
                    f"Failed to toggle testing mode: {response.error_message}",
                    severity="error"
                )
                switch = self.query_one("#testing-mode-switch", Switch)
                switch.value = self.testing_mode_enabled

        except Exception as e:
            # Error - reset switch
            self.notify(f"Error toggling testing mode: {e}", severity="error")
            switch = self.query_one("#testing-mode-switch", Switch)
            switch.value = self.testing_mode_enabled


__all__ = ["TestingModeToggle"]
