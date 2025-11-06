# Phase 1: Simple Retry - Implementation Guide

**Phase**: 1 (MVP)
**Goal**: Implement `/retry` command to undo last response
**Timeline**: 2-3 days
**Status**: Planning

---

## Overview

Phase 1 implements a simple `/retry` command that allows users to undo the last response and try again. This is the foundation for the checkpoint system and must be rock-solid before expanding to auto-checkpoints.

---

## User Story

**As a user**, I want to be able to undo the last response if I don't like it, so that I can get a different response without starting over.

**Acceptance Criteria**:
- ✅ `/retry` command removes last response from chapter
- ✅ Response counter decrements correctly
- ✅ Agent cache is cleared
- ✅ Safety backup is created before modification
- ✅ Clear feedback messages
- ✅ Graceful error handling

---

## Technical Specification

### 1. Files to Create

#### `src/story_version_control.py` (NEW)

Main module for retry/checkpoint functionality.

**Classes**:
- `RetryManager` - Handles retry operations
- `BackupManager` - Manages safety backups

**RetryManager Methods**:
```python
class RetryManager:
    def __init__(self, rp_dir: Path):
        """Initialize retry manager"""

    def can_retry(self) -> bool:
        """Check if there's a response to undo"""

    def get_last_response_info(self) -> dict:
        """Get info about last response (number, chapter, content preview)"""

    def create_backup(self) -> Path:
        """Create safety backup before retry"""

    def remove_last_response(self) -> bool:
        """Remove last response from chapter file"""

    def restore_from_backup(self, backup_path: Path) -> bool:
        """Restore files from backup if retry fails"""

    def cleanup_old_backups(self, keep_last_n: int = 5):
        """Remove old retry backups"""
```

**Implementation Details**: See ARCHITECTURE.md for detailed design

---

### 2. Files to Modify

#### `src/tui_bridge.py` (MODIFY)

Add retry command handler in main loop.

**Location**: In the main message processing loop, before API calls

**Code to Add**:
```python
# Add after /new command handling, before orchestrator call

# Check for /retry command
if message.strip().lower() == "/retry":
    from src.story_version_control import RetryManager

    retry_manager = RetryManager(rp_dir)

    # Check if retry is possible
    if not retry_manager.can_retry():
        response = "❌ Cannot retry: No previous response to undo."
        file_manager.write_ipc_response(response, state_dir=state_dir)
        done_flag.touch()
        print("📤 Response sent to TUI")
        print()
        continue

    # Get info about what will be removed
    last_response_info = retry_manager.get_last_response_info()
    print(f"🔄 Retry requested - will remove Response #{last_response_info['number']}")

    try:
        # Create safety backup
        backup_path = retry_manager.create_backup()
        print(f"💾 Safety backup created: {backup_path}")

        # Remove last response
        success = retry_manager.remove_last_response()

        if success:
            response = f"""✅ Retry successful!

Removed: Response #{last_response_info['number']}
Preview: {last_response_info['preview']}

You can now send your message again to get a new response."""

            print("✓ Last response removed")
            print("✓ Response counter decremented")
            print("✓ Agent cache cleared")

        else:
            response = "❌ Retry failed: Could not remove last response."
            print("✗ Retry failed")

    except Exception as e:
        # Restore from backup on error
        log_to_file(log_file, f"[ERROR] Retry failed: {e}")
        retry_manager.restore_from_backup(backup_path)
        response = f"❌ Retry failed and was rolled back: {str(e)}"
        print(f"✗ Retry failed: {e}")
        print("✓ Restored from backup")

    # Send response to TUI
    file_manager.write_ipc_response(response, state_dir=state_dir)
    done_flag.touch()
    print("📤 Response sent to TUI")
    print()
    continue
```

