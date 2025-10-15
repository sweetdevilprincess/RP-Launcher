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

# Import write queue for efficient file operations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fs_write_queue import get_write_queue
from src.automation.core import get_response_count as core_get_response_count
from src.file_manager import FileManager


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
    """Get active characters from session_triggers.json (or .txt with auto-migration)"""
    try:
        fm = FileManager(rp_dir)
        characters = fm.read_session_triggers()
        return characters if characters else ["None"]
    except Exception:
        # Fallback to old parsing if FileManager fails
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
    """Get current response count (wrapper for core function)"""
    return core_get_response_count(counter_file)


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
    """Overlay for viewing entities from entities/ directory"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        # Use EntityManager to get all indexed entities
        try:
            from src.entity_manager import EntityManager
            entity_mgr = EntityManager(self.rp_dir)

            content = "# 🎭 Entities\n\n"

            if not entity_mgr.entities:
                content += "*No entity cards found in entities/ directory.*\n"
                content += "*Create entity cards with [CHAR], [LOC], or [ORG] tags.*"
            else:
                # Group by type
                by_type = entity_mgr.entities_by_type

                for entity_type in ['character', 'location', 'organization', 'unknown']:
                    entities_of_type = by_type.get(entity_type, [])
                    if entities_of_type:
                        type_emoji = {
                            'character': '👤',
                            'location': '📍',
                            'organization': '🏢',
                            'unknown': '❓'
                        }.get(entity_type, '📄')

                        content += f"\n## {type_emoji} {entity_type.title()}s ({len(entities_of_type)})\n\n"

                        for name in sorted(entities_of_type):
                            entity = entity_mgr.entities[name]
                            triggers = len(entity.triggers)
                            content += f"- **{name}** ({triggers} triggers)\n"

                content += f"\n**Total**: {len(entity_mgr.entities)} entities, {len(entity_mgr.trigger_map)} trigger words"

        except Exception as e:
            content = f"# 🎭 Entities\n\n*Error loading entities: {e}*"

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
        counter_file = self.rp_dir / "state" / "response_counter.json"
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
        self.config_file = rp_dir.parent / "config" / "config.json"  # Global config

    def compose(self) -> ComposeResult:
        # Load existing config
        config = self.load_config()
        claude_api_key = config.get("anthropic_api_key", "")
        deepseek_api_key = config.get("deepseek_api_key", "")
        openrouter_model = config.get("openrouter_model", "deepseek/deepseek-chat-v3.1")
        use_api_mode = config.get("use_api_mode", False)
        use_proxy = config.get("use_proxy", False)
        thinking_mode = config.get("thinking_mode", "megathink")

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

                yield Static("## Thinking Mode Configuration", classes="settings-section-title")
                yield Static("ℹ️  Changes take effect on next bridge restart", classes="settings-info")
                yield Static("")

                yield Static("Thinking Mode (controls Claude's reasoning budget):", classes="settings-label")
                yield Static(f"Current: {thinking_mode}", classes="settings-info")
                yield Static("")

                yield Static("Enter thinking mode (leave blank to keep current):", classes="settings-label")
                yield Input(
                    placeholder="disabled, think, think hard, megathink, think harder, ultrathink",
                    id="thinking-mode-input"
                )
                yield Static("")

                yield Static("💡 Thinking modes:", classes="settings-hint")
                yield Static("   • disabled (0 tokens) - Fastest, minimal reasoning", classes="settings-info")
                yield Static("   • think (5k tokens) - Quick planning, simple tasks (5-10s)", classes="settings-info")
                yield Static("   • think hard (10k tokens) - Feature design, debugging (10-20s)", classes="settings-info")
                yield Static("   • megathink (10k tokens) - Balanced, same as 'think hard' (DEFAULT)", classes="settings-info")
                yield Static("   • think harder (25k tokens) - Complex bugs, architecture (30-60s)", classes="settings-info")
                yield Static("   • ultrathink (32k tokens) - System design, major refactoring (1-3min)", classes="settings-info")
                yield Static("   See docs/THINKING_MODES.md for details", classes="settings-info")
                yield Static("")

                yield Static("## OpenRouter API Configuration", classes="settings-section-title")
                yield Static("ℹ️  Changes take effect immediately (no restart needed)", classes="settings-info")
                yield Static("")

                yield Static("OpenRouter API Key (provides access to DeepSeek for auto-generation):", classes="settings-label")
                if deepseek_api_key:
                    yield Static(f"Current: {masked_deepseek_key}", classes="settings-info")
                else:
                    yield Static("Current: Not set (auto-generation disabled)", classes="settings-info")
                yield Static("")

                yield Static("Enter new OpenRouter API key (leave blank to keep current):", classes="settings-label")
                yield Input(
                    placeholder="sk-or-v1-...",
                    password=True,
                    id="deepseek-api-key-input"
                )
                yield Static("")

                yield Static("💡 Get OpenRouter key from: https://openrouter.ai/keys",
                           classes="settings-hint")
                yield Static("   ⚠️  Must start with 'sk-or-v1-' (OpenRouter format)", classes="settings-hint")
                yield Static("   Used for: Entity card generation, Story arc generation", classes="settings-info")
                yield Static("")

                yield Static("OpenRouter Model:", classes="settings-label")
                yield Static(f"Current: {openrouter_model}", classes="settings-info")
                yield Static("")

                yield Static("Enter model name (leave blank to keep current):", classes="settings-label")
                yield Input(
                    placeholder="deepseek/deepseek-chat-v3.1",
                    id="openrouter-model-input"
                )
                yield Static("")

                yield Static("💡 Browse models at: https://openrouter.ai/models",
                           classes="settings-hint")
                yield Static("   Examples: deepseek/deepseek-chat-v3-0324, anthropic/claude-3.5-sonnet", classes="settings-info")
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
            # Use write queue for efficient config saves
            write_queue = get_write_queue()
            write_queue.write_json(self.config_file, config, indent=2)
            # Flush immediately for settings to ensure they're saved
            write_queue.flush()
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
        thinking_mode_input = self.query_one("#thinking-mode-input", Input)
        deepseek_key_input = self.query_one("#deepseek-api-key-input", Input)
        model_input = self.query_one("#openrouter-model-input", Input)
        proxy_switch = self.query_one("#proxy-switch", Switch)

        # Load existing config
        config = self.load_config()

        # Track if API mode changed (this requires restart)
        old_api_mode = config.get("use_api_mode", False)
        new_api_mode = api_mode_switch.value
        api_mode_changed = old_api_mode != new_api_mode

        # Update API mode
        config["use_api_mode"] = new_api_mode

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

        # Update thinking mode if provided
        new_thinking_mode = thinking_mode_input.value.strip().lower()
        if new_thinking_mode:
            # Validate thinking mode (ordered from lowest to highest budget)
            valid_modes = ["disabled", "think", "think hard", "megathink", "think harder", "ultrathink"]
            if new_thinking_mode not in valid_modes:
                self.app.notify(
                    f"Invalid thinking mode! Must be one of: {', '.join(valid_modes)}",
                    severity="error",
                    timeout=10
                )
                return
            config["thinking_mode"] = new_thinking_mode

        # Update OpenRouter API key if provided
        new_deepseek_key = deepseek_key_input.value.strip()
        if new_deepseek_key:
            # Basic validation - OpenRouter keys start with 'sk-or-v1-'
            if not new_deepseek_key.startswith("sk-or-v1-"):
                self.app.notify(
                    "Warning: OpenRouter API key should start with 'sk-or-v1-'",
                    severity="warning",
                    timeout=5
                )
            config["deepseek_api_key"] = new_deepseek_key

        # Update OpenRouter model if provided
        new_model = model_input.value.strip()
        if new_model:
            config["openrouter_model"] = new_model
        elif "openrouter_model" not in config:
            # Set default if not present
            config["openrouter_model"] = "deepseek/deepseek-chat-v3.1"

        # Preserve other settings
        if "auto_entity_cards" not in config:
            config["auto_entity_cards"] = True
        if "entity_mention_threshold" not in config:
            config["entity_mention_threshold"] = 2
        if "auto_story_arc" not in config:
            config["auto_story_arc"] = True
        if "arc_frequency" not in config:
            config["arc_frequency"] = 50
        if "thinking_mode" not in config:
            config["thinking_mode"] = "megathink"

        # Save config
        if self.save_config(config):
            # Show success message
            mode_status = "enabled" if config["use_api_mode"] else "disabled"

            updates = []
            if new_claude_key:
                updates.append("Claude key updated")
            if new_thinking_mode:
                updates.append(f"Thinking mode set to {new_thinking_mode}")
            if new_deepseek_key:
                updates.append("OpenRouter key updated")
            if new_model:
                updates.append(f"Model set to {new_model}")
            if not updates:
                updates.append("settings saved")

            proxy_status = "enabled" if config["use_proxy"] else "disabled"
            self.app.notify(
                f"✅ {', '.join(updates)}! API: {mode_status}, Proxy: {proxy_status}",
                severity="information",
                timeout=5
            )

            # Show restart message if API mode or thinking mode changed
            needs_restart = api_mode_changed or new_thinking_mode
            if needs_restart:
                changes = []
                if api_mode_changed:
                    changes.append("API mode")
                if new_thinking_mode:
                    changes.append("thinking mode")

                self.app.notify(
                    f"⚠️  {', '.join(changes)} changed - press F10 to restart bridge",
                    severity="warning",
                    timeout=10
                )

            # Notify that OpenRouter settings take effect immediately
            if new_deepseek_key or new_model:
                self.app.notify(
                    "ℹ️  OpenRouter settings active immediately (no restart needed)",
                    severity="information",
                    timeout=5
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
        counter_file = self.rp_dir / "state" / "response_counter.json"

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
F1-F9    Overlays
F10      Restart Bridge
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
        Binding("f10", "restart_bridge", "Restart Bridge"),
    ]

    def __init__(self, rp_dir: Path, bridge_restart_callback=None):
        super().__init__()
        self.rp_dir = rp_dir
        self.state_dir = rp_dir / "state"
        self.input_file = self.state_dir / "rp_client_input.json"
        self.response_file = self.state_dir / "rp_client_response.json"
        self.ready_flag = self.state_dir / "rp_client_ready.flag"
        self.done_flag = self.state_dir / "rp_client_done.flag"
        self.tui_active_flag = self.state_dir / "tui_active.flag"
        self.waiting_for_response = False
        self.file_manager = FileManager(rp_dir)
        self.bridge_restart_callback = bridge_restart_callback

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
        # Create TUI active flag (signals bridge that TUI is running)
        try:
            self.tui_active_flag.touch()
        except Exception as e:
            print(f"Warning: Could not create TUI active flag: {e}")

        self.query_one(ChatDisplay).add_message(
            "System",
            "RP Client TUI started. Type your message and press Ctrl+Enter to send (Enter for new line)."
        )

        # Watch for response file
        self.set_interval(0.5, self.check_for_response)

    def on_unmount(self) -> None:
        """Cleanup when app is shutting down"""
        # Remove TUI active flag (signals bridge to shut down)
        try:
            self.tui_active_flag.unlink(missing_ok=True)
        except Exception as e:
            print(f"Warning: Could not remove TUI active flag: {e}")

    def action_quit(self) -> None:
        """Override quit to ensure cleanup"""
        # Cleanup flags before quitting
        try:
            self.tui_active_flag.unlink(missing_ok=True)
            self.ready_flag.unlink(missing_ok=True)
            self.done_flag.unlink(missing_ok=True)
        except Exception:
            pass
        # Call parent quit
        super().action_quit()

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

        # Write to file (JSON format)
        try:
            self.file_manager.write_ipc_input(message, self.state_dir)
            self.ready_flag.touch()
        except Exception as e:
            self.show_status(f"❌ Error writing input: {e}")
            return

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
            # Read response (JSON format with fallback to .txt)
            try:
                response = self.file_manager.read_ipc_response(self.state_dir)
            except Exception as e:
                response = f"Error reading response: {e}"

            # Add to chat
            if response:
                self.query_one(ChatDisplay).add_message("Claude", response)

            # Clean up (handle both .json and .txt files)
            self.done_flag.unlink(missing_ok=True)
            self.ready_flag.unlink(missing_ok=True)
            self.response_file.unlink(missing_ok=True)
            (self.state_dir / "rp_client_response.txt").unlink(missing_ok=True)  # Old format
            self.input_file.unlink(missing_ok=True)
            (self.state_dir / "rp_client_input.txt").unlink(missing_ok=True)  # Old format

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

    def action_restart_bridge(self) -> None:
        """Restart the bridge process"""
        if self.bridge_restart_callback:
            self.notify("🔄 Restarting bridge...", severity="information", timeout=3)
            try:
                self.bridge_restart_callback()
                self.notify("✅ Bridge restarted successfully!", severity="information", timeout=5)
            except Exception as e:
                self.notify(f"❌ Failed to restart bridge: {e}", severity="error", timeout=10)
        else:
            self.notify("⚠️ Bridge restart not available", severity="warning", timeout=5)

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
- **F10** - Restart Bridge (use after changing settings)

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
