# Architecture Violations Analysis

**Date**: 2025-11-06
**Analyst**: Claude (Systematic Codebase Analysis)
**Context**: Phase 3 verification following SYSTEMATIC_CODEBASE_ANALYSIS_PLAN.md

---

## Executive Summary

**Two identified violations:**

1. **ChatlogOrganizer in Domain Layer** - ⚠️ **CONFIRMED VIOLATION** (Medium Severity)
   - Current: `src/domain/sessions/chatlog_organizer.py`
   - Should be: `src/infrastructure/sessions/` or `src/presentation/export/`
   - Issue: Performs infrastructure concerns (file I/O, directory management)

2. **EntityService has Too Many Responsibilities** - ⚠️ **CONFIRMED VIOLATION** (Medium Severity)
   - Has 5 distinct responsibilities violating Single Responsibility Principle
   - Mixing queries, mutations, templates, AI generation, and automation integration
   - Makes testing and maintenance difficult

---

## 1. ChatlogOrganizer Architecture Violation

### 1.1 Current Location

**Path:** `src/domain/sessions/chatlog_organizer.py`

**Layer:** Domain (INCORRECT)

### 1.2 What ChatlogOrganizer Does

**Purpose:** Organizes session messages into chapter-based chatlog files for export/navigation

**Operations:**
```python
class ChatlogOrganizer:
    # File I/O operations
    def update_chapter_file(session_id, chapter_number, chapter_title)
        # Writes to sessions/chatlogs/{session_id}/chapter_N.json

    def append_message_to_chapter(session_id, message)
        # Appends to chapter file with atomic write

    def finalize_chapter(session_id, chapter_number, chapter_title)
        # Updates chapter file with title

    # Query operations
    def get_chapter_info(session_id, chapter_number)
        # Reads chapter metadata

    def list_chapters(session_id)
        # Lists all chapter files

    # File operations
    def _write_chapter_file(session_id, chapter_number, data)
        # Atomic write: temp file + rename
        # Creates directories
        # Handles encoding

    def _read_chapter_file(session_id, chapter_number)
        # Reads JSON from file
```

### 1.3 Infrastructure Concerns (Not Domain Logic)

**File System Operations:**
- Creates directory structure: `sessions/chatlogs/{session_id}/`
- Writes JSON files: `chapter_1.json`, `chapter_2.json`, etc.
- Atomic writes using temp files + rename pattern
- Directory existence checks and creation
- File path resolution

**Code Example:**
```python
def _write_chapter_file(self, session_id, chapter_number, chapter_data):
    chapter_file = self._get_chapter_file_path(session_id, chapter_number)

    # Ensure directory exists ← Infrastructure concern
    chapter_file.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically (temp file + rename) ← Infrastructure concern
    temp_file = chapter_file.with_suffix(".json.tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(chapter_data, f, indent=2, ensure_ascii=False)
    temp_file.replace(chapter_file)  # Atomic operation
```

**Dependencies:**
- `StatePaths` (infrastructure) - for file path resolution
- `JsonStore` (infrastructure) - for reading session data
- Direct file I/O (`open()`, `json.dump()`, `Path.mkdir()`)

### 1.4 Why This is a Violation

**Domain Layer Should:**
- Define business entities and rules
- Pure logic without infrastructure dependencies
- Technology-agnostic

**Domain Layer Should NOT:**
- Perform file I/O operations
- Manage directory structures
- Handle encoding, temp files, atomic writes
- Deal with file system paths

**ChatlogOrganizer is:**
- ❌ Performing file I/O (reading/writing JSON files)
- ❌ Managing directory structure (mkdir, path resolution)
- ❌ Handling infrastructure concerns (atomic writes, temp files)
- ❌ Depending on infrastructure layer (StatePaths, JsonStore)
- ✅ Using domain models (SessionMessage, SessionData) - only domain aspect

### 1.5 Where It Should Be

**Option 1: Infrastructure Layer** (RECOMMENDED)

**Path:** `src/infrastructure/sessions/chatlog_organizer.py`

