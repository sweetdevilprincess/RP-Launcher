# TUI Feature Implementation Roadmap

**Created:** 2025-10-23
**Status:** Planning Complete

---

## Overview

This document provides a prioritized roadmap for implementing the remaining TUI features. The core TUI-Bridge integration is **complete and functional**. The items below are enhancements for full CRUD capabilities.

---

## Current Status Summary

### ✅ Fully Functional (Ready to Ship)
- All 9 bridge handlers implemented
- All 7 TUI pages connected via IPC
- Entity **viewing** (read-only)
- Branch **viewing and switching**
- Module configuration (full CRUD)
- Settings management (full CRUD)
- Message sending with automation pipeline
- Error handling and connection management

### ⚠️ Partially Implemented (Read-Only)
- Entity management (create/update/delete not implemented)
- Branch operations (create/compare not implemented)

---

## Implementation Priorities

### Priority 1: Entity CRUD Operations (MEDIUM)

**Why:** Users can view entities but can't modify them through the TUI

**Effort:** ~400 lines, 4-6 hours

**Impact:** Allows full entity management without manual file editing

**Dependencies:** None

**See:** `ENTITY_CRUD_IMPLEMENTATION_GUIDE.md`

**Steps:**
1. Check if `FixtureEntityRepository` has save/delete methods (if not, implement them)
2. Implement `CREATE_ENTITY`, `UPDATE_ENTITY`, `DELETE_ENTITY` in EntityHandler
3. Wire up TUI EntityManager save/delete functionality
4. Add delete button to entity drawer UI
5. Test with all entity types

**Quick Start:**
```bash
# Check repository methods
code src/domain/entities/entity_repository.py

# Implement handlers
code src/presentation/bridge/handlers/entity_handler.py

# Update TUI
code src/presentation/tui/components/entity_manager.py
```

---

### Priority 2: Branch Creation (MEDIUM)

**Why:** Users can view and switch branches but can't create new ones

**Effort:** ~250 lines, 3-4 hours

**Impact:** Enables timeline experimentation and "what-if" scenarios

**Dependencies:** Need `save_session_state()` method in SessionStateService

**See:** `BRANCH_OPERATIONS_IMPLEMENTATION_GUIDE.md` (Phase 1, 3, 4)

**Steps:**
1. Check if `SessionStateService.save_session_state()` exists (if not, add it)
2. Implement `CREATE_BRANCH` in BranchHandler
3. Add branch creation dialog to BranchesPage
4. Test branch creation and auto-switch

**Quick Start:**
```bash
# Check save method
code src/infrastructure/sessions/session_state_service.py

# Implement handler
code src/presentation/bridge/handlers/branch_handler.py

# Add UI
code src/presentation/tui/components/branches_page.py
```

---

### Priority 3: Branch Comparison (LOW)

**Why:** Nice-to-have for understanding differences between timelines

**Effort:** ~180 lines, 2-3 hours

**Impact:** Helps users compare alternate storylines

**Dependencies:** None (CREATE_BRANCH recommended first)

**See:** `BRANCH_OPERATIONS_IMPLEMENTATION_GUIDE.md` (Phase 2, 5)

**Steps:**
1. Implement `COMPARE_BRANCHES` in BranchHandler
2. Add helper methods for diff calculation
3. Add comparison screen to BranchesPage
4. Test with various branch relationships

---

## Detailed Guides

Each feature has a comprehensive implementation guide:

| Feature | Guide | Lines | Hours |
|---------|-------|-------|-------|
| Entity CRUD | `ENTITY_CRUD_IMPLEMENTATION_GUIDE.md` | ~400 | 4-6 |
| Branch Create | `BRANCH_OPERATIONS_IMPLEMENTATION_GUIDE.md` (Phase 1,3,4) | ~250 | 3-4 |
| Branch Compare | `BRANCH_OPERATIONS_IMPLEMENTATION_GUIDE.md` (Phase 2,5) | ~180 | 2-3 |

---

## Quick Reference: What Needs Implementation

### Entity Operations

**Backend (Bridge):**
```python
# File: src/domain/entities/entity_repository.py
def save_character(self, character: CharacterEntity) -> None: ...
def save_location(self, location: LocationEntity) -> None: ...
def save_organization(self, organization: OrganizationEntity) -> None: ...
def save_item(self, item: ItemEntity) -> None: ...
def delete_character(self, name: str) -> None: ...
# ... similar for other types

# File: src/presentation/bridge/handlers/entity_handler.py
def _handle_create_entity(self, request: IPCRequest) -> str: ...
def _handle_update_entity(self, request: IPCRequest) -> str: ...
def _handle_delete_entity(self, request: IPCRequest) -> str: ...
```

**Frontend (TUI):**
```python
# File: src/presentation/tui/components/entity_manager.py
def save_entity(self, entity_id: str, entity_data: dict) -> None:
    # Call CREATE_ENTITY or UPDATE_ENTITY via IPC
    ...

def delete_entity(self, entity_id: str) -> None:
    # Call DELETE_ENTITY via IPC
    ...
```

