# Fixture-Based Entity Loading Analysis

**Analysis Date**: 2025-11-06
**Scope**: Entity file storage formats (JSON vs Markdown), sync mechanisms, fixture regeneration
**Status**: ✅ Complete

---

## Executive Summary

The system implements a **dual-format entity storage** with markdown files preferred for loading but **only JSON files** supported for saving. This creates a **one-way sync issue** where:

1. ✅ Markdown files are loaded if they exist (priority)
2. ✅ JSON files are fallback if no markdown exists
3. ❌ **BUT**: Saving entities only writes JSON files
4. ❌ **NO sync mechanism** between markdown and JSON
5. ❌ **NO fixture regeneration** process found

**Severity**: 🟡 Medium - Could cause data loss if users expect markdown to be source of truth

**Impact**: If both markdown and JSON exist for same entity:
- Loading will read markdown (ignoring JSON)
- Saving will write JSON (markdown becomes stale)
- User edits to JSON are invisible until markdown is deleted

---

## Current File Structure

### Test RP (Current State)
```
RPs/test_rp/
├── characters/
│   └── character_aurora_lys.json    ← Only entity file
├── entities/                         ← Empty (doesn't exist)
└── [no markdown files exist]
```

### Supported File Locations

**Priority 1: Markdown files** (src/domain/entities/entity_service.py:162-166)
```python
# Try characters/ directory (markdown)
char_md = self._rp_dir / "characters" / f"{name}.md"
if char_md.exists():
    paths.append(char_md)
    continue
```

**Priority 2: JSON files** (entity_service.py:168-182)
```python
# Try entities/ directory (JSON) - try all entity types
entity_patterns = [
    f"character_{name_lower}.json",
    f"location_{name_lower}.json",
    f"organization_{name_lower}.json",
    f"item_{name_lower}.json",
]
for pattern in entity_patterns:
    entity_path = self._rp_dir / "entities" / pattern
    if entity_path.exists():
        paths.append(entity_path)
```

**Fallback for characters**: JSON in characters/ directory
```
characters/character_{name_slug}.json  ← Also checked by FixtureEntityRepository
```

---

## File Format Details

### JSON Format (Saveable)

**File**: `character_aurora_lys.json`
```json
{
  "name": "Aurora Lys",
  "type": "character",
  "basics": {
    "full_name": "Aurora Lys"
  },
  "appearance": {},
  "personality": {
    "core_mandate": "Inspire hope through music"
  },
  "preferences": {},
  "abilities": {},
  "background": {},
  "metadata": {
    "tags": ["pilot", "Aurora"]
  }
}
```

**Parser**: `parse_character()` (src/domain/entities/entity_parser.py:84-108)
- Requires all 8 sections: name, basics, appearance, personality, preferences, abilities, background, metadata
- Converts to `CharacterEntity` dataclass

**Writer**: `FixtureEntityRepository._write_json()` (entity_repository.py:85-88)
```python
def _write_json(self, path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
```

### Markdown Format (Read-Only)

**Purpose**: Used by TieredFileLoader for LLM prompts

**Code Reference**: src/infrastructure/filesystem/loaders/tiered_loader.py:285-334
```python
def _load_main_character(self) -> Iterable[tuple[str, Path, str, dict[str, Any]]]:
    characters_dir = (self.paths.rp_dir / "characters").resolve()
    for char_file in sorted(characters_dir.glob("*.md")):
        content = self._read_direct(char_file)
        # Returns raw markdown content for prompt building
```

**Current Status**: ❌ No markdown files exist in test RP
**Parser**: ❌ No markdown → entity dataclass parser found
**Writer**: ❌ No entity → markdown writer found

---

## Loading and Saving Workflows

### Loading Workflow (EntityService.prepare_entities)

**Code Reference**: src/domain/entities/entity_service.py:192-234

```
User Message: "Alice went to The Old Lighthouse"
    ↓
1. EntityService.detect_mentions()
   → Detects: {"Alice", "The Old Lighthouse"}
    ↓
2. EntityService._entity_names_to_paths()
   → Priority 1: Check characters/Alice.md    ← If exists, USE THIS
   → Priority 2: Check entities/character_alice.json
   → Priority 3: Check entities/location_the_old_lighthouse.json
    ↓
3. TieredFileLoader.load_tier3(paths)
   → Loads file content (markdown OR JSON)
    ↓
4. PromptBuilder
   → Includes content in LLM context
```

