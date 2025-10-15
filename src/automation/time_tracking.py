#!/usr/bin/env python3
"""
Time Tracking Module

Calculates elapsed time based on activities mentioned in user messages.
Integrates with Timing.txt for activity durations.
"""

import re
from pathlib import Path
from typing import Tuple, Dict

from src.fs_write_queue import get_write_queue
from src.automation.core import log_to_file


# Get write queue instance
_write_queue = get_write_queue()


class TimeTracker:
    """Handles time calculation from activities"""

    def __init__(self, timing_file: Path, log_file: Path):
        """Initialize time tracker

        Args:
            timing_file: Path to Timing.txt (activity durations)
            log_file: Path to log file
        """
        self.timing_file = timing_file
        self.log_file = log_file
        self.activities: Dict[str, int] = {}

        # Load timing data
        if timing_file.exists():
            self._load_timing_data()

    def _load_timing_data(self) -> None:
        """Load and parse Timing.txt"""
        try:
            content = self.timing_file.read_text(encoding='utf-8')

            # Parse activities (format: "activity: minutes" or comma-separated)
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Parse comma-separated format: eat: 10, drink: 3, ...
                pairs = line.split(',')
                for pair in pairs:
                    if ':' in pair:
                        parts = pair.split(':', 1)
                        activity = parts[0].strip().lower()
                        try:
                            minutes = int(parts[1].strip())
                            self.activities[activity] = minutes
                        except ValueError:
                            continue

        except Exception as e:
            log_to_file(self.log_file, f"WARNING: Could not load Timing.txt: {e}")

    def calculate_time(self, message: str, state_file: Path) -> Tuple[int, str]:
        """Calculate elapsed time from activities in message

        Args:
            message: User message to scan for activities
            state_file: Path to current_state.md (for updating)

        Returns:
            Tuple of (total_minutes, activities_description)
        """
        if not self.timing_file.exists():
            log_to_file(self.log_file, f"WARNING: Timing.txt not found at {self.timing_file}")
            return 0, ""

        # Find activities in message
        total_minutes = 0
        activities_found = []
        message_lower = message.lower()

        for activity, minutes in self.activities.items():
            # Word boundary matching
            if re.search(r'\b' + re.escape(activity) + r'\b', message_lower):
                total_minutes += minutes
                activities_found.append(f"{activity} ({minutes} min)")

        # Log and update state file if activities found
        if activities_found:
            activities_desc = ", ".join(activities_found)
            log_to_file(self.log_file, f"Time tracking: {activities_desc} = {total_minutes} minutes")

            self._update_state_file(state_file, activities_desc, total_minutes)

            return total_minutes, activities_desc
        else:
            log_to_file(self.log_file, "No standard activities detected")
            return 0, ""

    def _update_state_file(self, state_file: Path, activities_desc: str, total_minutes: int) -> None:
        """Update current_state.md with time calculation suggestion

        Args:
            state_file: Path to current_state.md
            activities_desc: Description of detected activities
            total_minutes: Total calculated time
        """
        if not state_file.exists():
            return

        try:
            current_content = state_file.read_text(encoding='utf-8')

            # Remove any existing time suggestion
            lines = current_content.split('\n')
            filtered_lines = []
            skip_section = False

            for line in lines:
                if line.startswith('## Time Calculation Suggestion'):
                    skip_section = True
                elif line.startswith('##') and skip_section:
                    skip_section = False

                if not skip_section:
                    filtered_lines.append(line)

            # Add new suggestion
            suggestion = f"""
## Time Calculation Suggestion (Latest)
**Activities detected**: {activities_desc}
**Suggested time elapsed**: {total_minutes} minutes
**Note**: Review and adjust for modifiers (fast/slow) or unknown activities
"""
            updated_content = '\n'.join(filtered_lines).rstrip() + '\n' + suggestion
            _write_queue.write_text(state_file, updated_content, encoding='utf-8')

        except Exception as e:
            log_to_file(self.log_file, f"WARNING: Could not update current_state.md: {e}")


# Convenience function for backward compatibility
def calculate_time(message: str, timing_file: Path, state_file: Path, log_file: Path) -> Tuple[int, str]:
    """Calculate elapsed time from activities (convenience function)

    Args:
        message: User message
        timing_file: Path to Timing.txt
        state_file: Path to current_state.md
        log_file: Path to log file

    Returns:
        Tuple of (total_minutes, activities_description)
    """
    tracker = TimeTracker(timing_file, log_file)
    return tracker.calculate_time(message, state_file)
