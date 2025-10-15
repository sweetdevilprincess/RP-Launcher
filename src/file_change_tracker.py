#!/usr/bin/env python3
"""
File Change Tracker

Tracks file modification times and notifies Claude when files have been updated.
Especially important for DeepSeek-generated content (entity cards, story arcs, etc.)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from src.fs_write_queue import get_write_queue


class FileChangeTracker:
    """Tracks file changes and generates update notifications"""

    def __init__(self, rp_dir: Path, debounce_ms: int = 500):
        self.rp_dir = rp_dir
        self.state_dir = rp_dir / "state"
        self.tracking_file = self.state_dir / "file_changes.json"
        self.tracked_files = self._load_tracking_data()

        # Get global write queue instance
        self.write_queue = get_write_queue(debounce_ms=debounce_ms)

    def _load_tracking_data(self) -> dict:
        """Load previous file tracking data"""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_tracking_data(self):
        """Save current file tracking data (queued with debouncing)"""
        try:
            self.state_dir.mkdir(exist_ok=True)
            # Use write queue instead of direct write
            self.write_queue.write_json(self.tracking_file, self.tracked_files, indent=2)
        except Exception as e:
            print(f"Warning: Could not queue file tracking data: {e}")

    def _get_file_mtime(self, file_path: Path) -> Optional[float]:
        """Get file modification time"""
        try:
            return file_path.stat().st_mtime
        except Exception:
            return None

    def check_files_for_updates(self, files_to_check: List[Path]) -> Tuple[List[dict], List[Path]]:
        """Check if any files have been updated since last check

        Args:
            files_to_check: List of file paths to check

        Returns:
            Tuple of (update_notifications, updated_files)
            - update_notifications: List of dicts with update info
            - updated_files: List of file paths that were updated
        """
        updates = []
        updated_files = []

        for file_path in files_to_check:
            if not file_path.exists():
                continue

            file_key = str(file_path.relative_to(self.rp_dir))
            current_mtime = self._get_file_mtime(file_path)

            if current_mtime is None:
                continue

            # Check if file is tracked
            if file_key in self.tracked_files:
                last_mtime = self.tracked_files[file_key].get('mtime')

                # File was updated!
                if last_mtime and current_mtime > last_mtime:
                    update_info = {
                        'file_path': file_path,
                        'file_name': file_path.name,
                        'relative_path': file_key,
                        'last_seen': datetime.fromtimestamp(last_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'category': self._categorize_file(file_path),
                        'is_auto_generated': self.tracked_files[file_key].get('auto_generated', False)
                    }
                    updates.append(update_info)
                    updated_files.append(file_path)

            # Update tracking data
            self.tracked_files[file_key] = {
                'mtime': current_mtime,
                'auto_generated': self.tracked_files.get(file_key, {}).get('auto_generated', False)
            }

        # Save updated tracking data
        if updates:
            self._save_tracking_data()

        return updates, updated_files

    def mark_file_as_auto_generated(self, file_path: Path):
        """Mark a file as auto-generated (by DeepSeek, etc.)"""
        file_key = str(file_path.relative_to(self.rp_dir))
        current_mtime = self._get_file_mtime(file_path)

        self.tracked_files[file_key] = {
            'mtime': current_mtime,
            'auto_generated': True,
            'generated_at': datetime.now().isoformat()
        }
        self._save_tracking_data()

    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file by directory/type"""
        parts = file_path.relative_to(self.rp_dir).parts

        if 'entities' in parts or 'characters' in parts:
            return 'entity'
        elif 'state' in parts:
            if 'story_arc' in file_path.name.lower():
                return 'story_arc'
            elif 'current_state' in file_path.name.lower():
                return 'state'
            else:
                return 'state'
        elif 'chapters' in parts:
            return 'chapter'
        else:
            return 'other'

    def generate_update_notification(self, updates: List[dict]) -> str:
        """Generate a formatted notification for Claude about file updates

        Args:
            updates: List of update info dicts from check_files_for_updates()

        Returns:
            Formatted notification string to inject into prompt
        """
        if not updates:
            return ""

        # Group by category
        by_category = {
            'entity': [],
            'story_arc': [],
            'state': [],
            'chapter': [],
            'other': []
        }

        for update in updates:
            category = update['category']
            by_category[category].append(update)

        notification_parts = [
            "<!-- ========================================",
            "📢 FILE UPDATE NOTIFICATIONS",
            "======================================== -->",
            "",
            "⚠️ **IMPORTANT: The following files have been UPDATED since you last saw them:**",
            ""
        ]

        # Entity/Character updates
        if by_category['entity']:
            notification_parts.append("## 🎭 Character/Entity Updates")
            for update in by_category['entity']:
                auto_tag = " [AUTO-GENERATED]" if update['is_auto_generated'] else ""
                notification_parts.append(f"- **{update['file_name']}**{auto_tag}")
                notification_parts.append(f"  - Last seen: {update['last_seen']}")
                notification_parts.append(f"  - Updated at: {update['updated_at']}")
                notification_parts.append(f"  - ⚠️ **REREAD this file carefully - content has changed!**")
            notification_parts.append("")

        # Story arc updates
        if by_category['story_arc']:
            notification_parts.append("## 📖 Story Arc Updates")
            for update in by_category['story_arc']:
                auto_tag = " [AUTO-GENERATED]" if update['is_auto_generated'] else ""
                notification_parts.append(f"- **{update['file_name']}**{auto_tag}")
                notification_parts.append(f"  - Updated at: {update['updated_at']}")
                notification_parts.append(f"  - ⚠️ **Story arc has been regenerated - review new direction!**")
            notification_parts.append("")

        # State updates
        if by_category['state']:
            notification_parts.append("## 📍 State Updates")
            for update in by_category['state']:
                notification_parts.append(f"- **{update['file_name']}**")
                notification_parts.append(f"  - Updated at: {update['updated_at']}")
            notification_parts.append("")

        # Chapter updates
        if by_category['chapter']:
            notification_parts.append("## 📚 Chapter Updates")
            for update in by_category['chapter']:
                notification_parts.append(f"- **{update['file_name']}**")
                notification_parts.append(f"  - Updated at: {update['updated_at']}")
            notification_parts.append("")

        # Other updates
        if by_category['other']:
            notification_parts.append("## 📄 Other Updates")
            for update in by_category['other']:
                notification_parts.append(f"- **{update['file_name']}**")
                notification_parts.append(f"  - Updated at: {update['updated_at']}")
            notification_parts.append("")

        notification_parts.extend([
            "**Action Required:**",
            "1. Carefully REREAD all updated files above",
            "2. Acknowledge any new information or changes",
            "3. Integrate updates into your understanding of the story",
            "",
            "<!-- ======================================== -->"
        ])

        return '\n'.join(notification_parts)

    def track_all_rp_files(self) -> List[Path]:
        """Get list of all trackable RP files"""
        files = []

        # Track characters
        chars_dir = self.rp_dir / "characters"
        if chars_dir.exists():
            files.extend(chars_dir.glob("*.md"))

        # Track entities
        entities_dir = self.rp_dir / "entities"
        if entities_dir.exists():
            files.extend(entities_dir.glob("*.md"))

        # Track state files
        state_dir = self.rp_dir / "state"
        if state_dir.exists():
            files.extend([
                state_dir / "current_state.md",
                state_dir / "story_arc.md"
            ])

        # Track core files
        files.extend([
            self.rp_dir / "AUTHOR'S_NOTES.md",
            self.rp_dir / "STORY_GENOME.md",
            self.rp_dir / "SCENE_NOTES.md"
        ])

        # Track chapters (recent ones)
        chapters_dir = self.rp_dir / "chapters"
        if chapters_dir.exists():
            chapter_files = sorted(
                chapters_dir.glob("*.txt"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:5]  # Track only 5 most recent chapters
            files.extend(chapter_files)

        return [f for f in files if f.exists()]


def format_file_update_alert(file_name: str, file_type: str = "file") -> str:
    """Quick helper to format a file update alert for immediate injection

    Args:
        file_name: Name of file that was updated
        file_type: Type of file (entity, arc, state, etc.)

    Returns:
        Formatted alert string
    """
    return f"""
<!-- ⚠️ FILE UPDATE ALERT ⚠️ -->
**{file_name}** has been UPDATED (just now via auto-generation)
- This {file_type} contains NEW information you haven't seen before
- Carefully REREAD the entire file
- Acknowledge the changes in your response
<!-- ======================== -->
"""
