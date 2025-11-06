# Workstream F: Trigger & Template Handling - Implementation Guide

**Status:** ✅ Complete
**Branch:** `feature/refactor-d-automation-pipeline`
**Implementation Date:** 2025-10-20

## Overview

Workstream F implements a clean, extensible trigger and template system for the automation pipeline. This refactors the existing trigger/template logic from `src/` into a well-structured architecture with proper separation of concerns.

### Key Features

**Trigger System:**
- 3 evaluator types: Keyword (fast), Regex (flexible), Semantic (intelligent)
- Pattern loading from entity file metadata
- Frequency tracking with auto-escalation (TIER_3 → TIER_2)
- Result deduplication and ranking
- Configurable evaluation behavior

**Template System:**
- 4 template modes: auto, composite, modular, layered
- LRU caching for performance
- Lazy loading (templates loaded on-demand)
- Genre detection from ROLEPLAY_OVERVIEW.md
- Extensible template discovery

## Architecture

### Trigger System Components

```
refactoring/src/automation/triggers/
├── protocols.py              # Core protocols and dataclasses
├── keyword_evaluator.py      # Fast keyword matching
├── regex_evaluator.py        # Pattern-based matching
├── semantic_evaluator.py     # AI-powered semantic matching
├── registry.py               # Evaluator factory
├── coordinator.py            # Evaluation orchestration
├── pattern_loader.py         # Entity file discovery & parsing
├── frequency_tracker.py      # Auto-escalation tracking
└── __init__.py              # Public exports
```

### Template System Components

```
refactoring/src/automation/templates/
├── template_cache.py         # LRU cache implementation
├── template_loader.py        # JSON template loading
├── template_registry.py      # Template discovery
├── narrative_template_manager.py  # High-level manager
└── __init__.py              # Public exports
```

### Integration Points

```
refactoring/src/automation/agents/
└── fallback_trigger_strategy.py  # Trigger system integration

refactoring/src/automation/services/
└── prompt_builder.py             # Template system integration

refactoring/src/shared/interfaces/
└── ai_client.py                  # AI client protocol for semantic evaluation
```

## Component Details

### 1. Trigger Protocols (`protocols.py`)

**Core Data Structures:**

```python
@dataclass(frozen=True)
class TriggerContext:
    """Input for trigger evaluation."""
    message: str
    loaded_entities: List[str]
    response_count: int
    rp_dir: Path
    previous_triggers: Optional[List[Path]] = None

@dataclass(frozen=True)
class TriggerPatterns:
    """Trigger patterns from an entity file."""
    file_path: Path
    entity_name: str
    keywords: List[str]
    regex_patterns: List[str]
    semantic_descriptions: List[str]

@dataclass(frozen=True)
class TriggerResult:
    """Result of successful trigger match."""
    file_path: Path
    entity_name: str
    trigger_type: str  # 'keyword', 'regex', 'semantic'
    matched_pattern: str
    confidence: float = 1.0
    metadata: Optional[dict] = None
```

**Protocol:**

```python
class TriggerEvaluator(Protocol):
    def evaluate(self, patterns: TriggerPatterns, context: TriggerContext) -> Optional[TriggerResult]: ...
    def evaluate_batch(self, patterns_list: List[TriggerPatterns], context: TriggerContext) -> List[TriggerResult]: ...
```

### 2. Keyword Evaluator (`keyword_evaluator.py`)

**Features:**
- Case-sensitive and case-insensitive matching
- Word boundary enforcement (prevents "cat" matching "category")
- Regex caching for boundary patterns
- Batch evaluation optimization

**Configuration:**
```python
KeywordEvaluator(
    case_sensitive=False,        # Default: case-insensitive
    use_word_boundaries=True     # Default: enforce word boundaries
)
```

