# EntityService Refactoring - Migration Impact Analysis

**Date**: 2025-11-06
**Context**: Impact assessment for splitting EntityService into 6 focused services
**Scope**: All files that would need changes during migration

---

## Executive Summary

**Total Files to Modify:** 8 production files + 2 test files = **10 files**

**Effort Estimate:**
- Phase 1 (Create new services + facade): 2 hours
- Phase 2 (Migrate callers): 2-3 hours
- Phase 3 (Remove facade, cleanup): 1 hour
- **Total: 5-6 hours**

**Risk Level:** MEDIUM
- Most changes are simple import/instantiation updates
- One complex file (automation_service.py) needs careful migration
- Good test coverage exists

---

## Files Requiring Changes

### 1. Core Service Files (NEW - To Be Created)

**Location:** `src/domain/entities/`

#### 1.1 entity_query_service.py (NEW)
```python
"""Query operations for entities."""
class EntityQueryService:
    def list_characters() -> list[CharacterEntity]
    def list_locations() -> list[LocationEntity]
    def list_organizations() -> list[OrganizationEntity]
    def list_items() -> list[ItemEntity]
    def list_memory_logs() -> list[MemoryLog]
    def get_character(name: str) -> CharacterEntity | None
    def stats() -> EntityStats
```

**Extracted from:** EntityService lines 58-89

---

#### 1.2 entity_detection_service.py (NEW)
```python
"""Entity mention detection in text."""
class EntityDetectionService:
    def detect_mentions(text: str) -> set[str]
```

**Extracted from:** EntityService lines 91-115

---

#### 1.3 entity_automation_service.py (NEW)
**Location:** `src/automation/entities/` (Automation layer, not Domain)

```python
"""Entity preparation for automation pipeline."""
class EntityAutomationService:
    def prepare_entities(context: AutomationContext) -> AutomationContext
```

**Extracted from:** EntityService lines 192-393

---

#### 1.4 entity_template_service.py (NEW)
```python
"""Template generation for entity creation."""
class EntityTemplateService:
    def generate_entity_card_template(name: str, entity_type: EntityType) -> str
    def generate_character_preferences_template(name: str) -> dict[str, Any]
```

**Extracted from:** EntityService lines 398-402

---

#### 1.5 entity_preference_generation_service.py (NEW)
```python
"""AI-powered preference generation for characters."""
class EntityPreferenceGenerationService:
    def generate_character_preferences(character_name: str) -> PreferenceResult
```

**Extracted from:** EntityService lines 407-469

---

#### 1.6 entity_mutation_service.py (NEW)
```python
"""Entity persistence operations."""
class EntityMutationService:
    def save_character(character: CharacterEntity) -> CharacterEntity
    def append_memory_entry(character_name: str, entry: dict) -> MemoryLog
```

**Extracted from:** EntityService lines 474-484

---

### 2. Files Requiring Import Changes

#### 2.1 src/domain/entities/__init__.py

**Current:**
```python
from .entity_service import EntityService

__all__ = [
    "EntityService",
    # ... other exports
]
```

**After Phase 1 (Facade approach):**
```python
from .entity_service import EntityService  # Deprecated facade
from .entity_query_service import EntityQueryService
from .entity_detection_service import EntityDetectionService
from .entity_template_service import EntityTemplateService
from .entity_preference_generation_service import EntityPreferenceGenerationService
from .entity_mutation_service import EntityMutationService

__all__ = [
    "EntityService",  # Deprecated - use specific services
    "EntityQueryService",
    "EntityDetectionService",
    "EntityTemplateService",
    "EntityPreferenceGenerationService",
    "EntityMutationService",
    # ... other exports
]
```

**After Phase 3 (Remove facade):**
```python
# EntityService removed entirely
from .entity_query_service import EntityQueryService
from .entity_detection_service import EntityDetectionService
from .entity_template_service import EntityTemplateService
from .entity_preference_generation_service import EntityPreferenceGenerationService
from .entity_mutation_service import EntityMutationService

__all__ = [
    "EntityQueryService",
    "EntityDetectionService",
    "EntityTemplateService",
    "EntityPreferenceGenerationService",
    "EntityMutationService",
    # ... other exports
]
```

**Lines Changed:** ~10 lines
**Complexity:** Low

---

#### 2.2 src/automation/__init__.py (NEW)

**Add exports for automation layer service:**
```python
from .entities.entity_automation_service import EntityAutomationService

__all__ = [
    "EntityAutomationService",
    # ... other automation exports
]
```

