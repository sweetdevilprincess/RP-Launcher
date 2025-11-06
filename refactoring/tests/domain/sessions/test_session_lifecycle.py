"""Comprehensive lifecycle tests for session management.

Tests the full workflow: create → append → checkpoint → branch → archive
"""

import tempfile
from pathlib import Path

import pytest
from refactoring.src.domain.sessions import (
    SessionMessage,
    SessionRepository,
    SessionWriteBack,
)
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


@pytest.fixture
def write_back(repository, logger):
    """Create SessionWriteBack for testing."""
    return SessionWriteBack(repository=repository, logger=logger)


class TestSessionLifecycle:
    """Test full session lifecycle."""

    def test_create_session_end_to_end(self, repository, write_back):
        """Test complete session creation workflow."""
        # Create initial session
        session = repository.ensure_active_session(rp_name="Test RP", chapter=1)

        assert session.session_id == "main"
        assert session.current_response == 0
        assert len(session.messages) == 0
        assert session.rp_metadata["rp_name"] == "Test RP"

        # Append first message
        response_num = write_back.append_message(
            user_message="Hello, world!",
            assistant_response="Greetings!",
            chapter=1,
            agent_data_immediate={"entities": ["Alice", "Bob"]},
        )

        assert response_num == 1

        # Load and verify
        session = repository.load_active_session()
        assert session.current_response == 1
        assert len(session.messages) == 1
        assert session.messages[0].user_message == "Hello, world!"
        assert session.messages[0].agent_data_immediate["entities"] == ["Alice", "Bob"]

    def test_append_messages_with_write_back(self, write_back, repository):
        """Test appending multiple messages."""
        # Ensure session exists
        repository.ensure_active_session()

        # Append 3 messages
        for i in range(1, 4):
            response_num = write_back.append_message(
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
                chapter=1,
            )
            assert response_num == i

        # Verify
        session = repository.load_active_session()
        assert session.current_response == 3
        assert len(session.messages) == 3

        for i, msg in enumerate(session.messages, start=1):
            assert msg.response_num == i
            assert msg.user_message == f"Message {i}"

    def test_checkpoint_and_restore(self, repository):
        """Test checkpoint creation and restoration."""
        # Create session with messages
        session = repository.ensure_active_session()
        for i in range(1, 4):
            msg = SessionMessage(
                response_num=i,
                timestamp="2025-01-01T00:00:00Z",
                chapter=1,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
            )
            repository.append_message(msg)

        # Create checkpoint at message 2
        checkpoint = repository.create_checkpoint(
            session_id="main",
            message_index=2,
            description="Test checkpoint",
        )

        assert checkpoint.message_index == 2
        assert checkpoint.description == "Test checkpoint"

        # Verify checkpoint was saved
        checkpoints = repository.list_checkpoints("main")
        assert len(checkpoints) == 1
        assert checkpoints[0].checkpoint_id == checkpoint.checkpoint_id

        # Restore checkpoint (creates branch)
        branch = repository.restore_checkpoint("main", checkpoint.checkpoint_id)

        assert branch.session_type == "branch"
        assert branch.parent_session == "main"
        assert branch.branch_point == 2
        assert len(branch.messages) == 2

    def test_branch_from_checkpoint(self, repository):
        """Test branching workflow from checkpoint."""
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

        # Create checkpoint at message 3
        checkpoint = repository.create_checkpoint(
            session_id="main",
            message_index=3,
            description="Branch point",
        )

        # Create branch from checkpoint
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="alternate",
            branch_point=3,
            description="Alternate timeline",
        )

        # Verify branch
        assert branch.session_id == "main_branch_alternate"
        assert branch.parent_session == "main"
        assert branch.branch_point == 3
        assert len(branch.messages) == 3
        assert branch.description == "Alternate timeline"

    def test_archive_and_unarchive(self, repository, paths):
        """Test session archival workflow."""
        # Create a non-main session
        repository.ensure_active_session()
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="test_archive",
            branch_point=0,
        )

        branch_id = branch.session_id

        # Archive the branch
        repository.archive_session(branch_id)

        # Verify it's archived
        assert not (paths.sessions_dir / f"session_{branch_id}.json").exists()
        assert (paths.session_archived_dir / f"session_{branch_id}.json").exists()

        # List archived sessions
        archived = repository.list_sessions(archived=True)
        assert any(s.session_id == branch_id for s in archived)

        # Unarchive
        repository.unarchive_session(branch_id)

        # Verify it's back
        assert (paths.sessions_dir / f"session_{branch_id}.json").exists()
        assert not (paths.session_archived_dir / f"session_{branch_id}.json").exists()

    def test_full_lifecycle_create_checkpoint_branch_archive(self, repository, write_back):
        """Test complete lifecycle workflow."""
        # 1. Create session
        repository.ensure_active_session(rp_name="Full Test", chapter=1)

        # 2. Add messages
        for i in range(1, 6):
            write_back.append_message(
                user_message=f"User {i}",
                assistant_response=f"Assistant {i}",
                chapter=1,
            )

        # 3. Create checkpoint
        checkpoint = repository.create_checkpoint(
            session_id="main",
            message_index=3,
            description="Mid-point checkpoint",
        )

        # 4. Create branch
        branch = repository.create_branch(
            source_session_id="main",
            branch_name="test_branch",
            branch_point=3,
        )

        # 5. Archive branch
        repository.archive_session(branch.session_id)

        # 6. Verify final state
        main_session = repository.load_active_session()
        assert len(main_session.messages) == 5
        assert len(main_session.checkpoints) == 1

        archived = repository.list_sessions(archived=True)
        assert any(s.session_id == branch.session_id for s in archived)

    def test_update_message_content(self, repository, write_back):
        """Test updating message content after creation."""
        # Create session and add message
        repository.ensure_active_session()
        write_back.append_message(
            user_message="Original user message",
            assistant_response="Original assistant response",
            chapter=1,
        )

        # Update the message
        write_back.update_message_content(
            response_num=1,
            updated_user_message="Updated user message",
            updated_assistant_response="Updated assistant response",
        )

        # Verify
        session = repository.load_active_session()
        msg = session.messages[0]
        assert msg.user_message == "Updated user message"
        assert msg.assistant_response == "Updated assistant response"

    def test_add_agent_data_after_creation(self, repository, write_back):
        """Test adding agent data to existing message."""
        # Create session and add message
        repository.ensure_active_session()
        write_back.append_message(
            user_message="Test message",
            assistant_response="Test response",
            chapter=1,
        )

        # Add background agent data
        write_back.add_agent_data(
            response_num=1,
            background_data={"scene_type": "action", "pacing": "fast"},
        )

        # Add immediate agent data
        write_back.add_agent_data(
            response_num=1,
            immediate_data={"entities": ["Alice", "Bob"]},
        )

        # Verify
        session = repository.load_active_session()
        msg = session.messages[0]
        assert msg.agent_data_background["scene_type"] == "action"
        assert msg.agent_data_immediate["entities"] == ["Alice", "Bob"]


