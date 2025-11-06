# Workstream F - Known Issues and Blockers

## Current Status

**Date:** 2025-10-20
**Status:** ✅ **RESOLVED - All 206 tests passing, circular import fixed**

---

## ✅ RESOLVED: Circular Import Dependencies (Fixed 2025-10-20)

### Resolution Summary

**Fix Applied:** Moved `EntityType` to `shared/models.py` per Option 1 recommendation below.

**Result:** All 206 Workstream F tests now passing + 337/344 total tests passing (98%)

**Files Modified:**
1. Created `src/shared/models.py` with `EntityType` enum
2. Updated `src/domain/entities/models.py` to import from shared
3. Updated `src/infrastructure/templates/state_service.py` to import from shared
4. Updated `src/domain/entities/entity_service.py` to import from shared
5. Updated `src/shared/__init__.py` to export EntityType
6. Updated `src/domain/entities/__init__.py` to re-export EntityType

**Circular dependency BROKEN** - Architecture now follows proper layered design.

---

## Historical Issue Record: Circular Import Dependencies (RESOLVED)

### Problem Description

The main refactoring folder (`C:\Users\green\Desktop\RP Claude Code\refactoring`) has circular import dependencies that prevent **all tests** from running, including Workstream F tests.

### Import Cycle

```
infrastructure/templates/state_service.py (line 9)
  ↓ imports EntityType
domain/entities/models.py
  ↓ imports EntityService
domain/entities/entity_service.py (line 9)
  ↓ imports StateTemplateService
infrastructure/templates/state_service.py
  ↓ 🔄 CIRCULAR DEPENDENCY
```

### Full Error Stack

```
ImportError: cannot import name 'StateTemplateService' from partially initialized module
'refactoring.src.infrastructure.templates.state_service'
(most likely due to a circular import)
```

### Impact

- ❌ **Cannot run ANY tests** in main refactoring folder
- ❌ Cannot verify Workstream F code integration
- ❌ Cannot verify Workstream E/G code integration
- ❌ All pytest imports fail at module loading stage

### Affected Components

**Everything that imports from `automation` namespace:**
- `automation/triggers/*` (via FrequencyTracker → JsonStore → infrastructure)
- `automation/templates/*` (via TemplateLoader → infrastructure)
- `automation/services/*` (via factory imports)
- All test files

### Additional Import Issues Found

