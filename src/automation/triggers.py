#!/usr/bin/env python3
"""
Triggers Module

Handles:
- TIER_3 trigger identification (conditional file loading)
- Trigger frequency tracking
- Auto-escalation of frequently triggered files to TIER_2
"""

import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from src.trigger_system.trigger_system import TriggerMatcher
from src.automation.core import log_to_file
from src.fs_write_queue import get_write_queue


# Get write queue instance
_write_queue = get_write_queue()


class TriggerManager:
    """Manages trigger identification and tracking"""

    def __init__(self, rp_dir: Path, log_file: Path, config: Optional[dict] = None):
        """Initialize trigger manager

        Args:
            rp_dir: RP directory path
            log_file: Path to log file
            config: Optional configuration dict
        """
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.config = config or {}

        # Initialize trigger matcher
        self.matcher = self._create_trigger_matcher()

    def _create_trigger_matcher(self) -> TriggerMatcher:
        """Create configured TriggerMatcher instance

        Returns:
            Configured TriggerMatcher
        """
        # Build trigger system configuration
        trigger_config = self.config.get('trigger_system', {})

        # Default configuration: keyword + regex enabled, semantic optional
        full_config = {
            'trigger_system': {
                'keyword_matching': trigger_config.get('keyword_matching', {
                    'enabled': True,
                    'case_sensitive': False,
                    'use_word_boundaries': True
                }),
                'regex_matching': trigger_config.get('regex_matching', {
                    'enabled': True,
                    'max_patterns_per_file': 10
                }),
                'semantic_matching': trigger_config.get('semantic_matching', {
                    'enabled': False,  # Optional, requires sentence-transformers
                    'model': 'all-MiniLM-L6-v2',
                    'similarity_threshold': 0.7
                })
            }
        }

        log_to_file(self.log_file, "--- Using Enhanced Trigger System ---")
        log_to_file(self.log_file,
                    f"Keyword: {full_config['trigger_system']['keyword_matching']['enabled']}, "
                    f"Regex: {full_config['trigger_system']['regex_matching']['enabled']}, "
                    f"Semantic: {full_config['trigger_system']['semantic_matching']['enabled']}")

        return TriggerMatcher(full_config)

    def identify_triggers(self, message: str) -> Tuple[List[Path], List[str]]:
        """Identify conditional files to load based on trigger words

        Args:
            message: User message to analyze

        Returns:
            Tuple of (files_to_load, entity_names_loaded)
        """
        files_to_load = []
        entity_names = []

        try:
            # Find triggered files
            matches = self.matcher.find_triggered_files(
                message,
                self.rp_dir,
                log_callback=lambda msg: log_to_file(self.log_file, msg)
            )

            # Convert matches to file paths and entity names
            for match in matches:
                files_to_load.append(match.file_path)
                entity_names.append(match.entity_name)

                # Log match details
                if match.trigger_type == 'semantic':
                    log_to_file(self.log_file,
                        f"TRIGGER: {match.entity_name} ({match.trigger_type}, "
                        f"pattern: '{match.matched_pattern}', confidence: {match.confidence:.3f})")
                else:
                    log_to_file(self.log_file,
                        f"TRIGGER: {match.entity_name} ({match.trigger_type}, "
                        f"pattern: '{match.matched_pattern}')")

            if files_to_load:
                log_to_file(self.log_file, f"Conditional files loaded: {len(files_to_load)}")

        except Exception as e:
            log_to_file(self.log_file, f"ERROR in enhanced trigger system: {e}")
            log_to_file(self.log_file, "Falling back to no triggers")
            import traceback
            log_to_file(self.log_file, traceback.format_exc())

        return files_to_load, entity_names

    def track_trigger_history(self, triggered_files: List[Path], history_file: Path) -> List[Path]:
        """Track TIER_3 trigger frequency and identify escalated files

        Files triggered 3+ times in last 10 responses get escalated to TIER_2

        Args:
            triggered_files: List of files triggered in current response
            history_file: Path to trigger_history.json

        Returns:
            List of files to escalate to TIER_2
        """
        if not triggered_files:
            return []

        # Load or initialize trigger history
        if history_file.exists():
            try:
                history = json.loads(history_file.read_text(encoding='utf-8'))
            except Exception:
                history = {"trigger_history": []}
        else:
            history = {"trigger_history": []}

        # Add current triggers to history
        current_triggers = [str(f) for f in triggered_files]
        history["trigger_history"].append(current_triggers)

        # Keep only last 10 responses
        history["trigger_history"] = history["trigger_history"][-10:]

        # Save updated history (queued)
        try:
            _write_queue.write_json(history_file, history, encoding='utf-8', indent=2)
        except Exception as e:
            log_to_file(self.log_file, f"WARNING: Could not queue trigger history: {e}")

        # Find files that should be escalated (3+ triggers in last 10)
        trigger_counts: Dict[str, int] = {}
        for response_triggers in history["trigger_history"]:
            for file_path in response_triggers:
                trigger_counts[file_path] = trigger_counts.get(file_path, 0) + 1

        escalated = []
        for file_path, count in trigger_counts.items():
            if count >= 3:
                escalated.append(Path(file_path))
                log_to_file(self.log_file,
                    f"TIER_3 ESCALATION: {Path(file_path).name} triggered {count}/10 times")

        return escalated


# Convenience functions for backward compatibility
def identify_triggers(message: str, rp_dir: Path, log_file: Path, config: dict = None) -> Tuple[List, List]:
    """Identify conditional files to load (convenience function)

    Args:
        message: User message
        rp_dir: RP directory path
        log_file: Path to log file
        config: Optional configuration dict

    Returns:
        Tuple of (files_to_load, entity_names_loaded)
    """
    manager = TriggerManager(rp_dir, log_file, config)
    return manager.identify_triggers(message)


def track_tier3_triggers(triggered_files: list, tracker_file: Path, log_file: Path) -> list:
    """Track TIER_3 trigger frequency (convenience function)

    Args:
        triggered_files: List of triggered files
        tracker_file: Path to trigger_history.json
        log_file: Path to log file

    Returns:
        List of files to escalate to TIER_2
    """
    # Get rp_dir from tracker_file path
    rp_dir = tracker_file.parent.parent  # Go up from state/ to RP root
    manager = TriggerManager(rp_dir, log_file)
    return manager.track_trigger_history(triggered_files, tracker_file)
