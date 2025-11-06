# KnowledgeExtractionAgent Implementation Plan

**Date:** 2025-11-04
**Status:** 📋 **PLANNED** - Ready to implement
**Estimated Time:** 8 hours

---

## Overview

KnowledgeExtractionAgent will automatically extract world-building facts and lore from Claude's responses, storing them in a structured timeline-specific JSON format with intelligent contradiction reconciliation.

---

## Storage Solution: Merged Timeline-Specific JSON

### File Structure
```
state/
  knowledge_main.json              # Main timeline knowledge
  knowledge_branch_a.json          # Branch A (inherits main at branch point)
  knowledge_branch_b.json          # Branch B (inherits main at branch point)
```

**Single source of truth:** JSON file contains both:
- User-created entries (converted from `knowledge_base.md` on first run, or wizard)
- Agent-extracted entries (automated from Claude's responses)

**Branch Inheritance:** Just like sessions!
- Create branch at message 50 → Copy `knowledge_main.json` to `knowledge_branch_a.json`
- Each branch tracks knowledge independently after branch point
- Switch branch → Load that branch's knowledge file

---

## Data Structure

### Complete JSON Schema (knowledge_{session_id}.json)

```json
{
  "session_id": "main",
  "last_updated": "2025-11-04T15:30:00Z",
  "last_updated_message": 50,
  "total_entries": 25,
  "entries": [
    {
      "id": "know_a1b2c3d4",
      "categories": ["magic_system", "culture"],
      "fact": "Magic requires verbal incantations for most users",
      "details": "Standard teaching is that spells need spoken words. However, advanced mages like Bob can cast silently after years of training.",
      "confidence": 0.85,
      "tags": ["magic", "established_canon", "training"],
      "source": "user_created",
      "source_message": null,
      "source_timestamp": "2025-11-04T10:00:00Z",
      "mentioned_by": [],
      "location": null,
      "chapter": null,
      "revision_history": [
        {
          "message": 10,
          "fact": "Magic requires verbal incantations",
          "confidence": 0.9,
          "reason": "Initial extraction"
        },
        {
          "message": 50,
          "fact": "Advanced users can cast silently",
          "confidence": 0.8,
          "synthesis": "Reconciled contradiction - both are true depending on skill level"
        }
      ]
    },
    {
      "id": "know_xyz789",
      "categories": ["history", "organizations"],
      "fact": "The Academy was founded 100 years ago after the Great War",
      "details": "Built to regulate magic users and prevent another catastrophic conflict.",
      "confidence": 0.9,
      "tags": ["history", "academy", "established_canon"],
      "source": "auto_extracted",
      "source_message": 23,
      "source_timestamp": "2025-11-04T14:20:00Z",
      "mentioned_by": ["Professor Alice"],
      "location": "Academy Library",
      "chapter": "Chapter 3",
      "revision_history": []
    }
  ],
  "categories_index": {
    "magic_system": 8,
    "history": 5,
    "geography": 4,
    "culture": 3,
    "organizations": 5
  }
}
```

### Field Explanations

**Top-Level Fields:**
- `session_id` - Timeline identifier (matches session state)
- `last_updated` - ISO timestamp of last update
- `last_updated_message` - Message number of last update
- `total_entries` - Count of knowledge entries
- `entries` - Array of knowledge objects
- `categories_index` - Count per category for quick reference

**Knowledge Entry Fields:**
- `id` - Unique identifier (format: `know_{8_hex_chars}`)
- `categories` - **Array** of categories (multiple allowed)
- `fact` - Short statement of the fact (1 sentence)
- `details` - Extended explanation (2-3 sentences)
- `confidence` - Float 0.0-1.0 (how certain is this knowledge)
- `tags` - Array of descriptive tags (from taxonomy)
- `source` - "user_created" or "auto_extracted"
- `source_message` - Message number where extracted (null for user_created)
- `source_timestamp` - ISO timestamp from TimeTrackingAgent
- `mentioned_by` - Array of character names who stated this
- `location` - Where the fact was revealed (from scene_context)
- `chapter` - Chapter where fact was revealed (from scene_context)
- `revision_history` - Array of revisions (contradiction reconciliation)

---

## Standardized Taxonomies

### Categories (Strict - Must Use These)

```python
KNOWLEDGE_CATEGORIES = [
    # World Rules
    "magic_system",
    "technology",
    "supernatural",
    "physics_laws",

    # History & Time
    "history",
    "timeline",
    "past_events",
    "legends_myths",

    # Society & Culture
    "culture",
    "customs",
    "laws",
    "religion",
    "language",

    # Geography & Places
    "geography",
    "locations",
    "climate",

    # Organizations & Power
    "organizations",
    "factions",
    "government",
    "military",

    # Economy & Resources
    "economy",
    "trade",
    "resources",

    # Other
    "species_races",
    "lore",
    "prophecy",
    "secrets"
]
```

**Category Descriptions (for wizard):**
- `magic_system` - How magic works, rules, limitations
- `technology` - Tech level, devices, inventions
- `supernatural` - Supernatural beings, phenomena
- `physics_laws` - How the world's physics work
- `history` - Historical events, past
- `timeline` - When events occurred
- `past_events` - Specific past happenings
- `legends_myths` - Stories, myths, legends
- `culture` - Cultural norms, practices
- `customs` - Traditions, rituals
- `laws` - Legal rules, regulations
- `religion` - Religious beliefs, practices
- `language` - Languages, communication
- `geography` - Terrain, regions, biomes
- `locations` - Specific places
- `climate` - Weather, seasons
- `organizations` - Groups, institutions
- `factions` - Political groups, sides
- `government` - Ruling structures
- `military` - Armed forces, warfare
- `economy` - Economic systems, currency
- `trade` - Commerce, trading
- `resources` - Natural resources, materials
- `species_races` - Races, species in the world
- `lore` - General world lore
- `prophecy` - Prophecies, predictions
- `secrets` - Hidden knowledge

### Tags (Strict - Must Use These)

```python
KNOWLEDGE_TAGS = [
    # Certainty
    "established_canon",
    "implied",
    "rumor",
    "uncertain",

    # Importance
    "critical",
    "important",
    "background",
    "flavor",

    # Type
    "rule",
    "fact",
    "limitation",
    "exception",
    "secret",

    # Scope
    "global",
    "regional",
    "local",
    "character_specific",

    # Story
    "plot_relevant",
    "worldbuilding",
    "backstory",
    "foreshadowing"
]
```

---

## Contradiction Synthesis (Intelligent Reconciliation)

### The Problem
User at message 10: "Magic requires verbal incantations"
User at message 50: "Bob casts magic silently"

**Old approach:** Store both, flag conflict, confuse users
**New approach:** Synthesize an explanation that makes both true

### The Solution

**Step 1: Detect Contradiction**
- Use text similarity (SequenceMatcher) between new fact and existing facts
- If >80% similar but contradictory meaning → Flag for synthesis

**Step 2: LLM Synthesis Call**
```
These facts appear to contradict:

EXISTING (Message 10, confidence 0.9): "Magic requires verbal incantations"
NEW (Message 50, confidence 0.8): "Bob casts magic silently without speaking"

Reconcile these facts by finding an explanation that makes BOTH true:
- Consider: skill levels, exceptions, special conditions, context, character abilities
- Example: "Magic typically requires incantations, but advanced users can cast silently"
- Example: "Magic requires incantations normally, but Bob has a rare mutation"

If they are TRULY irreconcilable (direct contradiction with no explanation), return can_reconcile: false

Respond with JSON:
{
  "can_reconcile": true,
  "synthesized_fact": "Magic requires verbal incantations for most users, but advanced mages can cast silently",
  "synthesis_explanation": "Bob is an advanced magic user who has trained for years to cast without words",
  "confidence": 0.85,
  "revision_note": "Reconciled: Added silent casting as advanced technique"
}
```

**Step 3: Update Entry**
```json
{
  "id": "know_abc123",
  "fact": "Magic requires verbal incantations for most users, but advanced mages can cast silently",
  "details": "Standard teaching requires spoken words. Bob demonstrated silent casting through advanced training.",
  "confidence": 0.85,
  "revision_history": [
    {
      "message": 10,
      "fact": "Magic requires verbal incantations",
      "confidence": 0.9,
      "reason": "Initial extraction"
    },
    {
      "message": 50,
      "fact": "Bob casts silently",
      "confidence": 0.8,
      "synthesis": "Reconciled: Advanced users can cast without words"
    }
  ]
}
```

**Benefits:**
- Preserves story evolution
- Makes sense of apparent contradictions
- Tracks how knowledge evolved
- No user confusion

---

## Knowledge Base Conversion (.md → JSON)

### Current System
Wizard creates `state/knowledge_base.md`:
```markdown
# WORLD KNOWLEDGE BASE

## Geography
### Locations
- The Capital City is surrounded by mountains
- The Dark Forest lies to the north

## Organizations
- The Magic Academy regulates all magic users
- The City Guard maintains order

## World Rules
- Magic requires incantations
- Iron disrupts magical energy
```

### Conversion Process (First Run Only)

**On Agent First Execution:**
1. Check if `state/knowledge_base.md` exists
2. If exists:
   - Parse markdown sections
   - Convert to JSON entries
   - Mark with `"source": "user_created"`
   - Save to `knowledge_{session_id}.json`
   - Rename .md to `.md.converted` (backup)

**Parsing Logic:**
```python
def _parse_knowledge_base_md(md_path: Path) -> list[dict]:
    """Parse knowledge_base.md into knowledge entries."""

    content = md_path.read_text(encoding="utf-8")
    entries = []

    # Parse by sections
    sections = {
        "Geography": ["geography", "locations"],
        "Organizations": ["organizations", "factions"],
        "World Rules": ["magic_system", "physics_laws"],
        "Cultural Details": ["culture", "customs"],
        "Historical Events": ["history", "past_events"],
        "Important Items": ["resources"],
    }

    for section_name, default_categories in sections.items():
        # Extract bullet points from section
        facts = extract_bullets_from_section(content, section_name)

        for fact_text in facts:
            entries.append({
                "id": f"know_{uuid4().hex[:8]}",
                "categories": default_categories,
                "fact": fact_text.strip(),
                "details": "",
                "confidence": 1.0,  # User-created = certain
                "tags": ["established_canon", "user_created"],
                "source": "user_created",
                "source_message": None,
                "source_timestamp": datetime.now().isoformat(),
                "mentioned_by": [],
                "location": None,
                "chapter": None,
                "revision_history": []
            })

    return entries
```

**Result:**
```json
{
  "entries": [
    {
      "id": "know_a1b2c3d4",
      "categories": ["geography", "locations"],
      "fact": "The Capital City is surrounded by mountains",
      "details": "",
      "confidence": 1.0,
      "tags": ["established_canon", "user_created"],
      "source": "user_created"
    }
  ]
}
```

---

## Session State Integration

### Add Knowledge Pointer to session.json

**Current session.json structure:**
```json
{
  "timeline": {...},
  "arc_tracking": {...},
  "relationship_tracking": {...},
  "plot_threads": {...},
  "scene_context": {...}
}
```

**Add:**
```json
{
  "knowledge": {
    "knowledge_file": "state/knowledge_main.json"
  }
}
```

### Update SessionStateService

**File:** `src/infrastructure/sessions/session_state_service.py`

**In `initialize_session_state()` (around line 95):**
```python
# Add after plot_threads
"knowledge": existing_data.get("knowledge", {
    "knowledge_file": f"state/knowledge_{session_id}.json",
}),
```

**In `switch_timeline()` (around line 291):**
```python
# Add after plot_threads
if "knowledge" not in state:
    state["knowledge"] = {}
state["knowledge"]["knowledge_file"] = f"state/knowledge_{session_id}.json"
```

---

## Agent Implementation

### Class Structure

**File:** `src/automation/agents/implementations/knowledge_extraction_agent.py`

```python
class KnowledgeExtractionAgent(BaseAgent):
    """Extract world-building facts and lore from Claude's responses.

    Features:
    - Multi-category support
    - Intelligent contradiction synthesis
    - Converts knowledge_base.md to JSON (first run)
    - Timeline-specific storage
    """

    def get_agent_id(self) -> str:
        return "knowledge_extraction"

    def execute(
        self,
        user_message: str,
        message_number: int,
        claude_response: str | None = None,
        **kwargs
    ) -> str:
        """Execute knowledge extraction and save to knowledge file."""
```

### Key Methods

```python
# LLM Interaction
def _build_knowledge_prompt() -> str
def _build_synthesis_prompt() -> str

# Data Loading/Saving
def _load_existing_knowledge() -> dict
def _save_knowledge() -> bool

# Knowledge Base Conversion
def _convert_knowledge_base_md() -> list[dict]
def _should_convert_md() -> bool

# Contradiction Handling
def _check_for_contradictions() -> dict | None
def _synthesize_contradiction() -> dict

# Entry Management
def _apply_knowledge_updates() -> dict
def _create_knowledge_entry() -> dict
def _generate_knowledge_id() -> str

# Utilities
def _format_summary() -> str
```

---

## LLM Prompt Design

### Extraction Prompt

```python
def _build_knowledge_prompt(
    self,
    user_message: str,
    claude_response: str,
    existing_knowledge: list[dict],
    characters_in_scene: list[str],
    location: str,
    chapter: str
) -> str:
    """Build LLM prompt for knowledge extraction."""

    # Format existing knowledge (prevent duplicates)
    existing_text = self._format_existing_knowledge(existing_knowledge)

    categories_str = ", ".join(KNOWLEDGE_CATEGORIES)
    tags_str = ", ".join(KNOWLEDGE_TAGS)
    characters_str = ", ".join(characters_in_scene) if characters_in_scene else "Unknown"

    return f"""Analyze this roleplay response for world-building facts and lore.

USER MESSAGE:
{user_message}

CLAUDE'S RESPONSE:
{claude_response}

CURRENT SCENE:
- Chapter: {chapter if chapter else "None"}
- Location: {location}
- Characters: {characters_str}

EXISTING KNOWLEDGE (DO NOT DUPLICATE):
{existing_text}

Extract NEW world-building facts about:
1. **World Rules** - Magic, physics, technology, supernatural
2. **History** - Past events, timeline, legends
3. **Culture & Society** - Customs, laws, language, religion
4. **Geography** - Locations, terrain, climate
5. **Organizations** - Factions, governments, groups

IMPORTANT RULES:
- Only extract facts that are NEW (not already in existing knowledge)
- Facts must be explicitly stated or strongly implied
- Do NOT extract character feelings/actions (that's memories)
- Do NOT extract temporary scene details (weather, mood)
- Facts must be important for narrative consistency

**Confidence Scale:**
- 0.9-1.0: Explicitly stated as fact
- 0.7-0.9: Strongly implied
- 0.5-0.7: Inferred from context
- Below 0.5: Too uncertain, don't extract

**Categories (MUST use these):** {categories_str}
**Tags (MUST use these):** {tags_str}

**MULTIPLE CATEGORIES ALLOWED** - If fact touches multiple topics, include all relevant categories.

Example:
- "The Academy was founded after the war to regulate magic"
- Categories: ["organizations", "history", "magic_system"]

Respond with JSON ONLY:
{{
  "knowledge": [
    {{
      "categories": ["magic_system", "culture"],
      "fact": "Magic requires verbal incantations for most users",
      "details": "Standard teaching requires spoken words. Some advanced users can cast silently.",
      "confidence": 0.9,
      "tags": ["magic", "established_canon", "rule"],
      "mentioned_by": ["Professor Alice"]
    }}
  ]
}}

If no NEW knowledge found, return: {{"knowledge": []}}"""
```

### Synthesis Prompt

```python
def _build_synthesis_prompt(
    self,
    existing_entry: dict,
    new_fact: str,
    new_details: str,
    new_confidence: float,
    new_message: int
) -> str:
    """Build LLM prompt for contradiction synthesis."""

    return f"""Two knowledge facts appear to contradict each other:

EXISTING FACT (Message {existing_entry['source_message']}, confidence {existing_entry['confidence']}):
"{existing_entry['fact']}"
Details: {existing_entry['details']}

NEW FACT (Message {new_message}, confidence {new_confidence}):
"{new_fact}"
Details: {new_details}

Reconcile these facts by finding an explanation that makes BOTH true:

Consider these possibilities:
- Different skill levels (basic vs advanced)
- Exceptions to the rule (rare cases)
- Special conditions (time, place, circumstances)
- Character-specific abilities (mutations, training)
- Context matters (different situations)
- Evolution of knowledge (old belief vs new discovery)

Examples of good synthesis:
- "Magic requires incantations normally, but advanced mages can cast silently"
- "Iron disrupts magic for most users, but doesn't affect Bob due to his unique bloodline"
- "The war happened 50 years ago according to common belief, but historical records show it was 60 years ago"

If they are TRULY irreconcilable with no reasonable explanation:
- Return can_reconcile: false
- Provide reason why they cannot be reconciled

Respond with JSON ONLY:
{{
  "can_reconcile": true,
  "synthesized_fact": "One sentence combining both facts with explanation",
  "synthesized_details": "2-3 sentences explaining how both are true",
  "synthesis_explanation": "Why this reconciliation makes sense",
  "confidence": 0.85,
  "revision_note": "Brief note about what changed"
}}

OR if irreconcilable:
{{
  "can_reconcile": false,
  "reason": "Why these facts cannot be reconciled",
  "recommendation": "mark_for_review"
}}"""
```

---

## Wizard Integration (IMPORTANT TODO)

### Current Wizard Behavior
- Creates `state/knowledge_base.md` with hardcoded sections
- User manually fills in markdown

### Required Changes

**File:** `src/infrastructure/rp_initialization/rp_creator.py`

**Change 1: Add Knowledge Category Selection to Wizard**

Add wizard step for users to input initial knowledge with category selection:

```python
# In wizard flow, add new page:
def _build_world_knowledge_page(self) -> Vertical:
    """Build world knowledge input page."""
    container = Vertical()

    container.compose_add_child(Static("World Knowledge", classes="page-title"))
    container.compose_add_child(Static(
        "Add initial world facts. You can add more later.",
        classes="page-description"
    ))

    # Categories dropdown
    container.compose_add_child(Label("Category:"))
    container.compose_add_child(Select(
        options=[
            ("Magic System", "magic_system"),
            ("History", "history"),
            ("Geography", "geography"),
            ("Organizations", "organizations"),
            ("Culture", "culture"),
            # ... all categories
        ],
        id="knowledge-category"
    ))

    container.compose_add_child(Label("Fact:"))
    container.compose_add_child(Input(
        placeholder="e.g., Magic requires verbal incantations",
        id="knowledge-fact"
    ))

    container.compose_add_child(Label("Details (optional):"))
    container.compose_add_child(TextArea(
        "Additional explanation...",
        id="knowledge-details"
    ))

    container.compose_add_child(Button("Add Another Fact", id="add-knowledge-btn"))
    container.compose_add_child(ListView(id="knowledge-list"))  # Show added facts

    return container
```

**Change 2: Save as JSON Instead of Markdown**

Replace `_create_state_files()` knowledge_base.md creation:

```python
# OLD (around line 710-747):
knowledge_base = f"""# WORLD KNOWLEDGE BASE
...
"""
(paths.state_dir / "knowledge_base.md").write_text(knowledge_base, encoding="utf-8")

# NEW:
def _create_knowledge_json(self, rp_dir: Path, knowledge_entries: list[dict]) -> None:
    """Create initial knowledge_{session_id}.json file."""

    knowledge_data = {
        "session_id": "main",
        "last_updated": datetime.now(datetime.UTC).isoformat(),
        "last_updated_message": 0,
        "total_entries": len(knowledge_entries),
        "entries": knowledge_entries,
        "categories_index": self._build_category_index(knowledge_entries)
    }

    knowledge_path = rp_dir / "state" / "knowledge_main.json"
    knowledge_path.parent.mkdir(parents=True, exist_ok=True)

    with open(knowledge_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
```

**Change 3: Category Index Builder**

```python
def _build_category_index(self, entries: list[dict]) -> dict[str, int]:
    """Build category count index."""
    index = {}
    for entry in entries:
        for category in entry.get("categories", []):
            index[category] = index.get(category, 0) + 1
    return index
```

**Wizard Changes Summary:**
- ✅ Add knowledge input page with category selection
- ✅ Allow multiple knowledge entries during setup
- ✅ Save as `knowledge_main.json` (not .md)
- ✅ Use standardized categories from taxonomy
- ✅ Mark entries as `"source": "user_created"`

---

## Implementation Steps

### Phase 1: Agent Core (3 hours)
1. Create `KnowledgeExtractionAgent` class skeleton
2. Implement `_load_existing_knowledge()` with timeline support
3. Implement `_save_knowledge()` to timeline-specific file
4. Implement `_build_knowledge_prompt()` with multi-category support
5. Implement basic extraction (no contradictions yet)

### Phase 2: MD Conversion (1.5 hours)
6. Implement `_convert_knowledge_base_md()` parser
7. Handle section → category mapping
8. Test conversion with sample .md files

### Phase 3: Contradiction Synthesis (2 hours)
9. Implement `_check_for_contradictions()` with text similarity
10. Implement `_synthesize_contradiction()` with LLM call
11. Implement revision history tracking
12. Test with conflicting facts

### Phase 4: Integration (1 hour)
13. Add knowledge pointer to SessionStateService
14. Update `switch_timeline()` with knowledge field
15. Register agent in background_agent_strategy.py
16. Enable in defaults.py

### Phase 5: Testing (0.5 hours)
17. Test .md conversion
18. Test extraction with sample responses
19. Test contradiction synthesis
20. Test timeline branching

**Total: ~8 hours**

---

## Testing Checklist

- [ ] **MD Conversion:** knowledge_base.md → JSON entries created correctly
- [ ] **Multi-Category:** Entry with multiple categories stored as array
- [ ] **Extraction:** Extracts 3-5 facts from world-building heavy response
- [ ] **No Duplicates:** Doesn't extract same fact twice
- [ ] **Contradiction Detection:** Detects conflicting facts (>80% similarity)
- [ ] **Synthesis Success:** Reconciles contradictions intelligently
- [ ] **Synthesis Failure:** Handles irreconcilable contradictions
- [ ] **Revision History:** Tracks fact evolution correctly
- [ ] **Timeline-Specific:** Each timeline has own knowledge file
- [ ] **Branch Inheritance:** New branch inherits parent's knowledge
- [ ] **Taxonomy Enforcement:** Rejects invalid categories/tags
- [ ] **Confidence Scores:** Assigns appropriate confidence levels
- [ ] **Source Marking:** user_created vs auto_extracted marked correctly

---

## Success Criteria

**Functionality:**
- ✅ Converts existing knowledge_base.md files to JSON
- ✅ Extracts 3-5 knowledge entries per response (when present)
- ✅ Synthesizes contradictions with >80% success rate
- ✅ Multi-category support working correctly
- ✅ Timeline-specific files with branch inheritance
- ✅ Taxonomy enforcement prevents invalid categories/tags

**Quality:**
- ✅ <5% duplicate extractions
- ✅ Confidence scores align with fact certainty
- ✅ Revision history tracks knowledge evolution
- ✅ Synthesis explanations make narrative sense

**Integration:**
- ✅ Session state pointer works correctly
- ✅ Branching copies knowledge files
- ✅ Agent executes without errors
- ✅ Works with ResponseAnalyzerAgent and TimeTrackingAgent

---

## TODO: Wizard Changes (HIGH PRIORITY)

**Must update wizard before agent is useful:**

1. **Add knowledge input page to wizard**
   - Category selection dropdown (from KNOWLEDGE_CATEGORIES)
   - Fact input field
   - Details textarea (optional)
   - List of added facts
   - "Add Another" button

2. **Change wizard to save as JSON**
   - Replace knowledge_base.md creation
   - Save as knowledge_main.json
   - Use structured format from this document

3. **Wizard flow:**
   - Basic Info → Characters → World Knowledge → Templates → Done
   - OR: Make knowledge input optional (skip if user prefers)

4. **Backward compatibility:**
   - Agent converts old .md files on first run
   - Users with existing .md files not broken
   - Rename .md to .md.converted after conversion

---

## Integration with Other Agents

### Dependencies (Consumes Data From)
- **ResponseAnalyzerAgent** - scene_context (location, chapter, characters)
- **TimeTrackingAgent** - timestamps

### Supports (Provides Data To)
- **ContradictionDetectionAgent** (future) - Knowledge base for checking
- **FactExtractionAgent** (immediate, future) - Knowledge for context injection
- **PlotThreadDetectionAgent** - Can reference knowledge reveals in threads

### Data Flow
```
ResponseAnalyzerAgent → scene_context_{session_id}.json
TimeTrackingAgent → time_context in scene_context
                    ↓
    KnowledgeExtractionAgent reads scene_context
                    ↓
    knowledge_{session_id}.json created/updated
                    ↓
    Other agents read knowledge for context
```

---

## Files to Create/Modify

### New Files
- `src/automation/agents/implementations/knowledge_extraction_agent.py` (~800 lines)

### Modified Files
- `src/automation/agents/implementations/__init__.py` - Add export
- `src/automation/agents/background_agent_strategy.py` - Register agent
- `src/infrastructure/config/defaults.py` - Enable agent
- `src/infrastructure/sessions/session_state_service.py` - Add knowledge pointer
- `src/infrastructure/rp_initialization/rp_creator.py` - **Wizard changes (CRITICAL)**

---

## Future Enhancements (Post-MVP)

1. **Semantic Deduplication:** Use embeddings instead of text similarity
2. **Knowledge Graphs:** Link related knowledge entries
3. **Confidence Decay:** Reduce confidence if contradicted frequently
4. **User Review UI:** Show contradictions, let user choose canon
5. **Knowledge Search:** Full-text search across all knowledge
6. **Export:** Generate knowledge wiki/documentation
7. **Knowledge Validation:** Cross-check with STORY_GENOME.md

---

## Notes

- Knowledge is **timeline-specific** (like plot threads)
- Contradictions are **synthesized intelligently** (not just flagged)
- **Multiple categories** per entry (rich categorization)
- **Strict taxonomy** (prevents inconsistent tags)
- **Wizard integration required** for best UX

**Status:** Ready to implement after wizard changes planned.