1. **Missing exports in `shared/interfaces/__init__.py`:**
   - Attempted to import `CounterService` (doesn't exist)
   - Attempted to import `TimeService` (doesn't exist)
   - **Fixed:** Removed non-existent imports

2. **Missing exports in `infrastructure/templates/__init__.py`:**
   - `StateTemplateService` not exported
   - `TemplateRenderer` not exported
   - **Fixed:** Added proper exports

3. **Factory imports broken:**
   - `automation/factory.py` imports `AgentRegistry` (unknown location)
   - Triggers cascade of import errors
   - **Workaround:** Commented out factory import in `automation/__init__.py`

## Workstream F Specific Issues

### 1. JsonStore Usage (RESOLVED by Workstream D)

**Files affected:**
- `src/automation/triggers/frequency_tracker.py`
- `src/automation/templates/template_loader.py`

**Original problem:**
- Called `JsonStore()` with no arguments (requires `root` and `logger`)
- Used non-existent methods `read_json()` and `write_json()`

**Resolution:**
- **FrequencyTracker:** Workstream D fixed to use JsonStore properly with root/logger
- **TemplateLoader:** Workstream E fixed with standard `json.load()` approach

### 2. Test File Path Issues (BLOCKED)

**Problem:** Tests cannot run due to circular imports, so path issues cannot be validated.

**Affected test files:**
- `tests/automation/triggers/test_pattern_loader.py` (created, not verified)
- `tests/automation/triggers/test_registry.py` (created, not verified)
- `tests/automation/templates/test_template_loader.py` (created, not verified)
- `tests/automation/templates/test_template_registry.py` (not created)
- `tests/automation/templates/test_narrative_template_manager.py` (not created)

## Test Status

### Tests That Passed (in isolation before circular import issue)

**Trigger System (102 tests):**
- ✅ KeywordEvaluator: 19/19 passing
- ✅ RegexEvaluator: 21/21 passing
- ✅ SemanticEvaluator: 20/20 passing
- ✅ TriggerCoordinator: 16/16 passing
- ✅ FrequencyTracker: 26/26 passing

**Template System (25 tests):**
- ✅ TemplateCache: 25/25 passing

**Loading/Registry (56 tests):**
- ✅ PatternLoader: 32/32 passing
- ✅ TriggerRegistry: 24/24 passing

**Total verified:** 183/183 tests passing ✅

### Tests Created But Not Verified (blocked by imports)

- 📝 TemplateLoader: ~25 tests created, cannot run
- ⏸️ TemplateRegistry: not yet created
- ⏸️ NarrativeTemplateManager: not yet created

## Resolution Options

### Option 1: Fix Circular Import (Recommended for main folder)

**Approach:** Break the cycle between `domain/entities` and `infrastructure/templates`

**Possible solutions:**
1. **Move EntityType** out of `domain/entities/models.py` into a separate shared module
2. **Use Protocol/ABC** instead of concrete import in EntityService
3. **Lazy import** StateTemplateService inside method instead of module level
4. **Restructure dependencies** so StateTemplateService doesn't need EntityType

**Pros:** Fixes the architectural problem permanently
**Cons:** Requires refactoring existing code outside Workstream F scope

### Option 2: Test in Workstream D's Worktree (Quick validation)

**Approach:** Run tests in `.worktrees/refactor-d/refactoring/` where imports worked

**Pros:** Quick validation of Workstream F code
**Cons:** Doesn't fix main folder issue

### Option 3: Mock/Stub Imports (Workaround for tests)

**Approach:** Create test-specific import mocks to bypass circular dependency

**Pros:** Tests can run
**Cons:** Doesn't validate real integration, just unit behavior

## Recommendations

### Immediate Actions

1. **Document issue** (this file) ✅
2. **Notify Workstream D** about circular import blocker
3. **Commit Workstream F code** to their worktree (tests passed there)
4. **Create integration test plan** for when circular import is fixed

### Short-term (This Sprint)

1. **Fix circular import** in main refactoring folder
2. **Verify all 183+ tests** pass in main folder
3. **Run integration tests** with real dependencies

### Long-term (Architecture)

1. **Review dependency graph** across all workstreams
2. **Establish import guidelines** to prevent future cycles
3. **Add CI check** for circular dependencies

## Workarounds Applied

### Temporary Changes to Allow Work to Continue

1. **`src/automation/__init__.py`:**
   ```python
   # Commented out to bypass factory import errors
   # from .factory import create_automation_service
   ```

2. **`src/shared/interfaces/__init__.py`:**
   ```python
   # Removed non-existent imports
   # from .counter_service import CounterService
   # from .time_service import TimeService
   ```

3. **`src/infrastructure/templates/__init__.py`:**
   ```python
   # Added missing exports
   from .state_service import StateTemplateService
   from .template_renderer import TemplateRenderer
   ```

**⚠️ IMPORTANT:** These are temporary workarounds. Real fix requires breaking the circular import.

## Files Modified by Workstream E

### Bug Fixes
- `src/automation/triggers/frequency_tracker.py` - Fixed JsonStore usage (OVERWRITTEN by Workstream D's fix)
- `src/automation/templates/template_loader.py` - Fixed JsonStore usage (simple json approach)

### Import Fixes
- `src/shared/interfaces/__init__.py` - Removed non-existent imports
- `src/infrastructure/templates/__init__.py` - Added missing exports
- `src/automation/__init__.py` - Commented out broken factory import

### Tests Created
- `tests/automation/triggers/test_pattern_loader.py` - 32 tests
- `tests/automation/triggers/test_registry.py` - 24 tests
- `tests/automation/templates/test_template_loader.py` - 25 tests (not verified)

### Documentation Created
- `docs/EXTENDING_TRIGGERS.md` - Complete extension guide
- `docs/EXTENDING_TEMPLATES.md` - Complete extension guide
- `docs/WORKSTREAM_F_ISSUES.md` - This file

## Next Steps

1. ✅ Document issues (completed)
2. ⏭️ Create Workstream F completion checklist
3. ⏭️ Update Workstream D on findings
4. ⏭️ Fix circular import in main refactoring folder
5. ⏭️ Re-run all tests to verify
6. ⏭️ Complete remaining template tests
7. ⏭️ Integration testing

## Contact

For questions about these issues:
- **Circular imports:** Architectural decision needed (both workstreams)
- **Workstream F code:** Workstream D (original implementer)
- **Workstream F tests/docs:** Workstream E (collaborator)
