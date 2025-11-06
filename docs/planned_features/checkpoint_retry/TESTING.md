# Testing Strategy - Checkpoint & Retry System

**Project**: Session Log-Based Retry/Branching System
**Last Updated**: 2025-10-17
**Status**: Planning

---

## Testing Overview

This document outlines the comprehensive testing strategy for the session log system.

---

## Test Levels

### 1. Unit Tests
Test individual components in isolation

### 2. Integration Tests
Test component interactions and workflows

### 3. Performance Tests
Measure speed and resource usage

### 4. User Acceptance Tests
Manual testing of user workflows

---

## Phase 1: Session Log Core Tests

### Unit Tests (`tests/test_session_manager.py`)

#### Session Creation & Loading

```python
def test_create_new_session():
    """Test creating a new session from scratch"""

def test_load_existing_session():
    """Test loading a session from JSON file"""

def test_save_session():
    """Test saving session to JSON file"""

def test_session_validation():
    """Test session format validation"""
```

#### Core copy_session() Operation

```python
def test_copy_session_to_response_n():
    """Test copying session up to specific response"""

def test_copy_session_preserves_agent_data():
    """Test that agent data is preserved in copy"""

def test_copy_session_with_tags():
    """Test copying with custom tags"""

def test_copy_session_creates_valid_json():
    """Test that copied session is valid JSON"""
```

#### Retry Operation

```python
def test_retry_removes_last_message():
    """Test that retry removes only last message"""

def test_retry_creates_archive():
    """Test that retry archives old session"""

def test_retry_with_one_message():
    """Edge case: retry with only one message"""

def test_retry_with_no_messages():
    """Edge case: retry with empty session"""

def test_retry_with_tags():
    """Test retry with custom tags"""
```

#### Branch Operation

```python
def test_branch_from_current():
    """Test creating branch from current response"""

def test_branch_from_specific_response():
    """Test creating branch from response N"""

def test_branch_naming():
    """Test branch name validation and sanitization"""

def test_branch_with_tags():
    """Test branch creation with tags"""

def test_branch_preserves_parent_reference():
    """Test that branch tracks parent session"""
```

#### Checkpoint Operation

```python
def test_checkpoint_at_current():
    """Test creating checkpoint at current point"""

def test_checkpoint_naming():
    """Test checkpoint naming"""

def test_checkpoint_with_description():
    """Test checkpoint with description field"""
```

#### Switch Operation

```python
def test_switch_to_branch():
    """Test switching to a branch"""

def test_switch_to_main():
    """Test switching back to main"""

def test_switch_loads_correct_session():
    """Test that switch loads the right session file"""

def test_switch_updates_active_session():
    """Test that active session pointer updates"""
```

#### Session Listing & Search

```python
def test_list_all_sessions():
    """Test listing all available sessions"""

def test_search_by_single_tag():
    """Test searching sessions by one tag"""

def test_search_by_multiple_tags():
    """Test searching with multiple tags (AND logic)"""

def test_search_with_no_results():
    """Test search that matches nothing"""

def test_list_sessions_sorted():
    """Test that sessions are sorted by date"""
```

#### Tagging System

```python
def test_add_tags_to_session():
    """Test adding tags to a session"""

def test_auto_tags_added():
    """Test that auto-tags are added (retry, chapter-N, etc.)"""

def test_tag_validation():
    """Test tag format validation"""

def test_list_all_tags():
    """Test getting all unique tags"""
```

---

### Integration Tests (`tests/test_session_integration.py`)

#### Full Workflow Tests

```python
def test_retry_workflow():
    """
    Test complete retry workflow:
    1. Create session with 5 messages
    2. Retry
    3. Verify main session has 4 messages
    4. Verify archive has 5 messages
    """

def test_branch_workflow():
    """
    Test complete branch workflow:
    1. Create session with 10 messages
    2. Branch from response 5
    3. Add 3 more messages to branch
    4. Verify main still has 10, branch has 8
    """

def test_switch_workflow():
    """
    Test switching between sessions:
    1. Create main with 10 messages
    2. Create branch from response 5
    3. Switch to branch
    4. Add message to branch
    5. Switch back to main
    6. Verify main unchanged
    """

def test_multiple_branches():
    """
    Test managing multiple branches:
    1. Create 3 branches from same point
    2. Switch between them
    3. Verify independence
    """
```

#### TUI Integration

```python
def test_tui_reload_on_retry():
    """Test that TUI reloads session after retry"""

def test_tui_reload_on_switch():
    """Test that TUI reloads session after switch"""

def test_tui_displays_correct_messages():
    """Test that TUI displays correct message count"""
```

#### Bridge Command Integration

```python
def test_bridge_retry_command():
    """Test /retry command through bridge"""

def test_bridge_branch_command():
    """Test /branch command through bridge"""

def test_bridge_switch_command():
    """Test /switch command through bridge"""

def test_bridge_sessions_command():
    """Test /sessions command through bridge"""

def test_bridge_command_with_tags():
    """Test commands with tag syntax: #tag"""
```

#### Agent Data Preservation

```python
def test_agent_data_in_session():
    """Test that agent data is stored in session"""

def test_agent_data_preserved_in_retry():
    """Test that retry preserves agent data"""

def test_agent_data_preserved_in_branch():
    """Test that branch preserves agent data"""

def test_agent_data_loaded_with_session():
    """Test that agent data loads with session"""
```

---

### Performance Tests (`tests/test_session_performance.py`)

#### Load Time Tests