**Example:**
```python
evaluator = KeywordEvaluator()
patterns = TriggerPatterns(
    file_path=Path("chars/Alice.md"),
    entity_name="Alice",
    keywords=["Alice", "protagonist"],
    regex_patterns=[],
    semantic_descriptions=[]
)
result = evaluator.evaluate(patterns, context)
# Returns TriggerResult if "Alice" found in message
```

### 3. Regex Evaluator (`regex_evaluator.py`)

**Features:**
- Compiled pattern caching
- Invalid pattern handling (graceful degradation)
- Configurable max patterns per file
- Case-sensitive/insensitive matching

**Configuration:**
```python
RegexEvaluator(
    case_sensitive=False,           # Default: case-insensitive
    max_patterns_per_file=10        # Safety limit
)
```

**Example:**
```python
evaluator = RegexEvaluator()
patterns = TriggerPatterns(
    file_path=Path("chars/Alice.md"),
    entity_name="Alice",
    keywords=[],
    regex_patterns=[r"alice['']s? \w+", r"talk(ing|ed)? (?:to|with) alice"],
    semantic_descriptions=[]
)
result = evaluator.evaluate(patterns, context)
# Returns TriggerResult if pattern matches
```

### 4. Semantic Evaluator (`semantic_evaluator.py`)

**Features:**
- Optional AI client (graceful degradation if unavailable)
- Confidence threshold filtering
- Lazy AI client initialization
- Error handling with fallback

**Configuration:**
```python
SemanticEvaluator(
    ai_client=optional_ai_client,   # Can be None
    confidence_threshold=0.7         # Minimum confidence to accept
)
```

**Example:**
```python
evaluator = SemanticEvaluator(ai_client=claude_client)
patterns = TriggerPatterns(
    file_path=Path("chars/Alice.md"),
    entity_name="Alice",
    keywords=[],
    regex_patterns=[],
    semantic_descriptions=["References to Alice", "Alice's family"]
)
result = evaluator.evaluate(patterns, context)
# Returns TriggerResult with confidence score
```

### 5. Pattern Loader (`pattern_loader.py`)

**Responsibilities:**
- Discover entity files in `characters/` and `entities/`
- Parse trigger metadata from file content
- Cache patterns for performance

**Supported Formats:**
```markdown
<!-- Entity file metadata -->
**Triggers**: Alice, protagonist
[Triggers:Alice,protagonist]
[RegexTriggers:alice['']s? \w+,talking to alice]
[SemanticTriggers:References to Alice,Alice's family]
```

**Example:**
```python
loader = PatternLoader()
patterns_list = loader.load_all_patterns(rp_dir)
# Returns List[TriggerPatterns] for all entities with triggers
```

### 6. Trigger Registry (`registry.py`)

**Responsibilities:**
- Create evaluators based on configuration
- Order evaluators by performance (keyword → regex → semantic)
- Manage optional AI client for semantic evaluation

**Example:**
```python
registry = TriggerRegistry(config_service, ai_client=optional_ai_client)
evaluators = registry.create_evaluators()
# Returns [KeywordEvaluator, RegexEvaluator, SemanticEvaluator]
```

**Configuration Keys:**
```python
triggers.keyword.case_sensitive = False
triggers.keyword.use_word_boundaries = True
triggers.regex.case_sensitive = False
triggers.regex.max_patterns_per_file = 10
triggers.semantic.enabled = True
triggers.semantic.confidence_threshold = 0.7
```

### 7. Trigger Coordinator (`coordinator.py`)

**Responsibilities:**
- Orchestrate evaluation across multiple evaluators
- Try evaluators in order, stop at first match per file
- Filter recently triggered files
- Deduplicate and rank results

**Algorithm:**
```
For each entity file:
    Try KeywordEvaluator
    If no match, try RegexEvaluator
    If no match, try SemanticEvaluator
    If match found, add to results and skip remaining evaluators

Filter out files in previous_triggers list
Rank by: keyword > regex > semantic, then by confidence
Limit to max_results (default: 10)
```

