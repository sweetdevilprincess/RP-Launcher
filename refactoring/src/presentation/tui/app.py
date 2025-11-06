"""Main TUI application for RP Client.

This module provides the complete Textual-based TUI application that
communicates with the Bridge via socket IPC.

Features:
- Tab-based navigation (Chat, Entities, Branches, Modules, Settings, Help, Status)
- Real-time IPC communication with Bridge service
- LLM provider configuration and module toggles
- Branch visualization and management
- Entity management with triggers
"""

from __future__ import annotations

import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, Static, Tabs, Tab, ContentSwitcher, Markdown

from ...infrastructure.ipc import IPCMessageType, SocketClient
from ...infrastructure.filesystem import StatePaths
from ...infrastructure.logging import LoggingService, PythonLoggingService
from ...infrastructure.sessions import SessionStateService
from ...domain.sessions import SessionRepository
from .components import (
    AddMessageRequest,
    AppHeader,
    SimpleMessage,
    BranchesPage,
    ChatDisplay,
    ContextPanel,
    EntityManager,
    RPTextArea,
    SettingsOverlay,
    UpdateMessageRequest,
)
from .screens import (
    BaseOverlay,
    BranchCreationDialog,
    ChapterCompressionDialog,
    CharacterSheetOverlay,
    StoryOverviewOverlay,
    HelpOverlay,
)
from .styles import get_app_css


# =============================================================================
# MAIN APP
# =============================================================================

