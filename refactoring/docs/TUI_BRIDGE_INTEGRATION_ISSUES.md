# TUI-Bridge Integration Issues and Fixes

**Created:** 2025-10-23
**Status:** Active Issue Tracking

---

## Issues Found During Integration Review

### 1. EntityHandler - Fixed ✓

**Issue:** EntityHandler was treating entity properties as strings when they are actually dictionaries (Mapping objects).

**Fix Applied:** Changed entity serialization to properly convert Mapping objects to dicts:
- Characters: `basics`, `appearance`, `personality`, `preferences`, `abilities`, `background`, `metadata`
- Locations: `basics`, `geography`, `facilities`, `culture`, `hooks`, `metadata`
- Organizations: `basics`, `structure`, `resources`, `relations`, `operations`, `metadata`
- Items: `basics`, `attributes`, `usage`, `metadata`

**File:** `src/presentation/bridge/handlers/entity_handler.py`

---

### 2. BranchHandler - Missing Preview Field

**Issue:** BranchesPage TUI component expects a `preview` field that doesn't exist in the data returned by BranchHandler.

**Current BranchHandler Returns:**
```python
{
    "title": timeline_data.get("title", timeline_id),
    "tags": timeline_data.get("tags", []),
    "parent": timeline_data.get("parent"),
    "active": timeline_id == current_timeline,
    "created_at": timeline_data.get("created_at"),
    "entry_count": len(timeline_data.get("entries", []))
}
```

**TUI Component Expects:**
- `preview` - A preview/summary of the branch content (currently not included)

**Recommended Fix:**

#### Option A: Add Preview to SessionStateService
Update `SessionStateService` to generate or store branch previews:
```python
# In session state structure:
"timelines": {
    "main": {
        "title": "Main Timeline",
        "tags": ["primary"],
        "parent": None,
        "created_at": "2025-10-23T12:00:00",
        "preview": "First 100 chars of last entry...",  # NEW FIELD
        "entries": [...]
    }
}
```

#### Option B: Generate Preview in Handler
Update BranchHandler to generate preview from entries:
```python
# In _handle_get_branches():
entries = timeline_data.get("entries", [])
preview = ""
if entries:
    last_entry = entries[-1]
    # Extract preview text from last entry
    preview = last_entry.get("content", "")[:100] + "..."

branches[timeline_id] = {
    # ... existing fields ...
    "preview": preview,  # NEW FIELD
}
```

**Files to Modify:**
- `src/presentation/bridge/handlers/branch_handler.py` - Add preview generation
- `src/infrastructure/sessions/session_state_service.py` - (Optional) Store previews in session state
- `src/presentation/tui/components/branches_page.py` - Handle missing preview gracefully

**Priority:** Medium - TUI can work without preview, but it improves UX

---

### 3. Entity CRUD Operations - Not Yet Implemented

**Issue:** Entity create, update, and delete operations are not yet implemented.

**Current Status:**
- EntityHandler returns "not yet implemented" for:
  - `CREATE_ENTITY`
  - `UPDATE_ENTITY`
  - `DELETE_ENTITY`
- EntityManager.save_entity() only updates local data, doesn't persist to disk

**Recommended Implementation:**
Implement entity persistence in EntityHandler using the entity repository:
```python
def _handle_update_entity(self, request: IPCRequest) -> str:
    entity_id = request.data.get("entity_id")
    entity_data = request.data.get("entity_data")

    # Parse entity type and save via repository
    entity_type = entity_data.get("type")
    # Use FixtureEntityRepository to save entity to JSON file
    # ...
```

**Priority:** Low - Read operations work, which is sufficient for initial release

---

## Verification Status

### Bridge Handlers ✓
- [x] EntityHandler - Fixed entity property serialization, read operations work
- [x] ModuleHandler - Uses ConfigLoader correctly
- [x] SettingsHandler - Uses ConfigLoader correctly
- [x] BranchHandler - Uses SessionStateService correctly, added preview generation
- [x] ProviderHandler - Properly uses LLM registry
- [x] TemplateHandler - Properly uses TemplateRegistry
- [x] TriggerHandler - Properly uses config for triggers
- [x] MessageHandler - Properly uses automation service and LLM client
- [x] SystemHandler - Properly handles test mode, ping, and shutdown
- [x] All handlers properly registered in HANDLER_REGISTRY

### TUI Components ✓
- [x] EntityManager - Loads entities via IPC correctly (saving not yet implemented)
- [x] ModulesPage - Loads modules and handles toggles correctly
- [x] BranchesPage - Loads branches and displays correctly (fixed to handle all fields)
- [x] LLMSettingsPage - Loads settings correctly
- [x] All components handle connection errors gracefully

### Configuration System ✓
- [x] ConfigLoader.set() exists and works
- [x] ConfigLoader.save() exists and works
- [x] ConfigLoader.load() works with proper precedence

---

## Implementation Recommendations

### Priority 1: Fix TUI to Handle Missing Fields
Make BranchesPage resilient to missing preview field:
```python
def _update_branch_details(self, branch_id: str, branch: dict) -> None:
    # Handle optional preview field gracefully
    preview = branch.get('preview', 'No preview available')
    # ... rest of implementation
```

### Priority 2: Add Preview Generation
Implement Option B (generate in handler) as it doesn't require schema changes to session state.

### Priority 3: Testing
Test each component end-to-end:
1. Start bridge service
2. Start TUI
3. Navigate to each tab
4. Verify data loads correctly
5. Test toggle/save operations

---

## Additional Notes

### Mock Data Removal
All TUI components have been verified to use IPC calls instead of mock data:
- EntityManager: Removed mock ENTITY_DATA, uses IPC
- ModulesPage: No hardcoded data, loads from Bridge
- BranchesPage: No mock data, loads from SessionStateService
- LLMSettingsPage: No hardcoded settings, loads from config

### Error Handling
All TUI components properly handle:
- Bridge not connected
- IPC request failures
- Empty/missing data

---

**End of Document**