**Justification:**
- Primarily performs file I/O operations
- Manages file system structure
- Similar to other infrastructure components (JsonStore, MarkdownStore, FileManager)
- Can still use domain models (SessionMessage) as data structures

**Similar Components:**
- `JsonStore` - infrastructure/filesystem/json_store.py (writes JSON files)
- `MarkdownStore` - infrastructure/filesystem/markdown_store.py (writes markdown files)
- `FileManager` - infrastructure/filesystem/file_manager.py (coordinates file operations)

---

**Option 2: Presentation Layer** (Alternative)

**Path:** `src/presentation/export/chatlog_exporter.py`

**Justification:**
- Formats data for export/presentation
- Used only by BridgeService (presentation layer)
- Not core business logic
- Export/formatting concern

**Decision Criteria:**
- If view as "export formatting" → Presentation
- If view as "organized persistence" → Infrastructure

**Recommendation:** Infrastructure is more appropriate because:
1. Primary concern is file persistence, not UI formatting
2. Used for data organization, not just export
3. Similar to other storage components already in infrastructure

### 1.6 Impact of Violation

**Current Problems:**

1. **Violates Clean Architecture:**
   - Domain layer depending on infrastructure concerns
   - Makes domain layer less portable

2. **Testing Difficulty:**
   - Domain tests require file system access
   - Can't test domain logic without mocking file I/O

3. **Confusing Organization:**
   - Developers expect domain layer to be pure logic
   - File I/O operations unexpected in domain

**Severity:** **MEDIUM**
- Code works correctly (no functional issues)
- But violates architectural principles
- Makes testing and maintenance harder

---

## 2. EntityService Has Too Many Responsibilities

### 2.1 Current Responsibilities

**EntityService** (`src/domain/entities/entity_service.py`) has **5 distinct responsibilities:**

#### Responsibility 1: Query Operations
```python
def list_characters() -> list[CharacterEntity]
def list_locations() -> list[LocationEntity]
def list_organizations() -> list[OrganizationEntity]
def list_items() -> list[ItemEntity]
def list_memory_logs() -> list[MemoryLog]
def get_character(name: str) -> CharacterEntity | None
def stats() -> EntityStats
```

**Concern:** Repository query facade

---

#### Responsibility 2: Entity Detection & Automation Integration
```python
def detect_mentions(text: str) -> set[str]
    # Analyzes text to find entity mentions

def prepare_entities(context: AutomationContext) -> AutomationContext
    # Detects mentions
    # Filters by scene context
    # Splits in-scene vs referenced
    # Converts names to file paths
    # Returns enriched automation context
```

**Concern:** Text analysis, scene filtering, automation pipeline integration

---

#### Responsibility 3: Template Generation
```python
def generate_entity_card_template(name: str, entity_type: EntityType) -> str
    # Returns template for new entity cards

def generate_character_preferences_template(name: str) -> dict[str, Any]
    # Returns template for character preferences
```

**Concern:** Template formatting for entity creation

---

#### Responsibility 4: AI-Powered Preference Generation
```python
def generate_character_preferences(character_name: str) -> PreferenceResult
    """Generate AI-powered relationship preferences for a character.

    Uses the PreferenceGenerator to analyze a character's personality core
    and generate structured preferences (likes, dislikes, hates).
    """
    # Loads character
    # Converts to EntityCard
    # Calls PreferenceGenerator (LLM-powered)
    # Returns AI-generated preferences
```

**Concern:** LLM integration, AI-powered generation, complex orchestration

---

#### Responsibility 5: Mutation Operations
```python
def save_character(character: CharacterEntity) -> CharacterEntity
    # Saves character to repository

def append_memory_entry(character_name: str, entry: dict) -> MemoryLog
    # Appends memory to character's log
```

**Concern:** Data persistence, repository writes

---

### 2.2 Why This Violates Single Responsibility Principle

**Single Responsibility Principle (SRP):**
> A class should have one, and only one, reason to change.

**EntityService has 5 reasons to change:**

1. **Query logic changes** (list/get methods)
2. **Detection algorithm changes** (detect_mentions, scene filtering)
3. **Template format changes** (template generation methods)
4. **LLM integration changes** (preference generation, PreferenceGenerator)
5. **Persistence logic changes** (save/append methods)