class RPClientApp(App):
    """Main RP Client TUI Application.

    This refactored TUI application:
    - Connects to Bridge via socket IPC
    - Tab-based navigation for different features
    - Real-time LLM communication with streaming
    - Entity management and branch visualization
    - Settings and module configuration
    """

    CSS = get_app_css()

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+j", "submit_message", "Send"),
        Binding("ctrl+t", "cycle_theme", "Theme"),
        Binding("f1", "show_help", "Help"),
        Binding("f2", "show_character_sheet", "Character"),
        Binding("f3", "show_story_overview", "Story"),
        Binding("f4", "show_status", "Status"),
    ]

    def __init__(self, rp_dir: Path, bridge_host: str = "127.0.0.1", bridge_port: int = 5555):
        """Initialize RP Client TUI.

        Args:
            rp_dir: Path to RP directory
            bridge_host: Bridge server host (default: 127.0.0.1)
            bridge_port: Bridge server port (default: 5555)
        """
        super().__init__()
        self.rp_dir = rp_dir
        self.bridge_host = bridge_host
        self.bridge_port = bridge_port

        # Components
        self.header: AppHeader | None = None
        self.context_panel: ContextPanel | None = None
        self.chat_display: ChatDisplay | None = None
        self.text_area: RPTextArea | None = None
        self.entity_manager: EntityManager | None = None
        self.settings_overlay: SettingsOverlay | None = None

        # IPC client
        self.ipc_client: SocketClient | None = None
        self.connected = False
        self.connection_time: float = 0.0  # Track when connection was made

        # Session repository for loading chat history
        paths = StatePaths(rp_dir=rp_dir)
        # Create logger (PythonLoggingService accepts a logging.Logger, not a name string)
        import logging
        logger = PythonLoggingService(logger=logging.getLogger("rp.tui.app"))

        # Create session state service (needed for branch tracking)
        session_state_service = SessionStateService(logger=logger)

        # Create session repository with session state service
        self.session_repository = SessionRepository(
            paths=paths,
            logger=logger,
            session_state_service=session_state_service
        )

        # Track last non-entity tab for transparency handling
        self.last_non_entity_tab = "tab-chat"

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        # Navigation tabs at the top
        yield Tabs(
            Tab("💬 Chat", id="tab-chat"),
            Tab("🎭 Entities", id="tab-entities"),
            Tab("🌳 Branches", id="tab-branches"),
            Tab("⚙️ Settings", id="tab-settings"),
            Tab("❓ Help", id="tab-help"),
            Tab("📊 Status", id="tab-status"),
            id="top-tabs"
        )

        # Content switcher for different pages
        with ContentSwitcher(id="content-switcher", initial="tab-chat"):
            # Chat page (default)
            with Vertical(id="tab-chat"):
                with Container(classes="page-container"):
                    self.context_panel = ContextPanel(self.rp_dir, id="context-panel")
                    yield self.context_panel

                    self.chat_display = ChatDisplay(id="chat-panel")
                    yield self.chat_display

                # Input container - only visible on chat page
                with Container(id="input-container"):
                    yield Static(">> Your Move", id="input-label")
                    with Horizontal(id="input-row"):
                        self.text_area = RPTextArea(id="input-area")
                        self.text_area.placeholder = "Type your message... (Ctrl+Enter to send)"
                        yield self.text_area
                        with Vertical(id="input-controls"):
                            yield Button("Send", id="send-button", variant="primary")
                            yield Static("Ctrl+Enter", id="send-hint")
                            yield Button("Compress Chapter", id="compress-chapter-button")
                    yield Static("", id="status-message")

            # Entities page - placeholder for now (will add EntityManager component)
            with Container(id="tab-entities", classes="transparent-page"):
                yield Static("Entities page coming soon...", classes="page-title")

            # Branches page
            yield BranchesPage(id="tab-branches")

            # Settings page (blank - overlay shown on tab click)
            with Container(id="tab-settings", classes="blank-page"):
                pass  # Empty - LLMSettingsPage overlay covers this

            # Help page
            with ScrollableContainer(id="tab-help", classes="help-page"):
                yield Markdown("""# ❓ Help

## Keyboard Shortcuts & Controls

### Main Controls
- **Ctrl+Enter** - Send message
- **Enter** - New line in message
- **Ctrl+Q** - Quit application
- **Ctrl+T** - Cycle through themes
- **F1** - Show help overlay

### Quick Access Overlays (F-keys)
- **F2** - Character Sheet
- **F3** - Story Overview (Arc + Genome)
- **F4** - Status overlay

### In Overlays
- **ESC** - Close overlay
- **↑/↓ or PgUp/PgDn** - Scroll content
- **Number keys** - Switch tabs (in tabbed overlays)

### Layout Guide
- **Left Panel**: Context information
- **Main Area**: Chat display or page content
- **Bottom**: Message input area (on Chat page)

### Writing Tips
- Type naturally - Enter adds new lines
- Multi-line messages supported
- Press Ctrl+Enter when ready to send

### Available Themes
Press **Ctrl+T** to cycle through themes
""")

            # Status page
            with ScrollableContainer(id="tab-status", classes="status-page"):
                yield Markdown("""# 📊 Status

## Progress
- **Total Responses**: 0
- **Arc Progress**: 0/50 turns
- **Completion**: 0.0%

## System Info
- **Theme**: Default
- **Status**: Running
- **Version**: 1.0.0

## Recent Activity
- No activity yet

*Status information will update as you use the application.*

---

**Tip:** Press F4 to open the detailed Status overlay.
""")

        # Footer with location/timestamp info
        self.header = AppHeader(self.rp_dir, id="app-header")
        yield self.header

        # Entity overlay - floats above content when entities tab is active
        self.entity_manager = EntityManager(id="entity-manager")
        yield self.entity_manager

        # Settings overlay - floats above content when settings tab is active
        self.settings_overlay = SettingsOverlay(id="settings-overlay")
        self.settings_overlay.styles.display = "none"  # Hidden by default
        yield self.settings_overlay

    def on_mount(self) -> None:
        """Initialize after mounting."""
        # Load theme from config
        self._load_theme()

        # Connect to bridge
        self._connect_to_bridge()

        # Load chat history from session
        self._load_chat_history()

        # Display welcome message
        if self.chat_display:
            self.post_message(
                AddMessageRequest(
                    sender="system",
                    content=f"[bold]✨ RP Client TUI Started[/]\n"
                    f"[dim]RP Directory: {self.rp_dir.name}\n"
                    f"Connection: {'Connected' if self.connected else 'Disconnected'}\n\n"
                    f"Type your message below and press [bold]Ctrl+Enter[/] to send.\n"
                    f"Press [bold]F1[/] for help or browse the tabs above.[/]"
                )
            )

    def _load_chat_history(self) -> None:
        """Load chat history from session and populate chat display."""
        if not self.chat_display:
            return

        try:
            # Load active session
            session = self.session_repository.load_active_session()

            # Add each message to the chat display
            for message in session.messages:
                # Add user message if it exists
                if message.user_message:
                    self.post_message(
                        AddMessageRequest(
                            sender="you",
                            content=message.user_message,
                            message_id=f"history-user-{message.response_num}",
                            response_num=message.response_num
                        )
                    )

                # Add assistant response if it exists
                if message.assistant_response:
                    self.post_message(
                        AddMessageRequest(
                            sender="claude",
                            content=message.assistant_response,
                            message_id=f"history-assistant-{message.response_num}",
                            response_num=message.response_num
                        )
                    )

            # Log success
            message_count = len(session.messages)
            if message_count > 0:
                self.log(f"Loaded {message_count} messages from session")

        except FileNotFoundError:
            # No session file yet - this is fine for new RPs
            self.log("No session file found, starting fresh")
        except Exception as e:
            # Log error but don't crash
            self.log(f"Error loading chat history: {e}")
            self.notify(f"⚠ Could not load chat history: {e}", severity="warning")

    def _load_theme(self) -> None:
        """Load theme from config file."""
        try:
            import json
            config_path = self.rp_dir / "config" / "config.json"
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)
                theme = config.get("system", {}).get("theme", "textual-dark")
                self.theme = theme
                self.log(f"Loaded theme from config: {theme}")
            else:
                self.log("Config file not found, using default theme")
        except Exception as e:
            self.log(f"Error loading theme: {e}")
            # Use default theme on error

    def _save_theme(self, theme: str) -> None:
        """Save theme to config file."""
        try:
            import json
            config_path = self.rp_dir / "config" / "config.json"
            if config_path.exists():
                # Read existing config
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)

                # Update theme
                if "system" not in config:
                    config["system"] = {}
                config["system"]["theme"] = theme

                # Write back to file
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                self.log(f"Saved theme to config: {theme}")
            else:
                self.log("Config file not found, cannot save theme")
        except Exception as e:
            self.log(f"Error saving theme: {e}")

    def _connect_to_bridge(self) -> None:
        """Attempt to connect to bridge service with retries."""
        import time

        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                self.ipc_client = SocketClient(
                    host=self.bridge_host,
                    port=self.bridge_port
                )
                self.ipc_client.connect()

                # Test connection with ping
                response = self.ipc_client.send_request(IPCMessageType.PING, timeout=5.0)
                if response and response.success:
                    import time
                    self.connected = True
                    self.connection_time = time.time()
                    self.notify("Connected to Bridge", severity="information")
                    return
                else:
                    # Ping failed, disconnect and retry
                    self.ipc_client.disconnect()
                    self.ipc_client = None

            except Exception as e:
                # Connection failed, clean up
                if self.ipc_client:
                    try:
                        self.ipc_client.disconnect()
                    except Exception:
                        pass
                    self.ipc_client = None

                # If not last attempt, wait and retry
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    # Final attempt failed
                    self.connected = False
                    self.notify(
                        f"Failed to connect to Bridge after {max_retries} attempts: {e}",
                        severity="error"
                    )
                    return

        # All retries exhausted
        self.connected = False
        self.notify("Could not connect to Bridge", severity="error")

    def action_submit_message(self) -> None:
        """Handle Ctrl+Enter to submit message."""
        if not self.text_area or not self.chat_display:
            return

        message = self.text_area.text.strip()
        if not message:
            self.show_status("[dim]Message is empty[/]")
            return

        # Generate message IDs for both user and assistant messages
        import uuid
        self._user_message_id = str(uuid.uuid4())
        self._streaming_message_id = str(uuid.uuid4())

        # Display user message
        self.post_message(
            AddMessageRequest(
                sender="you",
                content=message,
                message_id=self._user_message_id
            )
        )

        # Clear input
        self.text_area.clear()

        # Send to bridge
        if self.connected and self.ipc_client:
            try:
                # Initialize streaming buffer
                self._streaming_buffer = ""

                # Create initial LLM message (empty for now, will be updated via streaming)
                self.post_message(
                    AddMessageRequest(
                        sender="claude",
                        content="",
                        message_id=self._streaming_message_id
                    )
                )

                # Send asynchronously with streaming callback
                self.ipc_client.send_request_async(
                    IPCMessageType.SEND_MESSAGE,
                    callback=self._handle_llm_response,
                    streaming_callback=self._handle_streaming_chunk,
                    user_message=message
                )
                self.show_status("⏳ Sending message...")
            except Exception as e:
                self.post_message(
                    AddMessageRequest(sender="system", content=f"[Error sending message: {e}]")
                )
        else:
            self.post_message(
                AddMessageRequest(
                    sender="system",
                    content="[Not connected to Bridge. Check if bridge service is running.]"
                )
            )

    def _handle_streaming_chunk(self, chunk: str) -> None:
        """Handle streaming chunk from LLM.

        Args:
            chunk: Text chunk from streaming response
        """
        # Accumulate chunks in buffer for fallback
        self._streaming_buffer += chunk

        # Post update message to display in real-time
        if hasattr(self, '_streaming_message_id') and self.chat_display:
            self.post_message(
                UpdateMessageRequest(
                    message_id=self._streaming_message_id,
                    chunk=chunk
                )
            )

    def _handle_llm_response(self, response) -> None:
        """Handle LLM response from bridge.

        Args:
            response: IPCResponse from bridge
        """
        if not self.chat_display:
            return

        if response.success:
            # Check if this was a streaming response
            is_streaming = hasattr(self, '_streaming_buffer') and self._streaming_buffer

            # Get response number from bridge response
            response_num = response.data.get("response_num")

            if not is_streaming:
                # Non-streaming provider - add complete message
                llm_message = response.data.get("llm_response", "[No response]")
                self.post_message(
                    AddMessageRequest(
                        sender="claude",
                        content=llm_message,
                        response_num=response_num
                    )
                )
                # Update the user message with the same response_num
                if response_num is not None and hasattr(self, '_user_message_id'):
                    self.chat_display.update_message_index(
                        self._user_message_id,
                        response_num
                    )
            else:
                # Streaming message already exists - update its message_index with correct response_num
                if response_num is not None:
                    if hasattr(self, '_streaming_message_id'):
                        self.chat_display.update_message_index(
                            self._streaming_message_id,
                            response_num
                        )
                    # Also update the user message with the same response_num
                    if hasattr(self, '_user_message_id'):
                        self.chat_display.update_message_index(
                            self._user_message_id,
                            response_num
                        )

            # Update metadata if provided
            metadata = response.data.get("metadata", {})
            if metadata:
                provider = metadata.get("provider", "unknown")
                self.show_status(f"✅ Response from {provider}")
                self.set_timer(2.0, lambda: self.show_status(""))
        else:
            error_msg = response.error_message or "Unknown error"
            self.post_message(
                AddMessageRequest(sender="system", content=f"[Error: {error_msg}]")
            )

    async def action_compress_chapter(self) -> None:
        """Handle chapter compression button click."""
        # Get current chapter number from context panel
        chapter_number = 1  # Default
        if self.context_panel:
            try:
                chapter_text = self.context_panel.chapter_value
                # Extract number from "Chapter X" format
                if chapter_text and "Chapter" in chapter_text:
                    chapter_number = int(chapter_text.split()[-1])
            except (ValueError, IndexError):
                chapter_number = 1

        # Get message count from chat display
        message_count = 0
        if self.chat_display:
            message_count = self.chat_display.message_count

        # Show compression dialog
        result = await self.push_screen(
            ChapterCompressionDialog(
                chapter_number=chapter_number,
                message_count=message_count,
            )
        )

        # If user confirmed (didn't cancel)
        if result:
            chapter_title = result.get("chapter_title", "")
            tags = result.get("tags", "")
            chapter_num = int(result.get("chapter_number", chapter_number))

            # Parse tags (comma-separated to list)
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []

            # Send compression request via IPC
            if self.connected and self.ipc_client:
                try:
                    self.show_status(f"⏳ Compressing Chapter {chapter_num}...")

                    response = self.ipc_client.send_request(
                        IPCMessageType.COMPRESS_CHAPTER,
                        chapter_number=chapter_num,
                        chapter_title=chapter_title,
                        tags=tag_list,
                        session_id="main"
                    )

                    if response.success:
                        summary_path = response.data.get("summary_path", "")
                        word_count = response.data.get("word_count", 0)
                        self.notify(
                            f"✓ Chapter {chapter_num} compressed ({word_count} words)",
                            severity="information",
                            timeout=5
                        )
                        self.show_status(f"✅ Chapter compressed: {summary_path}")

                        # Update context panel to show new chapter number
                        if self.context_panel:
                            self.context_panel.update_context()

                    else:
                        error = response.error_message or "Unknown error"
                        self.notify(f"✗ Failed to compress chapter: {error}", severity="error", timeout=5)
                        self.show_status("")

                except Exception as e:
                    self.notify(f"✗ Error compressing chapter: {e}", severity="error", timeout=5)
                    self.show_status("")
            else:
                self.notify("Not connected to Bridge", severity="warning", timeout=3)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "send-button":
            self.action_submit_message()
        elif event.button.id == "compress-chapter-button":
            self.action_compress_chapter()

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle tab clicks - switch content based on active tab."""
        tab_id = event.tab.id

        if tab_id == "tab-settings":
            # Show settings overlay, hide others
            if self.settings_overlay:
                self.settings_overlay.styles.display = "block"
            if self.entity_manager:
                self.entity_manager.styles.display = "none"
                self.entity_manager.hide_drawer()
            # Switch to settings blank page
            self.query_one("#content-switcher", ContentSwitcher).current = tab_id
        elif tab_id == "tab-entities":
            # Show entity overlay, hide others, keep ContentSwitcher on last page for transparency
            if self.entity_manager:
                self.entity_manager.styles.display = "block"
            if self.settings_overlay:
                self.settings_overlay.styles.display = "none"
            # Keep on last non-entity tab for transparency
            self.query_one("#content-switcher", ContentSwitcher).current = self.last_non_entity_tab
        else:
            # Hide all overlays, switch to selected tab
            if self.entity_manager:
                self.entity_manager.styles.display = "none"
                self.entity_manager.hide_drawer()
            if self.settings_overlay:
                self.settings_overlay.styles.display = "none"
            self.last_non_entity_tab = tab_id
            self.query_one("#content-switcher", ContentSwitcher).current = tab_id

    def show_status(self, message: str) -> None:
        """Show status message with formatting."""
        if not message:
            self.query_one("#status-message", Static).update("")
            return

        if "❌" in message or "Error" in message:
            styled = f"[bold red]{message}[/]"
        elif "✅" in message or "success" in message.lower():
            styled = f"[bold green]{message}[/]"
        elif "⏳" in message or "Waiting" in message:
            styled = f"[bold yellow]{message}[/]"
        else:
            styled = f"{message}"

        self.query_one("#status-message", Static).update(styled)

    def _dismiss_current_overlay(self) -> None:
        """Dismiss any currently open overlay"""
        if len(self.screen_stack) > 1:
            self.pop_screen()

    # Overlay actions
    def action_show_character_sheet(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(CharacterSheetOverlay())

    def action_show_story_overview(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(StoryOverviewOverlay())

    def action_show_status(self) -> None:
        """Show status overlay with mock info"""
        class StatusOverlay(BaseOverlay):
            def compose(self) -> ComposeResult:
                content = """# Status