**Integration Notes**:
- Add before orchestrator runs (retry doesn't need automation)
- Use existing `file_manager` and `done_flag`
- Log to existing `log_file` for debugging

---

#### `src/file_manager.py` (EXTEND)

Add helper methods for chapter file manipulation.

**Methods to Add**:
```python
def get_current_chapter_file(self, state_dir: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Get path to current chapter file based on current_state.md"""
    # Read current chapter number from current_state.md
    # Return path to chapters/chapter_XXX.md

def find_last_response_marker(self, chapter_file: Path) -> Optional[int]:
    """Find line number of last ### Response #N marker"""
    # Read chapter file
    # Find last occurrence of "### Response #N"
    # Return line number or None

def remove_lines_after(self, file_path: Path, line_number: int) -> bool:
    """Remove all lines after specified line number"""
    # Read file
    # Keep lines up to line_number
    # Write back to file
    # Return success boolean

def get_response_preview(self, chapter_file: Path, response_num: int, max_chars: int = 200) -> str:
    """Get preview text of specified response"""
    # Read chapter file
    # Find ### Response #N
    # Extract first max_chars of response content
    # Return preview string
```

---

### 3. State Files to Modify

#### `chapters/chapter_XXX.md`

Remove last `### Response #N` block and everything after it.

**Before**:
```markdown
## Responses

### Response #44

[User message and response content]

### Response #45

[User message and response content]
```

**After** (`/retry`):
```markdown
## Responses

### Response #44

[User message and response content]
```

---

#### `state/response_counter.json`

Decrement the response count.

**Before**:
```json
{
  "count": 45,
  "last_updated": "2025-10-17T10:30:00"
}
```

**After**:
```json
{
  "count": 44,
  "last_updated": "2025-10-17T10:35:00"
}
```

---

#### `state/agent_analysis.json`

Clear the cache (delete file or set to empty).

**Approach**: Delete the file entirely for Phase 1
**Rationale**: Simplest and safest - agents will re-analyze on next response

---

#### `state/current_state.md`

May need rollback if auto-generated by agents.

**Phase 1 Approach**: Don't modify (accept slight staleness)
**Phase 2 Approach**: Restore from checkpoint

---

### 4. Backup Strategy

#### Backup Contents

Create zip file in `backups/retry_backup_TIMESTAMP.zip` containing:
- Current chapter file
- `response_counter.json`
- `agent_analysis.json` (if exists)
- `metadata.json` (retry info)

**Metadata Format**:
```json
{
  "backup_type": "retry",
  "timestamp": "2025-10-17T10:35:00",
  "response_number": 45,
  "chapter_number": 1,
  "reason": "User requested retry"
}
```

#### Backup Cleanup

- Keep last 5 retry backups
- Delete older backups automatically
- Run cleanup on each retry operation

---

## Implementation Steps

### Step 1: Create RetryManager Class (Day 1)

**File**: `src/story_version_control.py`

1. Create class skeleton
2. Implement `can_retry()` - check if response exists
3. Implement `get_last_response_info()` - parse chapter file
4. Implement `create_backup()` - zip current state
5. Implement `remove_last_response()` - modify chapter file
6. Implement `restore_from_backup()` - unzip and restore
7. Add error handling and validation

**Testing**: Unit tests for each method

---

### Step 2: Extend FileManager (Day 1)

**File**: `src/file_manager.py`

1. Add `get_current_chapter_file()` helper
2. Add `find_last_response_marker()` helper
3. Add `remove_lines_after()` helper
4. Add `get_response_preview()` helper

**Testing**: Test with real chapter files

---

### Step 3: Integrate with Bridge (Day 2)

**File**: `src/tui_bridge.py`

1. Add retry command detection
2. Import and use RetryManager
3. Handle backup creation
4. Handle success/failure feedback
5. Clear agent cache
6. Send confirmation to TUI

**Testing**: Manual testing with running system

---

### Step 4: Handle Edge Cases (Day 2)

1. **No responses to retry**: Clear error message
2. **Only one response**: Should work (remove first response)
3. **Pending file writes**: Flush FSWriteQueue before retry
4. **Corrupted chapter file**: Validate before modification
5. **Backup failure**: Abort retry, show error
6. **Restore failure**: Log error, alert user

---

### Step 5: Testing & Polish (Day 3)

1. Comprehensive testing (see Testing section below)
2. Error message improvements
3. Performance optimization
4. Documentation
5. Code review
6. User acceptance testing

---

## Testing Plan

### Unit Tests

**File**: `tests/test_story_version_control.py`

```python
def test_can_retry_with_responses():
    """Test can_retry returns True when responses exist"""

def test_can_retry_without_responses():
    """Test can_retry returns False when no responses"""

def test_get_last_response_info():
    """Test parsing last response from chapter file"""

def test_create_backup():
    """Test backup creation"""

def test_remove_last_response():
    """Test response removal"""

def test_restore_from_backup():
    """Test restoration from backup"""

def test_backup_cleanup():
    """Test old backup deletion"""
```

### Integration Tests

**File**: `tests/test_retry_integration.py`

```python
def test_retry_with_one_response():
    """Test retry with only one response in chapter"""

def test_retry_with_ten_responses():
    """Test retry with multiple responses"""

def test_retry_with_pending_writes():
    """Test retry with pending FSWriteQueue writes"""

def test_retry_failure_recovery():
    """Test recovery when retry fails"""

def test_agent_cache_clearing():
    """Test agent cache is cleared after retry"""

def test_counter_decrement():
    """Test response counter decrements correctly"""
```

### Manual Test Cases

1. **Happy Path**:
   - Send message, get response
   - Type `/retry`
   - Verify response removed
   - Send same message, get new response

2. **Edge Case - First Response**:
   - Start new chapter
   - Send first message
   - Type `/retry`
   - Verify chapter goes back to empty

3. **Edge Case - No Responses**:
   - Open fresh RP
   - Type `/retry` immediately
   - Verify clear error message

4. **Recovery Path**:
   - Artificially break chapter file
   - Type `/retry`
   - Verify backup restoration

5. **Concurrent Writes**:
   - Queue multiple file writes
   - Type `/retry` before they flush
   - Verify no corruption

---

## Error Handling

### Error Scenarios

1. **No previous response**:
   - Message: "❌ Cannot retry: No previous response to undo."
   - Action: Do nothing, wait for user input

2. **Chapter file not found**:
   - Message: "❌ Retry failed: Chapter file not found."
   - Action: Log error, check file paths

3. **Cannot parse chapter file**:
   - Message: "❌ Retry failed: Chapter file format invalid."
   - Action: Log error, suggest manual check

4. **Backup creation failed**:
   - Message: "❌ Retry aborted: Could not create safety backup."
   - Action: Abort retry, do not modify files

5. **Response removal failed**:
   - Message: "❌ Retry failed: Could not remove response."
   - Action: Restore from backup immediately

6. **Counter update failed**:
   - Message: "⚠️ Retry completed but counter may be incorrect."
   - Action: Log warning, manual fix may be needed

### Recovery Procedures

All errors trigger automatic restore from backup.

**Process**:
1. Log error details
2. Restore all files from backup zip
3. Verify restoration successful
4. Notify user of rollback
5. Preserve backup for manual inspection

---

## User Experience

### Success Flow

```
User: [Types some message]
Bridge: [Generates Response #45]
TUI: [Shows response]

User: /retry
Bridge: 🔄 Retry requested - will remove Response #45
Bridge: 💾 Safety backup created: retry_backup_20251017_103500.zip
Bridge: ✓ Last response removed
Bridge: ✓ Response counter decremented (45 → 44)
Bridge: ✓ Agent cache cleared
TUI: ✅ Retry successful!

     Removed: Response #45
     Preview: [First 200 chars of removed response]

     You can now send your message again to get a new response.

User: [Sends same or modified message]
Bridge: [Generates new Response #45]
TUI: [Shows new response]
```

### Error Flow

```
User: /retry
Bridge: 🔄 Retry requested...
Bridge: ✗ Retry failed: Could not parse chapter file
Bridge: ✓ Restored from backup
TUI: ❌ Retry failed and was rolled back: Could not parse chapter file

     Your files have been restored to their previous state.
     Please check the chapter file manually.
```

---

## Performance Considerations

### Backup Creation

- **Small RPs**: <100ms (few MB of data)
- **Large RPs**: <1s (tens of MB)
- **Optimization**: Only backup modified files

### Response Removal

- **Small chapters**: <50ms (parse and truncate)
- **Large chapters**: <200ms (10,000+ lines)
- **Optimization**: Use binary search for response markers

### Total Retry Time

- **Target**: <2 seconds end-to-end
- **Acceptable**: <5 seconds for large RPs

---

## Configuration

Add to `state/automation_config.json`:

```json
{
  "retry": {
    "enabled": true,
    "create_backup": true,
    "keep_backups": 5,
    "clear_agent_cache": true,
    "flush_pending_writes": true
  }
}
```

---

## Documentation

### User Documentation

Add to help screen in TUI:

```
/retry              - Undo last response and try again
                      Creates safety backup before modification
```

### Developer Documentation

- Code comments in RetryManager
- Docstrings for all methods
- Architecture diagram in ARCHITECTURE.md
- This implementation guide

---

## Success Criteria

Phase 1 is complete when:

- ✅ `/retry` command works reliably
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Manual testing completed
- ✅ Error handling tested
- ✅ Performance within targets
- ✅ Documentation complete
- ✅ Code reviewed
- ✅ User testing positive

---

## Next Steps

After Phase 1 completion:

1. Gather user feedback on retry workflow
2. Monitor for edge cases in production
3. Begin Phase 2 planning (auto-checkpoints)
4. Consider improvements based on usage

---

## References

- **Main Roadmap**: `ROADMAP.md`
- **Architecture**: `ARCHITECTURE.md`
- **Testing**: `TESTING.md`
- **Implementation Log**: `IMPLEMENTATION_LOG.md`

---

**Last Updated**: 2025-10-17
**Version**: 1.0
**Status**: Ready for implementation