**Each responsibility should be a separate class.**

### 2.3 Problems Caused

#### Problem 1: Testing Difficulty

**Current State:**
```python
def test_entity_service():
    # Need to mock:
    # - Repository (for queries)
    # - PreferenceGenerator (for AI generation)
    # - SessionStateService (for scene context)
    # - LLM client (for AI calls)
    # All for ONE test class!

    entity_service = EntityService(
        repository=mock_repo,
        templates=mock_templates,
        preference_generator=mock_pref_gen,  # Complex mock
        logger=mock_logger,
        session_state=mock_state,
        rp_dir=test_dir
    )
```

**Too many dependencies for one class!**

---

#### Problem 2: Unclear API

**What is EntityService?**
- A query facade? (list/get methods)
- A detection engine? (detect_mentions)
- A template generator? (template methods)
- An AI orchestrator? (preference generation)
- A repository wrapper? (save/append)

**Answer: All of the above!** This is confusing.

---

#### Problem 3: Tight Coupling

**EntityService couples:**
- Domain models (CharacterEntity, LocationEntity)
- Infrastructure (SessionStateService, file paths)
- Automation layer (AutomationContext)
- AI/LLM layer (PreferenceGenerator)
- Templates layer (StateTemplateService)

Too many cross-layer dependencies for one class.

---

#### Problem 4: Hard to Extend

**Want to add new detection algorithm?**
- Must modify EntityService (large class)
- Risk breaking unrelated features (queries, templates, AI)

**Want to add new AI generation feature?**
- Must modify EntityService again
- Couples AI logic with queries and detection

---

### 2.4 Recommended Refactoring

#### Split into 5 Classes:

**1. EntityQueryService** (Domain)
```python
class EntityQueryService:
    """Query facade for entity repository."""

    def list_characters() -> list[CharacterEntity]
    def list_locations() -> list[LocationEntity]
    def list_organizations() -> list[OrganizationEntity]
    def list_items() -> list[ItemEntity]
    def get_character(name: str) -> CharacterEntity | None
    def stats() -> EntityStats
```

**Dependencies:** Repository only
**Reason to change:** Query logic changes

---

**2. EntityDetectionService** (Domain)
```python
class EntityDetectionService:
    """Detects entity mentions in text."""

    def detect_mentions(text: str) -> set[str]
        # Text analysis, name matching

    def filter_by_scene(
        entities: set[str],
        scene_context: dict
    ) -> tuple[list[str], list[str]]:
        # Returns: (in_scene, referenced)
```

**Dependencies:** Repository for entity list, SessionStateService for scene context
**Reason to change:** Detection algorithm changes

---

**3. EntityAutomationService** (Automation Layer)
```python
class EntityAutomationService:
    """Prepares entities for automation pipeline."""

    def prepare_entities(context: AutomationContext) -> AutomationContext:
        # Uses EntityDetectionService
        # Converts names to paths
        # Enriches automation context
```

**Dependencies:** EntityDetectionService, path resolution
**Reason to change:** Automation pipeline integration changes

---

**4. EntityTemplateService** (Domain/Templates)
```python
class EntityTemplateService:
    """Generates templates for entity creation."""

    def generate_entity_card_template(name: str, entity_type: EntityType) -> str
    def generate_character_preferences_template(name: str) -> dict[str, Any]
```

**Dependencies:** StateTemplateService
**Reason to change:** Template format changes

---

**5. EntityPreferenceGenerationService** (Domain/AI)
```python
class EntityPreferenceGenerationService:
    """AI-powered preference generation for characters."""

    def generate_character_preferences(character_name: str) -> PreferenceResult:
        # Uses PreferenceGenerator (LLM)
        # Complex orchestration
```

**Dependencies:** Repository, PreferenceGenerator (LLM)
**Reason to change:** LLM integration changes, generation logic changes

---

**6. EntityMutationService** (Domain)
```python
class EntityMutationService:
    """Handles entity persistence operations."""

    def save_character(character: CharacterEntity) -> CharacterEntity
    def append_memory_entry(character_name: str, entry: dict) -> MemoryLog
```

