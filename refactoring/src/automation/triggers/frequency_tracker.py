"""Frequency tracker for trigger auto-escalation.

Tracks how often files are triggered and identifies files that should
be escalated from TIER_3 (conditional) to TIER_2 (always loaded).

Refactored from src/automation/triggers.py
"""

from __future__ import annotations

from pathlib import Path

from ...infrastructure.filesystem.json_store import JsonStore
from ...shared.interfaces import LoggingService
from ...shared.logging import get_logger


class FrequencyTracker:
    """Tracks trigger frequency and handles auto-escalation.

    Maintains a rolling window of recent trigger history and identifies
    files that are triggered frequently enough to warrant escalation to
    a higher tier (always loaded instead of conditionally loaded).

    Configuration:
        window_size: Number of recent responses to track (default: 10)
        escalation_threshold: Minimum triggers to escalate (default: 3)

    Example:
        >>> tracker = FrequencyTracker(history_file, window_size=10, escalation_threshold=3)
        >>> escalated = tracker.track_and_escalate([Path("chars/Alice.md"), Path("chars/Bob.md")])
        >>> if escalated:
        ...     print(f"Escalate {len(escalated)} files to TIER_2")
    """

    def __init__(
        self,
        history_file: Path,
        *,
        window_size: int = 10,
        escalation_threshold: int = 3,
        logger: LoggingService | None = None,
    ) -> None:
        """Initialize frequency tracker.

        Args:
            history_file: Path to trigger history JSON file
            window_size: Number of recent responses to track
            escalation_threshold: Minimum triggers in window to escalate
            logger: Optional logger (will create default if not provided)
        """
        self._history_file = history_file
        self._window_size = window_size
        self._escalation_threshold = escalation_threshold
        self._logger = logger or get_logger(__name__)

        # Create JsonStore with history file's parent as root
        self._json_store = JsonStore(
            root=history_file.parent,
            logger=self._logger,
        )
        # Use just the filename as relative path
        self._relative_path = Path(history_file.name)

    def track_and_escalate(self, triggered_files: list[Path]) -> list[Path]:
        """Track triggers and identify files to escalate.

        Args:
            triggered_files: List of files triggered in current response

        Returns:
            List of files that should be escalated to TIER_2
        """
        if not triggered_files:
            return []

        # Load or initialize history
        history = self._load_history()

        # Add current triggers to history
        current_triggers = [str(f) for f in triggered_files]
        history["trigger_history"].append(current_triggers)

        # Keep only last N responses
        history["trigger_history"] = history["trigger_history"][-self._window_size :]

        # Save updated history
        self._save_history(history)

        # Find files that should be escalated
        escalated = self._identify_escalations(history)

        if escalated:
            self._logger.info(
                "frequency_tracker.escalations_identified",
                context={
                    "escalated_count": len(escalated),
                    "escalated_files": [f.name for f in escalated],
                },
            )

        return escalated

    def get_trigger_counts(self) -> dict[str, int]:
        """Get current trigger counts for all files in the window.

        Returns:
            Dict mapping file paths to trigger counts
        """
        history = self._load_history()
        return self._calculate_counts(history)

    def clear_history(self) -> None:
        """Clear trigger history (useful for testing or reset)."""
        history = {"trigger_history": []}
        self._save_history(history)
        self._logger.info("frequency_tracker.history_cleared", context={})

    def _load_history(self) -> dict:
        """Load trigger history from file.

        Returns:
            History dict with trigger_history key
        """
        try:
            data = self._json_store.read(
                self._relative_path,
                default={"trigger_history": []},
            )
            if isinstance(data, dict) and "trigger_history" in data:
                return data
            self._logger.warning(
                "frequency_tracker.invalid_structure",
                context={"history_file": str(self._history_file)},
            )
            return {"trigger_history": []}
        except Exception as e:
            self._logger.warning(
                "frequency_tracker.load_error",
                context={
                    "history_file": str(self._history_file),
                    "error": str(e),
                },
            )
            return {"trigger_history": []}

    def _save_history(self, history: dict) -> None:
        """Save trigger history to file.

        Args:
            history: History dict to save
        """
        try:
            self._json_store.write(self._relative_path, history)
        except Exception as e:
            self._logger.error(
                "frequency_tracker.save_error",
                context={
                    "history_file": str(self._history_file),
                    "error": str(e),
                },
            )

    def _calculate_counts(self, history: dict) -> dict[str, int]:
        """Calculate trigger counts for all files in the window.

        Args:
            history: History dict with trigger_history

        Returns:
            Dict mapping file paths to counts
        """
        trigger_counts: dict[str, int] = {}

        for response_triggers in history.get("trigger_history", []):
            for file_path in response_triggers:
                trigger_counts[file_path] = trigger_counts.get(file_path, 0) + 1

        return trigger_counts

    def _identify_escalations(self, history: dict) -> list[Path]:
        """Identify files that should be escalated based on frequency.

        Args:
            history: History dict with trigger_history

        Returns:
            List of file paths to escalate
        """
        trigger_counts = self._calculate_counts(history)
        escalated: list[Path] = []

        for file_path_str, count in trigger_counts.items():
            if count >= self._escalation_threshold:
                file_path = Path(file_path_str)
                escalated.append(file_path)

                self._logger.debug(
                    "frequency_tracker.file_escalated",
                    context={
                        "file": file_path.name,
                        "count": count,
                        "window_size": self._window_size,
                        "threshold": self._escalation_threshold,
                    },
                )

        return escalated
