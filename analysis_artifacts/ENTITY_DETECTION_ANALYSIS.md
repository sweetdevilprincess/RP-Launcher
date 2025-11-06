# Entity Detection Analysis

**Date**: 2025-11-06
**Analyst**: Claude (Systematic Codebase Analysis)
**Context**: Phase 3 verification following SYSTEMATIC_CODEBASE_ANALYSIS_PLAN.md

---

## Executive Summary

**Finding**: EntityService and TieredFileLoader are **COMPLEMENTARY**, not duplicated.

**Roles**:
- `EntityService.detect_mentions()` - **Detection** (which entities mentioned in text?)
- `TieredFileLoader` - **Loading** (load file content for detected entities)

**Verdict**: ✅ **No duplication** - These components work together in a pipeline:
1. EntityService detects entity mentions → Returns file paths
2. TieredFileLoader loads content → Returns file content

---

## 1. Component Responsibilities

### 1.1 EntityService.detect_mentions()

**Location:** `src/domain/entities/entity_service.py:91-115`

**Purpose:** Detect which entities (characters, locations, organizations) are mentioned in text

**Implementation:**
```python
def detect_mentions(self, text: str) -> set[str]:
    """Detect entity mentions in text by matching names and tags."""
    lowered = text.lower()
    matches: set[str] = set()

    def _matches(entity_name: str, triggers: Iterable[str]) -> bool:
        # Check if entity name in text
        if entity_name.lower() in lowered:
            return True
        # Check if any trigger/tag in text
        return any(trigger and trigger.lower() in lowered for trigger in triggers)

    # Check all characters
    for character in self._repository.list_characters():
        triggers = character.metadata.get("tags", [])
        if _matches(character.name, triggers):
            matches.add(character.name)

    # Check all locations
    for location in self._repository.list_locations():
        triggers = location.metadata.get("tags", [])
        if _matches(location.name, triggers):
            matches.add(location.name)

    # Check all organizations
    for organization in self._repository.list_organizations():
        triggers = organization.metadata.get("tags", [])
        if _matches(organization.name, triggers):
            matches.add(organization.name)

    return matches
```

**Input:** User message text (string)

**Output:** Set of entity names mentioned (e.g., `{"Alice", "The Old Lighthouse", "Council of Elders"}`)

**Usage Pattern:**
```python
mentioned = entity_service.detect_mentions("Alice went to The Old Lighthouse")
# Result: {"Alice", "The Old Lighthouse"}
```

---

### 1.2 TieredFileLoader

**Location:** `src/infrastructure/filesystem/loaders/tiered_loader.py`

**Purpose:** Load file content for triggered entity paths

**Key Methods:**

#### `load_tier3(triggered_files: Sequence[Path])`
```python
def load_tier3(self, *, triggered_files: Sequence[Path]) -> dict[str, TieredLoadResult]:
    """Load full entity cards for in-scene entities."""
    return self._load_bundles({"triggered"}, triggered_files=triggered_files)
```

#### `load_tier3_referenced(triggered_files: Sequence[Path])`
```python
def load_tier3_referenced(self, *, triggered_files: Sequence[Path]) -> dict[str, TieredLoadResult]:
    """Load basics-only sections for referenced entities."""
    return self._load_bundles({"triggered_basics"}, triggered_files=triggered_files)
```

#### `_load_triggered_files(triggered_files: Sequence[Path])`
```python
def _load_triggered_files(self, triggered_files: Sequence[Path]):
    """Load content from provided file paths."""
    collected = []
    for path in triggered_files:
        content = self._read_direct(path)  # Read file content
        if content:
            meta = self._extract_entity_metadata(path, content)
            collected.append((display_key, path, content, meta))
    return collected
```

**Input:** List of file paths (already determined by EntityService)

**Output:** File content + metadata

**Usage Pattern:**
```python
paths = [Path("characters/Alice.md"), Path("entities/location_lighthouse.json")]
result = tiered_loader.load_tier3(triggered_files=paths)
# Result: {bundle_id: TieredLoadResult(files={"Alice.md": "# Alice\n...", ...})}
```

---

### 1.3 Metadata Extraction (Not Entity Detection)

TieredFileLoader has `_extract_entity_metadata()` but this is **NOT entity detection**:

```python
def _extract_entity_metadata(self, path: Path, content: str | None) -> dict[str, Any]:
    """Extract metadata from already-loaded entity file content."""
    if content is None:
        return {}

    # Only process files in entities/ or characters/ directories
    parent_name = path.parent.name
    if parent_name not in {"entities", "characters"}:
        return {}

    meta = {"entity_file": str(path)}

    # Check if content has personality core
    if "Personality Core" in content:
        meta.setdefault("entities_with_cores", []).append(path.stem)

    return meta
```

**Purpose:** Check if loaded entity has personality core (for prompt building)

