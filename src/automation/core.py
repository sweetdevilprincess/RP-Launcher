#!/usr/bin/env python3
"""
Automation Core Module

Basic automation utilities:
- Logging
- Configuration loading
- Response counter management
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.fs_write_queue import get_write_queue
from src.file_manager import FileManager


# Get write queue instance
_write_queue = get_write_queue()


def log_to_file(log_file: Path, message: str) -> None:
    """Log message to hook.log with timestamp

    Args:
        log_file: Path to log file
        message: Message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"WARNING: Could not write to log: {e}")


def load_config(config_file: Path) -> dict:
    """Load automation configuration from JSON

    Args:
        config_file: Path to automation_config.json

    Returns:
        Configuration dict with defaults applied
    """
    defaults = {
        # DeepSeek Agent Configuration
        "agents": {
            "background": {
                "response_analyzer": {"enabled": True, "priority": 1},
                "memory_creation": {"enabled": True, "priority": 2},
                "relationship_analysis": {"enabled": True, "priority": 3},
                "plot_thread_detection": {"enabled": True, "priority": 4},
                "knowledge_extraction": {"enabled": True, "priority": 5},
                "contradiction_detection": {"enabled": False, "priority": 6}
            },
            "immediate": {
                "quick_entity_analysis": {"enabled": True, "timeout_seconds": 5},
                "fact_extraction": {"enabled": True, "timeout_seconds": 3},
                "memory_extraction": {"enabled": True, "timeout_seconds": 3},
                "plot_thread_extraction": {"enabled": True, "timeout_seconds": 3}
            }
        },
        # Fallback System Configuration
        "fallback": {
            "use_trigger_system": True,
            "trigger_system_primary": False  # Agents are primary, triggers are fallback
        },
        # Legacy Settings (deprecated, kept for backward compatibility)
        "legacy": {
            "entity_mention_threshold": 2,
            "auto_entity_cards": False,  # Replaced by DeepSeek agents
            "old_entity_tracking": False  # Removed, replaced by agents
        },
        # Story Arc Generation
        "auto_story_arc": True,
        "arc_frequency": 50,
        # Narrative Templates
        "enable_narrative_templates": True,
        # Backward compatibility (kept at top level for existing code)
        "auto_entity_cards": True,
        "entity_mention_threshold": 2,
        "enable_contradiction_detection": False
    }

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Deep merge with defaults (preserve nested structure)
                return _deep_merge_config(defaults, config)
        except Exception:
            pass

    return defaults


def _deep_merge_config(defaults: dict, config: dict) -> dict:
    """Deep merge config with defaults, preserving nested structures

    Args:
        defaults: Default configuration
        config: User configuration

    Returns:
        Merged configuration
    """
    result = defaults.copy()
    for key, value in config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_config(result[key], value)
        else:
            result[key] = value
    return result


def _get_file_manager_for_counter(counter_file: Path) -> tuple[FileManager, Path]:
    """Extract common setup for counter operations (DRY helper)

    Args:
        counter_file: Path to counter file

    Returns:
        Tuple of (FileManager instance, state_dir path)
    """
    rp_dir = counter_file.parent.parent
    state_dir = counter_file.parent
    return FileManager(rp_dir), state_dir


def _read_counter_fallback(counter_file: Path) -> int:
    """Fallback method to read counter from .txt file

    Args:
        counter_file: Path to counter file

    Returns:
        Counter value or 0 if cannot read
    """
    if counter_file.exists():
        try:
            return int(counter_file.read_text(encoding='utf-8').strip())
        except Exception:
            return 0
    return 0


def increment_counter(counter_file: Path, config: dict, log_file: Path) -> tuple[int, bool]:
    """Increment response counter and check if arc generation is needed

    Args:
        counter_file: Path to response_counter.json (or .txt for backward compat)
        config: Configuration dict
        log_file: Path to log file

    Returns:
        Tuple of (new_count, should_generate_arc)
    """
    try:
        fm, state_dir = _get_file_manager_for_counter(counter_file)
        count = fm.increment_response_counter(state_dir)
    except Exception as e:
        # Fallback to old method if FileManager fails
        log_to_file(log_file, f"FileManager failed, using fallback: {e}")
        count = _read_counter_fallback(counter_file)
        count += 1
        _write_queue.write_text(counter_file, str(count), encoding='utf-8')

    log_to_file(log_file, f"Response counter: {count}")

    # Check if arc generation needed
    arc_frequency = config.get('arc_frequency', 50)
    should_generate_arc = (count % arc_frequency == 0 and config.get('auto_story_arc', True))

    if should_generate_arc:
        log_to_file(log_file, f"Arc generation threshold reached at response {count}")

    return count, should_generate_arc


def get_response_count(counter_file: Path) -> int:
    """Get current response count

    Args:
        counter_file: Path to response_counter.json (or .txt for backward compat)

    Returns:
        Current response count (0 if file doesn't exist)
    """
    try:
        fm, state_dir = _get_file_manager_for_counter(counter_file)
        return fm.read_response_counter(state_dir)
    except Exception:
        # Fallback to old method if FileManager fails
        return _read_counter_fallback(counter_file)
