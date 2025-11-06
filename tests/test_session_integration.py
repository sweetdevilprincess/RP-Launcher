"""
Integration Tests for Session Management System

Tests the full integration of session management including:
- Bridge command handling
- Tag parsing
- Full workflows (retry → new response, branch → switch, etc.)
- Error handling
- Session persistence
"""

import pytest
import tempfile
import shutil
from pathlib import Path

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
    """Create SessionManager instance."""
    return SessionManager(temp_rp_dir)


@pytest.fixture
def populated_session(session_manager):
    """Create a session with multiple messages."""
    session_manager.create_initial_session(rp_name="Test RP")

    for i in range(1, 6):
        session_manager.append_message(
            user_message=f"Message {i}",
            assistant_response=f"Response {i}"
        )

    return session_manager


# ==================== Tag Parsing Tests ====================

def test_parse_command_with_tags():
    """Test tag parsing from commands."""
    def parse_command_with_tags(command: str):
        """Parse command and extract hashtags."""
        tags = []
        parts = command.split()
        clean_parts = []

        for part in parts:
            if part.startswith("#"):
                tags.append(part[1:])
            else:
                clean_parts.append(part)

        return " ".join(clean_parts), tags

    # Test with tags
    cmd, tags = parse_command_with_tags("/retry #better-dialogue #rewrite")
    assert cmd == "/retry"
    assert tags == ["better-dialogue", "rewrite"]

    # Test without tags
    cmd, tags = parse_command_with_tags("/retry")
    assert cmd == "/retry"
    assert tags == []

    # Test branch with tags
    cmd, tags = parse_command_with_tags('/branch "romance" #romance #chapter-2')
    assert cmd == '/branch "romance"'
    assert tags == ["romance", "chapter-2"]


def test_parse_branch_command():
    """Test branch command parsing."""
    def parse_command_with_tags(command: str):
        tags = []
        parts = command.split()
        clean_parts = []
        for part in parts:
            if part.startswith("#"):
                tags.append(part[1:])
            else:
                clean_parts.append(part)
        return " ".join(clean_parts), tags

    def parse_branch_command(command: str):
        clean_command, tags = parse_command_with_tags(command)
        args = clean_command.replace("/branch", "").strip()
        parts = args.split(maxsplit=1)

        if len(parts) == 2 and parts[0].isdigit():
            return int(parts[0]), parts[1].strip('"\''), tags
        else:
            return None, args.strip('"\''), tags

    # Test branch without response number
    resp_num, name, tags = parse_branch_command('/branch "romance path"')
    assert resp_num is None
    assert name == "romance path"
    assert tags == []

    # Test branch with response number
    resp_num, name, tags = parse_branch_command('/branch 42 "romance path"')
    assert resp_num == 42
    assert name == "romance path"

    # Test branch with tags
    resp_num, name, tags = parse_branch_command('/branch 42 "romance" #romance #test')
    assert resp_num == 42
    assert name == "romance"
    assert tags == ["romance", "test"]


# ==================== Full Workflow Tests ====================

def test_full_retry_workflow(populated_session):
    """Test complete retry workflow: retry → new response → verify."""
    # Initial state: 5 messages
    assert populated_session.get_current_response_count() == 5

    # Retry
    archive_path = populated_session.retry(tags=["rewrite"])

    # Verify active session reduced to 4
    assert populated_session.get_current_response_count() == 4

    # Add new response
    populated_session.append_message(
        user_message="Revised message 5",
        assistant_response="Revised response 5"
    )

    # Verify back to 5 messages
    assert populated_session.get_current_response_count() == 5

    # Verify new message is different
    active = populated_session.load_session()
    assert active["messages"][-1]["user_message"] == "Revised message 5"

    # Verify archive still has original
    archived = populated_session.load_session(archive_path)
    assert archived["messages"][-1]["user_message"] == "Message 5"
    assert "rewrite" in archived["tags"]


def test_full_branch_workflow(populated_session):
    """Test complete branch workflow: branch → add messages → switch → verify."""
    # Create branch from response 3
    branch_path = populated_session.branch(
        branch_name="alternate_path",
        response_num=3,
        tags=["exploration"]
    )

    # Verify branch created correctly
    branched = populated_session.load_session(branch_path)
    assert branched["current_response"] == 3
    assert "exploration" in branched["tags"]

    # Add message to main
    populated_session.append_message(
        user_message="Main 6",
        assistant_response="Main response 6"
    )

    # Switch to branch
    populated_session.switch("alternate_path")

    # Add messages to branch
    populated_session.append_message(
        user_message="Branch 4",
        assistant_response="Branch response 4"
    )
    populated_session.append_message(
        user_message="Branch 5",
        assistant_response="Branch response 5"
    )

    # Verify branch state
    active = populated_session.load_session()
    assert active["session_id"] == "alternate_path"
    assert active["current_response"] == 5
    assert active["messages"][-1]["user_message"] == "Branch 5"

    # Switch back to main
    populated_session.switch("main")

    # Verify main state
    active = populated_session.load_session()
    assert active["session_id"] == "main"
    assert active["current_response"] == 6
    assert active["messages"][-1]["user_message"] == "Main 6"