**NOT detection:** This runs AFTER files are loaded, not to determine WHICH files to load

---

## 2. Complete Execution Flow

### 2.1 End-to-End Pipeline

```
User message: "Alice went to The Old Lighthouse to meet the Council"
  ↓
[1] EntityService.prepare_entities()
  ↓
EntityService.detect_mentions("Alice went to The Old Lighthouse to meet the Council")
  ↓
Scans repository:
  - Characters: Alice ✓, Bob ✗
  - Locations: The Old Lighthouse ✓, Town Square ✗
  - Organizations: Council of Elders ✓ (tag: "Council")
  ↓
Returns: {"Alice", "The Old Lighthouse", "Council of Elders"}
  ↓
Check scene context:
  - characters_in_scene: ["Alice"]
  - current_location: "The Old Lighthouse"
  ↓
Split entities:
  - in_scene: ["Alice", "The Old Lighthouse"]  (full cards)
  - referenced: ["Council of Elders"]          (basics only)
  ↓
Convert to file paths:
  - tier3_files: [
      Path("characters/Alice.md"),
      Path("entities/location_the_old_lighthouse.json")
    ]
  - tier3_referenced_files: [
      Path("entities/organization_council_of_elders.json")
    ]
  ↓
[2] AutomationService passes paths to FileAccessService
  ↓
[3] FileAccessService.load_tiered_context()
  ↓
TieredFileLoader.load_tier3(triggered_files=[Alice.md, lighthouse.json])
  ↓
Loads file content:
  - Alice.md → "# Alice\n## Basics\n- Age: 28\n..."
  - lighthouse.json → "{\"name\": \"The Old Lighthouse\", ...}"
  ↓
TieredFileLoader.load_tier3_referenced(triggered_files=[council.json])
  ↓
Loads BASICS ONLY:
  - council.json → Extracts "basics" section → "# Council (Basics)\n..."
  ↓
[4] Returns TieredLoadResult to PromptBuilder
  ↓
PromptBuilder combines content into LLM prompt
```

---

## 3. Code Verification

### 3.1 Where They Connect

**AutomationService** (automation/services/automation_service.py:85-97):
```python
def run(self, context: AutomationContext) -> AutomationResult:
    # ... (session enrichment, file loading)

    # [1] Entity detection happens here
    domain_context = self._entity_service.prepare_entities(hydrated_context)
    #    ↑ Returns context with tier3_files and tier3_referenced_files

    # [2] File loading happens here
    tiered = self._file_access.load_tiered_context(
        response_count=hydrated_context.response_count,
        triggered_files=domain_context.tier3_files,          # ← Paths from detection
        tier3_referenced_files=domain_context.tier3_referenced_files,
    )
    #    ↑ TieredFileLoader loads content from those paths

    # [3] Build prompt with loaded content
    prompt_result = self._prompt_builder.build(...)
```

**EntityService.prepare_entities()** (entity_service.py:192-393):
```python
def prepare_entities(self, context: AutomationContext) -> AutomationContext:
    """Detect entities and prepare file paths."""

    # [1] Detection
    mentioned = self.detect_mentions(context.message)  # ← TEXT ANALYSIS
    # Result: {"Alice", "The Old Lighthouse", "Council of Elders"}

    # [2] Scene filtering
    scene_context = self._get_scene_context()
    characters_in_scene = set(scene_context.get("characters_in_scene", []))
    current_location = scene_context.get("location", "Unknown")

    # [3] Split into in-scene vs referenced
    in_scene_entities = []
    referenced_entities = []
    for entity_name in mentioned:
        # Check if character in scene
        character = self.get_character(entity_name)
        if character and entity_name in characters_in_scene:
            in_scene_entities.append(entity_name)
        elif character:
            referenced_entities.append(entity_name)
        # Check if current location
        elif entity_name == current_location:
            in_scene_entities.append(entity_name)
        # ... (check locations, orgs, items)

    # [4] Convert names to file paths
    tier3_files = self._entity_names_to_paths(in_scene_entities)
    tier3_referenced_files = self._entity_names_to_paths(referenced_entities)

    # [5] Return updated context with paths
    return context.with_update(
        loaded_entities=list(mentioned),
        in_scene_entities=in_scene_entities,
        referenced_entities=referenced_entities,
        tier3_files=tier3_files,                    # ← Used by TieredFileLoader
        tier3_referenced_files=tier3_referenced_files,
    )
```

