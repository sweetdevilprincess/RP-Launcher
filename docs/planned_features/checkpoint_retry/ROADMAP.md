# Checkpoint & Retry System - Implementation Roadmap

**Feature**: Story Checkpointing & Retry (Phase 4.3 from main ROADMAP.md)
**Status**: Planning
**Created**: 2025-10-17

---

## Executive Summary

Implement a retry and checkpointing system to allow users to undo responses and explore different story directions without losing progress.

### Problem Statement

Currently, once Claude generates a response, there's no way to:
- Retry if the response doesn't match expectations
- Go back a few responses to try a different direction
- Explore "what if" scenarios without losing progress
- Recover from story directions you don't like

### Solution Overview

**KEY INSIGHT**: Use JSON session logs as single source of truth. Retry, checkpoints, and branching are **the same operation** - copying a session up to a specific response number.

Implement a **unified approach** using session logs:

1. **Phase 1 (Core)**: Session Log System + Retry/Branch/Checkpoint (4-5 days)
2. **Phase 2 (UI)**: TUI Integration for managing sessions (3 days)
3. **Phase 3 (Optional)**: Advanced features - comparison, merging (as needed)

**Total Timeline**: 7-8 days (vs 18+ days with old approach)

---

## User Requirements (Captured 2025-10-17)

### Workflow Preferences

**Question**: What should the retry/checkpoint workflow look like?
**Answer**: "I am thinking of something like a simple retry and something like auto checkpoints as different portions. I think that retying would be easiest to start with then we can expand on it to get to auto checkpoints."

**Decision**: Implement simple retry first, expand to auto-checkpoints after proven.

### UI Integration

**Question**: Should branches/checkpoints be visible in the TUI?
**Answer**: "I want to add the UI eventually so keep that in mind, but to do that I think we will have to start with /commands."

**Decision**: Start with slash commands in bridge, design for future TUI integration.

### Agent Cache Handling

**Question**: What should happen to agent caches when rolling back?
**Answer**: "Restore agent cache to checkpoint state"

**Decision**: Embed agent data directly in session log (no separate cache file).

### Tagging System

**User Request**: "When there is a branch or a retry we give players an option to leave a tag that way if they would like to return then they can find it easily and it does not mess with the naming structure."

**Decision**: Implement tagging system for all sessions - users can add tags when creating branches/retries, search by tags later.

---

## Phase Overview

| Phase | Goal | Duration | Commands | Status |
|-------|------|----------|----------|--------|
| **Phase 1** | Session Log Core | 4-5 days | `/retry`, `/branch`, `/checkpoint`, `/switch` | 🔵 Planning |
| **Phase 2** | UI Integration | 3 days | TUI session management screens | ⚪ Future |
| **Phase 3** | Advanced Features | As needed | `/diff`, `/merge`, search | ⚪ Optional |

**Key Change**: All commands implemented in Phase 1 because they use the same core operation (`copy_session()`)

---

## Phase 1: Session Log Core System

**Goal**: Implement session log system with retry, branching, and checkpointing

**Timeline**: 4-5 days

**Key Insight**: One core operation (`copy_session()`) powers all features!

### Features

**All implemented in Phase 1:**
- `/retry [#tags]` - Undo last response (archive to retry_TIMESTAMP.json)
- `/branch "name" [#tags]` - Create named branch from current point
- `/branch N "name" [#tags]` - Create branch from response N
- `/checkpoint "name" [#tags]` - Save checkpoint at current point
- `/switch "name"` - Switch to different session/branch
- `/sessions` - List all sessions
- `/sessions tag:TAG` - Search sessions by tag
- Optional tagging system - users can tag any operation for easy finding

### Technical Implementation

**See**: `PHASE_1_SESSION_LOGS.md` for detailed implementation guide

**Architecture**: Session logs as single source of truth (see `ARCHITECTURE.md`)

**Files to Create**:
- `src/session_manager.py` - SessionManager class with core operations
  - `copy_session()` - Core operation (used by all commands)
  - `retry()` - Archive and remove last message
  - `branch()` - Create named branch
  - `checkpoint()` - Save checkpoint
  - `switch()` - Load different session
  - `list_sessions()` - List available sessions
  - `search_by_tags()` - Find sessions by tags

**Files to Modify**:
- `src/tui_bridge.py` - Add command handlers for all commands
- `src/rp_client_tui.py` - Reload session on switch

**Data Structure**:
- `sessions/session_main.json` - Active session (PRIMARY)
- `sessions/branches/` - Named branches
- `sessions/archived/` - Retries and checkpoints

### User Experience

```
User: [Gets response they don't like]
User: /retry
Bridge: Creating safety backup...
Bridge: Removing last response from chapter_001.md...
Bridge: Resetting response counter (45 → 44)...
Bridge: Clearing agent cache...
Bridge: ✅ Ready to retry! Send your message again for a new response.
TUI: [Shows confirmation message]
User: [Sends same or modified message, gets new response]
```