**Example:**
```python
coordinator = TriggerCoordinator(evaluators, max_results=10)
results = coordinator.evaluate_triggers(patterns_list, context)
# Returns ranked, deduplicated List[TriggerResult]
```

### 8. Frequency Tracker (`frequency_tracker.py`)

**Responsibilities:**
- Track trigger frequency over rolling window
- Identify files for auto-escalation (TIER_3 → TIER_2)
- Persist history to JSON file

**Configuration:**
```python
FrequencyTracker(
    history_file=Path("state/trigger_history.json"),
    window_size=10,              # Last N responses
    escalation_threshold=3       # Triggers needed for escalation
)
```

**Example:**
```python
tracker = FrequencyTracker(history_file, window_size=10, escalation_threshold=3)
escalated = tracker.track_and_escalate([Path("chars/Alice.md")])
# Returns files triggered 3+ times in last 10 responses
```

**History Format:**
```json
{
  "trigger_history": [
    ["chars/Alice.md", "chars/Bob.md"],
    ["chars/Alice.md"],
    ...
  ]
}
```

### 9. Template Cache (`template_cache.py`)

**Features:**
- LRU eviction policy
- Hit rate tracking
- Thread-safe for reads
- Statistics collection

**Example:**
```python
cache = TemplateCache(max_size=50)
cache.put(Path("fantasy.json"), template_data)
cached = cache.get(Path("fantasy.json"))  # Returns data or None
stats = cache.get_stats()  # {"size": 1, "hits": 1, "misses": 0, "hit_rate": 1.0}
```

### 10. Template Loader (`template_loader.py`)

**Features:**
- Lazy loading (only load when requested)
- Template validation
- Cache integration
- Error handling

**Template Structure:**
```json
{
  "display_name": "Fantasy Adventure",
  "sections": {
    "tone": {
      "title": "Narrative Tone",
      "content": ["Epic and heroic", "Wonder and discovery"]
    },
    "focus": {
      "title": "Story Focus",
      "content": ["Character growth", "World exploration"]
    }
  },
  "highlights": ["Optional highlight 1", "Optional highlight 2"]
}
```

**Example:**
```python
loader = TemplateLoader(template_dir, cache)
template = loader.load_template("fantasy")  # Loads fantasy.json
sections = loader.load_template_sections("fantasy", ["tone", "focus"])
```

### 11. Template Registry (`template_registry.py`)

**Features:**
- Template discovery (scans *.json files)
- Genre name normalization
- Composite template finding

**Example:**
```python
registry = TemplateRegistry(template_dir)
available = registry.list_available_templates()  # ["fantasy", "horror", "dark_romance_thriller"]
has_template = registry.has_template("fantasy")  # True
composite = registry.find_composite_template("dark_romance", "thriller")  # "dark_romance_thriller"
```

**Genre Normalization:**
```python
normalize_genre_name("Dark Romance")  # → "dark_romance"
normalize_genre_name("Slice of Life")  # → "slice_of_life"
```

### 12. Narrative Template Manager (`narrative_template_manager.py`)

**Modes:**

**1. Auto Mode** (default):
```python
# Reads ROLEPLAY_OVERVIEW.md for genre detection
# Format: **Genre**: Primary / Secondary
# Tries composite → layered → primary template
```

**2. Composite Mode**:
```python
# config: narrative_template.mode = "composite"
# config: narrative_template.template = "dark_romance_thriller"
# Loads pre-made genre combination
```

**3. Modular Mode**:
```python
# config: narrative_template.mode = "modular"
# config: narrative_template.sections = {"tone": "fantasy", "focus": "thriller"}
# Mixes sections from different genres
```

**4. Layered Mode**:
```python
# config: narrative_template.mode = "layered"
# config: narrative_template.primary = "fantasy"
# config: narrative_template.secondary = "horror"
# Primary template + secondary highlights
```

