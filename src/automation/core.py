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
        "auto_entity_cards": True,
        "entity_mention_threshold": 2,
        "auto_story_arc": True,
        "arc_frequency": 50
    }

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults
                return {**defaults, **config}
        except Exception:
            pass

    return defaults


def increment_counter(counter_file: Path, config: dict, log_file: Path) -> tuple[int, bool]:
    """Increment response counter and check if arc generation is needed

    Args:
        counter_file: Path to response_counter.json (or .txt for backward compat)
        config: Configuration dict
        log_file: Path to log file

    Returns:
        Tuple of (new_count, should_generate_arc)
    """
    # Get RP directory from counter file path (counter_file = rp_dir/state/response_counter.json)
    rp_dir = counter_file.parent.parent
    state_dir = counter_file.parent

    try:
        fm = FileManager(rp_dir)
        count = fm.increment_response_counter(state_dir)
    except Exception as e:
        # Fallback to old method if FileManager fails
        log_to_file(log_file, f"FileManager failed, using fallback: {e}")
        count = 0
        if counter_file.exists():
            try:
                count = int(counter_file.read_text(encoding='utf-8').strip())
            except Exception:
                count = 0
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
    # Get RP directory from counter file path (counter_file = rp_dir/state/response_counter.json)
    rp_dir = counter_file.parent.parent
    state_dir = counter_file.parent

    try:
        fm = FileManager(rp_dir)
        return fm.read_response_counter(state_dir)
    except Exception:
        # Fallback to old method if FileManager fails
        if counter_file.exists():
            try:
                return int(counter_file.read_text(encoding='utf-8').strip())
            except Exception:
                return 0
        return 0
