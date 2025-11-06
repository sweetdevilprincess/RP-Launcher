"""
Unit Tests for SessionManager

Tests all core functionality of the session log system including:
- Session creation and loading
- Copy session operation
- Retry, branch, checkpoint commands
- Session switching
- Tag management
- Message appending
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.session_manager import SessionManager


# ==================== Fixtures ====================

@pytest.fixture
def temp_rp_dir():
    """Create temporary RP directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def session_manager(temp_rp_dir):
    """Create SessionManager instance with temp directory."""
    return SessionManager(temp_rp_dir)


@pytest.fixture
def sample_session():
    """Create sample session data for testing."""
    return {
        "session_id": "main",
        "session_type": "active",
        "parent_session": None,
        "branch_point": None,
        "created": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "current_response": 3,
        "tags": ["main-timeline"],
        "description": "",
        "rp_metadata": {
            "rp_name": "Test RP",
            "chapter": 1,
            "scene": "Test scene"
        },
        "messages": [
            {
                "response_num": 1,
                "timestamp": datetime.now().isoformat(),
                "chapter": 1,
                "user_message": "First message",
                "assistant_response": "First response",
                "agent_data_background": {},
                "agent_data_immediate": {},
                "model_info": {}
            },
            {
                "response_num": 2,
                "timestamp": datetime.now().isoformat(),
                "chapter": 1,
                "user_message": "Second message",
                "assistant_response": "Second response",
                "agent_data_background": {},
                "agent_data_immediate": {},
                "model_info": {}
            },
            {
                "response_num": 3,
                "timestamp": datetime.now().isoformat(),
                "chapter": 1,
                "user_message": "Third message",
                "assistant_response": "Third response",
                "agent_data_background": {},
                "agent_data_immediate": {},
                "model_info": {}
            }
        ]
    }


# ==================== Initialization Tests ====================

def test_session_manager_init(temp_rp_dir):
    """Test SessionManager initialization."""
    sm = SessionManager(temp_rp_dir)

    assert sm.rp_dir == temp_rp_dir
    assert sm.sessions_dir == temp_rp_dir / "sessions"
    assert sm.branches_dir == temp_rp_dir / "sessions" / "branches"
    assert sm.archived_dir == temp_rp_dir / "sessions" / "archived"

    # Directories should be created
    assert sm.sessions_dir.exists()
    assert sm.branches_dir.exists()
    assert sm.archived_dir.exists()


def test_session_manager_init_invalid_dir():
    """Test SessionManager with non-existent directory."""
    with pytest.raises(ValueError):
        SessionManager("/nonexistent/path")


# ==================== Session Loading & Saving Tests ====================

def test_save_and_load_session(session_manager, sample_session):
    """Test saving and loading a session."""
    # Save session
    session_manager.save_session(sample_session)

    # Load session
    loaded = session_manager.load_session()

    assert loaded["session_id"] == "main"
    assert loaded["current_response"] == 3
    assert len(loaded["messages"]) == 3
    assert loaded["messages"][0]["user_message"] == "First message"


