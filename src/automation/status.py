#!/usr/bin/env python3
"""
Status Module

Generates and updates CURRENT_STATUS.md with system status information.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List

from src.fs_write_queue import get_write_queue
from src.automation.core import get_response_count


# Get write queue instance
_write_queue = get_write_queue()


# Status file template (condensed for easier maintenance)
STATUS_TEMPLATE = """# Current RP Status

**Last Updated**: {timestamp}

---

## 📍 Current State

- **Timestamp**: {state_timestamp}
- **Location**: {location}
- **Chapter**: {chapter}
- **Response Count**: {response_count}

---

## 📊 Progress

**Story Arc**: {arc_progress} / {arc_frequency} responses
- Next arc generation in: **{arc_next} responses**
- Progress: {progress_bar}

---

## 🎭 Entities

**Entity Cards**: {entity_count} entities in entities/ directory
**Loaded This Response**: {loaded_entities}

---

## ⚙️ Automation

**Entity Cards**: {auto_cards} (Threshold: {card_threshold} mentions)
**Story Arcs**: {auto_arc} (Every {arc_frequency} responses)

---

## 📝 Quick Commands

- `/status` - Detailed status report
- `/continue` - Load session context
- `/endSession` - End session protocol
- `/arc` - Generate story arc
- `/gencard [type], [name]` - Create entity card
- `/note [text]` - Add quick note
- `/memory` - Update memory

---

*Keep this file open in a second pane for live status updates*
"""


class StatusManager:
    """Manages status file generation"""

    def __init__(self, rp_dir: Path):
        """Initialize status manager

        Args:
            rp_dir: RP directory path
        """
        self.rp_dir = rp_dir

    def update_status_file(self, status_file: Path, state_file: Path,
                           counter_file: Path,
                           config: dict, loaded_entities: List[str]) -> None:
        """Generate/update CURRENT_STATUS.md with system status

        Args:
            status_file: Path to CURRENT_STATUS.md
            state_file: Path to current_state.md
            counter_file: Path to response_counter.json
            config: Configuration dict
            loaded_entities: List of entity names loaded this response
        """
        # Get response count
        response_count = self._get_response_count(counter_file)

        # Get timestamp, location, chapter from current_state.md
        timestamp, location, chapter = self._parse_state_file(state_file)

        # Count entities from entities/ directory (using EntityManager)
        entity_count = self._count_entities_from_directory()

        # Calculate arc progress
        arc_frequency = config.get('arc_frequency', 50)
        arc_progress = response_count % arc_frequency
        arc_next = arc_frequency - arc_progress

        # Build progress bar
        progress_bar = self._format_progress_bar(arc_progress, arc_frequency)

        # Loaded entities string
        loaded_str = ', '.join(loaded_entities) if loaded_entities else "None"

        # Automation status (inlined from _get_automation_status for simplicity)
        auto_cards = "✅ ON" if config.get('auto_entity_cards', True) else "❌ OFF"
        auto_arc = "✅ ON" if config.get('auto_story_arc', True) else "❌ OFF"
        card_threshold = config.get('entity_mention_threshold', 2)

        # Generate status content from template
        status_content = STATUS_TEMPLATE.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            state_timestamp=timestamp,
            location=location,
            chapter=chapter,
            response_count=response_count,
            arc_progress=arc_progress,
            arc_frequency=arc_frequency,
            arc_next=arc_next,
            progress_bar=progress_bar,
            entity_count=entity_count,
            loaded_entities=loaded_str,
            auto_cards=auto_cards,
            auto_arc=auto_arc,
            card_threshold=card_threshold
        )

        try:
            _write_queue.write_text(status_file, status_content, encoding='utf-8')
        except Exception as e:
            print(f"WARNING: Could not queue status file: {e}")

    def _get_response_count(self, counter_file: Path) -> int:
        """Get current response count

        Args:
            counter_file: Path to response_counter.json

        Returns:
            Current response count
        """
        return get_response_count(counter_file)

    def _parse_state_file(self, state_file: Path) -> tuple[str, str, str]:
        """Parse current_state.md for timestamp, location, chapter

        Args:
            state_file: Path to current_state.md

        Returns:
            Tuple of (timestamp, location, chapter)
        """
        timestamp = "Unknown"
        location = "Unknown"
        chapter = "[Check current_state.md]"

        if state_file.exists():
            try:
                content = state_file.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if line.startswith('**Timestamp'):
                        timestamp = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
                    elif line.startswith('**Location'):
                        location = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
                    elif line.startswith('**Chapter'):
                        chapter = line.split(':', 1)[1].strip() if ':' in line else chapter
            except Exception:
                pass

        return timestamp, location, chapter

    def _count_entities_from_directory(self) -> int:
        """Count entity cards in entities/ directory

        Returns:
            Number of entity cards
        """
        entities_dir = self.rp_dir / "entities"
        if entities_dir.exists():
            try:
                # Count .md files in entities/ directory
                entity_files = list(entities_dir.glob("*.md"))
                return len(entity_files)
            except Exception:
                return 0
        return 0

    def _format_progress_bar(self, progress: int, total: int) -> str:
        """Format progress bar for arc generation

        Args:
            progress: Current progress
            total: Total needed

        Returns:
            Progress bar string
        """
        bar_filled = (progress * 10) // total
        bar_empty = 10 - bar_filled
        return '█' * bar_filled + '░' * bar_empty


# Convenience function for backward compatibility
def update_status_file(status_file: Path, state_file: Path, counter_file: Path,
                       config: dict, loaded_entities: List[str]) -> None:
    """Generate/update status file (convenience function)

    Args:
        status_file: Path to CURRENT_STATUS.md
        state_file: Path to current_state.md
        counter_file: Path to response_counter.json
        config: Configuration dict
        loaded_entities: List of entity names loaded
    """
    rp_dir = status_file.parent  # CURRENT_STATUS.md is in RP root
    manager = StatusManager(rp_dir)
    manager.update_status_file(status_file, state_file, counter_file, config, loaded_entities)
