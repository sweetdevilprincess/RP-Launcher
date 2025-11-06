# Phase 2: UI Integration - Implementation Guide

**Phase**: 2 (UI Enhancement)
**Goal**: Add TUI screens for managing sessions visually
**Timeline**: 3 days
**Status**: Planned
**Created**: 2025-10-17

---

## Overview

Phase 2 adds visual session management to the TUI, making it easy to view, switch, and manage sessions without using slash commands.

**Prerequisites**: Phase 1 complete (session log system working)

---

## Goals

### Primary Goals

1. **Session List Screen** - View all sessions in a scrollable list
2. **Session Switcher** - Easy switching between sessions
3. **Tag Browser** - Filter sessions by tags
4. **Session Details** - View session metadata and history preview

### Secondary Goals

5. **Branch Tree Visualization** - Visual representation of session branches
6. **Session Deletion** - Delete old archived sessions
7. **Session Export** - Export sessions for backup/sharing

---

## Features to Implement

### 1. Session List Screen

**Location**: New tab in TUI or modal overlay

**Layout**:
```
┌─ Sessions ────────────────────────────────────────┐
│                                                    │
│  ● session_main (Response 50) [ACTIVE]           │
│    └─ Tags: main-timeline                        │
│                                                    │
│  Branches:                                        │
│    session_romance (Response 48)                 │
│    └─ Tags: romance, exploring-options           │
│    └─ "Exploring romantic relationship"          │
│                                                    │
│    session_action (Response 47)                  │
│    └─ Tags: action, high-stakes                  │
│                                                    │
│  Archived:                                        │
│    retry_20251017_103500 (Response 44)          │
│    └─ Tags: retry, better-dialogue               │
│                                                    │
│    checkpoint_before_choice (Response 40)        │
│    └─ Tags: checkpoint, important                │
│                                                    │
│  [Switch] [Details] [Delete] [Close]            │
└────────────────────────────────────────────────────┘
```

**Interactions**:
- Arrow keys: Navigate sessions
- Enter: Switch to selected session
- D: View details
- X: Delete session (with confirmation)
- Esc: Close

### 2. Tag Filter

**Feature**: Filter sessions by tags

**UI Addition**:
```
Filter: [romance______] (type tag name)

Showing 2 sessions tagged "romance"
```

**Implementation**: Use SessionManager.list_sessions(tag_filter="romance")

### 3. Session Details Modal

**Shows**:
- Session metadata (created, last modified, response count)
- All tags
- Description
- First few messages preview
- Parent session (if branched)
- Branch point (if branched)

**Layout**:
```
┌─ Session Details: romance_path ──────────────────┐
│                                                   │
│  Type: Branch                                    │
│  Created: 2025-10-17 10:35:00                   │
│  Modified: 2025-10-17 11:20:00                  │
│  Response Count: 48                             │
│  Parent: main (branched from response 45)       │
│                                                   │
│  Tags: romance, exploring-options, chapter-2    │
│                                                   │
│  Description:                                    │
│  "Exploring romantic relationship with Silas"   │
│                                                   │
│  Recent Messages:                                │
│  - Response 48: "I lean closer..."              │
│  - Response 47: "Silas's eyes meet mine..."     │
│  - Response 46: "The tension builds..."         │
│                                                   │
│  [Switch to This] [Close]                       │
└───────────────────────────────────────────────────┘
```

### 4. Branch Tree Visualization (Advanced)

**Goal**: Visual tree showing branch relationships

**Example**:
```
main
├─ 45: romance_path
│   └─ 50: romance_alt
└─ 42: action_path
    └─ 48: stealth_route
```

**Implementation**: Parse parent_session and branch_point from all sessions

---

## Technical Implementation

### New TUI Components

**Files to Create**:
- `src/tui/session_list.py` - Session list widget
- `src/tui/session_details.py` - Session details modal
- `src/tui/tag_filter.py` - Tag filtering component

**Files to Modify**:
- `src/rp_client_tui.py` - Add sessions tab/modal trigger

### Session List Widget

```python
from textual.widgets import DataTable
from textual.screen import Screen

class SessionListScreen(Screen):
    """Screen for managing sessions."""

    def compose(self):
        yield Header()
        yield DataTable()
        yield Footer()

    def on_mount(self):
        """Load sessions on mount."""
        from src.session_manager import SessionManager

        session_manager = SessionManager(self.app.rp_dir)
        sessions = session_manager.list_sessions()

        # Populate table
        table = self.query_one(DataTable)
        table.add_columns("Name", "Type", "Responses", "Tags")

        for session in sessions:
            table.add_row(
                session["name"],
                session["type"],
                str(session["response_count"]),
                ", ".join(session["tags"][:3])
            )

    def on_data_table_row_selected(self, event):
        """Handle session selection."""
        # Switch to selected session
        pass
```

### Keyboard Shortcuts

Add to TUI:
- `Ctrl+S` - Open session list
- `Ctrl+B` - Create branch from current point
- `Ctrl+R` - Retry (quick access)

---

## User Workflows

### Workflow 1: Browse and Switch Sessions

1. User presses `Ctrl+S`
2. Session list opens
3. User navigates with arrow keys
4. User presses Enter on "romance_path"
5. TUI switches to that session
6. Chat reloads with romance_path messages

### Workflow 2: View Session Details

1. User opens session list
2. User selects session and presses `D`
3. Details modal opens
4. User reads metadata and tags
5. User presses `Esc` to close

### Workflow 3: Delete Old Retries

1. User opens session list
2. User filters by tag "retry"
3. User selects old retry and presses `X`
4. Confirmation dialog appears
5. User confirms deletion
6. Session removed from list

---

## Testing Plan

### Manual Tests

- [ ] Open session list, verify all sessions shown
- [ ] Filter by tag, verify correct sessions shown
- [ ] Switch to branch, verify chat reloads
- [ ] View session details, verify metadata correct
- [ ] Delete archived session, verify removed
- [ ] Navigate with keyboard shortcuts

### Integration Tests

- [ ] Test session list loads correctly
- [ ] Test tag filtering works
- [ ] Test session switching updates TUI
- [ ] Test deletion removes file

---

## Timeline

**Day 1**: Session list widget
- Create SessionListScreen
- Populate with data from SessionManager
- Basic navigation

**Day 2**: Tag filtering & details
- Add tag filter input
- Create SessionDetailsModal
- Wire up details view

**Day 3**: Polish & testing
- Add keyboard shortcuts
- Delete functionality
- Manual testing
- Documentation

---

## Success Criteria

Phase 2 is complete when:

- ✅ Session list screen works
- ✅ Tag filtering works
- ✅ Session switching from UI works
- ✅ Session details modal works
- ✅ Keyboard shortcuts work
- ✅ TUI reloads correctly after switch
- ✅ All manual tests pass
- ✅ User documentation updated

---

## Future Enhancements (Phase 3+)

- Branch tree visualization
- Session comparison view
- Session merge functionality
- Session export/import
- Session statistics

---

## References

- **Phase 1**: `PHASE_1_SESSION_LOGS.md`
- **Architecture**: `ARCHITECTURE.md`
- **Main Roadmap**: `ROADMAP.md`

---

**Last Updated**: 2025-10-17
**Version**: 1.0 (Placeholder)
**Status**: Planned (awaiting Phase 1 completion)