def test_multiple_branches(populated_session):
    """Test managing multiple independent branches."""
    # Create 3 branches from same point
    branch1 = populated_session.branch("romance", response_num=3)
    branch2 = populated_session.branch("action", response_num=3)
    branch3 = populated_session.branch("mystery", response_num=3)

    # Switch to each and add unique message
    for branch_name, msg in [("romance", "Kiss"), ("action", "Fight"), ("mystery", "Clue")]:
        populated_session.switch(branch_name)
        populated_session.append_message(
            user_message=msg,
            assistant_response=f"{msg} response"
        )

    # Verify each branch is independent
    for branch_name, expected_msg in [("romance", "Kiss"), ("action", "Fight"), ("mystery", "Clue")]:
        # Find branch file
        branch_file = populated_session.branches_dir / f"session_{branch_name}.json"
        branch = populated_session.load_session(branch_file)

        assert branch["current_response"] == 4
        assert branch["messages"][-1]["user_message"] == expected_msg


def test_checkpoint_and_restore_workflow(populated_session):
    """Test creating checkpoint and restoring from it."""
    # Create checkpoint at response 3
    populated_session.switch("main")  # Ensure on main
    checkpoint_path = populated_session.checkpoint(
        checkpoint_name="before_divergence",
        tags=["important", "decision-point"]
    )

    # Continue on main for 2 more responses
    populated_session.append_message("Message 6", "Response 6")
    populated_session.append_message("Message 7", "Response 7")

    # Verify main is at 7
    assert populated_session.get_current_response_count() == 7

    # Switch to checkpoint
    populated_session.switch("before_divergence")

    # Verify back at checkpoint state
    active = populated_session.load_session()
    assert active["current_response"] == 5
    assert active["session_id"] == "before_divergence"
    assert "important" in active["tags"]


# ==================== Session Listing & Search Tests ====================

def test_list_all_sessions(populated_session):
    """Test listing all sessions."""
    # Create multiple sessions
    populated_session.branch("branch1", tags=["romance"])
    populated_session.branch("branch2", tags=["action"])
    populated_session.retry(tags=["retry"])

    # List all
    sessions = populated_session.list_sessions()

    # Should have: active, 2 branches, 1 retry
    assert len(sessions) == 4

    types = [s["type"] for s in sessions]
    assert "active" in types
    assert types.count("branch") == 2
    assert "archived" in types


def test_list_sessions_with_tag_filter(populated_session):
    """Test filtering sessions by tag."""
    # Create sessions with different tags
    populated_session.branch("romance1", tags=["romance", "silas"])
    populated_session.branch("romance2", tags=["romance", "marcus"])
    populated_session.branch("action1", tags=["action", "fight"])

    # Filter by romance
    romance_sessions = populated_session.list_sessions(tag_filter="romance")
    assert len(romance_sessions) == 2
    names = [s["name"] for s in romance_sessions]
    assert "romance1" in names
    assert "romance2" in names

    # Filter by action
    action_sessions = populated_session.list_sessions(tag_filter="action")
    assert len(action_sessions) == 1
    assert action_sessions[0]["name"] == "action1"


def test_list_sessions_sorted_by_date(populated_session):
    """Test that sessions are sorted by last_modified (newest first)."""
    import time

    # Create sessions with delays
    populated_session.branch("old_branch")
    time.sleep(0.1)
    populated_session.branch("new_branch")
    time.sleep(0.1)
    populated_session.branch("newest_branch")

    sessions = populated_session.list_sessions()

    # Filter to branches only
    branches = [s for s in sessions if s["type"] == "branch"]

    # Should be in reverse chronological order
    assert branches[0]["name"] == "newest_branch"
    assert branches[1]["name"] == "new_branch"
    assert branches[2]["name"] == "old_branch"


# ==================== Error Handling Tests ====================

def test_retry_on_empty_session(session_manager):
    """Test retry error handling on empty session."""
    session_manager.create_initial_session("Test RP")

    with pytest.raises(ValueError, match="Session is empty"):
        session_manager.retry()


def test_branch_with_invalid_name(populated_session):
    """Test branch error handling with invalid name."""
    with pytest.raises(ValueError, match="cannot be empty"):
        populated_session.branch("")


def test_branch_with_invalid_response_num(populated_session):
    """Test branch error handling with invalid response number."""
    with pytest.raises(ValueError, match="Invalid response number"):
        populated_session.branch("test", response_num=100)


def test_switch_to_nonexistent_session(populated_session):
    """Test switch error handling with non-existent session."""
    with pytest.raises(FileNotFoundError, match="Session not found"):
        populated_session.switch("nonexistent")