**Example:**
```python
manager = NarrativeTemplateManager(rp_dir, config_service, loader, registry)
instructions = manager.generate_narrative_instructions()
# Returns formatted markdown for prompt injection
```

## Integration

### Fallback Trigger Strategy

**File:** `refactoring/src/automation/agents/fallback_trigger_strategy.py`

**Integration:**
```python
strategy = FallbackTriggerStrategy(
    logger=logger,
    config_service=config,
    use_trigger_system=True
)

result = strategy.execute(agent_context, prompt, automation_context)
# Returns AutomationResult with:
# - enhanced_prompt (with triggered context injected)
# - metadata["triggered_files"] (List[Path])
# - metadata["escalated_files"] (List[Path])
```

**Workflow:**
1. Load patterns from entity files
2. Evaluate triggers (keyword → regex → semantic)
3. Filter recently triggered files
4. Track frequency for auto-escalation
5. Format and inject triggered context
6. Return enhanced prompt with metadata

### Prompt Builder

**File:** `refactoring/src/automation/services/prompt_builder.py`

**Integration:**
```python
builder = PromptBuilder(config=config, logger=logger)
prompt = builder.build_prompt(automation_context)
# Returns prompt with narrative template prepended (if enabled)
```

**Workflow:**
1. Initialize template system (lazy, on first prompt build)
2. Generate narrative instructions based on mode
3. Build all prompt sections
4. Combine: narrative template + sections
5. Return final prompt

## Configuration Reference

### Trigger Configuration

```python
# Keyword Matching
triggers.keyword.case_sensitive = False
triggers.keyword.use_word_boundaries = True

# Regex Matching
triggers.regex.case_sensitive = False
triggers.regex.max_patterns_per_file = 10

# Semantic Matching
triggers.semantic.enabled = True
triggers.semantic.confidence_threshold = 0.7

# Frequency Tracking
triggers.frequency_tracking.enabled = True
triggers.frequency_tracking.window_size = 10
triggers.frequency_tracking.escalation_threshold = 3
```

### Template Configuration

```python
# Template System
narrative_template.enabled = True
narrative_template.mode = "auto"  # auto/composite/modular/layered
narrative_template.template_dir = "config/templates/prompts"
narrative_template.cache_size = 50

# Composite Mode
narrative_template.template = "dark_romance_thriller"

# Modular Mode
narrative_template.sections = {"tone": "fantasy", "focus": "thriller"}

# Layered Mode
narrative_template.primary = "fantasy"
narrative_template.secondary = "horror"
```

## File Locations

### Source Files

**Triggers:**
- `refactoring/src/automation/triggers/protocols.py`
- `refactoring/src/automation/triggers/keyword_evaluator.py`
- `refactoring/src/automation/triggers/regex_evaluator.py`
- `refactoring/src/automation/triggers/semantic_evaluator.py`
- `refactoring/src/automation/triggers/registry.py`
- `refactoring/src/automation/triggers/coordinator.py`
- `refactoring/src/automation/triggers/pattern_loader.py`
- `refactoring/src/automation/triggers/frequency_tracker.py`
- `refactoring/src/automation/triggers/__init__.py`

**Templates:**
- `refactoring/src/automation/templates/template_cache.py`
- `refactoring/src/automation/templates/template_loader.py`
- `refactoring/src/automation/templates/template_registry.py`
- `refactoring/src/automation/templates/narrative_template_manager.py`
- `refactoring/src/automation/templates/__init__.py`

**Integration:**
- `refactoring/src/automation/agents/fallback_trigger_strategy.py` (updated)
- `refactoring/src/automation/services/prompt_builder.py` (updated)
- `refactoring/src/shared/interfaces/ai_client.py` (new)
- `refactoring/src/shared/logging.py` (copied from main)

### Tests

