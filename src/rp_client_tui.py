#!/usr/bin/env python3
"""
RP Client TUI - Enhanced Terminal Interface for Claude Code RP System

Features:
- Better text input (multi-line, no glitches)
- Quick reference overlays (Ctrl+M for memory, Ctrl+A for arc, etc.)
- Real-time context display (chapter, time, location, progress)
- File-based Claude Code integration (zero cost)
"""

import sys
import json
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Static,
    TextArea,
    Button,
    Label,
    ProgressBar,
    Input,
    Switch,
)
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.message import Message
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def read_file(path: Path) -> str:
    """Read file contents, return empty string if not found."""
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return ""


def read_json(path: Path) -> dict:
    """Read JSON file, return empty dict if not found."""
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def get_chapter_info(state_file: Path) -> tuple[str, str, str]:
    """Extract chapter, timestamp, location from current_state.md"""
    content = read_file(state_file)

    chapter = "Unknown"
    timestamp = "Unknown"
    location = "Unknown"

    for line in content.split('\n'):
        if line.startswith('**Chapter'):
            chapter = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
        elif line.startswith('**Timestamp'):
            timestamp = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
        elif line.startswith('**Location'):
            location = line.split(':', 1)[1].strip() if ':' in line else "Unknown"

    return chapter, timestamp, location


def get_active_characters(rp_dir: Path) -> list[str]:
    """Get active characters from session_triggers.txt"""
    triggers_file = rp_dir / "state" / "session_triggers.txt"
    content = read_file(triggers_file)

    characters = []
    for line in content.split('\n'):
        if line.strip() and not line.startswith('#'):
            # Format: "- Silas (Triggers: Silas, him, boyfriend)"
            if '(' in line:
                name = line.split('(')[0].replace('-', '').strip()
                if name:
                    characters.append(name)

    return characters if characters else ["None"]


def get_response_count(counter_file: Path) -> int:
    """Get current response count"""
    try:
        return int(read_file(counter_file).strip())
    except:
        return 0


def get_arc_progress(counter_file: Path, arc_frequency: int = 50) -> tuple[int, int, float]:
    """Get arc progress: (current, next, percentage)"""
    count = get_response_count(counter_file)
    progress = count % arc_frequency
    next_arc = arc_frequency - progress
    percentage = (progress / arc_frequency) * 100
    return progress, next_arc, percentage


# =============================================================================
# OVERLAY SCREENS
# =============================================================================