**Dependencies:** Repository
**Reason to change:** Persistence logic changes

---

### 2.5 Benefits of Refactoring

**Before Refactoring:**
```
EntityService (490 lines, 5 responsibilities, 6+ dependencies)
```

**After Refactoring:**
```
EntityQueryService           (50 lines, 1 responsibility, 1 dependency)
EntityDetectionService       (80 lines, 1 responsibility, 2 dependencies)
EntityAutomationService      (120 lines, 1 responsibility, 2 dependencies)
EntityTemplateService        (40 lines, 1 responsibility, 1 dependency)
EntityPreferenceGenService   (80 lines, 1 responsibility, 3 dependencies)
EntityMutationService        (60 lines, 1 responsibility, 1 dependency)
```

**Improvements:**

1. **Each class has one reason to change** ✅
2. **Smaller, focused classes** (easier to understand)
3. **Easier to test** (fewer mocks per test)
4. **Clearer API** (class name indicates purpose)
5. **Easier to extend** (modify one class without risk to others)
6. **Better separation of concerns**

---

### 2.6 Migration Strategy

**Phase 1: Extract without breaking** (Zero breaking changes)

1. Create new service classes with distinct responsibilities
2. Keep EntityService as a facade that delegates to new services
3. Migrate internal callers to use new services directly
4. Mark EntityService methods as deprecated

**Example:**
```python
class EntityService:
    """DEPRECATED: Use specific entity services instead."""

    def __init__(self, ...):
        self._query_service = EntityQueryService(repository)
        self._detection_service = EntityDetectionService(repository, session_state)
        self._template_service = EntityTemplateService(templates)
        self._preference_service = EntityPreferenceGenerationService(...)
        self._mutation_service = EntityMutationService(repository)

    @deprecated("Use EntityQueryService.list_characters() instead")
    def list_characters(self):
        return self._query_service.list_characters()

    @deprecated("Use EntityDetectionService.detect_mentions() instead")
    def detect_mentions(self, text):
        return self._detection_service.detect_mentions(text)

    # ... etc for all methods
```

**Phase 2: Migrate callers**

Update code to use new services:
```python
# Before:
entity_service = EntityService(...)
mentioned = entity_service.detect_mentions(text)
character = entity_service.get_character("Alice")

# After:
query_service = EntityQueryService(repository)
detection_service = EntityDetectionService(repository, session_state)
mentioned = detection_service.detect_mentions(text)
character = query_service.get_character("Alice")
```

**Phase 3: Remove facade**

Once all callers migrated, remove EntityService entirely.

---

### 2.7 Impact of Violation

**Current Problems:**

1. **Violates Single Responsibility Principle:**
   - Class has 5 distinct reasons to change
   - Makes maintenance risky (changes affect multiple features)

2. **Testing Difficulty:**
   - Tests require mocking 6+ dependencies
   - Hard to test one concern in isolation

3. **Unclear API:**
   - Users don't know what EntityService does
   - Name doesn't communicate purpose

4. **Tight Coupling:**
   - Couples multiple layers (domain, automation, AI, infrastructure)
   - Hard to reuse components independently

**Severity:** **MEDIUM**
- Code works correctly (no functional issues)
- But violates SOLID principles
- Makes testing and extension difficult
- Should be refactored for long-term maintainability

---

## 3. Summary & Recommendations

### 3.1 ChatlogOrganizer

| Aspect | Current | Recommended |
|--------|---------|-------------|
| **Location** | `src/domain/sessions/` | `src/infrastructure/sessions/` |
| **Reason** | File I/O, directory management | Infrastructure concern |
| **Priority** | Medium | Can live with current, but should move |
| **Effort** | 30 minutes | Move file + update imports |
| **Risk** | Low | Simple refactor |

**Action Items:**
1. Move file to `src/infrastructure/sessions/chatlog_organizer.py`
2. Update imports in `domain/sessions/__init__.py`
3. Update imports in `presentation/bridge/bridge_service.py`
4. Update tests (if any)

---

### 3.2 EntityService