def test_load_nonexistent_session(session_manager):
    """Test loading session that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        session_manager.load_session()


def test_validate_session_valid(session_manager, sample_session):
    """Test session validation with valid session."""
    # Should not raise
    session_manager._validate_session(sample_session)


def test_validate_session_missing_field(session_manager, sample_session):
    """Test session validation with missing required field."""
    del sample_session["session_id"]

    with pytest.raises(ValueError, match="missing required field"):
        session_manager._validate_session(sample_session)


def test_validate_session_invalid_messages(session_manager, sample_session):
    """Test session validation with invalid message structure."""
    sample_session["messages"][0].pop("user_message")

    with pytest.raises(ValueError, match="missing required field"):
        session_manager._validate_session(sample_session)


# ==================== Core copy_session() Tests ====================

def test_copy_session_basic(session_manager, sample_session):
    """Test basic copy_session operation."""
    # Save initial session
    session_manager.save_session(sample_session)

    # Copy session up to response 2
    branch_path = session_manager.copy_session(
        up_to_response=2,
        new_session_name="test_branch",
        session_type="branch",
        tags=["test"]
    )

    assert branch_path.exists()

    # Load copied session
    copied = session_manager.load_session(branch_path)

    assert copied["session_id"] == "test_branch"
    assert copied["session_type"] == "branch"
    assert copied["current_response"] == 2
    assert len(copied["messages"]) == 2
    assert copied["parent_session"] == "main"
    assert copied["branch_point"] == 2


def test_copy_session_with_tags(session_manager, sample_session):
    """Test copy_session with custom tags."""
    session_manager.save_session(sample_session)

    branch_path = session_manager.copy_session(
        up_to_response=2,
        new_session_name="tagged_branch",
        session_type="branch",
        tags=["romance", "chapter-1"]
    )

    copied = session_manager.load_session(branch_path)

    # Should have user tags plus auto-tags
    assert "romance" in copied["tags"]
    assert "chapter-1" in copied["tags"]
    assert "branch" in copied["tags"]
    assert any("date-" in tag for tag in copied["tags"])


def test_copy_session_invalid_response_num(session_manager, sample_session):
    """Test copy_session with invalid response number."""
    session_manager.save_session(sample_session)

    with pytest.raises(ValueError, match="Invalid response number"):
        session_manager.copy_session(
            up_to_response=10,  # More than current_response
            new_session_name="invalid",
            session_type="branch"
        )


def test_copy_session_duplicate_name(session_manager, sample_session):
    """Test copy_session with duplicate name."""
    session_manager.save_session(sample_session)

    # Create first branch
    session_manager.copy_session(
        up_to_response=2,
        new_session_name="duplicate",
        session_type="branch"
    )

    # Try to create another with same name
    with pytest.raises(ValueError, match="already exists"):
        session_manager.copy_session(
            up_to_response=2,
            new_session_name="duplicate",
            session_type="branch"
        )


# ==================== Retry Tests ====================

def test_retry_success(session_manager, sample_session):
    """Test successful retry operation."""
    session_manager.save_session(sample_session)

    # Retry
    archive_path = session_manager.retry()

    # Check active session
    active = session_manager.load_session()
    assert active["current_response"] == 2  # Reduced from 3
    assert len(active["messages"]) == 2

    # Check archive
    archived = session_manager.load_session(archive_path)
    assert archived["current_response"] == 3  # Original state
    assert len(archived["messages"]) == 3
    assert "retry" in archived["tags"]


def test_retry_with_tags(session_manager, sample_session):
    """Test retry with custom tags."""
    session_manager.save_session(sample_session)

    archive_path = session_manager.retry(tags=["rewrite", "better-dialogue"])

    archived = session_manager.load_session(archive_path)
    assert "rewrite" in archived["tags"]
    assert "better-dialogue" in archived["tags"]
    assert "retry" in archived["tags"]


def test_retry_empty_session(session_manager, sample_session):
    """Test retry on empty session."""
    sample_session["messages"] = []
    sample_session["current_response"] = 0
    session_manager.save_session(sample_session)

    with pytest.raises(ValueError, match="Session is empty"):
        session_manager.retry()


# ==================== Branch Tests ====================

def test_branch_from_current(session_manager, sample_session):
    """Test creating branch from current response."""
    session_manager.save_session(sample_session)

    branch_path = session_manager.branch(
        branch_name="romance_path",
        tags=["romance"]
    )

    branched = session_manager.load_session(branch_path)
    assert branched["session_id"] == "romance_path"
    assert branched["session_type"] == "branch"
    assert branched["current_response"] == 3  # Current
    assert "romance" in branched["tags"]


def test_branch_from_specific_response(session_manager, sample_session):
    """Test creating branch from specific response."""
    session_manager.save_session(sample_session)

    branch_path = session_manager.branch(
        branch_name="action_path",
        response_num=2
    )

    branched = session_manager.load_session(branch_path)
    assert branched["current_response"] == 2
    assert len(branched["messages"]) == 2


def test_branch_empty_name(session_manager, sample_session):
    """Test branch with empty name."""
    session_manager.save_session(sample_session)

    with pytest.raises(ValueError, match="cannot be empty"):
        session_manager.branch(branch_name="")


# ==================== Checkpoint Tests ====================

def test_checkpoint_success(session_manager, sample_session):
    """Test creating checkpoint."""
    session_manager.save_session(sample_session)

    checkpoint_path = session_manager.checkpoint(
        checkpoint_name="before_choice",
        tags=["important"]
    )

    checkpoint = session_manager.load_session(checkpoint_path)
    assert checkpoint["session_id"] == "before_choice"
    assert checkpoint["session_type"] == "checkpoint"
    assert checkpoint["current_response"] == 3
    assert "checkpoint" in checkpoint["tags"]
    assert "important" in checkpoint["tags"]


def test_checkpoint_empty_name(session_manager, sample_session):
    """Test checkpoint with empty name."""
    session_manager.save_session(sample_session)

    with pytest.raises(ValueError, match="cannot be empty"):
        session_manager.checkpoint(checkpoint_name="")


# ==================== Switch Tests ====================

def test_switch_to_branch(session_manager, sample_session):
    """Test switching to a branch."""
    session_manager.save_session(sample_session)

    # Create branch
    branch_path = session_manager.branch(
        branch_name="test_branch",
        response_num=2
    )

    # Switch to branch
    new_active = session_manager.switch("test_branch")

    # Active session should now be the branch
    active = session_manager.load_session()
    assert active["session_id"] == "test_branch"
    assert active["current_response"] == 2


def test_switch_creates_backup(session_manager, sample_session):
    """Test that switch creates backup of active session."""
    session_manager.save_session(sample_session)

    branch_path = session_manager.branch("test_branch")
    session_manager.switch("test_branch")

    # Check for backup
    backups = list(session_manager.archived_dir.glob("switch_backup_*.json"))
    assert len(backups) == 1


def test_switch_nonexistent_session(session_manager, sample_session):
    """Test switching to non-existent session."""
    session_manager.save_session(sample_session)

    with pytest.raises(FileNotFoundError, match="Session not found"):
        session_manager.switch("nonexistent")


# ==================== List Sessions Tests ====================

def test_list_sessions_empty(session_manager):
    """Test listing sessions when none exist."""
    sessions = session_manager.list_sessions()
    assert len(sessions) == 0


def test_list_sessions_with_active(session_manager, sample_session):
    """Test listing sessions with active session."""
    session_manager.save_session(sample_session)

    sessions = session_manager.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["type"] == "active"
    assert sessions[0]["name"] == "main"


def test_list_sessions_with_branches(session_manager, sample_session):
    """Test listing sessions with multiple branches."""
    session_manager.save_session(sample_session)

    session_manager.branch("branch1")
    session_manager.branch("branch2")

    sessions = session_manager.list_sessions()

    # Should have active + 2 branches
    assert len(sessions) == 3

    branches = [s for s in sessions if s["type"] == "branch"]
    assert len(branches) == 2


def test_list_sessions_with_tag_filter(session_manager, sample_session):
    """Test listing sessions with tag filter."""
    session_manager.save_session(sample_session)

    session_manager.branch("branch1", tags=["romance"])
    session_manager.branch("branch2", tags=["action"])

    # Filter by romance tag
    sessions = session_manager.list_sessions(tag_filter="romance")

    assert len(sessions) == 1
    assert sessions[0]["name"] == "branch1"


# ==================== Message Management Tests ====================

def test_append_message(session_manager, sample_session):
    """Test appending message to session."""
    session_manager.save_session(sample_session)

    # Append new message
    response_num = session_manager.append_message(
        user_message="Fourth message",
        assistant_response="Fourth response"
    )

    assert response_num == 4

    # Load and check
    active = session_manager.load_session()
    assert active["current_response"] == 4
    assert len(active["messages"]) == 4
    assert active["messages"][-1]["user_message"] == "Fourth message"


def test_append_message_with_agent_data(session_manager, sample_session):
    """Test appending message with agent data."""
    session_manager.save_session(sample_session)

    agent_background = {"scene_type": "dialogue", "tension": 7}
    agent_immediate = {"entities_to_load": ["character1"]}
    model_info = {"model": "claude-sonnet-4", "tokens": 1000}

    session_manager.append_message(
        user_message="Test",
        assistant_response="Response",
        agent_data_background=agent_background,
        agent_data_immediate=agent_immediate,
        model_info=model_info
    )

    active = session_manager.load_session()
    last_msg = active["messages"][-1]

    assert last_msg["agent_data_background"] == agent_background
    assert last_msg["agent_data_immediate"] == agent_immediate
    assert last_msg["model_info"] == model_info


def test_update_message_agent_data(session_manager, sample_session):
    """Test updating agent data for existing message."""
    session_manager.save_session(sample_session)

    new_data = {"scene_type": "action", "pacing": "fast"}

    session_manager.update_message_agent_data(
        response_num=2,
        field="agent_data_background",
        data=new_data
    )

    active = session_manager.load_session()
    assert active["messages"][1]["agent_data_background"] == new_data


def test_update_message_agent_data_invalid_field(session_manager, sample_session):
    """Test updating with invalid field name."""
    session_manager.save_session(sample_session)

    with pytest.raises(ValueError, match="Invalid field"):
        session_manager.update_message_agent_data(
            response_num=1,
            field="invalid_field",
            data={}
        )


# ==================== Helper Methods Tests ====================

def test_sanitize_name(session_manager):
    """Test name sanitization."""
    assert session_manager._sanitize_name("Test Branch") == "test_branch"
    assert session_manager._sanitize_name("Test-Branch_123") == "test-branch_123"
    assert session_manager._sanitize_name("Test  Multiple   Spaces") == "test_multiple_spaces"
    assert session_manager._sanitize_name("Test@#$%Invalid") == "testinvalid"


def test_add_auto_tags(session_manager):
    """Test automatic tag addition."""
    user_tags = ["romance", "chapter-1"]

    tags = session_manager._add_auto_tags(
        user_tags=user_tags,
        session_type="branch",
        response_num=42,
        chapter=2
    )

    assert "romance" in tags
    assert "chapter-1" in tags
    assert "branch" in tags
    assert "chapter-2" in tags
    assert "response-42" in tags
    assert any("date-" in tag for tag in tags)


def test_get_current_response_count(session_manager, sample_session):
    """Test getting current response count."""
    session_manager.save_session(sample_session)

    count = session_manager.get_current_response_count()
    assert count == 3


def test_session_exists(session_manager, sample_session):
    """Test checking if session exists."""
    assert not session_manager.session_exists("main")

    session_manager.save_session(sample_session)

    assert session_manager.session_exists("main")


def test_create_initial_session(session_manager):
    """Test creating initial empty session."""
    session_manager.create_initial_session(rp_name="Test RP", chapter=1)

    active = session_manager.load_session()
    assert active["session_id"] == "main"
    assert active["current_response"] == 0
    assert len(active["messages"]) == 0
    assert active["rp_metadata"]["rp_name"] == "Test RP"


def test_create_initial_session_already_exists(session_manager, sample_session):
    """Test creating initial session when one already exists."""
    session_manager.save_session(sample_session)

    with pytest.raises(FileExistsError):
        session_manager.create_initial_session(rp_name="Test")


# ==================== Integration Tests ====================

def test_full_retry_workflow(session_manager, sample_session):
    """Test complete retry workflow."""
    # 1. Save initial session
    session_manager.save_session(sample_session)

    # 2. Retry
    archive_path = session_manager.retry(tags=["rewrite"])

    # 3. Verify active session reduced
    active = session_manager.load_session()
    assert active["current_response"] == 2

    # 4. Add new response
    session_manager.append_message("New message", "New response")

    # 5. Verify new response added
    active = session_manager.load_session()
    assert active["current_response"] == 3
    assert active["messages"][-1]["user_message"] == "New message"

    # 6. Verify archive still has old response
    archived = session_manager.load_session(archive_path)
    assert archived["messages"][-1]["user_message"] == "Third message"


def test_full_branch_workflow(session_manager, sample_session):
    """Test complete branching workflow."""
    # 1. Create main session
    session_manager.save_session(sample_session)

    # 2. Create branch from response 2
    branch_path = session_manager.branch("alt_path", response_num=2)

    # 3. Add message to main
    session_manager.append_message("Main 4", "Main response 4")

    # 4. Switch to branch
    session_manager.switch("alt_path")

    # 5. Add message to branch
    session_manager.append_message("Branch 3", "Branch response 3")

    # 6. Verify branch has different path
    active = session_manager.load_session()
    assert active["messages"][-1]["user_message"] == "Branch 3"
    assert active["current_response"] == 3

    # 7. Switch back to main
    session_manager.switch("main")

    # 8. Verify main has its own path
    active = session_manager.load_session()
    assert active["messages"][-1]["user_message"] == "Main 4"
    assert active["current_response"] == 4


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