**Lines Changed:** ~3 lines
**Complexity:** Low

---

### 3. Files Requiring Instantiation Changes

#### 3.1 src/automation/factory.py

**Current (lines 219-230):**
```python
entity_repository = FixtureEntityRepository(
    rp_dir=rp_dir,
    session_state_service=session_state_service,
)
template_service = StateTemplateService()
entity_service = EntityService(
    repository=entity_repository,
    templates=template_service,
    logger=logger,
    session_state=session_state_service,  # For scene context access
    rp_dir=rp_dir,  # For entity file path resolution
)
```

**After Phase 1 (Facade):**
```python
entity_repository = FixtureEntityRepository(
    rp_dir=rp_dir,
    session_state_service=session_state_service,
)
template_service = StateTemplateService()

# Use facade during migration
entity_service = EntityService(
    repository=entity_repository,
    templates=template_service,
    logger=logger,
    session_state=session_state_service,
    rp_dir=rp_dir,
)
```

**After Phase 2 (New services):**
```python
entity_repository = FixtureEntityRepository(
    rp_dir=rp_dir,
    session_state_service=session_state_service,
)

# Create focused services
entity_query_service = EntityQueryService(repository=entity_repository, logger=logger)
entity_detection_service = EntityDetectionService(
    repository=entity_repository,
    session_state=session_state_service,
    rp_dir=rp_dir,
    logger=logger
)
entity_automation_service = EntityAutomationService(
    query_service=entity_query_service,
    detection_service=entity_detection_service,
    session_state=session_state_service,
    rp_dir=rp_dir,
    logger=logger
)
```

**Lines Changed:** ~20 lines
**Complexity:** Medium
**Used By:** `AutomationService.__init__()` - needs to receive `entity_automation_service`

---

#### 3.2 src/presentation/bridge/bridge_service.py

**Current (line 128):**
```python
self.entity_service = EntityService()
```

**After Phase 1 (Facade):**
```python
self.entity_service = EntityService()  # Deprecated facade
```

**After Phase 2 (New services):**
```python
# Create entity repository
entity_repository = FixtureEntityRepository(
    rp_dir=self.rp_dir,
    session_state_service=self.session_state_service
)

# Create focused services
self.entity_query_service = EntityQueryService(
    repository=entity_repository,
    logger=self.logger
)

# EntityHandler only uses query methods, so only need query service
```

**Lines Changed:** ~10 lines
**Complexity:** Low
**Used By:** `EntityHandler` - needs to use `bridge.entity_query_service`

---

### 4. Files Requiring Method Call Changes

#### 4.1 src/automation/services/automation_service.py

**Current (line 85):**
```python
domain_context = self._entity_service.prepare_entities(hydrated_context)
```

**After Phase 2:**
```python
domain_context = self._entity_automation_service.prepare_entities(hydrated_context)
```

**Changes Required:**
1. Update `__init__()` to accept `entity_automation_service` instead of `entity_service`
2. Store as `self._entity_automation_service`
3. Update method call (line 85)

**Current __init__ (lines 30-42):**
```python
def __init__(
    self,
    *,
    config: ConfigService,
    logger: LoggingService,
    entity_service: EntityService,  # ← Change this
    session_service: SessionService,
    prompt_builder: PromptBuilder,
    agent_runner: AgentRunner,
    file_access: FileAccessService,
) -> None:
    self._config = config
    self._logger = logger
    self._entity_service = entity_service  # ← And this
    # ...
```

**After Phase 2:**
```python
def __init__(
    self,
    *,
    config: ConfigService,
    logger: LoggingService,
    entity_automation_service: EntityAutomationService,  # ← Changed
    session_service: SessionService,
    prompt_builder: PromptBuilder,
    agent_runner: AgentRunner,
    file_access: FileAccessService,
) -> None:
    self._config = config
    self._logger = logger
    self._entity_automation_service = entity_automation_service  # ← Changed
    # ...
```

**Lines Changed:** ~5 lines
**Complexity:** Low
**Impact:** Must also update `factory.py` where `AutomationService` is created

---

#### 4.2 src/presentation/bridge/handlers/entity_handler.py

**Current (lines 57-60):**
```python
characters = self.bridge.entity_service.list_characters()
locations = self.bridge.entity_service.list_locations()
organizations = self.bridge.entity_service.list_organizations()
items = self.bridge.entity_service.list_items()
```