class MemoryOverlay(ModalScreen):
    """Overlay for viewing user memory (Ctrl+M)"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        memory_file = self.rp_dir / "state" / "user_memory.md"
        content = read_file(memory_file)

        if not content:
            content = "# User Memory\n\n*Memory file not found. Use `/memory` command to create.*"

        with Container(id="overlay-container"):
            yield Static("📖 User Memory", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class ArcOverlay(ModalScreen):
    """Overlay for viewing story arc (Ctrl+A)"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        arc_file = self.rp_dir / "state" / "story_arc.md"
        content = read_file(arc_file)

        if not content:
            content = "# Story Arc\n\n*Story arc not generated yet. Use `/arc` command to create.*"

        with Container(id="overlay-container"):
            yield Static("📊 Story Arc", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class CharactersOverlay(ModalScreen):
    """Overlay for viewing characters (Ctrl+C)"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        chars_dir = self.rp_dir / "characters"

        # Get active characters
        active = get_active_characters(self.rp_dir)

        # Get all character files
        char_files = sorted(chars_dir.glob("*.md")) if chars_dir.exists() else []

        content = "# 🎭 Characters\n\n"
        content += "## Active This Scene\n"
        for char in active:
            content += f"- **{char}**\n"

        content += "\n## All Characters\n"
        for char_file in char_files:
            name = char_file.stem
            content += f"- {name}\n"

        content += "\n*Select a character file from the file explorer to view full sheet*"

        with Container(id="overlay-container"):
            yield Static("🎭 Characters", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class SceneNotesOverlay(ModalScreen):
    """Overlay for viewing scene notes (Ctrl+N)"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        notes_file = self.rp_dir / "SCENE_NOTES.md"
        content = read_file(notes_file)

        if not content:
            content = "# Scene Notes\n\n*No scene notes found.*"

        with Container(id="overlay-container"):
            yield Static("📝 Scene Notes", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class EntitiesOverlay(ModalScreen):
    """Overlay for viewing tracked entities (Ctrl+E)"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        tracker_file = self.rp_dir / "state" / "entity_tracker.json"
        entities = read_json(tracker_file).get("entities", {})

        content = "# 🎭 Tracked Entities\n\n"

        if not entities:
            content += "*No entities tracked yet.*"
        else:
            content += "| Name | Mentions | Card | Last Chapter |\n"
            content += "|------|----------|------|-------------|\n"

            for name, data in sorted(entities.items(), key=lambda x: x[1].get('mentions', 0), reverse=True):
                mentions = data.get('mentions', 0)
                has_card = "✅" if data.get('card_created', False) else "⏳"
                last_chapter = data.get('last_chapter', '?')
                content += f"| {name} | {mentions} | {has_card} | {last_chapter} |\n"

        with Container(id="overlay-container"):
            yield Static("🎭 Entities", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class GenomeOverlay(ModalScreen):
    """Overlay for viewing story genome (Ctrl+G)"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        genome_file = self.rp_dir / "STORY_GENOME.md"
        content = read_file(genome_file)

        if not content:
            content = "# Story Genome\n\n*Story genome not found.*"

        with Container(id="overlay-container"):
            yield Static("📖 Story Genome", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class StatusOverlay(ModalScreen):
    """Overlay for system status (Ctrl+T)"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        # Read status info
        counter_file = self.rp_dir / "state" / "response_counter.txt"
        config_file = self.rp_dir / "state" / "automation_config.json"
        log_file = self.rp_dir / "state" / "hook.log"

        count = get_response_count(counter_file)
        progress, next_arc, _ = get_arc_progress(counter_file)
        config = read_json(config_file)

        content = "# 📊 System Status\n\n"
        content += "## Progress\n"
        content += f"- **Total Responses**: {count}\n"
        content += f"- **Next Arc Generation**: {next_arc} responses away\n"
        content += f"- **Arc Progress**: {progress}/50\n\n"

        content += "## Automation\n"
        auto_cards = config.get('auto_entity_cards', True)
        auto_arc = config.get('auto_story_arc', True)
        threshold = config.get('entity_mention_threshold', 2)
        frequency = config.get('arc_frequency', 50)

        content += f"- **Entity Cards**: {'✅ ON' if auto_cards else '❌ OFF'} (Threshold: {threshold} mentions)\n"
        content += f"- **Story Arcs**: {'✅ ON' if auto_arc else '❌ OFF'} (Every {frequency} responses)\n\n"

        content += "## Recent Activity\n"
        log_content = read_file(log_file)
        if log_content:
            lines = log_content.strip().split('\n')[-10:]  # Last 10 lines
            for line in lines:
                if line.strip():
                    content += f"- {line}\n"
        else:
            content += "*No recent activity logged.*\n"

        with Container(id="overlay-container"):
            yield Static("📊 Status", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class SettingsScreen(ModalScreen):
    """Settings screen for API configuration"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir
        self.config_file = rp_dir.parent / "config.json"  # Global config

    def compose(self) -> ComposeResult:
        # Load existing config
        config = self.load_config()
        claude_api_key = config.get("anthropic_api_key", "")
        deepseek_api_key = config.get("deepseek_api_key", "")
        use_api_mode = config.get("use_api_mode", False)
        use_proxy = config.get("use_proxy", False)

        # Mask API keys for display
        def mask_key(key):
            if key:
                if len(key) > 12:
                    return key[:8] + "..." + key[-4:]
                else:
                    return "***...***"
            return ""

        masked_claude_key = mask_key(claude_api_key)
        masked_deepseek_key = mask_key(deepseek_api_key)

        with Container(id="settings-container"):
            yield Static("⚙️ Settings", id="settings-title")

            with ScrollableContainer(id="settings-content"):
                yield Static("## Claude API Configuration", classes="settings-section-title")
                yield Static("")

                yield Static("API Mode (uses Anthropic API with prompt caching):", classes="settings-label")
                yield Switch(value=use_api_mode, id="api-mode-switch")
                yield Static("")

                yield Static("Anthropic API Key (for main Claude responses):", classes="settings-label")
                if claude_api_key:
                    yield Static(f"Current: {masked_claude_key}", classes="settings-info")
                else:
                    yield Static("Current: Not set", classes="settings-info")
                yield Static("")

                yield Static("Enter new Claude API key (leave blank to keep current):", classes="settings-label")
                yield Input(
                    placeholder="sk-ant-api03-...",
                    password=True,
                    id="claude-api-key-input"
                )
                yield Static("")

                yield Static("💡 Get Claude key from: https://console.anthropic.com/settings/keys",
                           classes="settings-hint")
                yield Static("   ⚠️  Must start with 'sk-ant-'", classes="settings-hint")
                yield Static("")

                yield Static("## DeepSeek API Configuration", classes="settings-section-title")
                yield Static("")

                yield Static("DeepSeek API Key (for auto-generation features):", classes="settings-label")
                if deepseek_api_key:
                    yield Static(f"Current: {masked_deepseek_key}", classes="settings-info")
                else:
                    yield Static("Current: Not set (auto-generation disabled)", classes="settings-info")
                yield Static("")

                yield Static("Enter new DeepSeek API key (leave blank to keep current):", classes="settings-label")
                yield Input(
                    placeholder="sk-...",
                    password=True,
                    id="deepseek-api-key-input"
                )
                yield Static("")

                yield Static("💡 Get DeepSeek key from: https://platform.deepseek.com/api_keys",
                           classes="settings-hint")
                yield Static("   Used for: Entity card generation, Story arc generation", classes="settings-info")
                yield Static("")

                yield Static("## Proxy Settings", classes="settings-section-title")
                yield Static("")

                yield Static("Proxy Mode (prepend custom instructions to all prompts):", classes="settings-label")
                yield Switch(value=use_proxy, id="proxy-switch")
                yield Static("")

                yield Static("📝 When enabled, adds instructions from proxy_prompt.txt", classes="settings-info")
                yield Static("   Edit proxy_prompt.txt to customize the injected prompt", classes="settings-info")
                yield Static("")

                with Horizontal(classes="button-row"):
                    yield Button("Save", variant="primary", id="save-button")
                    yield Button("Cancel", variant="default", id="cancel-button")
                    yield Button("Edit Proxy", variant="default", id="edit-proxy-button")

            yield Static("[ESC to close]", id="settings-footer")

    def load_config(self) -> dict:
        """Load configuration from global config file"""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text(encoding='utf-8'))
            except Exception:
                return {}
        return {}

    def save_config(self, config: dict) -> bool:
        """Save configuration to global config file"""
        try:
            self.config_file.write_text(
                json.dumps(config, indent=2),
                encoding='utf-8'
            )
            return True
        except Exception as e:
            self.app.notify(f"Error saving config: {e}", severity="error")
            return False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "cancel-button":
            self.dismiss()
        elif event.button.id == "save-button":
            self.save_settings()
        elif event.button.id == "edit-proxy-button":
            self.edit_proxy_file()

    def edit_proxy_file(self) -> None:
        """Open proxy prompt file in default editor"""
        proxy_file = self.config_file.parent / "proxy_prompt.txt"

        # Create default proxy file if it doesn't exist
        if not proxy_file.exists():
            default_content = """# Proxy Prompt - Injected Before All Messages

This prompt will be prepended to every message sent through the RP launcher when Proxy Mode is enabled.

Use this for:
- System-level instructions that apply to all responses
- Role-play style guidance
- Custom formatting rules
- Behavior modifications

Example:
---
You are an expert storyteller with a focus on vivid descriptions and emotional depth.
Always maintain character consistency and advance the plot naturally.
---

Replace this with your own instructions:
"""
            try:
                proxy_file.write_text(default_content, encoding='utf-8')
            except Exception as e:
                self.app.notify(f"Error creating proxy file: {e}", severity="error")
                return

        # Open in default editor
        import subprocess
        import sys

        try:
            if sys.platform == "win32":
                subprocess.Popen(["notepad.exe", str(proxy_file)])
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(proxy_file)])

            self.app.notify(
                "Proxy file opened in editor. Save and close to apply changes.",
                severity="information",
                timeout=5
            )
        except Exception as e:
            self.app.notify(f"Error opening proxy file: {e}", severity="error")

    def save_settings(self) -> None:
        """Save settings and close"""
        # Get widgets
        api_mode_switch = self.query_one("#api-mode-switch", Switch)
        claude_key_input = self.query_one("#claude-api-key-input", Input)
        deepseek_key_input = self.query_one("#deepseek-api-key-input", Input)
        proxy_switch = self.query_one("#proxy-switch", Switch)

        # Load existing config
        config = self.load_config()

        # Update API mode
        config["use_api_mode"] = api_mode_switch.value

        # Update proxy mode
        config["use_proxy"] = proxy_switch.value

        # Update Claude API key if provided
        new_claude_key = claude_key_input.value.strip()
        if new_claude_key:
            # Validate Anthropic key format
            if not new_claude_key.startswith("sk-ant-"):
                self.app.notify(
                    "Invalid Anthropic API key! Must start with 'sk-ant-'",
                    severity="error",
                    timeout=10
                )
                return
            config["anthropic_api_key"] = new_claude_key

        # Update DeepSeek API key if provided
        new_deepseek_key = deepseek_key_input.value.strip()
        if new_deepseek_key:
            # Basic validation - DeepSeek keys typically start with 'sk-'
            if not new_deepseek_key.startswith("sk-"):
                self.app.notify(
                    "Warning: DeepSeek API key should start with 'sk-'",
                    severity="warning",
                    timeout=5
                )
            config["deepseek_api_key"] = new_deepseek_key

        # Preserve other settings
        if "auto_entity_cards" not in config:
            config["auto_entity_cards"] = True
        if "entity_mention_threshold" not in config:
            config["entity_mention_threshold"] = 2
        if "auto_story_arc" not in config:
            config["auto_story_arc"] = True
        if "arc_frequency" not in config:
            config["arc_frequency"] = 50

        # Save config
        if self.save_config(config):
            # Show success message
            mode_status = "enabled" if config["use_api_mode"] else "disabled"

            updates = []
            if new_claude_key:
                updates.append("Claude key updated")
            if new_deepseek_key:
                updates.append("DeepSeek key updated")
            if not updates:
                updates.append("settings saved")

            proxy_status = "enabled" if config["use_proxy"] else "disabled"
            self.app.notify(
                f"✅ {', '.join(updates)}! API: {mode_status}, Proxy: {proxy_status}",
                severity="information",
                timeout=5
            )

            # Show restart message if API mode changed
            if config["use_api_mode"]:
                self.app.notify(
                    "⚠️  Restart the bridge for changes to take effect",
                    severity="warning",
                    timeout=10
                )

        self.dismiss()


