"""Unit tests for FrequencyTracker.

Tests trigger frequency tracking and auto-escalation with:
- Trigger history tracking and persistence
- Rolling window management
- Escalation threshold logic
- History file loading/saving
- Error handling for corrupt data
"""

import tempfile
from pathlib import Path

import pytest
from refactoring.src.automation.triggers.frequency_tracker import FrequencyTracker


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def history_file(temp_dir):
    """Create temporary history file path."""
    return temp_dir / "trigger_history.json"


@pytest.fixture
def tracker(history_file):
    """Create FrequencyTracker with default settings."""
    return FrequencyTracker(history_file=history_file, window_size=10, escalation_threshold=3)


class TestBasicTracking:
    """Test basic trigger tracking functionality."""

    def test_first_trigger_no_escalation(self, tracker, temp_dir):
        """Test first trigger doesn't escalate (below threshold)."""
        alice_path = temp_dir / "Alice.md"

        escalated = tracker.track_and_escalate([alice_path])

        # No escalation on first trigger (threshold is 3)
        assert len(escalated) == 0

    def test_empty_triggered_files_returns_empty(self, tracker):
        """Test empty triggered files list returns empty."""
        escalated = tracker.track_and_escalate([])

        assert len(escalated) == 0

    def test_multiple_files_single_trigger(self, tracker, temp_dir):
        """Test tracking multiple files in single trigger."""
        alice_path = temp_dir / "Alice.md"
        bob_path = temp_dir / "Bob.md"

        escalated = tracker.track_and_escalate([alice_path, bob_path])

        # No escalation yet (first trigger)
        assert len(escalated) == 0

        # Verify both files tracked
        counts = tracker.get_trigger_counts()
        assert counts[str(alice_path)] == 1
        assert counts[str(bob_path)] == 1

    def test_successive_triggers_increment_count(self, tracker, temp_dir):
        """Test successive triggers increment count."""
        alice_path = temp_dir / "Alice.md"

        # Trigger once
        tracker.track_and_escalate([alice_path])
        counts1 = tracker.get_trigger_counts()
        assert counts1[str(alice_path)] == 1

        # Trigger again
        tracker.track_and_escalate([alice_path])
        counts2 = tracker.get_trigger_counts()
        assert counts2[str(alice_path)] == 2

        # Trigger third time
        tracker.track_and_escalate([alice_path])
        counts3 = tracker.get_trigger_counts()
        assert counts3[str(alice_path)] == 3


class TestEscalationLogic:
    """Test escalation threshold logic."""

    def test_escalate_at_threshold(self, tracker, temp_dir):
        """Test file is escalated when threshold is reached."""
        alice_path = temp_dir / "Alice.md"

        # Trigger 3 times (threshold is 3)
        tracker.track_and_escalate([alice_path])
        tracker.track_and_escalate([alice_path])
        escalated = tracker.track_and_escalate([alice_path])

        # Should escalate on 3rd trigger
        assert len(escalated) == 1
        assert escalated[0] == alice_path

    def test_no_escalate_below_threshold(self, tracker, temp_dir):
        """Test file is not escalated below threshold."""
        alice_path = temp_dir / "Alice.md"

        # Trigger only 2 times (threshold is 3)
        tracker.track_and_escalate([alice_path])
        escalated = tracker.track_and_escalate([alice_path])

        # Should not escalate (2 < 3)
        assert len(escalated) == 0

    def test_escalate_above_threshold(self, tracker, temp_dir):
        """Test file remains escalated above threshold."""
        alice_path = temp_dir / "Alice.md"

        # Trigger 5 times (well above threshold)
        for _ in range(5):
            tracker.track_and_escalate([alice_path])

        escalated = tracker.track_and_escalate([alice_path])

        # Should still be escalated
        assert alice_path in escalated

    def test_multiple_files_different_thresholds(self, tracker, temp_dir):
        """Test multiple files with different trigger counts."""
        alice_path = temp_dir / "Alice.md"
        bob_path = temp_dir / "Bob.md"
        charlie_path = temp_dir / "Charlie.md"

        # Alice triggered 5 times (above threshold)
        for _ in range(5):
            tracker.track_and_escalate([alice_path])

        # Bob triggered 3 times (at threshold)
        for _ in range(3):
            tracker.track_and_escalate([bob_path])

        # Charlie triggered 2 times (below threshold)
        for _ in range(2):
            escalated = tracker.track_and_escalate([charlie_path])

        # Only Alice and Bob should be escalated
        assert len(escalated) == 2
        escalated_set = set(escalated)
        assert alice_path in escalated_set
        assert bob_path in escalated_set
        assert charlie_path not in escalated_set

    def test_custom_escalation_threshold(self, history_file, temp_dir):
        """Test custom escalation threshold configuration."""
        tracker_custom = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=5
        )
        alice_path = temp_dir / "Alice.md"

        # Trigger 4 times (below custom threshold of 5)
        for _ in range(4):
            escalated = tracker_custom.track_and_escalate([alice_path])

        # Should not escalate (4 < 5)
        assert len(escalated) == 0

        # Trigger 5th time
        escalated = tracker_custom.track_and_escalate([alice_path])

        # Should escalate now (5 >= 5)
        assert len(escalated) == 1
        assert escalated[0] == alice_path