```python
def test_load_small_session():
    """Test loading session with 10 messages (<50ms)"""

def test_load_medium_session():
    """Test loading session with 100 messages (<100ms)"""

def test_load_large_session():
    """Test loading session with 1000 messages (<500ms)"""

def test_load_very_large_session():
    """Test loading session with 10000 messages (<2s)"""
```

#### Copy Operation Performance

```python
def test_copy_small_session():
    """Test copying 10-message session (<50ms)"""

def test_copy_medium_session():
    """Test copying 100-message session (<100ms)"""

def test_copy_large_session():
    """Test copying 1000-message session (<500ms)"""
```

#### Search Performance

```python
def test_search_few_sessions():
    """Test searching 10 sessions (<50ms)"""

def test_search_many_sessions():
    """Test searching 100 sessions (<500ms)"""

def test_tag_search_performance():
    """Test tag filtering with many sessions"""
```

#### File Size Tests

```python
def test_session_file_size():
    """Measure typical session file sizes"""

def test_session_compression():
    """Test if JSON compression would help"""
```

---

### User Acceptance Tests (Manual)

#### Basic Retry

1. Start RP, send message, get response
2. Type `/retry`
3. Verify bridge shows: "Retry ready! Response N removed."
4. Verify TUI chat no longer shows response
5. Send message again
6. Verify new response appears

**Expected**: Old response gone, new response generated

#### Retry with Tags

1. Send message, get response
2. Type `/retry #better-dialogue #rewrite`
3. Verify archive has tags
4. Type `/sessions tag:rewrite`
5. Verify retry session appears in search

**Expected**: Tags work, search finds it

#### Create Branch

1. Have session with 20 messages
2. Type `/branch "romance path" #romance #exploring`
3. Verify confirmation message
4. Send new message
5. Verify main session still at 20, branch at 21

**Expected**: Branch created, sessions independent

#### Switch Sessions

1. Have main session + branch
2. Type `/switch "romance path"`
3. Verify TUI reloads and shows correct chat
4. Type `/switch "main"`
5. Verify TUI reloads back to main

**Expected**: Switching works, correct chat displayed

#### List Sessions

1. Create multiple branches and retries
2. Type `/sessions`
3. Verify all sessions listed with tags
4. Type `/sessions tag:romance`
5. Verify only romance-tagged sessions shown

**Expected**: List accurate, search works

#### Large Session

1. Create session with 500+ messages
2. Test retry, branch, switch operations
3. Measure performance (should be <1s each)

**Expected**: Still fast with large session

---

## Edge Cases & Error Conditions

### Edge Case Tests

```python
def test_retry_on_empty_session():
    """What happens if user retries with no messages?"""

def test_retry_on_first_message():
    """What happens if user retries after first message?"""

def test_branch_with_invalid_name():
    """What happens with invalid branch name?"""

def test_branch_with_duplicate_name():
    """What happens if branch name already exists?"""

def test_switch_to_nonexistent_session():
    """What happens if user switches to missing session?"""

def test_corrupted_session_file():
    """What happens if session JSON is corrupted?"""

def test_missing_session_file():
    """What happens if active session file missing?"""
```

### Error Handling Tests

```python
def test_save_failure():
    """Test handling of save failures (disk full, etc.)"""

def test_load_failure():
    """Test handling of load failures (permissions, etc.)"""

def test_invalid_json():
    """Test handling of invalid JSON in session file"""

def test_concurrent_modifications():
    """Test handling of concurrent session modifications"""
```

---

## Test Data

### Test Session Fixtures

Create fixture sessions for testing:

**Small Session** (10 messages):
- File: `tests/fixtures/session_small.json`
- Size: ~50KB
- Use: Basic functionality tests

**Medium Session** (100 messages):
- File: `tests/fixtures/session_medium.json`
- Size: ~500KB
- Use: Performance tests

**Large Session** (1000 messages):
- File: `tests/fixtures/session_large.json`
- Size: ~5MB
- Use: Stress tests

**Branched Session** (with branches):
- Files: Multiple session files with parent references
- Use: Branch/switch tests

---

## Test Coverage Goals

- **Unit Test Coverage**: >90%
- **Integration Test Coverage**: >80%
- **Critical Path Coverage**: 100%

**Critical Paths**:
- Retry workflow
- Branch workflow
- Switch workflow
- Session loading
- Save/restore operations

---

## Continuous Testing

### Pre-Commit Tests

Run before every commit:
```bash
pytest tests/test_session_manager.py
pytest tests/test_session_integration.py --fast
```

### Full Test Suite

Run before merging:
```bash
pytest tests/ --cov=src/session_manager
```

### Performance Regression

Monitor performance over time:
```bash
pytest tests/test_session_performance.py --benchmark
```

---

## Test Environment Setup

### Dependencies

```bash
pip install pytest pytest-cov pytest-benchmark
```

### Test Directory Structure

```
tests/
├── test_session_manager.py          # Unit tests
├── test_session_integration.py      # Integration tests
├── test_session_performance.py      # Performance tests
├── fixtures/
│   ├── session_small.json
│   ├── session_medium.json
│   └── session_large.json
└── conftest.py                       # Shared fixtures
```

---

## Success Criteria

Phase 1 testing is complete when:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Performance tests meet targets
- [ ] Edge cases handled gracefully
- [ ] Error conditions tested
- [ ] User acceptance tests pass
- [ ] Test coverage >90%
- [ ] No known critical bugs

---

**Last Updated**: 2025-10-17
**Status**: Ready for implementation