# =============================================================================
# CONTEXT PANEL
# =============================================================================

class ContextPanel(Static):
    """Left panel showing context, progress, and quick access menu"""

    def __init__(self, rp_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self.rp_dir = rp_dir

    def on_mount(self) -> None:
        """Set up auto-refresh"""
        self.set_interval(2.0, self.refresh_context)
        self.refresh_context()

    def refresh_context(self) -> None:
        """Update context display"""
        state_file = self.rp_dir / "state" / "current_state.md"
        counter_file = self.rp_dir / "state" / "response_counter.txt"

        chapter, timestamp, location = get_chapter_info(state_file)
        active_chars = get_active_characters(self.rp_dir)
        progress, next_arc, percentage = get_arc_progress(counter_file)
        count = get_response_count(counter_file)

        # Build progress bar
        bar_length = 20
        filled = int((percentage / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        content = f"""[bold cyan]📍 CONTEXT[/]
─────────────
Chapter: {chapter}
Time: {timestamp}
Location: {location}
Active: {', '.join(active_chars)}

[bold green]📊 PROGRESS[/]
─────────────
{count}/250 responses
Arc: {bar} {int(percentage)}%
Next: {next_arc} responses

[bold magenta]📖 QUICK ACCESS[/]
─────────────
Ctrl+↵   Send
Enter    New Line
F1       Help
⬇️       Footer buttons
         for overlays
"""

        self.update(content)


# =============================================================================
# CUSTOM TEXT AREA WITH CTRL+ENTER SUPPORT
# =============================================================================

class RPTextArea(TextArea):
    """Custom TextArea with Ctrl+Enter to send messages

    - Ctrl+Enter: Send message
    - Enter: New line (works naturally)
    """

    class Submitted(Message, bubble=True):
        """Message posted when Ctrl+Enter is pressed"""
        def __init__(self, text_area: "RPTextArea") -> None:
            super().__init__()
            self.text_area = text_area


# =============================================================================
# CHAT DISPLAY
# =============================================================================

class ChatDisplay(ScrollableContainer):
    """Center panel showing RP conversation history"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []

    def add_message(self, sender: str, content: str):
        """Add a message to chat history"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if sender == "You":
            message = f"[dim]{timestamp}[/] [bold cyan]👤 You:[/]\n{content}\n"
        else:
            message = f"[dim]{timestamp}[/] [bold green]🤖 Claude:[/]\n{content}\n"

        self.messages.append(message)

        # Create new static with all messages
        self.mount(Static(f"\n{'─' * 60}\n".join(self.messages)))

        # Auto-scroll to bottom
        self.scroll_end(animate=False)


# =============================================================================
# MAIN APP
# =============================================================================

class RPClientApp(App):
    """Main RP Client TUI Application"""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        layout: horizontal;
        height: 1fr;
    }

    #context-panel {
        width: 30;
        background: $panel;
        padding: 1;
        border-right: solid $primary;
    }

    #chat-panel {
        width: 1fr;
        padding: 1;
    }

    #input-container {
        height: 10;
        background: $panel;
        padding: 1;
        border-top: solid $primary;
    }

    #input-area {
        height: 1fr;
        background: $surface;
    }

    #overlay-container {
        width: 80%;
        height: 80%;
        background: $panel;
        border: thick $primary;
        padding: 1;
    }

    #overlay-title {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 1;
    }

    #overlay-content {
        height: 1fr;
        margin-top: 1;
    }

    #overlay-footer {
        text-style: dim;
        text-align: center;
        padding-top: 1;
    }

    #status-message {
        text-align: center;
        color: $warning;
        text-style: bold;
    }

    #settings-container {
        width: 70%;
        height: 80%;
        background: $panel;
        border: thick $primary;
        padding: 1;
    }

    #settings-title {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 1;
    }

    #settings-content {
        height: 1fr;
        margin-top: 1;
    }

    #settings-footer {
        text-style: dim;
        text-align: center;
        padding-top: 1;
    }

    .settings-section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .settings-label {
        color: $text;
        margin-top: 1;
    }

    .settings-info {
        color: $text-muted;
        text-style: dim;
    }

    .settings-hint {
        color: $accent;
        text-style: dim;
        margin-top: 1;
    }

    .button-row {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+j", "submit_message", "Send"),  # Ctrl+Enter sends as Ctrl+J
        # Overlay actions - F-keys for overlays
        Binding("f1", "show_help", "Help"),
        Binding("f2", "show_memory", "Memory"),
        Binding("f3", "show_arc", "Arc"),
        Binding("f4", "show_characters", "Characters"),
        Binding("f5", "show_notes", "Notes"),
        Binding("f6", "show_entities", "Entities"),
        Binding("f7", "show_genome", "Genome"),
        Binding("f8", "show_status", "Status"),
        Binding("f9", "show_settings", "Settings"),
    ]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir
        self.input_file = rp_dir / "state" / "rp_client_input.txt"
        self.response_file = rp_dir / "state" / "rp_client_response.txt"
        self.ready_flag = rp_dir / "state" / "rp_client_ready.flag"
        self.done_flag = rp_dir / "state" / "rp_client_done.flag"
        self.waiting_for_response = False

    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            yield ContextPanel(self.rp_dir, id="context-panel")
            yield ChatDisplay(id="chat-panel")

        with Container(id="input-container"):
            yield Label("✍️ Your Response:", id="input-label")
            yield RPTextArea(id="input-area")
            yield Static("", id="status-message")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize app"""
        self.query_one(ChatDisplay).add_message(
            "System",
            "RP Client TUI started. Type your message and press Ctrl+Enter to send (Enter for new line)."
        )

        # Watch for response file
        self.set_interval(0.5, self.check_for_response)

    def action_submit_message(self) -> None:
        """Handle Ctrl+J (Ctrl+Enter) - check if TextArea is focused first"""
        # Only send if the input area is focused
        input_area = self.query_one("#input-area", RPTextArea)
        if self.focused == input_area:
            self.action_send_message()

    def action_send_message(self) -> None:
        """Send message to Claude Code (triggered by Ctrl+Enter in TextArea)"""
        input_area = self.query_one("#input-area", RPTextArea)
        message = input_area.text.strip()

        if not message:
            return

        if self.waiting_for_response:
            self.show_status("⏳ Already waiting for response...")
            return

        # Add to chat display
        self.query_one(ChatDisplay).add_message("You", message)

        # Write to file
        self.input_file.write_text(message, encoding='utf-8')
        self.ready_flag.touch()

        # Clear input
        input_area.clear()

        # Set waiting state
        self.waiting_for_response = True
        self.show_status("⏳ Waiting for Claude...")

    def check_for_response(self) -> None:
        """Check if Claude has responded"""
        if not self.waiting_for_response:
            return

        if self.done_flag.exists():
            # Read response
            response = read_file(self.response_file)

            # Add to chat
            if response:
                self.query_one(ChatDisplay).add_message("Claude", response)

            # Clean up
            self.done_flag.unlink(missing_ok=True)
            self.ready_flag.unlink(missing_ok=True)
            self.response_file.unlink(missing_ok=True)
            self.input_file.unlink(missing_ok=True)

            self.waiting_for_response = False
            self.show_status("✅ Response received")

            # Clear status after 2 seconds
            self.set_timer(2.0, lambda: self.show_status(""))

    def show_status(self, message: str) -> None:
        """Show status message"""
        self.query_one("#status-message", Static).update(message)

    def _dismiss_current_overlay(self) -> None:
        """Dismiss any currently open overlay before showing new one"""
        # Check if there's a modal screen and dismiss it
        if len(self.screen_stack) > 1:
            self.pop_screen()

    # Overlay actions
    def action_show_memory(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(MemoryOverlay(self.rp_dir))

    def action_show_arc(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(ArcOverlay(self.rp_dir))

    def action_show_characters(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(CharactersOverlay(self.rp_dir))

    def action_show_notes(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(SceneNotesOverlay(self.rp_dir))

    def action_show_entities(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(EntitiesOverlay(self.rp_dir))

    def action_show_genome(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(GenomeOverlay(self.rp_dir))

    def action_show_status(self) -> None:
        self._dismiss_current_overlay()
        self.push_screen(StatusOverlay(self.rp_dir))

    def action_show_settings(self) -> None:
        """Show settings screen"""
        self._dismiss_current_overlay()
        self.push_screen(SettingsScreen(self.rp_dir))

    def action_show_help(self) -> None:
        """Show help overlay"""
        help_text = """# Keyboard Shortcuts