**Created by Workstream E:**
- `refactoring/tests/automation/triggers/test_keyword_evaluator.py`
- `refactoring/tests/automation/triggers/test_regex_evaluator.py`
- `refactoring/tests/automation/triggers/test_semantic_evaluator.py`
- `refactoring/tests/automation/triggers/test_coordinator.py`
- `refactoring/tests/automation/triggers/test_frequency_tracker.py`
- `refactoring/tests/automation/templates/test_template_cache.py`
- `refactoring/tests/automation/templates/test_template_loader.py`
- `refactoring/tests/automation/templates/test_template_registry.py`
- `refactoring/tests/automation/templates/test_narrative_template_manager.py`

### Documentation

**Created by Workstream E:**
- `refactoring/docs/EXTENDING_TRIGGERS.md`
- `refactoring/docs/EXTENDING_TEMPLATES.md`

**This Document:**
- `refactoring/docs/architecture/workstream_f_implementation.md`

## Performance Considerations

### Trigger System

**Optimizations:**
1. **Evaluator Ordering:** Keyword (fastest) → Regex (medium) → Semantic (slowest)
2. **Early Exit:** Stop at first match per file
3. **Pattern Caching:** Compiled regex patterns cached
4. **Batch Operations:** Single message scan for all keywords
5. **Recent Filter:** Skip recently triggered files (O(1) lookup)

**Expected Performance:**
- Keyword: < 1ms per file
- Regex: 1-5ms per file
- Semantic: 100-500ms per file (network call)
- Total: ~50-200ms for typical RP with 20 entities (keyword/regex only)

### Template System

**Optimizations:**
1. **Lazy Loading:** Templates loaded only when requested
2. **LRU Caching:** Hot templates stay in memory
3. **Single Parse:** JSON parsed once, reused
4. **Genre Normalization:** Consistent cache keys

**Expected Performance:**
- Cache Hit: < 1ms
- Cache Miss: 5-10ms (file read + JSON parse)
- First Load: 10-20ms (directory scan + template load)

## Success Criteria

✅ **All Criteria Met:**

1. **Trigger System:**
   - ✅ Keyword, regex, semantic evaluators implemented
   - ✅ Pattern loading from entity files
   - ✅ Frequency tracking with auto-escalation
   - ✅ Configurable behavior
   - ✅ Integrated into FallbackTriggerStrategy

2. **Template System:**
   - ✅ All 4 modes implemented (auto/composite/modular/layered)
   - ✅ LRU caching with hit rate tracking
   - ✅ Lazy loading for performance
   - ✅ Genre detection from ROLEPLAY_OVERVIEW.md
   - ✅ Integrated into PromptBuilder

3. **Code Quality:**
   - ✅ Follows naming conventions (snake_case modules, PascalCase classes)
   - ✅ Comprehensive type hints
   - ✅ Structured logging throughout
   - ✅ Clean separation of concerns
   - ✅ Protocol-based design for extensibility

4. **Documentation:**
   - ✅ Implementation guide (this document)
   - ✅ Extension guides (by Workstream E)
   - ✅ Inline documentation and examples

5. **Testing:**
   - ✅ Unit tests for all evaluators (by Workstream E)
   - ✅ Unit tests for template components (by Workstream E)
   - ✅ Comprehensive test coverage

## Next Steps

1. **User Testing:** Test trigger/template systems in real RPs
2. **Performance Monitoring:** Track evaluator performance in production
3. **Cache Tuning:** Adjust cache sizes based on usage patterns
4. **AI Client Implementation:** Create concrete AiClient for semantic evaluation

## Related Workstreams

- **Workstream D:** Automation Pipeline (parent workstream)
- **Workstream E:** Agent System (parallel work, collaborated on tests/docs)
- **Workstream G:** Session Management (completed, ready for integration)

---

**Implementation Complete:** 2025-10-20
**Primary Developer:** Workstream D (Claude Code Instance)
**Test & Documentation Support:** Workstream E (Claude Code Instance)