class TestSessionMetadata:
    """Test session metadata operations."""

    def test_list_sessions_metadata(self, repository):
        """Test listing sessions with metadata only."""
        # Create main session
        repository.ensure_active_session(rp_name="Main RP")

        # Create branches
        repository.create_branch(
            source_session_id="main",
            branch_name="branch1",
            branch_point=0,
        )
        repository.create_branch(
            source_session_id="main",
            branch_name="branch2",
            branch_point=0,
        )

        # List active sessions
        active = repository.list_sessions(archived=False, include_branches=False)
        assert len(active) >= 1  # At least main

        # List with branches
        all_sessions = repository.list_sessions(archived=False, include_branches=True)
        assert len(all_sessions) >= 3  # main + 2 branches

    def test_get_session_metadata(self, repository):
        """Test retrieving session metadata."""
        # Create session
        repository.ensure_active_session(rp_name="Test RP", chapter=2)

        # Add messages
        for i in range(3):
            msg = SessionMessage(
                response_num=i + 1,
                timestamp="2025-01-01T00:00:00Z",
                chapter=2,
                user_message=f"Msg {i}",
                assistant_response=f"Resp {i}",
            )
            repository.append_message(msg)

        # Get metadata
        metadata = repository.get_session_metadata("main")

        assert metadata is not None
        assert metadata.session_id == "main"
        assert metadata.message_count == 3
        assert "chapter-2" in metadata.tags

    def test_session_exists_check(self, repository):
        """Test session existence checking."""
        # Create session
        repository.ensure_active_session()

        assert repository.session_exists("main")
        assert not repository.session_exists("nonexistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