**Key Code** (entity_service.py:365-366):
```python
# Convert entity names to file paths
tier3_files = self._entity_names_to_paths(in_scene_entities)
tier3_referenced_files = self._entity_names_to_paths(referenced_entities)
```

### Saving Workflow (EntityService.save_character)

**Code Reference**:
- src/domain/entities/entity_service.py:474-477
- src/domain/entities/entity_repository.py:106-117

```
TUI Entity Editor: User clicks "Save"
    ↓
1. TUI → IPC: UPDATE_ENTITY request
    ↓
2. EntityHandler._handle_update_entity() [NOT IMPLEMENTED]
    ↓
3. EntityService.save_character(character_data)
    ↓
4. FixtureEntityRepository.save_character()
   → Converts to mapping
   → Determines path: base_dir/character_{slug}.json
   → Writes JSON file ONLY
```

**Key Code** (entity_repository.py:106-117):
```python
def save_character(self, data: MappingLike) -> CharacterEntity:
    mapping = self._to_mapping(data)
    name = str(mapping.get("name"))
    path = self._character_index.get(name)
    if path is None:
        slug = self._slug(name)
        path = self.base_dir / f"character_{slug}.json"  # ← ALWAYS JSON
    self._write_json(path, mapping)  # ← Only writes JSON
    return parse_character(mapping)
```

---

## Sync Issues and Gaps

### Issue 1: Markdown Shadows JSON Updates

**Scenario**:
1. User creates `characters/Alice.md` (markdown)
2. User also has `entities/character_alice.json` (JSON)
3. User edits Alice via TUI entity manager
4. System saves to `character_alice.json`
5. **Problem**: Next load reads `Alice.md` (priority 1), ignoring JSON changes

**Code Causing Issue** (entity_service.py:162-166):
```python
# Markdown checked first
char_md = self._rp_dir / "characters" / f"{name}.md"
if char_md.exists():
    paths.append(char_md)
    continue  # ← Never checks JSON if markdown exists
```

### Issue 2: No Markdown → JSON Sync

**Gap**: No code found to:
- Convert markdown files to JSON format
- Update JSON when markdown changes
- Detect markdown vs JSON staleness

**Search Results**:
```bash
# No conversion code found
grep -r "parse.*markdown\|markdown.*parse" src → No results
grep -r "generate.*json\|json.*generate" src → Only IPC message serialization
```

### Issue 3: No JSON → Markdown Sync

**Gap**: No code found to:
- Generate markdown from JSON entities
- Keep markdown files updated when JSON changes
- Bulk export entities to markdown

**Writer Code**: Only `_write_json()` exists, no `_write_markdown()`

### Issue 4: Unclear Source of Truth

**Question**: Which format is authoritative?

**Evidence for Markdown**:
- Loaded with priority 1
- TieredFileLoader expects markdown for prompts
- File search checks markdown first

**Evidence for JSON**:
- Only format that can be saved
- FixtureEntityRepository only writes JSON
- Entity IPC handlers will create JSON
- Test fixtures all use JSON

**Conclusion**: ❌ **No clear source of truth** - system is inconsistent

---

## Fixture Regeneration

### Current Mechanism: ❌ None Found

**Search Results**:
```bash
find -name "*fixture*"
→ tests/entities/fixtures/  ← Test fixtures only
→ src/domain/entities/fixtures.py  ← Test helper utilities
→ tests/entities/test_fixture_loader.py  ← Unit tests

# No production fixture generation scripts
```

**Test Fixtures vs Production Fixtures**:

| Aspect | Test Fixtures | Production Fixtures |
|--------|--------------|-------------------|
| **Location** | tests/entities/fixtures/ | RPs/{rp_name}/characters/ or entities/ |
| **Purpose** | Unit testing | Runtime entity data |
| **Management** | Manually created for tests | Created via save_character() or manually |
| **Loader** | fixtures.py (FixtureLoader) | entity_repository.py (FixtureEntityRepository) |