## Progress
- **Total Responses**: 0
- **Arc Progress**: 0/50

## System Info
- **Theme**: Default
- **Status**: Running

*Status information coming soon.*
"""
                yield from self._create_overlay("📊 Status", content)

        self._dismiss_current_overlay()
        self.push_screen(StatusOverlay())


    def action_cycle_theme(self) -> None:
        """Cycle through available themes"""
        # Built-in Textual themes
        available_themes = [
            "textual-dark",
            "textual-light",
            "nord",
            "gruvbox",
            "catppuccin-mocha",
            "dracula",
            "tokyo-night",
            "monokai",
            "solarized-light",
        ]

        try:
            current_theme = self.theme
            if current_theme in available_themes:
                current_idx = available_themes.index(current_theme)
                next_theme = available_themes[(current_idx + 1) % len(available_themes)]
            else:
                next_theme = available_themes[0]

            self.theme = next_theme
            self._save_theme(next_theme)  # Persist theme to config
            self.notify(f"🎨 Theme: {next_theme}", severity="information", timeout=2)
        except Exception as e:
            self.notify(f"⚠️ Theme error: {e}", severity="warning", timeout=5)

    def action_show_help(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(HelpOverlay())

    # =========================================================================
    # Branch Creation Handlers
    # =========================================================================

    def on_simple_message_branch_requested(
        self, event: SimpleMessage.BranchRequested
    ) -> None:
        """Handle branch request from a message.

        Args:
            event: BranchRequested event with message details
        """
        # Show branch creation dialog
        def handle_dialog_result(result: dict[str, str | bool] | None) -> None:
            """Handle the result from the branch creation dialog.

            Args:
                result: Dialog result or None if cancelled
            """
            if result is None:
                # User cancelled
                return

            # Extract form data
            branch_name = result.get("branch_name", "")
            description = result.get("description", "")
            tags_str = result.get("tags", "")
            switch_immediately = result.get("switch_immediately", False)
            branch_point = result.get("branch_point", event.message_index)

            # Parse tags
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

            # Send IPC request to create branch
            self._create_branch_via_ipc(
                branch_name=branch_name,
                branch_point=branch_point,
                description=description,
                tags=tags,
                switch_immediately=switch_immediately
            )

        # Show the dialog
        self.push_screen(
            BranchCreationDialog(
                message_index=event.message_index,
                message_sender=event.sender,
                message_content=event.content
            ),
            handle_dialog_result
        )

    def _create_branch_via_ipc(
        self,
        branch_name: str,
        branch_point: int,
        description: str = "",
        tags: list[str] | None = None,
        switch_immediately: bool = False
    ) -> None:
        """Create a new branch via IPC.

        Args:
            branch_name: Name for the new branch
            branch_point: Message index to branch from
            description: Optional description
            tags: Optional list of tags
            switch_immediately: Whether to switch to the new branch
        """
        if not self.connected or not self.ipc_client:
            self.notify("Not connected to Bridge", severity="warning")
            return

        try:
            # Send create branch request
            response = self.ipc_client.send_request(
                IPCMessageType.CREATE_BRANCH,
                timeout=10.0,
                branch_name=branch_name,
                branch_point=branch_point,
                description=description,
                tags=tags or []
            )

            if response.success:
                branch_id = response.data.get("branch_id", branch_name)
                self.notify(
                    f"✓ Branch '{branch_name}' created from message #{branch_point}",
                    severity="information",
                    timeout=5
                )

                # Switch to new branch if requested
                if switch_immediately:
                    self._switch_branch_via_ipc(branch_id)
            else:
                error = response.error_message or "Unknown error"
                self.notify(f"✗ Failed to create branch: {error}", severity="error", timeout=5)

        except Exception as e:
            self.notify(f"✗ Error creating branch: {e}", severity="error", timeout=5)

    def _switch_branch_via_ipc(self, timeline_id: str) -> None:
        """Switch to a different timeline via IPC.

        Args:
            timeline_id: ID of the timeline to switch to
        """
        if not self.connected or not self.ipc_client:
            self.notify("Not connected to Bridge", severity="warning")
            return

        try:
            response = self.ipc_client.send_request(
                IPCMessageType.SWITCH_BRANCH,
                timeout=5.0,
                timeline_id=timeline_id
            )

            if response.success:
                self.notify(f"✓ Switched to branch '{timeline_id}'", severity="information")
                # Reload chat history for the new branch
                if self.chat_display:
                    # Clear existing messages
                    self.chat_display._by_id.clear()
                    self.chat_display._order.clear()
                    self.chat_display.message_count = 0
                    # Reload history
                    self._load_chat_history()
            else:
                error = response.error_message or "Unknown error"
                self.notify(f"✗ Failed to switch branch: {error}", severity="error")

        except Exception as e:
            self.notify(f"✗ Error switching branch: {e}", severity="error")

    def on_simple_message_bookmark_requested(
        self, event: SimpleMessage.BookmarkRequested
    ) -> None:
        """Handle bookmark request from a message.

        Args:
            event: BookmarkRequested event with message index
        """
        # TODO: Implement bookmarking functionality
        self.notify(f"Bookmarked message #{event.message_index}", severity="information")

    def on_simple_message_copy_requested(
        self, event: SimpleMessage.CopyRequested
    ) -> None:
        """Handle copy request from a message.

        Args:
            event: CopyRequested event with message content
        """
        try:
            # Copy to system clipboard using pyperclip
            import pyperclip
            pyperclip.copy(event.content)
            self.notify(f"📋 Copied message #{event.message_index} to clipboard", severity="information")
        except ImportError:
            # Fallback if pyperclip not available
            self.notify("⚠ Clipboard library not available. Install pyperclip: pip install pyperclip", severity="warning")
        except Exception as e:
            self.notify(f"✗ Failed to copy: {e}", severity="error")

    # =========================================================================
    # Chat Message Handlers (for widget-based display)
    # =========================================================================

    def on_add_message_request(self, event: AddMessageRequest) -> None:
        """Handle request to add a new message to chat display.

        This handler receives AddMessageRequest messages posted from any source
        (UI thread or background threads). It delegates to ChatDisplay's thread-safe
        public API.

        Args:
            event: AddMessageRequest with sender, content, message_id, and optional response_num
        """
        if not self.chat_display:
            return

        self.chat_display.add_message(
            sender=event.sender,
            content=event.content,
            message_id=event.message_id,
            response_num=event.response_num
        )

    def on_update_message_request(self, event: UpdateMessageRequest) -> None:
        """Handle request to update an existing message (streaming).

        This handler receives UpdateMessageRequest messages posted from background
        threads during streaming responses. It delegates to ChatDisplay's thread-safe
        public API.

        Args:
            event: UpdateMessageRequest with message_id and chunk
        """
        if not self.chat_display:
            return

        self.chat_display.append_chunk(
            message_id=event.message_id,
            chunk=event.chunk
        )

    def on_unmount(self) -> None:
        """Cleanup before closing."""
        if self.ipc_client and self.connected:
            try:
                self.ipc_client.disconnect()
            except Exception:
                pass


__all__ = ["RPClientApp"]