class TestWindowManagement:
    """Test rolling window management."""

    def test_window_size_respected(self, history_file, temp_dir):
        """Test only window_size responses are kept."""
        tracker_small = FrequencyTracker(
            history_file=history_file, window_size=3, escalation_threshold=2
        )
        alice_path = temp_dir / "Alice.md"
        bob_path = temp_dir / "Bob.md"

        # Trigger Alice 3 times
        tracker_small.track_and_escalate([alice_path])
        tracker_small.track_and_escalate([alice_path])
        tracker_small.track_and_escalate([alice_path])

        # Now trigger Bob 2 times (window keeps last 3 responses: Alice, Bob, Bob)
        tracker_small.track_and_escalate([bob_path])
        tracker_small.track_and_escalate([bob_path])

        # Check counts
        counts = tracker_small.get_trigger_counts()

        # Alice should have 1 (two oldest dropped from window)
        assert counts[str(alice_path)] == 1

        # Bob should have 2
        assert counts[str(bob_path)] == 2

    def test_old_triggers_expire_from_window(self, history_file, temp_dir):
        """Test old triggers are removed when window is full."""
        tracker_small = FrequencyTracker(
            history_file=history_file, window_size=2, escalation_threshold=2
        )
        alice_path = temp_dir / "Alice.md"
        bob_path = temp_dir / "Bob.md"

        # Fill window with Alice
        tracker_small.track_and_escalate([alice_path])
        tracker_small.track_and_escalate([alice_path])

        # Alice count should be 2
        counts1 = tracker_small.get_trigger_counts()
        assert counts1[str(alice_path)] == 2

        # Add Bob triggers (pushes Alice out of window)
        tracker_small.track_and_escalate([bob_path])
        tracker_small.track_and_escalate([bob_path])

        # Alice should be gone, Bob should be 2
        counts2 = tracker_small.get_trigger_counts()
        assert str(alice_path) not in counts2
        assert counts2[str(bob_path)] == 2

    def test_window_tracks_responses_not_files(self, history_file, temp_dir):
        """Test window tracks number of responses, not number of files."""
        tracker_small = FrequencyTracker(
            history_file=history_file, window_size=3, escalation_threshold=2
        )
        alice_path = temp_dir / "Alice.md"
        bob_path = temp_dir / "Bob.md"

        # Response 1: Both Alice and Bob
        tracker_small.track_and_escalate([alice_path, bob_path])

        # Response 2: Both again
        tracker_small.track_and_escalate([alice_path, bob_path])

        # Response 3: Only Alice
        tracker_small.track_and_escalate([alice_path])

        # Response 4: Only Bob (should drop response 1)
        tracker_small.track_and_escalate([bob_path])

        counts = tracker_small.get_trigger_counts()

        # Alice: responses 2, 3 = 2 triggers
        assert counts[str(alice_path)] == 2

        # Bob: responses 2, 4 = 2 triggers
        assert counts[str(bob_path)] == 2


class TestHistoryPersistence:
    """Test history file loading and saving."""

    def test_history_persists_across_instances(self, history_file, temp_dir):
        """Test history persists when creating new tracker instance."""
        alice_path = temp_dir / "Alice.md"

        # Create first tracker and add some triggers
        tracker1 = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=3
        )
        tracker1.track_and_escalate([alice_path])
        tracker1.track_and_escalate([alice_path])

        # Create second tracker with same history file
        tracker2 = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=3
        )

        # History should be loaded
        counts = tracker2.get_trigger_counts()
        assert counts[str(alice_path)] == 2

    def test_missing_history_file_creates_new(self, history_file, temp_dir):
        """Test tracker works when history file doesn't exist."""
        tracker = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=3
        )
        alice_path = temp_dir / "Alice.md"

        # Should work fine with no existing history
        escalated = tracker.track_and_escalate([alice_path])

        assert len(escalated) == 0
        assert history_file.exists()

    def test_corrupt_history_file_starts_fresh(self, history_file, temp_dir):
        """Test corrupt history file is handled gracefully."""
        # Write corrupt JSON to history file
        history_file.write_text("{ corrupt json content }", encoding="utf-8")

        tracker = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=3
        )
        alice_path = temp_dir / "Alice.md"

        # Should start with fresh history
        escalated = tracker.track_and_escalate([alice_path])

        assert len(escalated) == 0

        # Should have 1 trigger now
        counts = tracker.get_trigger_counts()
        assert counts[str(alice_path)] == 1

    def test_invalid_history_structure_starts_fresh(self, history_file, temp_dir):
        """Test invalid history structure is handled gracefully."""
        # Write valid JSON but wrong structure
        history_file.write_text('{"wrong_key": []}', encoding="utf-8")

        tracker = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=3
        )
        alice_path = temp_dir / "Alice.md"

        # Should start with fresh history
        escalated = tracker.track_and_escalate([alice_path])

        assert len(escalated) == 0
        counts = tracker.get_trigger_counts()
        assert counts[str(alice_path)] == 1