**Code Reference** (src/domain/entities/fixtures.py:1-51):
```python
"""Utilities for loading entity test fixtures."""

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "entities" / "fixtures"

def load_character_fixture() -> dict[str, Any]:
    return FixtureLoader().load_json("character_aurora.json")  # ← TEST ONLY
```

### How JSON Fixtures Are Created

**Method 1: Manual Creation**
- User creates JSON file with required structure
- 8 required sections for characters
- Must match parse_character() requirements

**Method 2: Entity Creation API** (Not yet implemented)
```python
# entity_handler.py:136-142 (CREATE_ENTITY handler)
def _handle_create_entity(self, request: IPCRequest) -> str:
    """Handle CREATE_ENTITY request - create new entity."""
    # TODO: Implement entity creation
    return create_error_response(
        request.request_id,
        "Entity creation not yet implemented"
    )
```

**Method 3: Entity Update API** (Not yet implemented)
```python
# entity_handler.py:144-150 (UPDATE_ENTITY handler)
def _handle_update_entity(self, request: IPCRequest) -> str:
    """Handle UPDATE_ENTITY request - update existing entity."""
    # TODO: Implement entity updates
    return create_error_response(
        request.request_id,
        "Entity updates not yet implemented"
    )
```

**Current Status**: Only manual JSON creation works. IPC handlers are stubs.

---

## Component Interactions

### FixtureEntityRepository

**File**: src/domain/entities/entity_repository.py:31-392

**Responsibilities**:
1. Index JSON files on initialization
2. Load entities from JSON
3. Save entities to JSON
4. Manage memory logs (with timeline support)
5. Manage relationships (with timeline support)

**Indexing Code** (entity_repository.py:51-74):
```python
def __init__(self, rp_dir: Path | None = None, base_dir: Path | None = None, ...):
    # Determine base directory
    if rp_dir:
        entities_dir = rp_dir / "entities"
        characters_dir = rp_dir / "characters"
        self.base_dir = entities_dir if entities_dir.exists() else characters_dir

    # Build indices of JSON files
    self._character_index = self._index("character_*.json")
    self._location_index = self._index("location_*.json")
    self._organization_index = self._index("organization_*.json")
    self._item_index = self._index("item_*.json")
    self._memory_index = self._index("*_memories.json")

def _index(self, pattern: str) -> dict[str, Path]:
    """Map entity name → JSON file path"""
    index: dict[str, Path] = {}
    for path in self.base_dir.glob(pattern):
        data = json.load(path.open())
        name = str(data.get("name") or data.get("character"))
        if name:
            index[name] = path
    return index
```

**File Search Order**:
1. Checks `entities/` directory first
2. Falls back to `characters/` directory
3. Only indexes JSON files (ignores markdown)

### EntityService

**File**: src/domain/entities/entity_service.py:18-491

**Relevant Methods**:

**_entity_names_to_paths()** (lines 140-190):
- Converts entity names to file paths
- Priority: markdown → JSON in entities/ → (fallback handled by repository)
- Used by prepare_entities() to build tier3_files list

**prepare_entities()** (lines 192-393):
- Detects mentions in user message
- Splits into in-scene vs referenced
- Converts names to paths
- Returns AutomationContext with file paths

**save_character()** (lines 474-477):
- Delegates to repository.save_character()
- Only logs the operation
- No markdown handling

### TieredFileLoader

**File**: src/infrastructure/filesystem/loaders/tiered_loader.py:285-334

**Purpose**: Load markdown files for LLM prompts

**Code**:
```python
def _load_main_character(self) -> Iterable[tuple[str, Path, str, dict[str, Any]]]:
    characters_dir = (self.paths.rp_dir / "characters").resolve()
    for char_file in sorted(characters_dir.glob("*.md")):
        content = self._read_direct(char_file)
        meta = self._extract_yaml(content)
        return [(self._display_key(char_file), char_file, content, meta)]
```

**Current Usage**: Loads markdown if exists, but NO markdown files exist in test RP

### Entity Handler (IPC)

**File**: src/presentation/bridge/handlers/entity_handler.py:1-162

**Current State**: ❌ Creation/Update handlers not implemented

