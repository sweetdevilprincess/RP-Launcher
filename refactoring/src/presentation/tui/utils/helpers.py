"""Helper utilities for TUI operations.

This module provides utility functions for file I/O, state extraction,
and data parsing used throughout the TUI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_file(path: Path) -> str:
    """Read file contents, return empty string if not found.

    Args:
        path: Path to file to read

    Returns:
        File contents as string, or empty string if file doesn't exist
    """
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return ""


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON file, return empty dict if not found.

    Args:
        path: Path to JSON file to read

    Returns:
        Parsed JSON as dictionary, or empty dict if file doesn't exist
    """
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def get_chapter_info(state_file: Path) -> tuple[str, str, str]:
    """Extract chapter, timestamp, location from active session log.

    Args:
        state_file: Path to current_state.md file (used to find RP directory)

    Returns:
        Tuple of (chapter, timestamp, location)
    """
    # Get RP directory - use main session (active timeline)
    rp_dir = state_file.parent.parent  # Go up from state/ to RP root
    session_id = "main"  # Always use main session for now

    # Read from active session log
    session_file = rp_dir / "sessions" / f"session_{session_id}.json"

    if session_file.exists():
        session_data = read_json(session_file)
        messages = session_data.get("messages", [])

        if messages:
            # Get latest message
            latest_message = messages[-1]
            scene_snapshot = latest_message.get("agent_data_background", {}).get("scene_context_snapshot", {})

            chapter = scene_snapshot.get("chapter", "Unknown") or "Unknown"
            location = scene_snapshot.get("location", "Unknown") or "Unknown"

            # Get timestamp from time_context
            time_context = scene_snapshot.get("time_context", {})
            timestamp = time_context.get("current_time", "Unknown") or "Unknown"

            return chapter, timestamp, location

    # Fallback: return default values
    return "Unknown", "Unknown", "Unknown"


def get_active_characters(triggers_file: Path) -> list[str]:
    """Get active characters from active session log.

    Args:
        triggers_file: Path to session_triggers file (used to find RP directory)

    Returns:
        List of character names, or [] if no characters found
    """
    # Get RP directory - use main session (active timeline)
    rp_dir = triggers_file.parent.parent  # Go up from state/ to RP root
    session_id = "main"  # Always use main session for now

    # Read from active session log
    session_file = rp_dir / "sessions" / f"session_{session_id}.json"

    if session_file.exists():
        session_data = read_json(session_file)
        messages = session_data.get("messages", [])

        if messages:
            # Get latest message
            latest_message = messages[-1]
            scene_snapshot = latest_message.get("agent_data_background", {}).get("scene_context_snapshot", {})

            characters = scene_snapshot.get("characters_in_scene", [])
            return characters if characters else []

    # Fallback: return empty list
    return []


def get_response_count(counter_file: Path) -> int:
    """Get current response count from active session log.

    Args:
        counter_file: Path to response_counter file (used to find RP directory)

    Returns:
        Response count as integer, or 0 if session doesn't exist
    """
    # Get RP directory - use main session (active timeline)
    rp_dir = counter_file.parent.parent  # Go up from state/ to RP root
    session_id = "main"  # Always use main session for now

    # Read from active session log
    session_file = rp_dir / "sessions" / f"session_{session_id}.json"

    if session_file.exists():
        session_data = read_json(session_file)
        return session_data.get("current_response", 0)

    # Fallback: return 0
    return 0


def get_arc_progress(counter_file: Path, arc_frequency: int = 50) -> tuple[int, int, float]:
    """Get arc progress based on response count.

    Args:
        counter_file: Path to response_counter.txt
        arc_frequency: Number of responses per arc (default: 50)

    Returns:
        Tuple of (current_progress, responses_until_next, percentage)
    """
    count = get_response_count(counter_file)
    progress = count % arc_frequency
    next_arc = arc_frequency - progress
    percentage = (progress / arc_frequency) * 100
    return progress, next_arc, percentage


__all__ = [
    "read_file",
    "read_json",
    "get_chapter_info",
    "get_active_characters",
    "get_response_count",
    "get_arc_progress",
]
