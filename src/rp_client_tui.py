#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RP Client TUI - Enhanced Terminal Interface for Claude Code RP System

Features:
- Better text input (multi-line, no glitches)
- Quick reference overlays (Ctrl+M for memory, Ctrl+A for arc, etc.)
- Real-time context display (chapter, time, location, progress)
- File-based Claude Code integration (zero cost)
"""

import sys
import io

# Ensure UTF-8 encoding for all output (MUST be first)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
    Footer,
    Static,
    TextArea,
    Button,
    Input,
    Switch,
    Tabs,
    Tab,
    ContentSwitcher,
)
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.message import Message
from textwrap import dedent

from rich import box
from rich.align import Align
from rich.console import Group, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.padding import Padding
from rich.style import Style
from rich.table import Table
from rich.text import Text

# Setup path for local imports
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

for candidate in (SCRIPT_DIR, PARENT_DIR):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from fs_write_queue import get_write_queue
from automation.core import get_response_count as core_get_response_count
from file_manager import FileManager

PALETTE = {
    "primary": "#723d46",        # Wine - headers, overlays
    "surface": "#eaeada",         # Sage 800 - main light background
    "panel": "#dfe0c8",          # Sage 700 - sidebar panels
    "boost": "#ffedcb",          # Peach Yellow 700 - elevated areas
    "accent": "#e26d5c",         # Bittersweet - highlights, buttons
    "text": "#472d30",           # Van Dyke - primary text
    "text_muted": "#723d46",     # Wine - secondary text
    "border": "#723d46",         # Wine - borders and dividers
    "warning": "#e26d5c",        # Bittersweet - warnings
}

# Semantic style mappings - reference PALETTE colors by component use
STYLES = {
    # Chat message colors
    "message_you_text": PALETTE['accent'],
    "message_you_bg": PALETTE['panel'],
    "message_system_text": PALETTE['accent'],
    "message_system_bg": PALETTE['boost'],
    "message_dm_text": PALETTE['accent'],
    "message_dm_bg": PALETTE['surface'],

    # Context panel card borders
    "card_chapter": PALETTE['primary'],
    "card_time": PALETTE['accent'],
    "card_location": PALETTE['primary'],
    "card_characters": PALETTE['accent'],
    "card_momentum": PALETTE['border'],

    # Progress bar stages
    "progress_low": PALETTE['primary'],
    "progress_mid": PALETTE['accent'],
    "progress_high": PALETTE['text_muted'],

    # Context panel card background
    "card_bg": PALETTE['boost'],

    # Status message colors (using existing palette)
    "status_error": PALETTE['warning'],
    "status_success": PALETTE['accent'],
    "status_waiting": PALETTE['text_muted'],
    "status_info": PALETTE['text'],

    # Text styling colors
    "text_dim": PALETTE['text_muted'],
    "text_emphasis": PALETTE['accent'],

    # Button text colors
    "button_text_default": PALETTE['surface'],
    "button_text_primary": PALETTE['surface'],
}


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
        if line.startswith('**Current Chapter'):
            chapter = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
        elif line.startswith('**Current Timestamp'):
            timestamp = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
        elif line.startswith('**Current Location'):
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

class BaseOverlay(ModalScreen):
    """Base class for overlay screens - reduces code duplication"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def _create_overlay(self, title: str, content: str, footer: str = "[ESC to close]") -> ComposeResult:
        """Helper to create standard overlay layout"""
        with Container(id="overlay-container"):
            yield Static(title, id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static(footer, id="overlay-footer")


class CharacterSheetOverlay(BaseOverlay):
    """Overlay for viewing {{user}} character sheet (F2) - combines Memory + character info"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        # Build combined character sheet
        content = "# {{user}} Character Sheet\n\n"

        # Section 1: Memory
        memory_file = self.rp_dir / "state" / "user_memory.md"
        memory_content = read_file(memory_file)

        if memory_content:
            content += "## 📖 Memory\n\n"
            # Strip the header if the memory file has one
            if memory_content.startswith("# "):
                memory_content = "\n".join(memory_content.split("\n")[1:])
            content += memory_content + "\n\n"
        else:
            content += "## 📖 Memory\n\n*Memory file not found. Use `/memory` command to create.*\n\n"

        # Section 2: Character Info (if exists)
        character_file = self.rp_dir / "entities" / "user.md"
        if not character_file.exists():
            character_file = self.rp_dir / "characters" / "user.md"

        if character_file.exists():
            char_content = read_file(character_file)
            content += "---\n\n## 👤 Character Info\n\n" + char_content + "\n\n"

        # Section 3: Relationship Summary (if relationship system enabled)
        relationship_tracker = self.rp_dir / "state" / "relationship_tracker.json"
        if relationship_tracker.exists():
            relationships = read_json(relationship_tracker)
            if relationships.get("relationships"):
                content += "---\n\n## 💕 Relationships\n\n"
                for char_name, rel_data in relationships["relationships"].items():
                    score = rel_data.get("score", 0)
                    tier = rel_data.get("tier", "Stranger")
                    content += f"- **{char_name}**: {tier} ({score}/100)\n"

        with Container(id="overlay-container"):
            yield Static("👤 Character Sheet", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class StoryOverviewOverlay(ModalScreen):
    """Overlay for viewing story overview (F3) - combines Arc + Genome with tabs"""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("1", "show_arc", "Arc"),
        ("2", "show_genome", "Genome")
    ]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir
        self.current_tab = "arc"  # Default to arc tab

    def compose(self) -> ComposeResult:
        with Container(id="overlay-container"):
            yield Static("📖 Story Overview", id="overlay-title")
            yield Static("[1] Arc  [2] Genome", id="tab-selector")
            yield ScrollableContainer(
                Static("", id="story-content"),
                id="overlay-content"
            )
            yield Static("[ESC to close | 1/2 to switch tabs]", id="overlay-footer")

    def on_mount(self) -> None:
        """Load initial content"""
        self.show_arc_content()

    def action_show_arc(self) -> None:
        """Switch to Arc tab"""
        self.current_tab = "arc"
        self.show_arc_content()

    def action_show_genome(self) -> None:
        """Switch to Genome tab"""
        self.current_tab = "genome"
        self.show_genome_content()

    def show_arc_content(self) -> None:
        """Load and display story arc"""
        arc_file = self.rp_dir / "state" / "story_arc.md"
        content = read_file(arc_file)

        if not content:
            content = "# Story Arc\n\n*Story arc not generated yet. Use `/arc` command to create.*"

        story_widget = self.query_one("#story-content", Static)
        story_widget.update(Markdown(content))

        # Update tab selector to show active tab
        tab_selector = self.query_one("#tab-selector", Static)
        tab_selector.update(f"[bold {PALETTE['accent']}][1] Arc[/]  [{STYLES['text_dim']}][2] Genome[/]")

    def show_genome_content(self) -> None:
        """Load and display story genome"""
        genome_file = self.rp_dir / "STORY_GENOME.md"
        content = read_file(genome_file)

        if not content:
            content = "# Story Genome\n\n*Story genome not found.*"

        story_widget = self.query_one("#story-content", Static)
        story_widget.update(Markdown(content))

        # Update tab selector to show active tab
        tab_selector = self.query_one("#tab-selector", Static)
        tab_selector.update(f"[{STYLES['text_dim']}][1] Arc[/]  [bold {PALETTE['accent']}][2] Genome[/]")


class CharactersOverlay(BaseOverlay):
    """Overlay for viewing characters (Ctrl+C)"""

    def compose(self) -> ComposeResult:
        chars_dir = self.rp_dir / "characters"

        # Get active characters
        active = get_active_characters(self.rp_dir)

        # Get all character files
        char_files = sorted(chars_dir.glob("*.md")) if chars_dir.exists() else []

        content = "# 🎭 Characters\n\n"
        content += "## Active This Scene\n"
        if active:
            for char in active:
                content += f"- **{char}**\n"
        else:
            content += "*No active characters*\n"

        content += "\n## All Characters\n"
        if char_files:
            for char_file in char_files:
                name = char_file.stem
                content += f"- {name}\n"
        else:
            content += "*No character files found*\n"

        content += "\n*Tip: Select a character file from the file explorer to view full sheet*"

        yield from self._create_overlay("🎭 Characters", content)


class SceneNotesOverlay(BaseOverlay):
    """Overlay for viewing scene notes (Ctrl+N)"""

    def compose(self) -> ComposeResult:
        notes_file = self.rp_dir / "SCENE_NOTES.md"
        content = read_file(notes_file)

        if not content:
            content = "# Scene Notes\n\n*No scene notes found. Edit SCENE_NOTES.md to add session guidance.*"

        yield from self._create_overlay("📝 Scene Notes", content)


class EntitiesOverlay(BaseOverlay):
    """Overlay for viewing entities from entities/ directory"""

    def compose(self) -> ComposeResult:
        # Use EntityManager to get all indexed entities
        try:
            from entity_manager import EntityManager
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

        yield from self._create_overlay("🎭 Entities", content)


class StatusOverlay(BaseOverlay):
    """Overlay for system status (Ctrl+T)"""

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

        yield from self._create_overlay("📊 Status", content)


class ModulesTabScreen(ModalScreen):
    """Tab screen for module management - placeholder for now"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir

    def compose(self) -> ComposeResult:
        content = """# 🔧 Module Management

This is a placeholder for the Modules management interface.

## Coming Soon

This tab will contain controls for:
- Enabling/disabling system modules
- Configuring automation settings
- Managing RP features

**For now**, use **F6** to access the Module Toggles overlay.
"""
        with Container(id="overlay-container"):
            yield Static("🔧 Modules", id="overlay-title")
            yield ScrollableContainer(
                Static(Markdown(content)),
                id="overlay-content"
            )
            yield Static("[ESC to close]", id="overlay-footer")


class ModuleTogglesOverlay(ModalScreen):
    """Overlay for toggling optional modules (F6)"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir
        self.config_file = rp_dir / "state" / "automation_config.json"

    def compose(self) -> ComposeResult:
        # Load current config
        config = read_json(self.config_file)

        # Get current values
        rel_config = config.get("relationship_system", {})
        mem_config = config.get("memory_system", {})
        plot_config = config.get("plot_tracking", {})
        kb_config = config.get("knowledge_base", {})
        char_config = config.get("character_consistency", {})

        with Container(id="settings-container"):
            yield Static("🔧 Module Toggles", id="settings-title")

            with ScrollableContainer(id="settings-content"):
                yield Static("## 💕 Relationship Tracking System", classes="settings-section-title")
                yield Static("")

                yield Static("Enable relationship tracking:", classes="settings-label")
                yield Switch(value=rel_config.get("enabled", True), id="rel-enabled-switch")
                yield Static("")

                yield Static("Auto-create preference files for new characters:", classes="settings-label")
                yield Switch(value=rel_config.get("auto_create_preferences", False), id="rel-auto-create-switch")
                yield Static("")

                # Show current status
                if rel_config.get("enabled", True):
                    tracker_file = self.rp_dir / "state" / "relationship_tracker.json"
                    if tracker_file.exists():
                        tracker = read_json(tracker_file)
                        rel_count = len(tracker.get("relationships", {}))
                        yield Static(f"ℹ️  Currently tracking: {rel_count} relationship(s)", classes="settings-info")
                    yield Static(f"ℹ️  Tier threshold: {rel_config.get('tier_threshold', 15)} points", classes="settings-info")
                    yield Static("")

                yield Static("## 💭 Memory System", classes="settings-section-title")
                yield Static("")

                yield Static("Enable memory extraction:", classes="settings-label")
                yield Switch(value=mem_config.get("enabled", True), id="mem-enabled-switch")
                yield Static("")

                yield Static("Auto-extract memories from responses:", classes="settings-label")
                yield Switch(value=mem_config.get("auto_extract", True), id="mem-auto-extract-switch")
                yield Static("")

                # Show current status
                if mem_config.get("enabled", True):
                    yield Static(f"ℹ️  Max memories per character: {mem_config.get('max_memories_per_character', 500)}", classes="settings-info")
                    mem_dir = self.rp_dir / "memories"
                    if mem_dir.exists():
                        mem_files = list(mem_dir.glob("*.md"))
                        yield Static(f"ℹ️  Memory files: {len(mem_files)}", classes="settings-info")
                    yield Static("")

                yield Static("## 📊 Plot Thread Tracking", classes="settings-section-title")
                yield Static("")

                yield Static("Enable plot thread tracking:", classes="settings-label")
                yield Switch(value=plot_config.get("enabled", True), id="plot-enabled-switch")
                yield Static("")

                yield Static("Auto-extract plot threads:", classes="settings-label")
                yield Switch(value=plot_config.get("auto_extract_threads", True), id="plot-auto-extract-switch")
                yield Static("")

                yield Static("Enable consequence countdowns:", classes="settings-label")
                yield Switch(value=plot_config.get("enable_consequences", True), id="plot-consequences-switch")
                yield Static("")

                # Show current status
                if plot_config.get("enabled", True):
                    plot_file = self.rp_dir / "state" / "plot_threads.json"
                    if plot_file.exists():
                        plot_data = read_json(plot_file)
                        thread_count = len(plot_data.get("threads", []))
                        yield Static(f"ℹ️  Active plot threads: {thread_count}", classes="settings-info")
                    yield Static("")

                yield Static("## 🔍 Knowledge Base & Contradiction Detection", classes="settings-section-title")
                yield Static("")

                yield Static("Enable knowledge base extraction:", classes="settings-label")
                yield Switch(value=kb_config.get("enabled", True), id="kb-enabled-switch")
                yield Static("")

                yield Static("Auto-extract world-building facts:", classes="settings-label")
                yield Switch(value=kb_config.get("auto_extract", True), id="kb-auto-extract-switch")
                yield Static("")

                # Show current status
                if kb_config.get("enabled", True):
                    kb_file = self.rp_dir / "state" / "knowledge_base.json"
                    if kb_file.exists():
                        kb_data = read_json(kb_file)
                        fact_count = len(kb_data.get("facts", []))
                        yield Static(f"ℹ️  Knowledge base facts: {fact_count}", classes="settings-info")
                    yield Static("")

                yield Static("## 🎭 Character Consistency", classes="settings-section-title")
                yield Static("")

                yield Static("Enable character consistency checks:", classes="settings-label")
                yield Switch(value=char_config.get("enabled", True), id="char-enabled-switch")
                yield Static("")

                yield Static("Always load Personality Cores:", classes="settings-label")
                yield Switch(value=char_config.get("always_load_cores", True), id="char-load-cores-switch")
                yield Static("")

                yield Static("Include consistency checklist:", classes="settings-label")
                yield Switch(value=char_config.get("include_checklist", True), id="char-checklist-switch")
                yield Static("")

                # Show current status
                if char_config.get("enabled", True):
                    # Count personality cores
                    try:
                        from entity_manager import EntityManager
                        entity_mgr = EntityManager(self.rp_dir)
                        entity_mgr.scan_and_index()
                        core_count = sum(1 for e in entity_mgr.entities.values() if e.personality_core)
                        yield Static(f"ℹ️  Characters with Personality Cores: {core_count}", classes="settings-info")
                    except:
                        pass
                    yield Static("")

            with Horizontal(classes="button-row"):
                yield Button("Save", variant="primary", id="save-modules-button")
                yield Button("Cancel", variant="default", id="cancel-modules-button")

            yield Static("[ESC to close]", id="settings-footer")

    def load_config(self) -> dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text(encoding='utf-8'))
            except Exception:
                return {}
        return {}

    def save_config(self, config: dict) -> bool:
        """Save configuration to file"""
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
        if event.button.id == "cancel-modules-button":
            self.dismiss()
        elif event.button.id == "save-modules-button":
            self.save_module_settings()

    def save_module_settings(self) -> None:
        """Save module settings and close"""
        # Get all switches
        rel_enabled = self.query_one("#rel-enabled-switch", Switch).value
        rel_auto_create = self.query_one("#rel-auto-create-switch", Switch).value
        mem_enabled = self.query_one("#mem-enabled-switch", Switch).value
        mem_auto_extract = self.query_one("#mem-auto-extract-switch", Switch).value
        plot_enabled = self.query_one("#plot-enabled-switch", Switch).value
        plot_auto_extract = self.query_one("#plot-auto-extract-switch", Switch).value
        plot_consequences = self.query_one("#plot-consequences-switch", Switch).value
        kb_enabled = self.query_one("#kb-enabled-switch", Switch).value
        kb_auto_extract = self.query_one("#kb-auto-extract-switch", Switch).value
        char_enabled = self.query_one("#char-enabled-switch", Switch).value
        char_load_cores = self.query_one("#char-load-cores-switch", Switch).value
        char_checklist = self.query_one("#char-checklist-switch", Switch).value

        # Load existing config
        config = self.load_config()

        # Update relationship system
        if "relationship_system" not in config:
            config["relationship_system"] = {}
        config["relationship_system"]["enabled"] = rel_enabled
        config["relationship_system"]["auto_create_preferences"] = rel_auto_create

        # Update memory system
        if "memory_system" not in config:
            config["memory_system"] = {}
        config["memory_system"]["enabled"] = mem_enabled
        config["memory_system"]["auto_extract"] = mem_auto_extract

        # Update plot tracking
        if "plot_tracking" not in config:
            config["plot_tracking"] = {}
        config["plot_tracking"]["enabled"] = plot_enabled
        config["plot_tracking"]["auto_extract_threads"] = plot_auto_extract
        config["plot_tracking"]["enable_consequences"] = plot_consequences

        # Update knowledge base
        if "knowledge_base" not in config:
            config["knowledge_base"] = {}
        config["knowledge_base"]["enabled"] = kb_enabled
        config["knowledge_base"]["auto_extract"] = kb_auto_extract

        # Update character consistency
        if "character_consistency" not in config:
            config["character_consistency"] = {}
        config["character_consistency"]["enabled"] = char_enabled
        config["character_consistency"]["always_load_cores"] = char_load_cores
        config["character_consistency"]["include_checklist"] = char_checklist

        # Save config
        if self.save_config(config):
            self.app.notify("✅ Module settings saved!", severity="information", timeout=3)
            self.dismiss()
        else:
            self.app.notify("❌ Failed to save settings", severity="error", timeout=5)


class SettingsScreen(ModalScreen):
    """Settings screen for API configuration"""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, rp_dir: Path):
        super().__init__()
        self.rp_dir = rp_dir
        # Use global config file (same location tui_bridge reads from)
        base_dir = Path(__file__).parent.parent
        self.config_file = base_dir / "config" / "config.json"  # Global config

    def compose(self) -> ComposeResult:
        # Load existing config
        config = self.load_config()
        claude_api_key = config.get("anthropic_api_key", "")
        # Support both new generic names and legacy anthropic-specific names
        proxy_url = config.get("proxy_url", "") or config.get("anthropic_proxy_url", "")
        proxy_token = config.get("proxy_token", "") or config.get("anthropic_proxy_token", "")
        deepseek_api_key = config.get("deepseek_api_key", "")
        openrouter_model = config.get("openrouter_model", "deepseek/deepseek-chat-v3.1")
        primary_llm = config.get("primary_llm", "anthropic_sdk")
        use_api_mode = config.get("use_api_mode", False)
        if primary_llm != "anthropic_sdk":
            use_api_mode = True
        use_proxy = config.get("use_proxy", False)
        thinking_mode = config.get("thinking_mode", "megathink")
        openai_api_key = config.get("openai_api_key", "")
        openai_model = config.get("openai_model", "gpt-4.1")
        openai_api_base = config.get("openai_api_base", "")

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
        masked_openai_key = mask_key(openai_api_key)

        with Container(id="settings-container"):
            yield Static("⚙️ Settings", id="settings-title")

            with ScrollableContainer(id="settings-content"):
                yield Static("## LLM Provider", classes="settings-section-title")
                yield Static("")

                yield Static("Primary LLM Provider (anthropic_sdk, anthropic_api, openai_api):", classes="settings-label")
                yield Input(
                    value=primary_llm,
                    placeholder="anthropic_sdk",
                    id="primary-llm-input"
                )
                yield Static("  ℹ When set to openai_api, the bridge will use OpenAI Responses API.", classes="settings-info")
                yield Static("")

                yield Static("## Claude API Configuration", classes="settings-section-title")
                yield Static("")

                yield Static("API Mode (uses Anthropic API with prompt caching):", classes="settings-label")
                yield Switch(value=use_api_mode, id="api-mode-switch", disabled=primary_llm != "anthropic_sdk")
                if primary_llm != "anthropic_sdk":
                    yield Static("  ℹ API mode is automatically enabled for non-SDK providers.", classes="settings-info")
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

                yield Static("Proxy URL (optional - works for both Anthropic & DeepSeek, e.g. http://localhost:42069):", classes="settings-label")
                yield Input(
                    placeholder="http://localhost:42069",
                    value=proxy_url,
                    id="proxy-url-input"
                )
                yield Static("")

                yield Static("Proxy Access Token (leave blank to keep, type 'clear' to remove):", classes="settings-label")
                if proxy_token:
                    yield Static("Current: **** (hidden)", classes="settings-info")
                else:
                    yield Static("Current: Not set", classes="settings-info")
                yield Static("  • Required when routing through proxy servers", classes="settings-info")
                yield Static("  • Works for both Anthropic API and DeepSeek/OpenRouter", classes="settings-info")
                yield Static("  • Paste the bearer token without the 'Bearer ' prefix", classes="settings-info")
                yield Input(
                    placeholder="your-access-token",
                    password=True,
                    id="proxy-token-input"
                )
                yield Static("")

                yield Button("🧪 Test Proxy Connection", variant="default", id="test-proxy-button")
                yield Static("(Tests connection, authentication, and message routing)", classes="settings-info")
                yield Static("")

                yield Static("Proxy Enabled (routes API calls through proxy):", classes="settings-label")
                yield Switch(value=use_proxy, id="proxy-enabled-switch")
                yield Static("")

                yield Static("💡 Get Claude key from: https://console.anthropic.com/settings/keys",
                           classes="settings-hint")
                yield Static("   ⚠️  Must start with 'sk-ant-'", classes="settings-hint")
                yield Static("")

                yield Static("## OpenAI API Configuration", classes="settings-section-title")
                yield Static("")

                yield Static("OpenAI API Key (for ChatGPT / GPT-4 models):", classes="settings-label")
                if openai_api_key:
                    yield Static(f"Current: {masked_openai_key}", classes="settings-info")
                else:
                    yield Static("Current: Not set", classes="settings-info")
                yield Static("")

                yield Static("Enter new OpenAI API key (leave blank to keep current):", classes="settings-label")
                yield Input(
                    placeholder="sk-...",
                    password=True,
                    id="openai-api-key-input"
                )
                yield Static("")

                yield Static("OpenAI Model (default gpt-4.1):", classes="settings-label")
                yield Input(
                    placeholder="gpt-4.1",
                    value=openai_model,
                    id="openai-model-input"
                )
                yield Static("")

                yield Static("OpenAI API Base (optional - override for Azure / proxy):", classes="settings-label")
                yield Input(
                    placeholder="https://api.openai.com/v1",
                    value=openai_api_base,
                    id="openai-base-input"
                )
                yield Static("")

                yield Static("   \u2139\ufe0f  Get API keys at: https://platform.openai.com/account/api-keys", classes="settings-info")
                yield Static("   \u2139\ufe0f  Leave base blank unless using Azure or a proxy.", classes="settings-info")
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

            with Horizontal(classes="button-row"):
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")

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
        elif event.button.id == "test-proxy-button":
            self.test_proxy_connection()

    def test_proxy_connection(self) -> None:
        """Test proxy connection through the bridge"""
        # Get proxy URL and token from inputs
        proxy_url_input = self.query_one("#proxy-url-input", Input)
        proxy_token_input = self.query_one("#proxy-token-input", Input)

        proxy_url = proxy_url_input.value.strip()
        proxy_token = proxy_token_input.value.strip()

        # Validate inputs
        if not proxy_url:
            self.app.notify("❌ Proxy URL is required to test", severity="error", timeout=5)
            return

        if not proxy_token:
            self.app.notify("❌ Proxy token is required to test", severity="error", timeout=5)
            return

        # Show testing status
        self.app.notify("🧪 Testing proxy connection... (Stage 1/3)", severity="information", timeout=10)

        # Create test request file for bridge
        try:
            test_request = {
                "proxy_url": proxy_url,
                "proxy_token": proxy_token
            }

            # Write test request to state directory
            state_dir = self.config_file.parent  # This is the config dir, we need state
            # Since we don't have direct access to the RP state dir from here,
            # we'll use a file in the config directory as a workaround
            test_request_file = self.config_file.parent / "proxy_test_request.json"
            test_results_file = self.config_file.parent / "proxy_test_results.json"

            # Clean up old results if they exist
            if test_results_file.exists():
                test_results_file.unlink()

            # Write the test request
            import json
            with open(test_request_file, 'w', encoding='utf-8') as f:
                json.dump(test_request, f)

            # Wait a bit for bridge to process (in a real implementation, this would be async)
            # For now, show a result if the file was created
            if test_request_file.exists():
                self.app.notify(
                    "✅ Proxy test request sent to bridge.\n"
                    "Check bridge logs for detailed test results.",
                    severity="information",
                    timeout=10
                )
        except Exception as e:
            self.app.notify(f"❌ Error initiating proxy test: {e}", severity="error", timeout=10)

    def save_settings(self) -> None:
        """Save settings and close"""
        # Get widgets
        api_mode_switch = self.query_one("#api-mode-switch", Switch)
        provider_input = self.query_one("#primary-llm-input", Input)
        claude_key_input = self.query_one("#claude-api-key-input", Input)
        openai_key_input = self.query_one("#openai-api-key-input", Input)
        openai_model_input = self.query_one("#openai-model-input", Input)
        openai_base_input = self.query_one("#openai-base-input", Input)
        proxy_url_input = self.query_one("#proxy-url-input", Input)
        proxy_token_input = self.query_one("#proxy-token-input", Input)
        thinking_mode_input = self.query_one("#thinking-mode-input", Input)
        deepseek_key_input = self.query_one("#deepseek-api-key-input", Input)
        model_input = self.query_one("#openrouter-model-input", Input)
        proxy_enabled_switch = self.query_one("#proxy-enabled-switch", Switch)

        # Load existing config
        config = self.load_config()

        # Update primary provider if changed
        allowed_providers = {"anthropic_sdk", "anthropic_api", "openai_api"}
        current_provider = config.get("primary_llm", "anthropic_sdk")
        new_provider_raw = provider_input.value.strip()
        if new_provider_raw:
            provider_choice = new_provider_raw.lower()
            if provider_choice not in allowed_providers:
                self.app.notify(
                    f"Invalid provider '{provider_choice}'! Choose from: {', '.join(sorted(allowed_providers))}",
                    severity="error",
                    timeout=10
                )
                return
            config["primary_llm"] = provider_choice
        elif "primary_llm" not in config:
            config["primary_llm"] = "anthropic_sdk"
        provider_choice = config.get("primary_llm", "anthropic_sdk")
        provider_changed = provider_choice != current_provider

        # Determine API mode (OpenAI/Anthropic API force API mode)
        old_api_mode = config.get("use_api_mode", False)
        if provider_choice == "anthropic_sdk":
            new_api_mode = api_mode_switch.value
        else:
            new_api_mode = True
        api_mode_changed = old_api_mode != new_api_mode
        config["use_api_mode"] = new_api_mode

        # Update proxy enabled state
        config["use_proxy"] = proxy_enabled_switch.value

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

        # Update proxy URL if modified
        new_proxy_url = proxy_url_input.value.strip()
        if new_proxy_url:
            if new_proxy_url.lower() == "clear":
                config.pop("proxy_url", None)
            else:
                config["proxy_url"] = new_proxy_url

        # Update proxy token if provided
        new_proxy_token = proxy_token_input.value.strip()
        if new_proxy_token:
            if new_proxy_token.lower() == "clear":
                config.pop("proxy_token", None)
            else:
                config["proxy_token"] = new_proxy_token

        # Update OpenAI API key if provided
        new_openai_key = openai_key_input.value.strip()
        openai_key_updated = False
        if new_openai_key:
            if not new_openai_key.startswith("sk-"):
                self.app.notify(
                    "Warning: OpenAI API key typically starts with 'sk-'",
                    severity="warning",
                    timeout=5
                )
            config["openai_api_key"] = new_openai_key
            openai_key_updated = True

        # Update OpenAI model if provided
        new_openai_model = openai_model_input.value.strip()
        openai_model_updated = False
        if new_openai_model:
            config["openai_model"] = new_openai_model
            openai_model_updated = True
        elif "openai_model" not in config:
            config["openai_model"] = "gpt-4.1"

        # Update OpenAI base URL if provided
        new_openai_base = openai_base_input.value.strip()
        openai_base_updated = False
        if new_openai_base:
            if new_openai_base.lower() == "clear":
                config.pop("openai_api_base", None)
            else:
                config["openai_api_base"] = new_openai_base
            openai_base_updated = True

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
            if provider_changed:
                updates.append(f"Provider set to {provider_choice}")
            if new_claude_key:
                updates.append("Claude key updated")
            if openai_key_updated:
                updates.append("OpenAI key updated")
            if openai_model_updated:
                updates.append(f"OpenAI model set to {config.get('openai_model')}")
            if openai_base_updated:
                updates.append("OpenAI base updated")
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
                f"✅ {', '.join(updates)}! API: {mode_status}, Proxy Routing: {proxy_status}",
                severity="information",
                timeout=5
            )

            # Show restart message if API mode or thinking mode changed
            needs_restart = api_mode_changed or new_thinking_mode or provider_changed
            if needs_restart:
                changes = []
                if api_mode_changed:
                    changes.append("API mode")
                if new_thinking_mode:
                    changes.append("thinking mode")
                if provider_changed:
                    changes.append("provider")

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

class ContextPanel(ScrollableContainer):
    """Left panel showing context, progress, and quick access menu - now scrollable"""

    def __init__(self, rp_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self.rp_dir = rp_dir
        self.content_widget = Static("", expand=True)

    def compose(self) -> ComposeResult:
        """Compose the scrollable context panel"""
        yield self.content_widget

    def on_mount(self) -> None:
        """Set up auto-refresh with optimized interval"""
        self.set_interval(3.0, self.refresh_context)  # Increased from 2s to 3s
        self.refresh_context()

    def refresh_context(self) -> None:
        """Update context display with improved formatting - more compact"""
        state_file = self.rp_dir / "state" / "current_state.md"
        counter_file = self.rp_dir / "state" / "response_counter.json"

        chapter, timestamp, location = get_chapter_info(state_file)
        active_chars = get_active_characters(self.rp_dir)
        progress, next_arc, percentage = get_arc_progress(counter_file)
        count = get_response_count(counter_file)

        def clean_value(value: Optional[str]) -> str:
            """Normalize strings for display within the context sidebar."""
            if not value:
                return "—"
            value = value.strip()
            return value or "—"

        def make_panel(title: str, lines: list[Text], border: str) -> Panel:
            """Build a compact panel with centered content."""
            renderables = lines or [Text("—", justify="center", style=STYLES["text_dim"])]
            content = Align.center(Group(*renderables), vertical="middle")
            return Panel(
                content,
                title=f"[b]{title}[/]",
                border_style=border,
                box=box.ROUNDED,
                padding=(0, 1),
                style=Style(bgcolor=STYLES["card_bg"]),
            )

        cards: list[RenderableType] = []

        def add_card(panel: Panel) -> None:
            cards.append(Padding(panel, (0, 0, 1, 0)))

        active_list = [
            char for char in active_chars if char and char.strip().lower() != "none"
        ]
        if not active_list:
            active_lines = [Text("No active characters", justify="center", style=STYLES["text_dim"])]
        else:
            display_names = active_list[:3]
            if len(active_list) > 3:
                display_names.append(f"+{len(active_list) - 3} more")
            active_lines = [
                Text(name, justify="center", style=f"bold {PALETTE['text']}" if idx == 0 else PALETTE['text'])
                for idx, name in enumerate(display_names)
            ]
        add_card(make_panel("Active Characters", active_lines, border=STYLES["card_characters"]))

        arc_total = max(progress + next_arc, 1)
        completion_ratio = progress / arc_total
        bar_length = 20
        filled = int(completion_ratio * bar_length)
        empty = bar_length - filled
        bar_body = "#" * filled + "-" * empty

        if completion_ratio < 0.33:
            bar_color = STYLES["progress_low"]
        elif completion_ratio < 0.66:
            bar_color = STYLES["progress_mid"]
        else:
            bar_color = STYLES["progress_high"]

        bar_text = Text(f"[{bar_body}]", justify="center", style=bar_color)
        progress_text = Text(
            f"{percentage:>5.1f}% complete",
            justify="center",
            style=f"bold {PALETTE['text']}",
        )
        plural_suffix = "s" if next_arc != 1 else ""
        next_text = Text(
            f"{next_arc} more turn{plural_suffix} to next beat",
            justify="center",
            style=STYLES["text_dim"],
        )
        arc_panel = make_panel(
            "Arc Progress",
            [
                Text(f"{progress}/{arc_total} turns", justify="center", style=f"bold {PALETTE['text']}"),
                bar_text,
                progress_text,
                next_text,
            ],
            border=bar_color,
        )
        add_card(arc_panel)

        momentum_text = Text(
            f"{count} total responses",
            justify="center",
            style=f"bold {PALETTE['text']}",
        )
        add_card(make_panel("Story Momentum", [momentum_text], border=STYLES["card_momentum"]))

        self.content_widget.update(Group(*cards))




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
    """Center panel showing RP conversation history - optimized for performance"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_widget: Static | None = None
        self.messages: list[RenderableType] = []
        self.max_display_messages = 100  # Prevent unlimited growth

    def compose(self) -> ComposeResult:
        """Compose the chat display"""
        self.message_widget = Static(Group(), id="message-content")
        yield self.message_widget

    def add_message(self, sender: str, content: str):
        """Add a message to chat history with optimized rendering"""
        if not self.message_widget:
            return

        sender_key = sender.lower()
        if sender_key == "system":
            body_text = Text.from_markup(content, justify="left")
        else:
            body_text = Text(content, justify="left")

        style_map = {
            "you": ("You", STYLES["message_you_text"], Style(bgcolor=STYLES["message_you_bg"])),
            "system": ("System", STYLES["message_system_text"], Style(bgcolor=STYLES["message_system_bg"])),
            "claude": ("DM", STYLES["message_dm_text"], Style(bgcolor=STYLES["message_dm_bg"])),
        }
        label, border, panel_style = style_map.get(
            sender_key, (sender or "DM", STYLES["message_dm_text"], Style(bgcolor=STYLES["message_dm_bg"]))
        )

        bubble = Panel(
            body_text,
            title=f"[b]{label}[/]",
            border_style=border,
            box=box.ROUNDED,
            padding=(0, 1),
            style=panel_style,
        )

        if sender_key == "you":
            aligned: RenderableType = Align.right(bubble)
        elif sender_key == "system":
            aligned = Align.center(bubble)
        else:
            aligned = Align.left(bubble)

        padded = Padding(aligned, (0, 1, 1, 1))
        self.messages.append(padded)

        if len(self.messages) > self.max_display_messages:
            self.messages = self.messages[-self.max_display_messages:]

        self.message_widget.update(Group(*self.messages))

        def scroll_bottom():
            self.scroll_end(animate=False)

        self.call_later(scroll_bottom)


# =============================================================================
# APP HEADER
# =============================================================================

class AppHeader(Static):
    """Compact banner showing RP title and quick hints."""

    def __init__(self, rp_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self.rp_dir = rp_dir

    def on_mount(self) -> None:
        self.refresh_header()
        self.set_interval(15.0, self.refresh_header)

    def refresh_header(self) -> None:
        chapter, timestamp, location = get_chapter_info(self.rp_dir / "state" / "current_state.md")
        renderables: list[RenderableType] = []

        location_display = location if location and location != "Unknown" else ""
        timestamp_display = timestamp if timestamp and timestamp != "Unknown" else ""

        if location_display or timestamp_display:
            top_row = Table.grid(expand=True, padding=(0, 0))
            top_row.pad_edge = False
            top_row.add_column()
            top_row.add_column(justify="right")
            top_row.add_row(
                Text(location_display, style=f"bold {PALETTE['accent']}") if location_display else Text(""),
                Text(timestamp_display, style=f"bold {PALETTE['accent']}") if timestamp_display else Text(""),
            )
            renderables.append(top_row)

        title = Text(self.rp_dir.name, style=f"bold {PALETTE['surface']}")
        if chapter and chapter != "Unknown":
            title.append("  •  ")
            title.append(chapter, style=f"bold {PALETTE['warning']}")

        hint_text = Text("F1 Help | Ctrl+T Theme | Ctrl+Q Quit", style=STYLES["text_dim"])

        bottom_row = Table.grid(expand=True, padding=(0, 0))
        bottom_row.pad_edge = False
        bottom_row.add_column()
        bottom_row.add_column(justify="right")
        bottom_row.add_row(title, hint_text)
        renderables.append(bottom_row)

        self.update(Group(*renderables))


# =============================================================================
# MAIN APP
# =============================================================================

class RPClientApp(App):
    """Main RP Client TUI Application"""

    CSS = dedent(
        f"""
/* ========================================
   GLOBAL STYLES
   ======================================== */
/* Spacing system:
   - Standard padding: 1 2 (vertical horizontal)
   - Compact padding: 0 1
   - Large padding: 2 3
   - Margins: 0 1 for buttons, 1 0 for switches
*/

Screen {{
    background: {PALETTE['surface']};
    color: {PALETTE['text']};
}}


/* ========================================
   LAYOUT & CONTAINERS
   ======================================== */
#top-tabs {{
    dock: top;
    background: {PALETTE['primary']};
    border-bottom: solid {PALETTE['border']};
    height: 3;
    padding: 0;
}}

#top-tabs Tab {{
    background: {PALETTE['primary']};
    color: {PALETTE['surface']};
    border: none;
    padding: 0 2;
    text-style: none;
}}

#top-tabs Tab:hover {{
    background: {PALETTE['text_muted']};
    color: {PALETTE['surface']};
    text-style: bold;
}}

#top-tabs Tab.-active {{
    background: {PALETTE['accent']};
    color: {PALETTE['surface']};
    text-style: bold;
    border-bottom: thick {PALETTE['boost']};
}}

#app-header {{
    dock: bottom;
    background: {PALETTE['primary']};
    color: {PALETTE['surface']};
    padding: 0 2;
    height: 2;
    border-top: solid {PALETTE['border']};
}}

#main-container {{
    layout: horizontal;
    height: 1fr;
}}


/* ========================================
   CONTENT PANELS
   ======================================== */
#context-panel {{
    width: 30%;
    background: {PALETTE['panel']};
    color: {PALETTE['text']};
    padding: 1 2;
    border-right: solid {PALETTE['border']};
    overflow-y: auto;
    overflow-x: hidden;
}}

#context-panel {{
    scrollbar-background: {PALETTE['surface']};
    scrollbar-background-hover: {PALETTE['surface']};
    scrollbar-color: {PALETTE['accent']};
    scrollbar-color-hover: {PALETTE['accent']};
    scrollbar-size: 2 1;
}}

#chat-panel {{
    width: 1fr;
    padding: 2 3 2 2;
    background: {PALETTE['surface']};
    overflow: auto;
    scrollbar-background: {PALETTE['surface']};
    scrollbar-background-hover: {PALETTE['surface']};
    scrollbar-color: {PALETTE['accent']};
    scrollbar-color-hover: {PALETTE['accent']};
    scrollbar-size: 2 1;
}}

#message-content {{
    width: 1fr;
    height: auto;
    color: {PALETTE['text']};
}}


/* ========================================
   INPUT SECTION
   ======================================== */
#input-container {{
    background: {PALETTE['panel']};
    padding: 1 2;
    border-top: solid {PALETTE['border']};
    layout: vertical;
    height: 10;
    min-height: 10;
    max-height: 10;
}}

#input-label {{
    color: {PALETTE['accent']};
    text-style: bold;
    height: 1;
}}

#input-row {{
    layout: horizontal;
    align: left middle;
    padding-right: 1;
    height: 6;
}}

#input-area {{
    height: 5;
    min-height: 5;
    max-height: 5;
    width: 1fr;
    background: {PALETTE['boost']};
    border: round {PALETTE['border']};
    padding: 0 1;
    color: {PALETTE['text']};
}}

#input-area:focus {{
    border: round {PALETTE['accent']};
    background: {PALETTE['surface']};
    color: {PALETTE['text']};
}}

#input-controls {{
    layout: vertical;
    width: 18;
    height: auto;
    align: center top;
    padding-left: 1;
}}

#send-button {{
    width: 1fr;
    margin-bottom: 1;
}}

#send-hint {{
    text-align: center;
    color: {PALETTE['text_muted']};
}}

#quick-settings-button {{
    background: {PALETTE['accent']};
}}

#quick-help-button {{
    background: {PALETTE['accent']};
}}

#quick-status-button {{
    background: {PALETTE['accent']};
}}

#status-message {{
    text-align: left;
    color: {PALETTE['text_muted']};
    height: 1;
}}


/* ========================================
   OVERLAYS
   ======================================== */
#overlay-container {{
    width: 100%;
    height: 100%;
    background: {PALETTE['panel']};
    border: round {PALETTE['border']};
    padding: 0;
    box-sizing: border-box;
}}

#overlay-title {{
    text-style: bold;
    background: {PALETTE['primary']};
    color: {PALETTE['surface']};
    padding: 1 2;
    dock: top;
    border-bottom: solid {PALETTE['border']};
}}

#overlay-content {{
    height: 1fr;
    padding: 1 2;
    background: {PALETTE['panel']};
    overflow-y: auto;
    scrollbar-background: {PALETTE['panel']};
    scrollbar-background-hover: {PALETTE['panel']};
    scrollbar-color: {PALETTE['accent']};
    scrollbar-color-hover: {PALETTE['accent']};
    scrollbar-size: 2 1;
}}

#overlay-footer {{
    text-style: dim;
    text-align: center;
    padding: 1 2;
    dock: bottom;
    background: {PALETTE['boost']};
    border-top: solid {PALETTE['border']};
    color: {PALETTE['text_muted']};
}}

#tab-selector {{
    text-align: center;
    padding: 1 2;
    text-style: bold;
    color: {PALETTE['text']};
    background: {PALETTE['boost']};
    border-bottom: solid {PALETTE['border']};
    dock: top;
}}

#story-content {{
    height: 1fr;
    color: {PALETTE['text']};
}}

/* ========================================
   SETTINGS
   ======================================== */
#settings-container {{
    width: 100%;
    height: 100%;
    background: {PALETTE['panel']};
    border: round {PALETTE['border']};
    padding: 0;
    box-sizing: border-box;
}}

#settings-title {{
    text-style: bold;
    background: {PALETTE['primary']};
    color: {PALETTE['surface']};
    padding: 1 2;
    dock: top;
    border-bottom: solid {PALETTE['border']};
}}

#settings-content {{
    height: 1fr;
    padding: 1 2;
    background: {PALETTE['panel']};
    overflow-y: auto;
    scrollbar-background: {PALETTE['panel']};
    scrollbar-background-hover: {PALETTE['panel']};
    scrollbar-color: {PALETTE['accent']};
    scrollbar-color-hover: {PALETTE['accent']};
    scrollbar-size: 2 1;
}}

#settings-footer {{
    text-style: dim;
    text-align: center;
    padding: 1 2;
    dock: bottom;
    background: {PALETTE['boost']};
    border-top: solid {PALETTE['border']};
    color: {PALETTE['text_muted']};
}}

.settings-section-title {{
    text-style: bold;
    color: {PALETTE['accent']};
    margin-top: 2;
    margin-bottom: 1;
}}

.settings-label {{
    color: {PALETTE['text']};
    margin-top: 1;
}}

.settings-info {{
    color: {PALETTE['text_muted']};
    text-style: dim;
    margin-left: 2;
}}

.settings-hint {{
    color: {PALETTE['warning']};
    text-style: dim;
    margin-top: 1;
    margin-left: 2;
}}

.button-row {{
    layout: horizontal;
    align: center middle;
    height: auto;
}}

.button-row Button {{
    margin: 0 1;
    width: 1fr;
    height: auto;
}}


/* ========================================
   FORM ELEMENTS
   ======================================== */
Button {{
    margin: 0 1;
    background: {PALETTE['text_muted']};
    color: {STYLES['button_text_default']};
    border: round {PALETTE['border']};
}}

Button:hover {{
    background: {PALETTE['primary']};
    color: {STYLES['button_text_default']};
    text-style: bold;
}}

Button.primary {{
    background: {PALETTE['accent']};
    color: {STYLES['button_text_primary']};
    border: round {PALETTE['accent']};
}}

Button.primary:hover {{
    background: {PALETTE['warning']};
    color: {STYLES['button_text_primary']};
    text-style: bold;
}}

Button:focus {{
    text-style: bold;
    border: round {PALETTE['accent']};
}}

Button:disabled {{
    background: {PALETTE['panel']};
    color: {PALETTE['text_muted']};
    text-style: dim;
}}

Input {{
    background: {PALETTE['boost']};
    color: {PALETTE['text']};
    border: round {PALETTE['border']};
}}

Input:focus {{
    border: round {PALETTE['accent']};
    color: {PALETTE['text']};
}}

Switch {{
    margin: 1 0;
}}
        """
    )

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+j", "submit_message", "Send"),  # Ctrl+Enter sends as Ctrl+J
        Binding("ctrl+t", "cycle_theme", "Theme"),  # Cycle theme with Ctrl+T
        # Overlay actions - F-keys for overlays (reorganized)
        Binding("f1", "show_help", "Help"),
        Binding("f2", "show_character_sheet", "Character"),
        Binding("f3", "show_story_overview", "Story"),
        Binding("f4", "show_entities", "Entities"),
        Binding("f5", "show_notes", "Notes"),
       
        Binding("f6", "show_modules", "Modules"),
        Binding("f7", "show_status", "Status"),
        Binding("f8", "show_settings", "Settings"),
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

        # Register cleanup on exit (atexit for guaranteed cleanup)
        import atexit
        atexit.register(self._cleanup_flags)

    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        # Navigation tabs at the top
        yield Tabs(
            Tab("💬 Chat", id="tab-chat"),
            Tab("🔧 Modules", id="tab-modules"),
            Tab("⚙️ Settings", id="tab-settings"),
            Tab("❓ Help", id="tab-help"),
            Tab("📊 Status", id="tab-status"),
            id="top-tabs"
        )

        with Container(id="main-container"):
            yield ContextPanel(self.rp_dir, id="context-panel")
            yield ChatDisplay(id="chat-panel")

        with Container(id="input-container"):
            yield Static(">> Your Move", id="input-label")
            with Horizontal(id="input-row"):
                yield RPTextArea(id="input-area")
                with Vertical(id="input-controls"):
                    yield Button("Send", id="send-button", variant="primary")
                    yield Static("Ctrl+Enter", id="send-hint")

            yield Static("", id="status-message")

        # Footer with location/timestamp info (previously header)
        yield AppHeader(self.rp_dir, id="app-header")

    def _cleanup_flags(self) -> None:
        """Clean up flags - called by atexit to ensure cleanup always happens"""
        try:
            print("[TUI] Cleaning up flags...")
            self.tui_active_flag.unlink(missing_ok=True)
            self.ready_flag.unlink(missing_ok=True)
            self.done_flag.unlink(missing_ok=True)
            print("[TUI] Flags cleaned up successfully")
        except Exception as e:
            print(f"[TUI] Error cleaning flags: {e}")

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals (Ctrl+C, terminal close)"""
        print(f"[TUI] Received signal {signum}, cleaning up...")
        self._cleanup_flags()
        import sys
        sys.exit(0)

    def on_mount(self) -> None:
        """Initialize app"""
        # Create TUI active flag (signals bridge that TUI is running)
        try:
            self.tui_active_flag.touch()
        except Exception as e:
            print(f"Warning: Could not create TUI active flag: {e}")

        self.query_one(ChatDisplay).add_message(
            "System",
            f"[bold {PALETTE['primary']}]✨ RP Client TUI Started[/]\n"
            f"[{STYLES['text_dim']}]Type your message below and press [bold {STYLES['text_emphasis']}]Ctrl+Enter[/] to send.\n"
            f"Press [bold {STYLES['text_emphasis']}]F1[/] for help or browse the F-key overlays above.[/]"
        )

        # Watch for response file
        self.set_interval(0.5, self.check_for_response)

    def on_unmount(self) -> None:
        """Cleanup when app is shutting down"""
        print("[TUI] on_unmount() called")
        # Remove TUI active flag (signals bridge to shut down)
        self._cleanup_flags()
        print("[TUI] on_unmount() complete")

    def action_quit(self) -> None:
        """Override quit to ensure cleanup"""
        print("[TUI] action_quit() called")
        # Cleanup flags before quitting
        self._cleanup_flags()
        print("[TUI] Calling parent quit...")
        # Call parent quit
        super().action_quit()
        print("[TUI] Parent quit returned")

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
            self.show_status(f"[{STYLES['text_dim']}]Message is empty[/]")
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
            self.show_status("📤 Message sent...")
        except Exception as e:
            self.show_status(f"❌ Error writing input: {e}")
            return

        # Clear input
        input_area.clear()

        # Set waiting state
        self.waiting_for_response = True
        self.show_status("⏳ Waiting for Claude...")

        # Update status after 1 second
        self.set_timer(1.0, lambda: self.show_status("⏳ Processing...") if self.waiting_for_response else None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-button":
            self.action_send_message()

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle tab clicks"""
        tab_id = event.tab.id
        if tab_id == "tab-modules":
            self.action_show_modules_tab()
        elif tab_id == "tab-settings":
            self.action_show_settings()
        elif tab_id == "tab-help":
            self.action_show_help()
        elif tab_id == "tab-status":
            self.action_show_status()
        # tab-chat is the default view, no action needed

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
        """Show status message with formatting"""
        if not message:
            self.query_one("#status-message", Static).update("")
            return

        # Add visual styling to status messages using palette
        if "❌" in message or "Error" in message:
            styled = f"[bold {STYLES['status_error']}]{message}[/]"
        elif "✅" in message or "success" in message.lower():
            styled = f"[bold {STYLES['status_success']}]{message}[/]"
        elif "⏳" in message or "Waiting" in message:
            styled = f"[bold {STYLES['status_waiting']}]{message}[/]"
        else:
            styled = f"[{STYLES['status_info']}]{message}[/]"

        self.query_one("#status-message", Static).update(styled)

    def _dismiss_current_overlay(self) -> None:
        """Dismiss any currently open overlay before showing new one"""
        # Check if there's a modal screen and dismiss it
        if len(self.screen_stack) > 1:
            self.pop_screen()

    # Overlay actions
    def action_show_character_sheet(self) -> None:
        """Show character sheet overlay (F2) - combines Memory + character info"""
        self._dismiss_current_overlay()
        self.push_screen(CharacterSheetOverlay(self.rp_dir))

    def action_show_story_overview(self) -> None:
        """Show story overview overlay (F3) - combines Arc + Genome with tabs"""
        self._dismiss_current_overlay()
        self.push_screen(StoryOverviewOverlay(self.rp_dir))

    def action_show_entities(self) -> None:
        """Show entities overlay (F4) - grouped by type"""
        self._dismiss_current_overlay()
        self.push_screen(EntitiesOverlay(self.rp_dir))

    def action_show_notes(self) -> None:
        """Show scene notes overlay (F5)"""
        self._dismiss_current_overlay()
        self.push_screen(SceneNotesOverlay(self.rp_dir))

    def action_show_modules(self) -> None:
        """Show module toggles overlay (F6)"""
        self._dismiss_current_overlay()
        self.push_screen(ModuleTogglesOverlay(self.rp_dir))

    def action_show_modules_tab(self) -> None:
        """Show modules tab screen"""
        self._dismiss_current_overlay()
        self.push_screen(ModulesTabScreen(self.rp_dir))

    def action_show_status(self) -> None:
        """Show status overlay (F7)"""
        self._dismiss_current_overlay()
        self.push_screen(StatusOverlay(self.rp_dir))

    def action_show_settings(self) -> None:
        """Show settings screen (F8)"""
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

    def action_cycle_theme(self) -> None:
        """Cycle through available themes"""
        available_themes = [
            "dark", "light", "nord", "dracula", "solarized-dark", "solarized-light", "monokai"
        ]

        try:
            current_theme = self.theme
            if current_theme in available_themes:
                current_idx = available_themes.index(current_theme)
                next_theme = available_themes[(current_idx + 1) % len(available_themes)]
            else:
                next_theme = available_themes[0]

            self.theme = next_theme
            self.notify(f"🎨 Theme changed to: {next_theme}", severity="information", timeout=2)
        except Exception as e:
            self.notify(f"⚠️ Theme error: {e}", severity="warning", timeout=5)

    def action_show_help(self) -> None:
        """Show help overlay"""
        help_text = """# Keyboard Shortcuts & Controls

## Main Controls
- **Ctrl+Enter** - Send message to Claude Code
- **Enter** - New line in message (works naturally)
- **Ctrl+Q** - Quit application
- **Ctrl+T** - Cycle through themes 🎨
- **F1** - Show this help

## Quick Access Overlays (F-keys)
- **F2** - Character Sheet (memory + character info)
- **F3** - Story Overview (Arc + Genome with tabs)
- **F4** - Entities (grouped by type)
- **F5** - Scene Notes
- **F6** - Module Toggles (features & automation)
- **F7** - System Status (progress & activity)
- **F8** - Settings (API keys & configuration)
- **F10** - Restart Bridge (after config changes)

## In Overlays
- **ESC** - Close overlay
- **Tab** - Switch between tabs (in tabbed overlays)
- **↑/↓ or PgUp/PgDn** - Scroll content
- **Number keys** - Switch tabs (1=Arc, 2=Genome in F3)

## Layout Guide
- **Left Panel**: RP time, location, active characters, arc progress
- **Main Area**: Chat display (DM responses and your messages)
- **Bottom**: Your response input area
- **Footer**: Quick key reference

## Writing Tips
- Type naturally - Enter adds new lines
- Multi-line messages supported
- Press Ctrl+Enter when ready to send
- Use F1-F8 while writing to reference info

## Available Themes
Press **Ctrl+T** to cycle:
dark, light, nord, dracula, solarized-dark, solarized-light, monokai
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