| Aspect | Current | Recommended |
|--------|---------|-------------|
| **Responsibilities** | 5 (query, detection, templates, AI, mutations) | 6 separate classes |
| **Reason** | Violates SRP | Each class = one responsibility |
| **Priority** | Medium-Low | Works fine, but hard to maintain |
| **Effort** | 4-6 hours | Extract classes, create facade |
| **Risk** | Medium | Larger refactor, needs testing |

**Action Items:**
1. Extract EntityQueryService (queries only)
2. Extract EntityDetectionService (text analysis)
3. Extract EntityAutomationService (automation integration)
4. Extract EntityTemplateService (template generation)
5. Extract EntityPreferenceGenerationService (AI generation)
6. Extract EntityMutationService (persistence)
7. Create EntityService facade for backward compatibility
8. Gradually migrate callers to new services
9. Remove facade once migration complete

---

### 3.3 Priority Assessment

**High Priority:**
- None (both violations are medium severity)

**Medium Priority:**
1. **ChatlogOrganizer layer violation** - Should be fixed for architectural correctness
2. **EntityService SRP violation** - Should be refactored for long-term maintainability

**Recommended Approach:**
1. Fix ChatlogOrganizer first (quick, low risk)
2. Refactor EntityService incrementally (phase 1 → phase 2 → phase 3)
3. Don't need to do both at once

---

## 4. Architectural Layers Review

### 4.1 Clean Architecture Layers

```
┌─────────────────────────────────────────────┐
│         Presentation Layer                  │
│   (UI, TUI, Bridge, Controllers)            │
│   - Handles user interaction                │
│   - Coordinates use cases                   │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│         Automation Layer                    │
│   (Pipeline, Agents, Services)              │
│   - Orchestrates domain operations          │
│   - Implements complex workflows            │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│         Domain Layer                        │
│   (Entities, Services, Business Logic)      │
│   - Pure business logic                     │
│   - Technology-agnostic                     │
│   - NO infrastructure dependencies          │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│         Infrastructure Layer                │
│   (File I/O, Database, External APIs)       │
│   - Technical concerns                      │
│   - File system operations                  │
│   - Network calls                           │
└─────────────────────────────────────────────┘
```

### 4.2 Where Components Should Be

| Component | Current Layer | Correct Layer | Reason |
|-----------|---------------|---------------|--------|
| ChatlogOrganizer | Domain | Infrastructure | File I/O, directory management |
| EntityService (all 5 responsibilities) | Domain | Split across Domain + Automation | Too many concerns |
| SessionRepository | Domain | Domain ✅ | Business entity persistence |
| FileManager | Infrastructure | Infrastructure ✅ | File operations |
| AgentRunner | Automation | Automation ✅ | Workflow orchestration |
| BridgeService | Presentation | Presentation ✅ | User interaction coordination |

---

## 5. Conclusion

### Violations Confirmed

1. **ChatlogOrganizer in Domain Layer:** ⚠️ **CONFIRMED**
   - Should be in Infrastructure layer
   - Medium priority fix (quick, low risk)

2. **EntityService has Too Many Responsibilities:** ⚠️ **CONFIRMED**
   - Violates Single Responsibility Principle
   - Should split into 6 focused classes
   - Medium-low priority (larger refactor)

### Both violations are:**
- ✅ Real architecture issues
- ✅ Should be fixed for long-term maintainability
- ❌ NOT urgent (code works correctly)
- ❌ NOT causing bugs (just harder to maintain)

### Recommended Action Plan:

**Short Term (1-2 weeks):**
1. Move ChatlogOrganizer to infrastructure layer
2. Update documentation to reflect correct location

**Medium Term (1-2 months):**
1. Extract EntityService into separate services (Phase 1 - create facade)
2. Gradually migrate callers to new services (Phase 2)
3. Remove facade once migration complete (Phase 3)

**Long Term:**
- Maintain architectural discipline
- Review new components for layer violations
- Document layer responsibilities clearly

---

**Document Status**: COMPLETE
**Violations Found**: 2 confirmed
**Priority**: Medium (should fix, not urgent)
**Next Steps**: Fix ChatlogOrganizer first, then refactor EntityService incrementally
