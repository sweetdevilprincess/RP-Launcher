# TUI Refactoring Plan

**Status:** 📋 **PLANNED** - To be done after agent work is complete
**Priority:** Medium (fix technical debt, not blocking current functionality)
**Estimated Time:** 8-12 hours

---

## Background

During KnowledgeExtractionAgent implementation, we discovered that the TUI has **outdated code patterns** from previous refactorings that weren't fully applied to the presentation layer.

**Example Found:**
- TUI was using old `SessionRepository(active_path=..., branches_dir=..., archived_dir=...)` signature
- New signature is `SessionRepository(paths=..., logger=..., session_state_service=...)`
- This suggests other outdated patterns may exist

---

## Issues to Address

### 1. Outdated Initialization Patterns

**Completed:**
- ✅ Fixed SessionRepository instantiation (app.py:114-118)

**To Check:**
- [ ] Verify all service instantiations match current signatures
- [ ] Check if EntityService, EntityManager use current patterns
- [ ] Verify StatePaths usage is consistent across TUI
- [ ] Check if any other repositories were refactored but TUI wasn't updated

**Files to Review:**
```
src/presentation/tui/
  app.py                    # Main app (SessionRepository now fixed)
  components/
    entity_manager.py       # Check entity service usage
    branches_page.py        # Check branch operations
    context_panel.py        # Check state access patterns
```

---

### 2. Incomplete Bridge IPC Integration

**TODOs Found:**

**entity_manager.py:254** - "TODO: Connect to Bridge IPC"
```python
# Current: Direct file manipulation
# Should: Send IPC commands to Bridge for entity operations
```

**llm_settings_page.py:352, 369** - "TODO: Auto-save to Bridge"
```python
# Current: Changes may not persist
# Should: Send config updates via IPC
```

**Action Items:**
- [ ] Review all IPC communication patterns
- [ ] Ensure TUI is read-only (no direct file writes)
- [ ] All mutations should go through Bridge via IPC
- [ ] Verify config changes are properly saved

---

### 3. Branch Functionality Completion

**branches_page.py TODOs:**
- Line 497: "TODO: Show branch selection dialog"
- Line 502: "TODO: Show branch creation dialog"
- Line 507: "TODO: Show branch comparison view"

**Testing Needed:**
- [ ] Test branch creation from TUI
- [ ] Test branch switching with SessionStateService
- [ ] Verify branch history displays correctly
- [ ] Test branch deletion (if implemented)
- [ ] Verify sessions load correctly after branch switch

**Files:**
```
src/presentation/tui/components/
  branches_page.py          # Main branch UI
  branchable_message.py     # Per-message branch option
```

---

### 4. Missing/Incomplete Features

**From TODO scan:**

**app.py:732** - Bookmarking functionality
```python
# TODO: Implement bookmarking functionality
```

**rp_selection_screen.py:418** - Delete RP confirmation
```python
# TODO: Implement delete with confirmation dialog
```

**rp_selection_screen.py:426** - Export functionality
```python
# TODO: Implement export functionality
```

**Action Items:**
- [ ] Decide which features are MVP vs nice-to-have
- [ ] Implement or remove TODO markers
- [ ] Document unimplemented features clearly

---

### 5. Testing Gaps

**Issues:**
- TUI wasn't tested after SessionRepository refactoring
- Changes can break TUI without detection
- No integration tests for TUI ↔ Bridge communication

**Recommendations:**
- [ ] Add smoke tests for TUI initialization
- [ ] Test TUI with various RP states (branches, empty, etc.)
- [ ] Add integration tests for key workflows
- [ ] Test IPC communication paths

---

## Refactoring Checklist

### Phase 1: Audit & Document (2-3 hours)
- [ ] Search for all service instantiations in TUI
- [ ] Compare with Bridge/Factory patterns
- [ ] List all outdated patterns
- [ ] Document IPC communication flows
- [ ] Create issue list with priorities

### Phase 2: Fix Initialization Patterns (2-3 hours)
- [ ] Update service instantiations to match current signatures
- [ ] Verify logger usage is consistent
- [ ] Check StatePaths usage
- [ ] Test TUI launches successfully
- [ ] Test basic workflows (load session, view entities, etc.)

### Phase 3: Complete Bridge Integration (3-4 hours)
- [ ] Review all direct file operations in TUI
- [ ] Convert mutations to IPC commands
- [ ] Implement auto-save for settings
- [ ] Verify entity operations go through Bridge
- [ ] Test IPC error handling

### Phase 4: Branch Functionality (2-3 hours)
- [ ] Complete branch dialogs
- [ ] Test branch switching with SessionStateService
- [ ] Verify branch history works
- [ ] Test edge cases (branch from branch, etc.)
- [ ] Add branch comparison view (if needed)

### Phase 5: Testing & Documentation (1-2 hours)
- [ ] Add smoke tests
- [ ] Test end-to-end workflows
- [ ] Document TUI architecture
- [ ] Document IPC patterns
- [ ] Update README with TUI status

---

## Success Criteria

**Must Have:**
- ✅ All service instantiations use current signatures
- ✅ No direct file writes from TUI (all via IPC)
- ✅ Branch switching works correctly
- ✅ TUI launches without errors
- ✅ Core workflows tested and working

**Nice to Have:**
- Branch comparison view
- Bookmarking functionality
- Export functionality
- Comprehensive test suite

---

## Files to Modify

**High Priority:**
```
src/presentation/tui/
  app.py                           # Main app initialization
  components/
    entity_manager.py              # Entity operations
    branches_page.py               # Branch UI
    llm_settings_page.py           # Settings persistence
```

**Medium Priority:**
```
src/presentation/tui/
  components/
    context_panel.py               # State access
    branchable_message.py          # Message actions
  screens/
    rp_selection_screen.py         # RP management
```

**Low Priority:**
```
src/presentation/tui/
  components/
    chat_display.py                # Display logic
    rp_text_area.py                # Input handling
```

---

## Notes

### Architecture Principles

1. **TUI is Read-Only**
   - TUI should never write files directly
   - All mutations go through Bridge via IPC
   - TUI displays state, Bridge manages state

2. **Consistent Patterns**
   - Match initialization patterns used in Bridge
   - Use same service signatures everywhere
   - Follow established IPC patterns

3. **Defensive Coding**
   - Handle missing services gracefully
   - Provide fallbacks for IPC failures
   - Clear error messages for users

### Why This Matters

- **Maintainability**: Consistent patterns are easier to update
- **Reliability**: Proper initialization prevents runtime errors
- **Testability**: Clean architecture is easier to test
- **User Experience**: Fewer crashes, better error handling

---

## Related Work

**Dependencies:**
- None (can start after agents are done)

**Enables:**
- Better TUI testing
- Easier feature additions
- More reliable branch switching
- Cleaner codebase

---

## Next Steps

1. ✅ Finish agent work (PlotThread ✓, Knowledge ✓, remaining agents)
2. Review this plan with user
3. Begin Phase 1: Audit & Document
4. Execute refactoring phases
5. Test and document changes

---

**Created:** 2025-11-04
**Last Updated:** 2025-11-04