### Success Criteria

- ✅ Can retry last response successfully
- ✅ Chapter file correctly modified
- ✅ Counter correctly decremented
- ✅ Agent cache cleared
- ✅ Safety backup created
- ✅ Can restore from backup if retry fails
- ✅ Works with pending file writes

---

## Phase 2: Auto-Checkpoints

**Goal**: Automatically save checkpoints, allow rolling back multiple responses

**Timeline**: 3-4 days

### Features

- Auto-save checkpoint before each response
- `/rollback N` command to go back N responses (1-10)
- `/checkpoints` command to list available checkpoints
- `/checkpoint save "name"` for manual checkpoints
- Restore all state from checkpoint (chapters, state files, agent cache)
- Keep last 10 checkpoints (configurable)

### Technical Implementation

**See**: `PHASE_2_AUTO_CHECKPOINTS.md` (to be created)

**Checkpoint Storage**:
```
<RP_DIR>/checkpoints/auto/
├── checkpoint_0001.zip
├── checkpoint_0002.zip
└── checkpoint_0003.zip
```

**Checkpoint Contents**:
- `chapter_XXX.md` - Chapter file at checkpoint time
- `response_counter.json` - Response number
- `agent_analysis.json` - Agent cache state
- `current_state.md` - Current state file
- `metadata.json` - Checkpoint info (timestamp, description, etc.)

### User Experience

```
User: [Sends message, gets response 45]
System: [Auto-creates checkpoint_0045.zip in background]

[10 responses later...]

User: /rollback 5
Bridge: Rolling back 5 responses (50 → 45)...
Bridge: Restoring from checkpoint_0045.zip...
Bridge: ✅ Rolled back to response 45
TUI: [Shows confirmation]
User: [Can now continue from response 45]
```

---

## Phase 3: UI Integration

**Goal**: Add TUI screens for managing checkpoints visually

**Timeline**: 3-4 days

### Features

- New TUI tab or modal: "Checkpoints"
- List all checkpoints with metadata
- Restore from checkpoint with button click
- Delete old checkpoints
- View checkpoint details
- Compare checkpoints visually

### Technical Implementation

**See**: `PHASE_3_UI_INTEGRATION.md` (to be created)

**UI Mockup**:
```
┌─ Checkpoints ────────────────────────────┐
│                                           │
│  ✅ Response 50 (Current)                │
│  📌 Response 45 - "Before big choice"    │
│  📌 Response 40 - Auto-checkpoint        │
│  📌 Response 35 - Auto-checkpoint        │
│  📌 Response 30 - "Chapter 1 complete"   │
│                                           │
│  [Restore] [Delete] [Details] [Close]    │
└───────────────────────────────────────────┘
```

---

## Phase 4: Full Branching (Optional)

**Goal**: Explore alternate story paths with named branches

**Timeline**: 5-7 days

### Features

- Create named branches from checkpoints
- Switch between branches
- Compare branches
- Merge elements between branches
- Branch visualization

### Technical Implementation

**See**:
- `PHASE_4_FULL_BRANCHING.md` (to be created)
- `docs/planned_features/version_control.md` (existing detailed design)

This phase builds on the existing detailed design in `version_control.md`.

---

## Technical Architecture

**See**: `ARCHITECTURE.md` for complete technical details

### Key Design Decisions

1. **Chapter File Format**: Markdown with `### Response #N` blocks
2. **Checkpoint Format**: Zip archives with all state files
3. **Backup Strategy**: Safety backup before any modification
4. **Agent Cache**: Cleared in Phase 1, restored in Phase 2+
5. **Transaction Model**: All-or-nothing state changes
6. **Storage Location**: `<RP_DIR>/checkpoints/` and `<RP_DIR>/backups/`

### Integration Points

- **FSWriteQueue**: Must flush pending writes before retry/rollback
- **Agent System**: Cache must be cleared or restored appropriately
- **File Manager**: Extend with chapter manipulation helpers
- **TUI Bridge**: Add command detection and handling
- **Orchestrator**: May need hooks for checkpoint triggers

---

## Testing Strategy

**See**: `TESTING.md` for complete test plan

### Phase 1 Testing

- ✅ Retry with 1 response in chapter
- ✅ Retry with 10+ responses in chapter
- ✅ Retry with pending file writes
- ✅ Retry failure recovery (restore from backup)
- ✅ Agent cache clearing verification
- ✅ Counter decrement verification

### Phase 2 Testing

- ✅ Auto-checkpoint creation after each response
- ✅ Rollback 1, 5, and 10 responses
- ✅ Checkpoint cleanup (keep last 10)
- ✅ Agent cache restoration
- ✅ State file restoration
- ✅ Manual checkpoint creation

---

## Success Metrics

### User Experience Metrics