def test_duplicate_branch_name(populated_session):
    """Test creating branch with duplicate name."""
    populated_session.branch("duplicate")

    with pytest.raises(ValueError, match="already exists"):
        populated_session.branch("duplicate")


# ==================== Agent Data Preservation Tests ====================

def test_agent_data_preserved_in_retry(session_manager):
    """Test that agent data is preserved when retrying."""
    session_manager.create_initial_session("Test RP")

    # Add message with agent data
    agent_data = {
        "scene_type": "dialogue",
        "tension": 7,
        "characters": ["Alice", "Bob"]
    }

    session_manager.append_message(
        user_message="Test message",
        assistant_response="Test response",
        agent_data_background=agent_data
    )

    # Retry
    archive_path = session_manager.retry()

    # Check archived session has agent data
    archived = session_manager.load_session(archive_path)
    assert archived["messages"][0]["agent_data_background"] == agent_data


def test_agent_data_preserved_in_branch(session_manager):
    """Test that agent data is preserved when branching."""
    session_manager.create_initial_session("Test RP")

    agent_data = {"scene_type": "action", "pacing": "fast"}

    session_manager.append_message(
        "Message 1", "Response 1",
        agent_data_background=agent_data
    )
    session_manager.append_message(
        "Message 2", "Response 2"
    )

    # Branch
    branch_path = session_manager.branch("test_branch", response_num=2)

    # Check branch has agent data
    branched = session_manager.load_session(branch_path)
    assert branched["messages"][0]["agent_data_background"] == agent_data


# ==================== Session Persistence Tests ====================

def test_session_persists_across_restarts(temp_rp_dir):
    """Test that sessions persist across SessionManager instances."""
    # Create first manager and session
    sm1 = SessionManager(temp_rp_dir)
    sm1.create_initial_session("Test RP")
    sm1.append_message("Message 1", "Response 1")
    sm1.append_message("Message 2", "Response 2")

    # Create new manager instance (simulating restart)
    sm2 = SessionManager(temp_rp_dir)

    # Load session
    session = sm2.load_session()

    assert session["current_response"] == 2
    assert len(session["messages"]) == 2
    assert session["messages"][0]["user_message"] == "Message 1"


def test_branches_persist_across_restarts(temp_rp_dir):
    """Test that branches persist across restarts."""
    # Create session with branches
    sm1 = SessionManager(temp_rp_dir)
    sm1.create_initial_session("Test RP")
    sm1.append_message("M1", "R1")
    sm1.append_message("M2", "R2")
    sm1.branch("test_branch")

    # New manager instance
    sm2 = SessionManager(temp_rp_dir)

    # List sessions
    sessions = sm2.list_sessions()

    branch_names = [s["name"] for s in sessions if s["type"] == "branch"]
    assert "test_branch" in branch_names


# ==================== Complex Scenarios ====================

def test_nested_retry_workflow(populated_session):
    """Test retrying multiple times."""
    # Initial: 5 messages

    # Retry 1
    populated_session.retry(tags=["attempt-1"])
    populated_session.append_message("Try 1", "Response 1")

    # Retry 2
    populated_session.retry(tags=["attempt-2"])
    populated_session.append_message("Try 2", "Response 2")

    # Verify final state
    active = populated_session.load_session()
    assert active["current_response"] == 5
    assert active["messages"][-1]["user_message"] == "Try 2"

    # Verify 2 retries in archive
    archived = [s for s in populated_session.list_sessions()
                if s["type"] == "archived"]
    assert len(archived) == 2


def test_branch_from_branch(populated_session):
    """Test creating branches from existing branches."""
    # Create first branch
    populated_session.branch("branch1", response_num=3)

    # Switch to branch1
    populated_session.switch("branch1")

    # Add message
    populated_session.append_message("Branch message", "Branch response")

    # Create sub-branch
    populated_session.branch("branch1_sub", response_num=4)

    # Verify sub-branch
    sub_branch_file = populated_session.branches_dir / "session_branch1_sub.json"
    sub_branch = populated_session.load_session(sub_branch_file)

    assert sub_branch["parent_session"] == "branch1"
    assert sub_branch["branch_point"] == 4


def test_checkpoint_at_multiple_points(populated_session):
    """Test creating checkpoints at different points."""
    # Checkpoint at different responses
    populated_session.checkpoint("checkpoint_1", tags=["early"])

    populated_session.append_message("M6", "R6")
    populated_session.checkpoint("checkpoint_2", tags=["middle"])

    populated_session.append_message("M7", "R7")
    populated_session.checkpoint("checkpoint_3", tags=["late"])

    # Verify all checkpoints exist
    checkpoints = [s for s in populated_session.list_sessions()
                   if s["type"] == "checkpoint"]

    assert len(checkpoints) == 3
    names = [c["name"] for c in checkpoints]
    assert "checkpoint_1" in names
    assert "checkpoint_2" in names
    assert "checkpoint_3" in names


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