**FileAccessService.load_tiered_context()** (file_access_service.py:55-118):
```python
def load_tiered_context(
    self,
    *,
    response_count: int | None,
    triggered_files: Sequence[Path] | None = None,        # ← From EntityService
    tier3_referenced_files: Sequence[Path] | None = None,
) -> TieredContext:
    """Load file content for detected entities."""

    # [1] Load full cards for in-scene entities
    tier3 = self._tier_loader.load_tier3(triggered_files=triggered_files)
    #       ↑ TieredFileLoader reads file content

    # [2] Load basics only for referenced entities
    tier3_referenced = self._tier_loader.load_tier3_referenced(
        triggered_files=tier3_referenced_files
    )

    return TieredContext(
        tier1=tier1,
        tier2=tier2,
        tier3=tier3,
        tier3_referenced=tier3_referenced,
    )
```

---

## 4. Why They're Complementary

### 4.1 Clear Separation of Concerns

| Aspect | EntityService | TieredFileLoader |
|--------|--------------|------------------|
| **Layer** | Domain | Infrastructure |
| **Input** | Text (user message) | File paths |
| **Process** | Text analysis, name matching | File I/O, content loading |
| **Output** | Entity names + paths | File content |
| **Knows About** | Entity repository, scene context | File system, bundles |
| **Doesn't Know** | How files are loaded | Which entities to load |

### 4.2 Single Responsibility Principle

**EntityService:**
- Knows WHAT entities exist (from repository)
- Knows HOW to detect mentions (text matching)
- Knows WHERE entity files are located (path resolution)
- Does NOT know how to load files efficiently

**TieredFileLoader:**
- Knows HOW to load files efficiently (bundles, caching)
- Knows HOW to extract sections (basics only vs full)
- Knows HOW to format results (TieredLoadResult)
- Does NOT know which entities to load (receives paths)

### 4.3 Reusability

**EntityService.detect_mentions()** could be used without TieredFileLoader:
```python
# Example: Just detect without loading
mentioned = entity_service.detect_mentions(user_message)
for entity in mentioned:
    print(f"User mentioned: {entity}")
# No file loading needed
```

**TieredFileLoader** could be used without EntityService:
```python
# Example: Load pre-determined files
paths = [Path("characters/Alice.md"), Path("config/guidelines.md")]
content = tiered_loader.load_tier3(triggered_files=paths)
# No entity detection needed
```

---

## 5. What TieredFileLoader Actually Does

### 5.1 NOT Entity Detection

TieredFileLoader does **NOT**:
- ❌ Analyze text to find entity mentions
- ❌ Match entity names against text
- ❌ Decide which entities to load
- ❌ Search for entities in directories

### 5.2 IS File Loading

TieredFileLoader **DOES**:
- ✅ Load content from provided file paths
- ✅ Organize files into bundles (tier1/2/3)
- ✅ Extract sections (basics vs full)
- ✅ Track metadata (has personality core?)
- ✅ Handle multiple file formats (JSON, Markdown)

### 5.3 Metadata Extraction vs Detection

**Metadata Extraction** (what TieredFileLoader does):
```python
# AFTER loading file content
content = load_file("characters/Alice.md")
if "Personality Core" in content:
    # Track that Alice has a core
    metadata["entities_with_cores"].append("Alice")
```

**Entity Detection** (what EntityService does):
```python
# BEFORE loading files
text = "Alice went to the lighthouse"
if "Alice" in text:
    # Alice is mentioned, should load her file
    paths.append(Path("characters/Alice.md"))
```

**Key Difference:**
- Detection: "Is this entity mentioned in the message?" → Determines WHICH files to load
- Metadata: "Does this loaded file have a personality core?" → Enriches ALREADY-loaded content

---

## 6. Testing the Separation

### 6.1 EntityService Works Without TieredFileLoader

```python
def test_entity_detection_standalone():
    """EntityService can detect mentions without file loading."""
    repository = FixtureEntityRepository(rp_dir=test_dir)
    service = EntityService(repository=repository)

    # Detection works independently
    mentioned = service.detect_mentions("Alice and Bob went to the lighthouse")

    assert "Alice" in mentioned
    assert "Bob" in mentioned
    # No file loading occurred
```

### 6.2 TieredFileLoader Works Without EntityService

```python
def test_file_loading_standalone():
    """TieredFileLoader can load files without entity detection."""
    loader = TieredFileLoader(paths=paths, markdown_store=store, logger=logger)

    # Provide paths directly (from anywhere)
    paths = [
        Path("characters/Alice.md"),
        Path("config/genre_fantasy.md")
    ]

    result = loader.load_tier3(triggered_files=paths)

    assert "Alice.md" in result["characters"].files
    # No entity detection occurred
```

### 6.3 Integration Test

```python
def test_entity_detection_and_loading():
    """Full pipeline: detect → load."""
    entity_service = EntityService(...)
    file_access = FileAccessService(tier_loader=loader, ...)

    # [1] Detection
    context = AutomationContext(message="Alice went to the lighthouse")
    context = entity_service.prepare_entities(context)

    assert "Alice" in context.loaded_entities
    assert len(context.tier3_files) > 0

    # [2] Loading
    tiered = file_access.load_tiered_context(
        response_count=1,
        triggered_files=context.tier3_files
    )

    assert "Alice" in str(tiered.tier3)  # Content loaded
```