## Main Controls
- **Ctrl+Enter** - Send message to Claude Code
- **Enter** - New line in message (works naturally)
- **Ctrl+Q** - Quit application
- **F1** - Show this help

## Quick Access Overlays
Use the **F-keys** to open overlays:
- **F1** - Help, **F2** - Memory, **F3** - Arc, **F4** - Characters
- **F5** - Notes, **F6** - Entities, **F7** - Genome, **F8** - Status
- **F9** - Settings (API configuration)

## In Overlays
- **ESC** - Close overlay
- **↑/↓ or PgUp/PgDn** - Scroll

## Text Input
All normal keys work - just type!
Multi-line messages work naturally - just press Enter for new lines.
Press Ctrl+Enter when you're ready to send!
"""

        class HelpOverlay(ModalScreen):
            BINDINGS = [("escape", "dismiss", "Close")]

            def compose(self) -> ComposeResult:
                with Container(id="overlay-container"):
                    yield Static("❓ Help", id="overlay-title")
                    yield ScrollableContainer(
                        Static(Markdown(help_text)),
                        id="overlay-content"
                    )
                    yield Static("[ESC to close]", id="overlay-footer")

        self._dismiss_current_overlay()
        self.push_screen(HelpOverlay())


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python rp_client_tui.py <RP_FOLDER_NAME>")
        print("Example: python rp_client_tui.py \"Example RP\"")
        sys.exit(1)

    # Get RP directory
    base_dir = Path(__file__).parent
    rp_folder = sys.argv[1]
    rp_dir = base_dir / rp_folder

    if not rp_dir.exists():
        print(f"Error: RP folder not found: {rp_dir}")
        sys.exit(1)

    if not (rp_dir / "state").exists():
        print(f"Error: Not a valid RP folder (no state/ directory): {rp_dir}")
        sys.exit(1)

    # Run the app
    app = RPClientApp(rp_dir)
    app.run()


if __name__ == "__main__":
    main()
