"""Settings Overlay - Full-screen settings with side navigation.

A comprehensive settings interface with:
- Side navigation for different settings categories
- Scrollable content areas
- LLM configuration with slider controls
- Proxy settings
- Multiple configuration sections
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Label, Input, Select, Button, Switch, ContentSwitcher, Collapsible
from textual.message import Message
from textual_slider import Slider

from ....infrastructure.ipc import IPCMessageType


class SettingsOverlay(Container):
    """Full-screen settings overlay with side navigation.

    Features:
    - Side navigation bar (left side, 15% width)
    - Content area (right side, 85% width) with scrollable sections
    - Multiple settings categories
    - Save/Load via IPC bridge
    """

    DEFAULT_CSS = """
    SettingsOverlay {
        display: none;
        width: 100%;
        height: 100%;
        margin-top: 3;
        margin-bottom: 2;
        layer: overlay;
        background: $panel;
        layout: horizontal;
    }

    /* Side Navigation */
    SettingsOverlay #settings-sidebar {
        width: 20%;
        height: 100%;
        background: $surface;
        border-right: solid $primary;
        padding: 1 0;
        layout: vertical;
        overflow-y: auto;
    }

    SettingsOverlay #settings-sidebar Static {
        width: 90%;
        height: 3;
        text-align: center;
        padding: 0 2;
        background: $primary;
        color: $surface;
        text-style: bold;
        margin-bottom: 1;
        content-align: center middle;
    }

    SettingsOverlay #settings-sidebar Button {
        width: 90%;
        height: 3;
        margin: 0;
        padding: 0 2;
        background: $surface;
        color: $text;
        border: none;
        text-align: left;
        text-style: none;
    }

    SettingsOverlay #settings-sidebar Button:hover {
        background: $panel;
        text-style: bold;
    }

    SettingsOverlay #settings-sidebar Button.active {
        background: $accent;
        color: $surface;
        text-style: bold;
        border-left: thick $primary;
    }

    /* Content Area */
    SettingsOverlay #settings-content {
        width: 85%;
        height: 100%;
        background: $panel;
        layout: vertical;
    }

    SettingsOverlay #settings-header {
        dock: top;
        width: 100%;
        height: 4;
        background: $primary;
        color: $surface;
        padding: 0 2;
        layout: horizontal;
        align: right middle;
    }

    SettingsOverlay #settings-title {
        width: 1fr;
        height: 3;
        text-style: bold;
        content-align: left middle;
    }

    SettingsOverlay #save-btn {
        width: auto;
        height: 3;
        margin: 0;
    }

    SettingsOverlay #settings-sections {
        width: 100%;
        height: 1fr;
    }

    /* Section Styles */
    SettingsOverlay .settings-section {
        width: 95%;
        height: 100%;
        padding: 2;
        background: $panel;
        overflow-y: auto;
    }

    SettingsOverlay .section-title {
        color: $accent;
        text-style: bold;
        margin-top: 2;
        margin-bottom: 1;
    }

    SettingsOverlay .section-divider {
        color: $primary;
        margin: 2 0;
    }

    SettingsOverlay .section-description {
        color: $text-muted;
        margin-bottom: 2;
        text-style: italic;
    }

    SettingsOverlay Label {
        color: $text;
        margin-top: 1;
        margin-bottom: 0;
    }

    SettingsOverlay Input {
        width: 95%;
        margin: 0 0 2 0;
        background: $surface;
        color: $text;
        border: round $primary;
    }

    SettingsOverlay Input:focus {
        border: round $accent;
    }

    SettingsOverlay Input:disabled {
        opacity: 0.5;
        color: $text-muted;
    }

    SettingsOverlay Select {
        width: 95%;
        margin: 0 0 2 0;
        background: $surface;
        color: $text;
        border: solid $primary;
        padding: 1;
    }

    SettingsOverlay Select:focus {
        border: solid $accent;
    }

    SettingsOverlay Select:disabled {
        opacity: 0.5;
        color: $text-muted;
    }

    SettingsOverlay Slider {
        width: 95%;
        margin: 0 0 1 0;
    }

    SettingsOverlay Slider:disabled {
        opacity: 0.5;
    }

    SettingsOverlay .slider-label {
        width: 90%;
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }

    SettingsOverlay .slider-value {
        color: $accent;
        text-style: bold;
        text-align: right;
        width: auto;
        margin-left: 2;
    }

    SettingsOverlay Switch {
        margin: 1 0 2 0;
    }

    SettingsOverlay .inline-field {
        layout: horizontal;
        width: 95%;
        height: auto;
        margin-bottom: 2;
    }

    SettingsOverlay .inline-field Label {
        width: 40%;
    }

    SettingsOverlay .inline-field Input {
        width: 1fr;
        margin: 0 1 0 0;
    }

    SettingsOverlay .inline-field Button {
        width: auto;
        margin: 0;
        min-width: 10;
    }

    /* Module Management Styles */
    SettingsOverlay Collapsible {
        margin: 1 0;
    }

    SettingsOverlay .module-header {
        width: 100%;
        height: auto;
        align: left middle;
    }

    SettingsOverlay .module-name {
        margin-left: 1;
    }

    SettingsOverlay .module-always-on {
        color: $success;
        text-style: bold;
        margin: 1 0 0 0;
    }

    SettingsOverlay .module-description {
        color: $text-muted;
        margin: 0 0 0 2;
    }

    SettingsOverlay .module-dependencies {
        color: $warning;
        text-style: italic;
        margin: 0 0 0 2;
    }

    SettingsOverlay .module-status-running {
        color: $success;
        margin: 0 0 1 2;
    }

    SettingsOverlay .module-status-disabled {
        color: $text-muted;
        margin: 0 0 1 2;
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
        self.settings: dict = {}
        self.current_section = "llm"
        # Module state will be loaded from bridge once implemented
        self.module_states: dict[str, bool] = {}

    def on_mount(self) -> None:
        """Initialize field states when overlay mounts."""
        # Disable proxy fields by default (proxy is off by default)
        self.query_one("#proxy-url", Input).disabled = True
        self.query_one("#proxy-username", Input).disabled = True
        self.query_one("#proxy-password", Input).disabled = True

        # Disable secondary LLM fields by default (secondary is off by default)
        self.query_one("#secondary-provider", Select).disabled = True
        self.query_one("#secondary-api-key", Input).disabled = True
        self.query_one("#secondary-model", Input).disabled = True
        self.query_one("#secondary-temperature", Slider).disabled = True

        # Load settings and module states from bridge
        self._load_settings()
        self._load_module_states()

    def compose(self) -> ComposeResult:
        """Compose the settings overlay."""
        # Left sidebar navigation
        with Vertical(id="settings-sidebar"):
            yield Button("🤖 LLM Setup", id="nav-llm", classes="active")
            yield Button("⚡ Performance", id="nav-performance")
            yield Button("🎨 Appearance", id="nav-appearance")
            yield Button("📁 Paths", id="nav-paths")
            yield Button("🔧 Advanced", id="nav-advanced")
            yield Button("🧪 Testing", id="nav-testing")
            yield Button("🔄 Automation", id="nav-automation")
            yield Button("📊 Modules", id="nav-modules")
            yield Button("💾 Data", id="nav-data")

        # Right content area
        with Vertical(id="settings-content"):
            # Header with save button
            with Horizontal(id="settings-header"):
                yield Static("LLM Setup", id="settings-title")
                yield Button("💾 Save", id="save-btn", variant="primary")

            # Content switcher for different sections
            with ContentSwitcher(id="settings-sections", initial="section-llm"):
                # LLM Setup Section
                with ScrollableContainer(id="section-llm", classes="settings-section"):
                    yield from self._compose_llm_section()

                # Performance Section
                with ScrollableContainer(id="section-performance", classes="settings-section"):
                    yield from self._compose_performance_section()

                # Appearance Section
                with ScrollableContainer(id="section-appearance", classes="settings-section"):
                    yield from self._compose_appearance_section()

                # Paths Section
                with ScrollableContainer(id="section-paths", classes="settings-section"):
                    yield from self._compose_paths_section()

                # Advanced Section
                with ScrollableContainer(id="section-advanced", classes="settings-section"):
                    yield from self._compose_advanced_section()

                # Testing Section
                with ScrollableContainer(id="section-testing", classes="settings-section"):
                    yield from self._compose_testing_section()

                # Automation Section
                with ScrollableContainer(id="section-automation", classes="settings-section"):
                    yield from self._compose_automation_section()

                # Modules Section
                with ScrollableContainer(id="section-modules", classes="settings-section"):
                    yield from self._compose_modules_section()

                # Data Section
                with ScrollableContainer(id="section-data", classes="settings-section"):
                    yield from self._compose_data_section()

    def _compose_llm_section(self) -> ComposeResult:
        """Compose LLM setup section."""
        yield Static("Primary LLM Provider", classes="section-title")
        yield Static("━" * 60, classes="section-divider")
        yield Static("Used for actual roleplaying and character interactions", classes="section-description")

        yield Label("Provider:")
        yield Select(
            [
                ("Anthropic Claude (API)", "claude_api_client"),
                ("Anthropic Claude (SDK)", "claude_sdk_client"),
                ("OpenAI", "openai_client"),
                ("OpenRouter", "openrouter_client"),
                ("Google Gemini", "google_client"),
                ("Ollama (Local)", "ollama_client"),
            ],
            id="primary-provider",
            value="claude_api_client"
        )

        yield Label("API Key:")
        yield Input(
            placeholder="Enter your API key (not needed for SDK mode)",
            id="primary-api-key",
            password=True
        )

        yield Label("Model:")
        yield Input(
            placeholder="e.g., claude-3-5-sonnet-20241022",
            id="primary-model",
            value="claude-3-5-sonnet-20241022"
        )

        # Temperature slider (using 0-200 scale, will convert to 0.0-2.0)
        yield Label("Temperature:")
        with Horizontal(classes="slider-label"):
            yield Label("(0 = focused, 200 = creative | Claude: 0-100, OpenAI/OR: 0-200)")
            yield Static("100", id="temp-value", classes="slider-value")
        yield Slider(
            min=0,
            max=200,
            value=100,
            step=5,
            id="primary-temperature"
        )

        with Horizontal(classes="inline-field"):
            yield Label("Max Tokens:")
            yield Input(placeholder="4096", id="primary-max-tokens", value="4096")

        yield Switch(id="primary-prompt-caching", value=True)
        yield Label("Enable prompt caching")

        yield Static("─" * 60, classes="section-divider")

        # Proxy Configuration
        yield Static("Proxy Configuration (Optional)", classes="section-title")
        yield Static("Configure proxy settings for API requests", classes="section-description")

        yield Switch(id="use-proxy", value=False)
        yield Label("Enable proxy")

        yield Label("Proxy URL:")
        yield Input(
            placeholder="http://proxy.example.com:8080",
            id="proxy-url"
        )

        yield Label("Proxy Username (optional):")
        yield Input(
            placeholder="username",
            id="proxy-username"
        )

        yield Label("Proxy Password (optional):")
        yield Input(
            placeholder="password",
            id="proxy-password",
            password=True
        )

        yield Static("─" * 60, classes="section-divider")

        # Secondary LLM Section
        yield Static("Secondary LLM (Optional)", classes="section-title")
        yield Static("Used for automation, summaries, and background tasks", classes="section-description")

        yield Switch(id="enable-secondary", value=False)
        yield Label("Enable secondary LLM")

        yield Label("Provider:")
        yield Select(
            [
                ("OpenAI", "openai_client"),
                ("Anthropic Claude", "claude_api_client"),
                ("OpenRouter", "openrouter_client"),
                ("Google Gemini", "google_client"),
            ],
            id="secondary-provider",
            value="openai_client"
        )

        yield Label("API Key:")
        yield Input(
            placeholder="Enter secondary API key",
            id="secondary-api-key",
            password=True
        )

        yield Label("Model:")
        yield Input(
            placeholder="e.g., gpt-4o",
            id="secondary-model"
        )

        # Temperature slider for secondary
        yield Label("Temperature:")
        with Horizontal(classes="slider-label"):
            yield Label("(Lower for automation | Claude: 0-100, OpenAI/OR: 0-200)")
            yield Static("100", id="secondary-temp-value", classes="slider-value")
        yield Slider(
            min=0,
            max=200,
            value=100,
            step=5,
            id="secondary-temperature"
        )

    def _compose_performance_section(self) -> ComposeResult:
        """Compose performance section."""
        yield Static("Performance Settings", classes="section-title")
        yield Static("━" * 60, classes="section-divider")

        yield Switch(id="enable-streaming", value=True)
        yield Label("Enable streaming responses")

        yield Switch(id="enable-caching", value=True)
        yield Label("Cache parsed templates")

        yield Label("Max cache size (MB):")
        yield Input(placeholder="100", id="cache-size", value="100")

        yield Label("Request timeout (seconds):")
        yield Input(placeholder="30", id="request-timeout", value="30")

    def _compose_appearance_section(self) -> ComposeResult:
        """Compose appearance section."""
        yield Static("Appearance Settings", classes="section-title")
        yield Static("━" * 60, classes="section-divider")

        yield Label("Theme:")
        yield Select(
            [
                ("Dark (Default)", "textual-dark"),
                ("Light", "textual-light"),
                ("Nord", "nord"),
                ("Gruvbox", "gruvbox"),
                ("Dracula", "dracula"),
            ],
            id="theme-select",
            value="textual-dark"
        )

        yield Label("Font size:")
        yield Select(
            [
                ("Small", "small"),
                ("Medium", "medium"),
                ("Large", "large"),
            ],
            id="font-size",
            value="medium"
        )

        yield Switch(id="show-timestamps", value=True)
        yield Label("Show message timestamps")

    def _compose_paths_section(self) -> ComposeResult:
        """Compose paths section."""
        yield Static("File Paths", classes="section-title")
        yield Static("━" * 60, classes="section-divider")

        yield Label("RPs root directory:")
        yield Input(placeholder="./RPs", id="rps-root", value="./RPs")

        yield Label("Templates directory:")
        yield Input(placeholder="./templates", id="templates-dir", value="./templates")

        yield Label("Logs directory:")
        yield Input(placeholder="./logs", id="logs-dir", value="./logs")

    def _compose_advanced_section(self) -> ComposeResult:
        """Compose advanced section."""
        yield Static("Advanced Settings", classes="section-title")
        yield Static("━" * 60, classes="section-divider")

        yield Label("Log level:")
        yield Select(
            [
                ("DEBUG", "DEBUG"),
                ("INFO", "INFO"),
                ("WARNING", "WARNING"),
                ("ERROR", "ERROR"),
            ],
            id="log-level",
            value="INFO"
        )

        yield Label("IPC Bridge host:")
        yield Input(placeholder="127.0.0.1", id="bridge-host", value="127.0.0.1")

        yield Label("IPC Bridge port:")
        yield Input(placeholder="5555", id="bridge-port", value="5555")

        yield Switch(id="enable-debug", value=False)
        yield Label("Enable debug mode")

    def _compose_testing_section(self) -> ComposeResult:
        """Compose testing section."""
        yield Static("Testing Mode", classes="section-title")
        yield Static("━" * 60, classes="section-divider")

        yield Switch(id="enable-testing", value=False)
        yield Label("Enable testing mode (uses mock responses)")

        yield Label("Mock response delay (ms):")
        yield Input(placeholder="500", id="mock-delay", value="500")

    def _compose_automation_section(self) -> ComposeResult:
        """Compose automation section."""
        yield Static("Automation Settings", classes="section-title")
        yield Static("━" * 60, classes="section-divider")

        yield Switch(id="enable-agents", value=True)
        yield Label("Enable automation agents")

        yield Switch(id="auto-generate-prefs", value=True)
        yield Label("Auto-generate entity preferences")

        yield Label("Auto-generation frequency:")
        yield Select(
            [
                ("Every 5 turns", "5"),
                ("Every 10 turns", "10"),
                ("Every 20 turns", "20"),
            ],
            id="auto-gen-freq",
            value="10"
        )

    def _compose_modules_section(self) -> ComposeResult:
        """Compose modules section with collapsible categories."""
        from .module_registry import MODULE_REGISTRY, ModuleCategory, get_modules_by_category

        yield Static("Module Management", classes="section-title")
        yield Static("━" * 60, classes="section-divider")

        # Core Modules Section
        core_modules = get_modules_by_category(ModuleCategory.CORE)
        with Collapsible(
            title=f"Core Modules (Essential - Always Enabled) • {len(core_modules)} modules",
            collapsed=False,
            id="collapsible-core"
        ):
            for module in core_modules:
                yield from self._compose_module_item(module, enabled=True)

        # Automation Modules Section
        automation_modules = get_modules_by_category(ModuleCategory.AUTOMATION)
        with Collapsible(
            title=f"Automation Modules (Recommended) • {len(automation_modules)} modules",
            collapsed=False,
            id="collapsible-automation"
        ):
            for module in automation_modules:
                yield from self._compose_module_item(module)

        # Optional Modules Section
        optional_modules = get_modules_by_category(ModuleCategory.OPTIONAL)
        with Collapsible(
            title=f"Optional Modules • {len(optional_modules)} modules",
            collapsed=False,
            id="collapsible-optional"
        ):
            for module in optional_modules:
                yield from self._compose_module_item(module)

        # Extensions Section (placeholder)
        yield Static("─" * 60, classes="section-divider")
        with Collapsible(
            title="Extensions • 0 installed",
            collapsed=True,
            id="collapsible-extensions"
        ):
            yield Static("Extension system coming soon", classes="section-description")
            yield Button("Browse Extensions...", id="browse-extensions", disabled=True)
            yield Button("Install from File...", id="install-extension", disabled=True)

    def _compose_module_item(self, module, enabled: bool = None) -> ComposeResult:
        """Compose a single module item with toggle and info.

        Args:
            module: ModuleInfo object
            enabled: Override enabled state (for non-toggleable modules)
        """
        from .module_registry import get_module_dependencies

        # Get current state from bridge (will be loaded via GET_MODULES IPC)
        if enabled is None:
            enabled = self.module_states.get(module.id, module.default_enabled)

        # Module toggle and name on same line
        if module.toggleable:
            with Horizontal(classes="module-header"):
                yield Switch(id=f"module-{module.id}", value=enabled)
                yield Label(module.name, classes="module-name")
        else:
            yield Static(f"✓ {module.name} (Always On)", classes="module-always-on")

        # Description
        yield Static(f"  {module.description}", classes="module-description")

        # Dependencies
        if module.dependencies:
            deps = get_module_dependencies(module.id)
            dep_names = ", ".join([d.name for d in deps])
            yield Static(f"  Requires: {dep_names}", classes="module-dependencies")

        # Status (with ID for dynamic updates)
        if enabled or not module.toggleable:
            yield Static("  Status: ✓ Running",
                        classes="module-status-running",
                        id=f"status-{module.id}")
        else:
            yield Static("  Status: ○ Disabled",
                        classes="module-status-disabled",
                        id=f"status-{module.id}")

        # Spacer between modules
        yield Static("")

    def _compose_data_section(self) -> ComposeResult:
        """Compose data section."""
        yield Static("Data Management", classes="section-title")
        yield Static("━" * 60, classes="section-divider")

        yield Switch(id="auto-backup", value=True)
        yield Label("Enable automatic backups")

        yield Label("Backup frequency:")
        yield Select(
            [
                ("Daily", "daily"),
                ("Weekly", "weekly"),
                ("On major changes", "on-change"),
            ],
            id="backup-frequency",
            value="daily"
        )

        yield Button("Backup Now", id="backup-now-btn")
        yield Button("Export All Data", id="export-data-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # Navigation buttons
        if button_id and button_id.startswith("nav-"):
            section = button_id.replace("nav-", "")
            self._switch_section(section)

        # Save button
        elif button_id == "save-btn":
            self._save_settings()

        # Action buttons
        elif button_id == "backup-now-btn":
            self.app.notify("Backup started...", severity="information")
        elif button_id == "export-data-btn":
            self.app.notify("Export started...", severity="information")

    def _handle_module_toggle(self, switch_id: str, enabled: bool) -> None:
        """Handle module enable/disable toggle.

        Args:
            switch_id: Switch ID (format: "module-{module_id}")
            enabled: Whether module is being enabled or disabled
        """
        from .module_registry import get_module_by_id

        # Extract module ID
        module_id = switch_id.replace("module-", "")
        module = get_module_by_id(module_id)

        if not module:
            return

        # Send TOGGLE_MODULE request to bridge via IPC
        if hasattr(self.app, 'ipc_client') and self.app.ipc_client and self.app.connected:
            try:
                response = self.app.ipc_client.send_request(
                    IPCMessageType.TOGGLE_MODULE,
                    timeout=5.0,
                    module_id=module_id,
                    enabled=enabled
                )

                if response.success:
                    # Update local state
                    self.module_states[module_id] = enabled

                    # Update status display
                    try:
                        status_widget = self.query_one(f"#status-{module_id}", Static)
                        if enabled:
                            status_widget.update("  Status: ✓ Running")
                            status_widget.remove_class("module-status-disabled")
                            status_widget.add_class("module-status-running")
                        else:
                            status_widget.update("  Status: ○ Disabled")
                            status_widget.remove_class("module-status-running")
                            status_widget.add_class("module-status-disabled")
                    except Exception:
                        pass

                    # Show notification
                    status_text = "enabled" if enabled else "disabled"
                    self.app.notify(f"✓ {module.name} {status_text}", severity="information")
                else:
                    # Revert toggle on failure
                    error_msg = response.error_message or "Unknown error"
                    self.app.notify(f"✗ Failed to toggle {module.name}: {error_msg}", severity="error")
                    switch = self.query_one(f"#{switch_id}", Switch)
                    switch.value = not enabled

            except Exception as e:
                # Revert toggle on exception
                self.app.notify(f"✗ Error toggling {module.name}: {e}", severity="error")
                switch = self.query_one(f"#{switch_id}", Switch)
                switch.value = not enabled
        else:
            # Not connected to bridge - show message
            self.app.notify("⚠ Not connected to Bridge - cannot toggle modules", severity="warning")
            # Revert toggle
            switch = self.query_one(f"#{switch_id}", Switch)
            switch.value = not enabled

    def _switch_section(self, section: str) -> None:
        """Switch to a different settings section."""
        # Update navigation button states
        for button in self.query("#settings-sidebar Button"):
            if button.id == f"nav-{section}":
                button.add_class("active")
            else:
                button.remove_class("active")

        # Update section title
        titles = {
            "llm": "LLM Setup",
            "performance": "Performance",
            "appearance": "Appearance",
            "paths": "Paths",
            "advanced": "Advanced",
            "testing": "Testing",
            "automation": "Automation",
            "modules": "Modules",
            "data": "Data",
        }
        title_widget = self.query_one("#settings-title", Static)
        title_widget.update(titles.get(section, "Settings"))

        # Switch content
        switcher = self.query_one("#settings-sections", ContentSwitcher)
        switcher.current = f"section-{section}"

        self.current_section = section

    def on_slider_changed(self, event: Slider.Changed) -> None:
        """Handle slider value changes."""
        slider_id = event.slider.id

        if slider_id == "primary-temperature":
            # Update display value (convert to 0.0-1.0)
            value_widget = self.query_one("#temp-value", Static)
            value_widget.update(str(event.value))
        elif slider_id == "secondary-temperature":
            value_widget = self.query_one("#secondary-temp-value", Static)
            value_widget.update(str(event.value))

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggle changes."""
        switch_id = event.switch.id

        if switch_id == "use-proxy":
            # Enable/disable proxy fields
            proxy_enabled = event.value
            self.query_one("#proxy-url", Input).disabled = not proxy_enabled
            self.query_one("#proxy-username", Input).disabled = not proxy_enabled
            self.query_one("#proxy-password", Input).disabled = not proxy_enabled

        elif switch_id == "enable-secondary":
            # Enable/disable secondary LLM fields
            secondary_enabled = event.value
            self.query_one("#secondary-provider", Select).disabled = not secondary_enabled
            self.query_one("#secondary-api-key", Input).disabled = not secondary_enabled
            self.query_one("#secondary-model", Input).disabled = not secondary_enabled
            self.query_one("#secondary-temperature", Slider).disabled = not secondary_enabled

        elif switch_id and switch_id.startswith("module-"):
            # Handle module toggle (mock system)
            self._handle_module_toggle(switch_id, event.value)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select dropdown changes."""
        select_id = event.select.id

        if select_id == "primary-provider":
            # Disable API key field when SDK mode is selected
            provider = str(event.value)
            api_key_input = self.query_one("#primary-api-key", Input)

            if provider == "claude_sdk_client":
                api_key_input.disabled = True
                api_key_input.placeholder = "Not needed for SDK mode"
            else:
                api_key_input.disabled = False
                api_key_input.placeholder = "Enter your API key"

        elif select_id == "theme-select":
            # Change theme immediately when selected
            theme = str(event.value)
            try:
                self.app.theme = theme
                self.app.notify(f"Theme changed to: {theme}", severity="information", timeout=2)
            except Exception as e:
                self.app.notify(f"Failed to change theme: {str(e)}", severity="error", timeout=3)

    def _load_module_states(self) -> None:
        """Load module states from bridge via GET_MODULES IPC call."""
        try:
            if hasattr(self.app, 'ipc_client') and self.app.ipc_client and self.app.connected:
                response = self.app.ipc_client.send_request(
                    IPCMessageType.GET_MODULES,
                    timeout=5.0
                )

                if response.success and response.data:
                    # Expected format: {"modules": {"module_id": {"enabled": true/false, ...}, ...}}
                    modules_data = response.data.get("modules", {})

                    for module_id, module_info in modules_data.items():
                        if isinstance(module_info, dict):
                            self.module_states[module_id] = module_info.get("enabled", False)
        except Exception as e:
            # Silently fail - modules will show default states from registry
            pass

    def _load_settings(self) -> None:
        """Load settings from bridge and populate form fields."""
        try:
            # Request settings from bridge via IPC
            if hasattr(self.app, 'ipc_client') and self.app.ipc_client and self.app.connected:
                response = self.app.ipc_client.send_request(
                    IPCMessageType.GET_SETTINGS,
                    timeout=5.0
                )

                if response.success and response.data:
                    settings = response.data

                    # Primary LLM
                    if "primary_provider" in settings:
                        self.query_one("#primary-provider", Select).value = settings["primary_provider"]
                    if "primary_api_key" in settings:
                        self.query_one("#primary-api-key", Input).value = settings["primary_api_key"]
                    if "primary_model" in settings:
                        self.query_one("#primary-model", Input).value = settings["primary_model"]
                    if "primary_temperature" in settings:
                        # Convert 0.0-2.0 to 0-200 slider scale
                        temp_value = int(settings["primary_temperature"] * 100)
                        self.query_one("#primary-temperature", Slider).value = temp_value
                        self.query_one("#temp-value", Static).update(str(temp_value))
                    if "primary_max_tokens" in settings:
                        self.query_one("#primary-max-tokens", Input).value = str(settings["primary_max_tokens"])
                    if "primary_prompt_caching" in settings:
                        self.query_one("#primary-prompt-caching", Switch).value = settings["primary_prompt_caching"]

                    # Proxy
                    if "use_proxy" in settings:
                        use_proxy = settings["use_proxy"]
                        self.query_one("#use-proxy", Switch).value = use_proxy
                        # Enable/disable proxy fields
                        self.query_one("#proxy-url", Input).disabled = not use_proxy
                        self.query_one("#proxy-username", Input).disabled = not use_proxy
                        self.query_one("#proxy-password", Input).disabled = not use_proxy
                    if "proxy_url" in settings:
                        self.query_one("#proxy-url", Input).value = settings["proxy_url"]
                    if "proxy_username" in settings:
                        self.query_one("#proxy-username", Input).value = settings["proxy_username"]
                    if "proxy_password" in settings:
                        self.query_one("#proxy-password", Input).value = settings["proxy_password"]

                    # Secondary LLM
                    if "enable_secondary" in settings:
                        enable_secondary = settings["enable_secondary"]
                        self.query_one("#enable-secondary", Switch).value = enable_secondary
                        # Enable/disable secondary fields
                        self.query_one("#secondary-provider", Select).disabled = not enable_secondary
                        self.query_one("#secondary-api-key", Input).disabled = not enable_secondary
                        self.query_one("#secondary-model", Input).disabled = not enable_secondary
                        self.query_one("#secondary-temperature", Slider).disabled = not enable_secondary
                    if "secondary_provider" in settings:
                        self.query_one("#secondary-provider", Select).value = settings["secondary_provider"]
                    if "secondary_api_key" in settings:
                        self.query_one("#secondary-api-key", Input).value = settings["secondary_api_key"]
                    if "secondary_model" in settings:
                        self.query_one("#secondary-model", Input).value = settings["secondary_model"]
                    if "secondary_temperature" in settings:
                        # Convert 0.0-2.0 to 0-200 slider scale
                        temp_value = int(settings["secondary_temperature"] * 100)
                        self.query_one("#secondary-temperature", Slider).value = temp_value
                        self.query_one("#secondary-temp-value", Static).update(str(temp_value))

                    # Store loaded settings
                    self.settings = settings

                else:
                    # Settings not available yet, use defaults
                    pass

        except Exception as e:
            # If loading fails, just use the default values already in the form
            self.app.notify(f"⚠ Could not load settings: {e}", severity="warning")

    def _save_settings(self) -> None:
        """Collect and save all settings."""
        # Collect settings from all widgets
        try:
            # Get all input values
            settings = {}

            # Primary LLM
            settings["primary_provider"] = str(self.query_one("#primary-provider", Select).value)
            settings["primary_api_key"] = self.query_one("#primary-api-key", Input).value
            settings["primary_model"] = self.query_one("#primary-model", Input).value
            settings["primary_temperature"] = self.query_one("#primary-temperature", Slider).value / 100.0
            settings["primary_max_tokens"] = self.query_one("#primary-max-tokens", Input).value
            settings["primary_prompt_caching"] = self.query_one("#primary-prompt-caching", Switch).value

            # Proxy
            settings["use_proxy"] = self.query_one("#use-proxy", Switch).value
            settings["proxy_url"] = self.query_one("#proxy-url", Input).value
            settings["proxy_username"] = self.query_one("#proxy-username", Input).value
            settings["proxy_password"] = self.query_one("#proxy-password", Input).value

            # Secondary LLM
            settings["enable_secondary"] = self.query_one("#enable-secondary", Switch).value
            settings["secondary_provider"] = str(self.query_one("#secondary-provider", Select).value)
            settings["secondary_api_key"] = self.query_one("#secondary-api-key", Input).value
            settings["secondary_model"] = self.query_one("#secondary-model", Input).value
            settings["secondary_temperature"] = self.query_one("#secondary-temperature", Slider).value / 100.0

            self.settings = settings

            # Send to bridge via IPC
            if hasattr(self.app, 'ipc_client') and self.app.ipc_client and self.app.connected:
                response = self.app.ipc_client.send_request(
                    IPCMessageType.UPDATE_SETTINGS,
                    timeout=5.0,
                    settings=settings
                )

                if response.success:
                    self.app.notify("✓ Settings saved successfully", severity="information")
                else:
                    self.app.notify(f"✗ Failed to save: {response.error_message}", severity="error")
            else:
                self.app.notify("⚠ Not connected to Bridge", severity="warning")

        except Exception as e:
            self.app.notify(f"✗ Error saving settings: {e}", severity="error")


__all__ = ["SettingsOverlay"]