**After Phase 2:**
```python
characters = self.bridge.entity_query_service.list_characters()
locations = self.bridge.entity_query_service.list_locations()
organizations = self.bridge.entity_query_service.list_organizations()
items = self.bridge.entity_query_service.list_items()
```

**Lines Changed:** 4 lines
**Complexity:** Low (simple find-replace)

---

#### 4.3 src/presentation/bridge/handlers/base.py

**Current (line 34):**
```python
data = self.bridge.entity_service.get_data()
```

**Issue:** This method doesn't exist in EntityService! This appears to be dead code or a bug.

**After Phase 2:**
- If this line is actually executed, it would throw AttributeError
- Likely dead code that should be removed or is a copy-paste error
- Need to verify if this handler is used

**Lines Changed:** 0 or 1 (remove if dead)
**Complexity:** Low (needs verification)

---

### 5. Test Files Requiring Changes

#### 5.1 tests/domain/entities/test_entity_service_preferences.py

**Current imports:**
```python
from refactoring.src.domain.entities.entity_service import EntityService
```

**Usage:**
- Tests `EntityService.generate_character_preferences()` method
- 8 test functions all create EntityService instances

**After Phase 2:**
```python
from refactoring.src.domain.entities.entity_preference_generation_service import (
    EntityPreferenceGenerationService
)
```