**GET_ENTITIES** (lines 53-134): ✅ Implemented
- Loads all entities from repository
- Formats for TUI display
- Returns JSON with entity data

**CREATE_ENTITY** (lines 136-142): ❌ Stub
```python
def _handle_create_entity(self, request: IPCRequest) -> str:
    return create_error_response(
        request.request_id,
        "Entity creation not yet implemented"
    )
```

**UPDATE_ENTITY** (lines 144-150): ❌ Stub
```python
def _handle_update_entity(self, request: IPCRequest) -> str:
    return create_error_response(
        request.request_id,
        "Entity updates not yet implemented"
    )
```

---

## Risk Assessment

### High-Risk Scenarios

**Scenario 1: Silent Data Loss**
```
1. User maintains canonical entity data in Alice.md (markdown)
2. User edits Alice via TUI (thinking it's connected)
3. System writes to character_alice.json
4. Next load reads Alice.md (ignoring JSON)
5. User's edits are lost
```

**Risk**: 🔴 High - Data loss without warning

**Scenario 2: Stale Prompt Data**
```
1. User updates Alice.json with new personality traits
2. Alice.md exists from older version
3. LLM receives Alice.md (stale data)
4. Responses inconsistent with current entity state
```

**Risk**: 🟡 Medium - Incorrect AI behavior

**Scenario 3: Confusion About File Format**
```
1. User sees entity_service.py prefers markdown
2. User creates markdown files
3. User tries to edit via TUI
4. Changes don't apply (no UPDATE_ENTITY implementation)
5. User doesn't know which format to use
```

**Risk**: 🟡 Medium - Poor UX, unclear expectations

### Low-Risk Scenarios

**Current Test RP**: ✅ No risk
- Only JSON files exist
- No markdown files to cause conflicts
- System works correctly in JSON-only mode

---

## Recommendations

### Recommendation 1: Pick Single Source of Truth

**Option A: JSON Only** (Recommended)
- ✅ Already implemented (save_character works)
- ✅ Structured data, validated schemas
- ✅ No sync issues
- ❌ Less human-readable for manual editing

**Changes Required**:
1. Remove markdown loading from _entity_names_to_paths()
2. Update documentation: "Entities must be JSON"
3. TieredFileLoader: Load JSON files, format as markdown for prompts
4. Effort: ~2 hours

**Option B: Markdown Only**
- ✅ Human-readable, easy to edit manually
- ✅ Already has loading code
- ❌ Need markdown → entity parser (complex)
- ❌ Need entity → markdown writer
- ❌ Harder to maintain structure validation

**Changes Required**:
1. Implement markdown parser (YAML frontmatter + sections)
2. Implement entity → markdown writer
3. Convert existing JSON to markdown
4. Remove JSON loading
5. Effort: ~8-12 hours

**Option C: Dual Format with Sync** (Not Recommended)
- ❌ Complex to maintain
- ❌ Sync conflicts still possible
- ❌ Unclear source of truth
- ❌ Doubled storage

**Effort**: ~20+ hours for robust bidirectional sync

### Recommendation 2: Implement Entity Update Handler

**Current Gap**: entity_handler.py:144-150 is a stub

**Required Implementation**:
```python
def _handle_update_entity(self, request: IPCRequest) -> str:
    try:
        entity_id = request.data.get("entity_id")
        entity_data = request.data.get("entity_data")

        # Parse entity type from entity_id (e.g., "char_alice")
        entity_type = entity_id.split("_")[0]

        if entity_type == "char":
            character = self.bridge.entity_service.save_character(entity_data)
            return create_response(request.request_id, success=True)
        # ... handle other types

    except Exception as e:
        return create_error_response(request.request_id, str(e))
```

**Effort**: 2-3 hours for all entity types

### Recommendation 3: Document Expected Format

**Add to documentation**:
```markdown
# Entity File Formats

RP Launcher uses JSON files for entity storage.

**Location**: `RPs/{rp_name}/characters/` or `RPs/{rp_name}/entities/`

**Naming Convention**:
- Characters: `character_{name_slug}.json`
- Locations: `location_{name_slug}.json`
- Organizations: `organization_{name_slug}.json`
- Items: `item_{name_slug}.json`

**Structure**: See entity_parser.py for required fields

**Markdown Support**: Deprecated - use JSON only
```