---

### Branch Operations

**Backend (Bridge):**
```python
# File: src/infrastructure/sessions/session_state_service.py
def save_session_state(self, rp_dir: Path, session_state: dict) -> None: ...

# File: src/presentation/bridge/handlers/branch_handler.py
def _handle_create_branch(self, request: IPCRequest) -> str: ...
def _handle_compare_branches(self, request: IPCRequest) -> str: ...
def _find_divergence_point(self, timeline_a, timeline_b, all_timelines) -> dict: ...
def _compare_entries(self, entries_a, entries_b, divergence_info) -> dict: ...
```

**Frontend (TUI):**
```python
# File: src/presentation/tui/components/branches_page.py
def create_branch_dialog(self) -> None:
    # Show modal for branch creation
    ...

def show_branch_comparison(self) -> None:
    # Show screen for comparing branches
    ...
```

---

## Testing Strategy

### For Each Feature

1. **Unit Tests:**
   - Test handler methods with mock data
   - Test repository save/delete operations
   - Test UI components in isolation

2. **Integration Tests:**
   - Start Bridge service
   - Start TUI
   - Test feature end-to-end
   - Verify file system changes

3. **Edge Cases:**
   - Invalid input
   - Missing data
   - Concurrent access
   - Network failures

---

## Recommended Implementation Order

### Week 1: Entity CRUD
**Goal:** Users can create, edit, and delete entities through the TUI

**Day 1-2:** Implement repository save/delete methods
**Day 3:** Implement EntityHandler CRUD methods
**Day 4:** Wire up TUI save/delete functionality
**Day 5:** Testing and bug fixes

---

### Week 2: Branch Creation
**Goal:** Users can create new timeline branches

**Day 1:** Check/implement save_session_state()
**Day 2:** Implement CREATE_BRANCH handler
**Day 3:** Add branch creation dialog UI
**Day 4:** Testing and bug fixes
**Day 5:** Documentation and polish

---

### Week 3: Branch Comparison (Optional)
**Goal:** Users can compare differences between branches

**Day 1:** Implement COMPARE_BRANCHES handler
**Day 2:** Add comparison screen UI
**Day 3:** Testing and refinement
**Day 4:** Documentation
**Day 5:** Buffer for any issues

---

## Success Criteria

### Entity CRUD ✓
- [ ] Can create new character through TUI
- [ ] Can edit existing character and save changes
- [ ] Changes persist to JSON file on disk
- [ ] Can delete character from TUI
- [ ] File is removed from entities/ directory
- [ ] Works for all entity types (character, location, organization, item)

### Branch Creation ✓
- [ ] Can create new branch from current position
- [ ] Can specify custom branch point
- [ ] New branch inherits entries up to branch point
- [ ] Can auto-switch to new branch
- [ ] Branch appears in tree visualization
- [ ] session.json is updated correctly

### Branch Comparison ✓
- [ ] Can select two branches to compare
- [ ] Shows shared entries
- [ ] Shows unique entries for each branch
- [ ] Displays divergence point
- [ ] Clear, readable diff format

---

## Post-Implementation: Advanced Features

Once core CRUD is complete, consider:

### Phase 4: Enhanced Entity Management
- Bulk operations (delete multiple entities)
- Entity search/filter
- Entity templates (create from template)
- Entity validation (required fields)

### Phase 5: Advanced Branch Features
- Branch merging
- Branch deletion (with cascade)
- Interactive timeline visualization
- Conflict resolution UI

### Phase 6: Settings Enhancements
- Provider-specific settings
- Model selection dropdown
- Temperature/token sliders
- API key validation

---

## Getting Started

### For Entity CRUD:
```bash
# Read the guide
cat docs/ENTITY_CRUD_IMPLEMENTATION_GUIDE.md

# Start with repository
code src/domain/entities/entity_repository.py

# Then handlers
code src/presentation/bridge/handlers/entity_handler.py

# Finally TUI
code src/presentation/tui/components/entity_manager.py
```

### For Branch Operations:
```bash
# Read the guide
cat docs/BRANCH_OPERATIONS_IMPLEMENTATION_GUIDE.md

# Check session service
code src/infrastructure/sessions/session_state_service.py

# Implement handlers
code src/presentation/bridge/handlers/branch_handler.py

# Add UI
code src/presentation/tui/components/branches_page.py
```

---

## Support Documents

- **Integration Status:** `TUI_BRIDGE_INTEGRATION_COMPLETE.md`
- **Known Issues:** `TUI_BRIDGE_INTEGRATION_ISSUES.md`
- **Entity Guide:** `ENTITY_CRUD_IMPLEMENTATION_GUIDE.md`
- **Branch Guide:** `BRANCH_OPERATIONS_IMPLEMENTATION_GUIDE.md`

---

**Document Version:** 1.0
**Last Updated:** 2025-10-23
**Status:** ✅ Ready for Implementation