**Changes:**
- Update imports
- Replace `EntityService` with `EntityPreferenceGenerationService` in all tests
- Tests remain largely the same (mocking behavior doesn't change)

**Lines Changed:** ~15 lines (imports + 8 instantiations)
**Complexity:** Low (mechanical changes)

---

#### 5.2 tests/entities/test_entity_service.py

**Current imports:**
```python
from refactoring.src.domain.entities.entity_service import EntityService
```

**Usage:**
- Tests basic EntityService functionality
- Creates EntityService with repository

**After Phase 2:**
- Need to determine which service is being tested
- If testing queries → use EntityQueryService
- If testing detection → use EntityDetectionService
- Might need to split into multiple test files

**Lines Changed:** ~10-20 lines
**Complexity:** Medium (may need to split tests)

---

### 6. Files NOT Requiring Changes

#### 6.1 src/automation/agents/implementations/memory_creation_agent.py

**Current (line 325):**
```python
repository.append_memory_entry(character, memory_entry)
```

**Note:** This calls the repository directly, NOT EntityService!

**No changes needed** - agent already bypasses EntityService

---

## Migration Phases

### Phase 1: Create New Services + Facade (Zero Breaking Changes)

**Files to Create:**
1. `src/domain/entities/entity_query_service.py` (NEW)
2. `src/domain/entities/entity_detection_service.py` (NEW)
3. `src/automation/entities/entity_automation_service.py` (NEW)
4. `src/domain/entities/entity_template_service.py` (NEW)
5. `src/domain/entities/entity_preference_generation_service.py` (NEW)
6. `src/domain/entities/entity_mutation_service.py` (NEW)

**Files to Modify:**
1. `src/domain/entities/entity_service.py` - Convert to facade that delegates
2. `src/domain/entities/__init__.py` - Export new services

**Test Changes:**
- None (facade maintains backward compatibility)

**Effort:** 2 hours
**Risk:** Low

---

### Phase 2: Migrate Callers (Gradual, One File at a Time)

**Files to Modify (in order):**

1. **src/automation/factory.py** (Medium complexity)
   - Create new service instances
   - Pass `EntityAutomationService` to `AutomationService`
   - Lines changed: ~20

2. **src/automation/services/automation_service.py** (Low complexity)
   - Update `__init__` signature
   - Update method call
   - Lines changed: ~5

3. **src/presentation/bridge/bridge_service.py** (Low complexity)
   - Create `EntityQueryService` instance
   - Remove old `EntityService` instance
   - Lines changed: ~10

4. **src/presentation/bridge/handlers/entity_handler.py** (Low complexity)
   - Update method calls from `.entity_service.` to `.entity_query_service.`
   - Lines changed: 4

5. **tests/domain/entities/test_entity_service_preferences.py** (Low complexity)
   - Update imports
   - Update instantiations
   - Lines changed: ~15

6. **tests/entities/test_entity_service.py** (Medium complexity)
   - Split tests or update imports
   - Lines changed: ~20

**Effort:** 2-3 hours
**Risk:** Medium (changes automation pipeline initialization)

---

### Phase 3: Remove Facade (Breaking Change)

**Files to Modify:**
1. `src/domain/entities/entity_service.py` - DELETE
2. `src/domain/entities/__init__.py` - Remove EntityService export

**Verification:**
- Ensure no imports of `EntityService` remain
- Run full test suite
- Verify automation pipeline works end-to-end

**Effort:** 1 hour
**Risk:** Low (all callers already migrated in Phase 2)

---

## Summary by File Type

### Production Code: 8 Files

| File | Type | Complexity | Lines Changed |
|------|------|------------|---------------|
| domain/entities/__init__.py | Import | Low | ~10 |
| automation/__init__.py | Import | Low | ~3 |
| automation/factory.py | Instantiation | Medium | ~20 |
| automation/services/automation_service.py | Method call | Low | ~5 |
| presentation/bridge/bridge_service.py | Instantiation | Low | ~10 |
| presentation/bridge/handlers/entity_handler.py | Method call | Low | 4 |
| presentation/bridge/handlers/base.py | Verification | Low | 0-1 |
| domain/entities/entity_service.py | Refactor → Delete | High | All |

**Total Production Lines Changed:** ~60 lines (excluding new services)

---

### Test Code: 2 Files

| File | Complexity | Lines Changed |
|------|------------|---------------|
| test_entity_service_preferences.py | Low | ~15 |
| test_entity_service.py | Medium | ~20 |

**Total Test Lines Changed:** ~35 lines

---

### New Files: 6 Services

| File | Lines | Complexity |
|------|-------|------------|
| entity_query_service.py | ~60 | Low |
| entity_detection_service.py | ~90 | Low |
| entity_automation_service.py | ~130 | Medium |
| entity_template_service.py | ~50 | Low |
| entity_preference_generation_service.py | ~90 | Medium |
| entity_mutation_service.py | ~70 | Low |

**Total New Lines:** ~490 lines (extracted from EntityService's 490 lines)

---

## Risk Assessment

### Low Risk Changes (Can do immediately)
- Import updates in `__init__.py` files
- Method call updates in `entity_handler.py` (simple find-replace)
- Test file updates (mechanical changes)

### Medium Risk Changes (Need careful testing)
- `automation/factory.py` - Creates core services for pipeline
- `automation/services/automation_service.py` - Core automation logic
- Splitting test files

### High Risk Changes (Need extensive testing)
- None! All changes are isolated and testable

---

## Testing Strategy

### Unit Tests
- Test each new service independently with mocked dependencies
- Reuse existing EntityService tests, split by responsibility

### Integration Tests
- Test automation pipeline end-to-end with new services
- Test entity handler end-to-end from TUI
- Test preference generation with real LLM calls

### Regression Tests
- Run full test suite after each phase
- Verify no behavioral changes (only structural)

---

## Rollback Strategy

### Phase 1 (Facade)
- **Rollback:** Simply don't expose new services, keep using facade
- **Risk:** None (backward compatible)

### Phase 2 (Migration)
- **Rollback:** Revert individual file changes one at a time
- **Risk:** Low (changes are isolated per file)

### Phase 3 (Remove Facade)
- **Rollback:** Restore EntityService.py from git history
- **Risk:** Low (all callers already migrated)

---

## Timeline Estimate

### Conservative Estimate (with testing)
- **Phase 1:** 1 day (2 hours implementation + testing)
- **Phase 2:** 2 days (3 hours implementation + thorough testing)
- **Phase 3:** 0.5 day (1 hour + verification)
- **Total:** 3.5 days

### Aggressive Estimate (minimal testing)
- **Phase 1:** 2 hours
- **Phase 2:** 3 hours
- **Phase 3:** 1 hour
- **Total:** 6 hours (1 day)

---

## Recommendation

**Proceed with refactoring?** YES, with phased approach

**Reasons:**
1. **Limited scope:** Only 10 files affected
2. **Clear migration path:** Three phases with zero breaking changes until Phase 3
3. **Good test coverage:** Can verify behavior doesn't change
4. **High value:** Makes codebase more maintainable long-term

**When to do it:**
- **Not urgent:** Current code works fine
- **Good time:** During a dedicated refactoring sprint
- **Bad time:** Before a major feature release

---

## Conclusion

**Refactoring EntityService is feasible** with:
- 10 files to modify
- ~95 total lines changed (excluding new service creation)
- 5-6 hours effort
- Medium risk (well-contained)

The phased approach with a facade ensures **zero breaking changes** until all callers are migrated, making this a **safe refactoring**.

---

**Document Status**: COMPLETE
**Files Identified**: 10 (8 production + 2 test)
**Recommended Approach**: Phased migration with facade
**Estimated Effort**: 5-6 hours