- **Retry Success Rate**: >95% of retries complete successfully
- **User Satisfaction**: Retry workflow feels natural and intuitive
- **Recovery Time**: <2 seconds for retry operation
- **Data Safety**: 0% data loss from retry operations

### Technical Metrics

- **Backup Success**: 100% of retries have valid backups
- **State Consistency**: All state files remain consistent after retry
- **Cache Integrity**: Agent cache properly cleared/restored
- **File Integrity**: Chapter files remain valid markdown

### Quality Metrics

- **Test Coverage**: >90% code coverage for retry logic
- **Error Handling**: All failure modes have recovery paths
- **Documentation**: All commands documented with examples
- **User Feedback**: Clear messages for all operations

---

## Implementation Timeline

### Week 1: Phase 1 - Simple Retry

**Days 1-2**: Core Implementation
- Create `story_version_control.py` with RetryManager
- Implement chapter parsing and modification
- Add backup/restore functionality

**Day 3**: Bridge Integration
- Add retry command detection in `tui_bridge.py`
- Integrate with FileManager
- Handle agent cache clearing

**Day 4**: Testing & Polish
- Comprehensive testing (see TESTING.md)
- Error handling and edge cases
- User feedback messages
- Documentation

### Week 2: Phase 2 - Auto-Checkpoints

**Days 1-2**: Checkpoint System
- Implement checkpoint creation/restoration
- Add zip-based storage
- Integrate with response flow

**Days 3-4**: Rollback Commands
- Add `/rollback N` command
- Add `/checkpoints` list command
- Testing and refinement

### Week 3: Phase 3 - UI Integration (Optional)

- Design TUI screens
- Implement checkpoint list view
- Add restore/delete actions
- Testing with user workflows

### Week 4+: Phase 4 - Full Branching (Optional)

- Design branching system
- Implement branch creation/switching
- Add comparison and merging
- Advanced features

---

## Dependencies

### Required Components

- ✅ File Manager (`src/file_manager.py`) - Exists
- ✅ FSWriteQueue (`src/fs_write_queue.py`) - Exists
- ✅ TUI Bridge (`src/tui_bridge.py`) - Exists
- ✅ Agent Cache (`state/agent_analysis.json`) - Exists
- ✅ Chapter Files (`chapters/*.md`) - Exists

### New Components

- ❌ RetryManager (Phase 1)
- ❌ CheckpointManager (Phase 2)
- ❌ BranchManager (Phase 4)

---

## Risks & Mitigation

### Risk 1: Data Loss During Retry

**Mitigation**:
- Always create backup before modification
- Validate file structure before/after changes
- Transaction-like rollback on failure

### Risk 2: Agent Cache Corruption

**Mitigation**:
- Clear cache entirely in Phase 1 (safe default)
- Validate cache structure before restoration in Phase 2
- Graceful degradation if cache invalid

### Risk 3: File Write Queue Conflicts

**Mitigation**:
- Flush all pending writes before retry
- Add synchronization between retry and write queue
- Test with concurrent writes

### Risk 4: Large Checkpoint Storage

**Mitigation**:
- Use zip compression
- Implement cleanup (keep last N checkpoints)
- Make checkpoint frequency configurable

---

## Future Enhancements

Beyond Phase 4, potential additions:

1. **Checkpoint Tagging**: Tag checkpoints with labels for easy finding
2. **Checkpoint Search**: Search checkpoints by content or metadata
3. **Checkpoint Export**: Export checkpoints for sharing or backup
4. **Checkpoint Diff**: Visual diff between checkpoints
5. **Branch Visualization**: Visual tree of branches
6. **Automatic Branch Naming**: AI-generated branch descriptions
7. **Checkpoint Comments**: Add user notes to checkpoints

---

## References

- **Main Roadmap**: `docs/planned_features/ROADMAP.md` (Phase 4.3)
- **Existing Design**: `docs/planned_features/version_control.md`
- **Phase 1 Details**: `checkpoint_retry/PHASE_1_SIMPLE_RETRY.md`
- **Phase 2 Details**: `checkpoint_retry/PHASE_2_AUTO_CHECKPOINTS.md`
- **Phase 3 Details**: `checkpoint_retry/PHASE_3_UI_INTEGRATION.md`
- **Phase 4 Details**: `checkpoint_retry/PHASE_4_FULL_BRANCHING.md`
- **Technical Architecture**: `checkpoint_retry/ARCHITECTURE.md`
- **Testing Strategy**: `checkpoint_retry/TESTING.md`

---

## Status Tracking

**Current Phase**: Phase 1 (Planning)
**Start Date**: 2025-10-17
**Target Completion**: TBD

**See**: `IMPLEMENTATION_LOG.md` for detailed progress tracking

---

**Last Updated**: 2025-10-17
**Version**: 1.0
**Status**: Planning - Ready to begin Phase 1 implementation