---

## 7. Architectural Benefits

### 7.1 Testability

**EntityService tests:**
- Mock repository, test detection logic
- No file I/O needed
- Fast unit tests

**TieredFileLoader tests:**
- Provide test paths, verify content loading
- No entity repository needed
- Test file I/O separately

### 7.2 Maintainability

**Change detection algorithm:**
- Modify `EntityService.detect_mentions()`
- TieredFileLoader unchanged
- File loading continues to work

**Change loading strategy:**
- Modify `TieredFileLoader.load_tier3()`
- EntityService unchanged
- Detection continues to work

### 7.3 Extensibility

**Add new entity types:**
- Update `EntityService.detect_mentions()` to check new repository methods
- TieredFileLoader unchanged (just receives paths)

**Add new file formats:**
- Update `TieredFileLoader._read_direct()` to handle new formats
- EntityService unchanged (just provides paths)

---

## 8. Conclusion

### Summary

**EntityService.detect_mentions()** and **TieredFileLoader** are **NOT duplicated**:

1. **Different responsibilities:**
   - EntityService: DETECT which entities (text analysis)
   - TieredFileLoader: LOAD entity files (file I/O)

2. **Different layers:**
   - EntityService: Domain layer (business logic)
   - TieredFileLoader: Infrastructure layer (file system)

3. **Pipeline relationship:**
   - EntityService outputs → TieredFileLoader inputs
   - Detection determines paths → Loading reads paths

4. **No overlap:**
   - TieredFileLoader has NO entity detection logic
   - EntityService has NO file loading logic
   - `_extract_entity_metadata()` is NOT detection (runs after loading)

### Verdict

✅ **COMPLEMENTARY** - These components work together correctly

No changes needed - this is good architectural design following:
- Single Responsibility Principle
- Separation of Concerns
- Dependency Inversion (Domain → Infrastructure via paths)

---

## Appendix A: Method Comparison

| Method | Component | Purpose | Input | Output |
|--------|-----------|---------|-------|--------|
| `detect_mentions()` | EntityService | Find which entities mentioned | Text string | Set of entity names |
| `prepare_entities()` | EntityService | Detect + categorize + resolve paths | AutomationContext | Context with paths |
| `load_tier3()` | TieredFileLoader | Load full entity cards | File paths | File content |
| `load_tier3_referenced()` | TieredFileLoader | Load entity basics only | File paths | Basics content |
| `_extract_entity_metadata()` | TieredFileLoader | Check if loaded content has core | Loaded content | Metadata dict |

**No duplication:** Each method has unique purpose and implementation.

---

## Appendix B: Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   User Message                          │
│       "Alice went to The Old Lighthouse"                │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              EntityService                              │
│  ┌────────────────────────────────────────────────┐    │
│  │ detect_mentions(text)                          │    │
│  │   - Scans entity repository                    │    │
│  │   - Matches names/tags against text            │    │
│  │   - Returns: {"Alice", "The Old Lighthouse"}   │    │
│  └──────────────────┬─────────────────────────────┘    │
│                     │                                    │
│  ┌──────────────────▼─────────────────────────────┐    │
│  │ prepare_entities()                             │    │
│  │   - Filters by scene context                   │    │
│  │   - Splits in-scene vs referenced              │    │
│  │   - Converts names to file paths               │    │
│  │   - Returns: tier3_files, tier3_referenced_files│   │
│  └──────────────────┬─────────────────────────────┘    │
└─────────────────────┼───────────────────────────────────┘
                      │
                      │ [File Paths]
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            FileAccessService                            │
│  ┌────────────────────────────────────────────────┐    │
│  │ load_tiered_context(triggered_files)           │    │
│  │   - Passes paths to TieredFileLoader           │    │
│  └──────────────────┬─────────────────────────────┘    │
└─────────────────────┼───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            TieredFileLoader                             │
│  ┌────────────────────────────────────────────────┐    │
│  │ load_tier3(triggered_files)                    │    │
│  │   - Reads file content from paths              │    │
│  │   - Formats as TieredLoadResult                │    │
│  │   - Returns: {files: {"Alice.md": "...", ...}} │    │
│  └──────────────────┬─────────────────────────────┘    │
└─────────────────────┼───────────────────────────────────┘
                      │
                      │ [File Content]
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              PromptBuilder                              │
│   Combines file content into LLM prompt                 │
└─────────────────────────────────────────────────────────┘
```

**Clear separation:** Detection → Path resolution → File loading → Prompt building

---

**Document Status**: COMPLETE
**Finding**: No duplication - components are complementary
**Action Required**: None - architecture is correct