class TestTriggerCounts:
    """Test get_trigger_counts functionality."""

    def test_empty_history_returns_empty_counts(self, tracker):
        """Test empty history returns empty counts dict."""
        counts = tracker.get_trigger_counts()

        assert counts == {}

    def test_counts_reflect_current_window(self, tracker, temp_dir):
        """Test counts reflect triggers in current window."""
        alice_path = temp_dir / "Alice.md"
        bob_path = temp_dir / "Bob.md"

        tracker.track_and_escalate([alice_path])
        tracker.track_and_escalate([alice_path, bob_path])
        tracker.track_and_escalate([bob_path])

        counts = tracker.get_trigger_counts()

        assert counts[str(alice_path)] == 2
        assert counts[str(bob_path)] == 2

    def test_counts_update_after_each_trigger(self, tracker, temp_dir):
        """Test counts update after each trigger."""
        alice_path = temp_dir / "Alice.md"

        # First trigger
        tracker.track_and_escalate([alice_path])
        counts1 = tracker.get_trigger_counts()
        assert counts1[str(alice_path)] == 1

        # Second trigger
        tracker.track_and_escalate([alice_path])
        counts2 = tracker.get_trigger_counts()
        assert counts2[str(alice_path)] == 2

        # Third trigger
        tracker.track_and_escalate([alice_path])
        counts3 = tracker.get_trigger_counts()
        assert counts3[str(alice_path)] == 3


class TestClearHistory:
    """Test clear_history functionality."""

    def test_clear_history_removes_all_triggers(self, tracker, temp_dir):
        """Test clear_history removes all triggers."""
        alice_path = temp_dir / "Alice.md"
        bob_path = temp_dir / "Bob.md"

        # Add some triggers
        tracker.track_and_escalate([alice_path, bob_path])
        tracker.track_and_escalate([alice_path])

        # Verify triggers exist
        counts_before = tracker.get_trigger_counts()
        assert len(counts_before) > 0

        # Clear history
        tracker.clear_history()

        # Verify history is empty
        counts_after = tracker.get_trigger_counts()
        assert counts_after == {}

    def test_clear_history_persists(self, history_file, temp_dir):
        """Test cleared history persists across instances."""
        alice_path = temp_dir / "Alice.md"

        # Create tracker and add triggers
        tracker1 = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=3
        )
        tracker1.track_and_escalate([alice_path])
        tracker1.clear_history()

        # Create new tracker with same file
        tracker2 = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=3
        )

        # Should have empty history
        counts = tracker2.get_trigger_counts()
        assert counts == {}

    def test_tracking_works_after_clear(self, tracker, temp_dir):
        """Test tracking works normally after clear."""
        alice_path = temp_dir / "Alice.md"

        # Add and clear
        tracker.track_and_escalate([alice_path])
        tracker.clear_history()

        # Add new triggers
        tracker.track_and_escalate([alice_path])
        tracker.track_and_escalate([alice_path])

        # Should count from clear point
        counts = tracker.get_trigger_counts()
        assert counts[str(alice_path)] == 2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_window_size(self, history_file, temp_dir):
        """Test tracker with window_size=0 (edge case)."""
        tracker_zero = FrequencyTracker(
            history_file=history_file, window_size=0, escalation_threshold=1
        )
        alice_path = temp_dir / "Alice.md"

        tracker_zero.track_and_escalate([alice_path])

        # Due to Python slicing behavior, history[-0:] returns all items
        # So window_size=0 actually keeps all history (edge case behavior)
        counts = tracker_zero.get_trigger_counts()
        assert counts[str(alice_path)] == 1

    def test_threshold_one(self, history_file, temp_dir):
        """Test tracker with escalation_threshold=1."""
        tracker_one = FrequencyTracker(
            history_file=history_file, window_size=10, escalation_threshold=1
        )
        alice_path = temp_dir / "Alice.md"

        # First trigger should escalate
        escalated = tracker_one.track_and_escalate([alice_path])

        assert len(escalated) == 1
        assert escalated[0] == alice_path

    def test_very_large_window(self, history_file, temp_dir):
        """Test tracker with very large window size."""
        tracker_large = FrequencyTracker(
            history_file=history_file, window_size=1000, escalation_threshold=3
        )
        alice_path = temp_dir / "Alice.md"

        # Add many triggers
        for _ in range(100):
            tracker_large.track_and_escalate([alice_path])

        # All should be retained
        counts = tracker_large.get_trigger_counts()
        assert counts[str(alice_path)] == 100

    def test_same_file_multiple_times_in_response(self, tracker, temp_dir):
        """Test same file triggered multiple times in single response."""
        alice_path = temp_dir / "Alice.md"

        # Trigger with same file twice in one response
        tracker.track_and_escalate([alice_path, alice_path])

        # Should count as 2 (once per occurrence)
        counts = tracker.get_trigger_counts()
        assert counts[str(alice_path)] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