**Effort**: 30 minutes

### Recommendation 4: Add Warning for Markdown Files

**Add to EntityService.prepare_entities()**:
```python
def _entity_names_to_paths(self, entity_names: Iterable[str]) -> list[Path]:
    paths = []
    for name in entity_names:
        char_md = self._rp_dir / "characters" / f"{name}.md"
        if char_md.exists():
            self._logger.warning(
                "entity_service.markdown_deprecated",
                context={
                    "file": str(char_md),
                    "message": "Markdown entity files are deprecated. Please convert to JSON."
                }
            )
            paths.append(char_md)
            continue
        # ... rest of logic
```

**Effort**: 15 minutes

---

## Migration Path (If Choosing JSON Only)

### Phase 1: Document Current Behavior (1 hour)
- ✅ This analysis document
- Update COMPONENT_DATA_FLOW.md
- Update AGENT_DOCUMENTATION.md entity detection section

### Phase 2: Implement Entity Update Handler (2-3 hours)
- Implement _handle_update_entity()
- Implement _handle_create_entity()
- Test with TUI entity manager
- Update CHANGELOG

### Phase 3: Remove Markdown Support (2 hours)
- Remove markdown check from _entity_names_to_paths()
- Update TieredFileLoader to load JSON files
- Add JSON → markdown formatting helper for prompts
- Test with existing JSON entities
- Update documentation

### Phase 4: Add Validation (2 hours)
- Add schema validation for JSON files
- Better error messages for malformed entities
- Warn on missing required fields

**Total Effort**: ~7-8 hours for complete migration to JSON-only

---

## Conclusion

**Current State**: Dual-format system with incomplete implementation

**Issues**:
1. ❌ Markdown preferred for loading but can't be saved
2. ❌ JSON can be saved but shadowed by markdown
3. ❌ No sync mechanism
4. ❌ No fixture regeneration
5. ❌ Entity creation/update handlers not implemented

**Recommended Action**: **Standardize on JSON only**

**Rationale**:
- JSON already works for saving
- Structured format easier to validate
- No sync issues
- Minimal code changes needed
- Clear migration path

**Next Steps**:
1. Implement entity update/create handlers (2-3 hours)
2. Remove markdown loading (2 hours)
3. Update documentation (30 min)
4. Add deprecation warnings (15 min)

**Total Effort**: ~5 hours for production-ready JSON-only system

---

## Appendix: File References

### Code Files Analyzed

| File | Lines | Purpose |
|------|-------|---------|
| src/domain/entities/entity_service.py | 140-190 | _entity_names_to_paths() - file resolution |
| src/domain/entities/entity_repository.py | 51-117 | Indexing and save_character() |
| src/domain/entities/entity_parser.py | 84-108 | JSON → CharacterEntity parsing |
| src/infrastructure/filesystem/loaders/tiered_loader.py | 285-334 | Markdown loading for prompts |
| src/presentation/bridge/handlers/entity_handler.py | 136-150 | IPC handlers (stubs) |
| src/domain/entities/fixtures.py | 1-51 | Test fixture utilities (not production) |

### Data Files Examined

| File | Purpose |
|------|---------|
| RPs/test_rp/characters/character_aurora_lys.json | Only production entity file |
| tests/entities/fixtures/*.json | Test fixtures (separate from production) |

### Search Commands Used

```bash
# Search for markdown entity files
find refactoring/RPs -name "*.md" -path "*/characters/*"
find refactoring/RPs -name "*.md" -path "*/entities/*"

# Search for JSON entity files
find refactoring/RPs -name "*.json" -path "*/characters/*"
find refactoring/RPs -name "*.json" -path "*/entities/*"

# Search for conversion/sync code
grep -r "parse.*markdown\|markdown.*parse" src
grep -r "generate.*fixture|fixture.*generat|to_json|from_markdown" src -i

# Search for fixture regeneration
find -name "*fixture*" -o -name "*generate*" -o -name "*sync*"
```

---

**Analysis Complete** ✅
**Next Investigation**: Move to next item in SYSTEMATIC_CODEBASE_ANALYSIS_PLAN.md
