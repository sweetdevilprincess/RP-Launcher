"""Tests for session branching functionality.

Tests branching workflows, branch listing, and branch restoration.
"""

import tempfile
from pathlib import Path

import pytest
from refactoring.src.domain.sessions import SessionMessage, SessionRepository
from refactoring.src.infrastructure.filesystem import StatePaths
from refactoring.src.shared.interfaces import LoggingService


class MockLogger(LoggingService):
    """Mock logger for testing."""

    def debug(self, event: str, *, context: dict | None = None) -> None:
        pass

    def info(self, event: str, *, context: dict | None = None) -> None:
        pass

    def warning(self, event: str, *, context: dict | None = None) -> None:
        pass

    def error(self, event: str, *, context: dict | None = None) -> None:
        pass


@pytest.fixture
def temp_rp_dir():
    """Create temporary RP directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rp_dir = Path(tmpdir) / "test_rp"
        rp_dir.mkdir()
        yield rp_dir


@pytest.fixture
def paths(temp_rp_dir):
    """Create StatePaths for testing."""
    return StatePaths(rp_dir=temp_rp_dir)


@pytest.fixture
def logger():
    """Create mock logger."""
    return MockLogger()


@pytest.fixture
def repository(paths, logger):
    """Create SessionRepository for testing."""
    return SessionRepository(paths=paths, logger=logger)


class TestBranching:
    """Test session branching operations."""

    def test_create_branch_at_specific_point(self, repository):
        """Test creating branch at specific message index."""
        # Create session with 5 messages
        repository.ensure_active_session()
        for i in range(1, 6):
            msg = SessionMessage(
                response_num=i,
                timestamp="2025-01-01T00:00:00Z",
                chapter=1,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
            )
            repository.append_message(msg)

        # Create branch at message 3
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="test_branch",
            branch_point=3,
            description="Test branch at message 3",
        )

        assert branch.session_id == "main_branch_test_branch"
        assert branch.parent_session == "main"
        assert branch.branch_point == 3
        assert len(branch.messages) == 3
        assert branch.current_response == 3
        assert "branch-test_branch" in branch.tags

    def test_create_branch_at_latest(self, repository):
        """Test creating branch at latest message (default)."""
        # Create session with 3 messages
        repository.ensure_active_session()
        for i in range(1, 4):
            msg = SessionMessage(
                response_num=i,
                timestamp="2025-01-01T00:00:00Z",
                chapter=1,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
            )
            repository.append_message(msg)

        # Create branch (no branch_point = use latest)
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="latest_branch",
        )

        assert len(branch.messages) == 3
        assert branch.branch_point == 3

    def test_create_branch_from_empty_session(self, repository):
        """Test creating branch from empty session."""
        # Create empty session
        repository.ensure_active_session()

        # Create branch at message 0
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="empty_branch",
            branch_point=0,
        )

        assert len(branch.messages) == 0
        assert branch.branch_point == 0

    def test_list_branches_for_session(self, repository):
        """Test listing all branches of a session."""
        # Create session
        repository.ensure_active_session()

        # Create multiple branches
        repository.create_branch(source_session_id="main", branch_name="branch1", branch_point=0)
        repository.create_branch(source_session_id="main", branch_name="branch2", branch_point=0)
        repository.create_branch(source_session_id="main", branch_name="branch3", branch_point=0)

        # List branches
        branches = repository.list_branches(base_session_id="main")

        assert len(branches) == 3
        branch_names = {b.session_id for b in branches}
        assert "main_branch_branch1" in branch_names
        assert "main_branch_branch2" in branch_names
        assert "main_branch_branch3" in branch_names

    def test_list_all_branches(self, repository):
        """Test listing all branches regardless of parent."""
        # Create main session
        repository.ensure_active_session()

        # Create branches
        repository.create_branch(source_session_id="main", branch_name="branch1", branch_point=0)

        # Create another session (via branch) and branch from it
        branch1 = repository.create_branch(
            source_session_id="main", branch_name="branch2", branch_point=0
        )

        # List all branches (no filter)
        all_branches = repository.list_branches(base_session_id=None)

        assert len(all_branches) >= 2

    def test_branch_preserves_metadata(self, repository):
        """Test that branching preserves RP metadata."""
        # Create session with metadata
        repository.ensure_active_session(rp_name="Test RP", chapter=3)

        # Add message
        msg = SessionMessage(
            response_num=1,
            timestamp="2025-01-01T00:00:00Z",
            chapter=3,
            user_message="Test",
            assistant_response="Response",
        )
        repository.append_message(msg)

        # Create branch
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="metadata_test",
            branch_point=1,
        )

        # Verify metadata preserved
        assert branch.rp_metadata["rp_name"] == "Test RP"
        assert branch.rp_metadata["chapter"] == 3

    def test_branch_from_archived_session(self, repository):
        """Test creating branch from archived session."""
        # Create session
        repository.ensure_active_session()

        # Create a branch
        first_branch = repository.create_branch(
            source_session_id="main",
            branch_name="first",
            branch_point=0,
        )

        # Archive it
        repository.archive_session(first_branch.session_id)

        # Create branch from archived session
        second_branch = repository.create_branch(
            source_session_id=first_branch.session_id,
            branch_name="from_archived",
            branch_point=0,
        )

        assert second_branch.parent_session == first_branch.session_id

    def test_branch_invalid_branch_point(self, repository):
        """Test error handling for invalid branch point."""
        # Create session with 3 messages
        repository.ensure_active_session()
        for i in range(1, 4):
            msg = SessionMessage(
                response_num=i,
                timestamp="2025-01-01T00:00:00Z",
                chapter=1,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
            )
            repository.append_message(msg)

        # Try to branch at invalid point
        with pytest.raises(ValueError, match="Invalid branch_point"):
            repository.create_branch(
                source_session_id="main",
                branch_name="invalid",
                branch_point=10,  # Out of range
            )

    def test_branch_from_nonexistent_session(self, repository):
        """Test error handling when branching from non-existent session."""
        with pytest.raises(FileNotFoundError, match="not found"):
            repository.create_branch(
                source_session_id="nonexistent",
                branch_name="test",
                branch_point=0,
            )


class TestCheckpointRestoration:
    """Test checkpoint-based restoration (which creates branches)."""

    def test_restore_checkpoint_creates_branch(self, repository):
        """Test that checkpoint restoration creates a branch."""
        # Create session with messages
        repository.ensure_active_session()
        for i in range(1, 6):
            msg = SessionMessage(
                response_num=i,
                timestamp="2025-01-01T00:00:00Z",
                chapter=1,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
            )
            repository.append_message(msg)

        # Create checkpoint
        checkpoint = repository.create_checkpoint(
            session_id="main",
            message_index=3,
            description="Restore point",
        )

        # Restore checkpoint
        branch = repository.restore_checkpoint("main", checkpoint.checkpoint_id)

        # Verify branch created
        assert branch.session_type == "branch"
        assert branch.parent_session == "main"
        assert branch.branch_point == 3
        assert len(branch.messages) == 3
        assert "Restored from checkpoint" in branch.description

    def test_restore_nonexistent_checkpoint(self, repository):
        """Test error handling for non-existent checkpoint."""
        repository.ensure_active_session()

        with pytest.raises(ValueError, match="Checkpoint .* not found"):
            repository.restore_checkpoint("main", "nonexistent_cp_id")

    def test_multiple_restores_from_same_checkpoint(self, repository):
        """Test multiple restorations from the same checkpoint."""
        # Create session
        repository.ensure_active_session()
        for i in range(1, 4):
            msg = SessionMessage(
                response_num=i,
                timestamp="2025-01-01T00:00:00Z",
                chapter=1,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
            )
            repository.append_message(msg)

        # Create checkpoint
        checkpoint = repository.create_checkpoint(
            session_id="main",
            message_index=2,
            description="Multi-restore test",
        )

        # Restore twice (should create two separate branches)
        branch1 = repository.restore_checkpoint("main", checkpoint.checkpoint_id)
        branch2 = repository.restore_checkpoint("main", checkpoint.checkpoint_id)

        # Both should have same content but different IDs
        assert branch1.session_id != branch2.session_id
        assert len(branch1.messages) == len(branch2.messages) == 2


class TestBranchEdgeCases:
    """Test edge cases in branching."""

    def test_branch_naming_with_special_characters(self, repository):
        """Test branch naming with special characters."""
        repository.ensure_active_session()

        # Create branch with special name
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="test-branch_v2.5",
            branch_point=0,
        )

        assert branch.session_id == "main_branch_test-branch_v2.5"

    def test_branch_preserves_checkpoints(self, repository):
        """Test that branches preserve checkpoints from source."""
        # Create session with checkpoint
        repository.ensure_active_session()
        for i in range(1, 4):
            msg = SessionMessage(
                response_num=i,
                timestamp="2025-01-01T00:00:00Z",
                chapter=1,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
            )
            repository.append_message(msg)

        repository.create_checkpoint(
            session_id="main",
            message_index=2,
            description="Test checkpoint",
        )

        # Create branch
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="preserve_test",
            branch_point=3,
        )

        # Note: Currently branches copy messages but not checkpoints
        # This test documents current behavior
        # If we want to preserve checkpoints, this would need to be implemented
        assert len(branch.checkpoints) == 0  # Current behavior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
