# Agent System - Complete Build Scope

**Date:** 2025-10-24
**Purpose:** Full inventory of what needs to be built for secondary LLM agent system
**Status:** Planning Phase

---

## Overview

This document breaks down EVERYTHING needed to implement the full agent system with secondary LLM support. We're tracking:

1. **Infrastructure** - Secondary LLM plumbing
2. **Data Structures** - New dataclasses for plot threads, knowledge, etc.
3. **Agent Implementations** - 10 agents that analyze responses
4. **Prompt Templates** - LLM prompts for each agent
5. **Integration Points** - How agents connect to main conversation flow
6. **Testing** - Unit and integration tests

---

## 1. Infrastructure (Secondary LLM) ✅ WELL-DEFINED

### Status: Ready to implement (~4-6 hours)

This is what we just documented in `SECONDARY_LLM_INFRASTRUCTURE_PLAN.md`.

**Components:**

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| AgentLLMConfig schema | `defaults.py` | ~40 | ❌ Need to add |
| `_initialize_agent_llm_client()` | `bridge_service.py` | ~50 | ❌ Need to add |
| AgentFactory signature update | `agent_factory.py` | ~5 | ❌ Need to add |
| AgentCoordinator wiring | `agent_coordinator.py` | ~5 | ❌ Need to add |
| Settings UI wiring | `llm_settings_page.py` | ~10 | ❌ Need to add |

**Dependencies:** None (all uses existing infrastructure)

**Complexity:** Low (copying existing patterns)

---

## 2. Data Structures (New Entities) ❌ NEEDS DESIGN

### Status: Need to design and implement (~2-4 hours)

You already have:
- ✅ `MemoryEntry` (entity_parser.py:58-68)
- ✅ `MemoryLog` (entity_parser.py:72-75)
- ✅ `CharacterEntity`, `LocationEntity`, etc.

You DON'T have:
- ❌ `PlotThread` - Track storylines and narrative arcs
- ❌ `KnowledgeEntry` - World-building facts and lore
- ❌ `Contradiction` - Narrative inconsistencies
- ❌ `ResponseClassification` - Scene type, pacing, etc.

### 2.1 PlotThread Dataclass

**File:** `src/domain/entities/entity_parser.py` (add after MemoryLog)

**Purpose:** Track ongoing storylines, character arcs, narrative threads

**Fields needed:**
```python
@dataclass(frozen=True)
class PlotThread:
    id: str  # e.g., "thread_alice_secret"
    title: str  # e.g., "Alice's Secret Identity"
    description: str  # Brief summary
    status: str  # "active", "resolved", "paused", "abandoned"
    participants: Sequence[str]  # Character names involved
    locations: Sequence[str]  # Where this thread takes place
    related_memories: Sequence[str]  # Memory IDs related to this thread
    tags: Sequence[str]  # ["mystery", "romance", "character_development"]
    priority: int  # 1-10, how important is this thread?
    started_at: str  # ISO timestamp
    last_updated: str  # ISO timestamp
    resolution_notes: str | None  # How it resolved (if status="resolved")
    message_index: int  # When thread was detected
```

**Repository methods needed:**
- `get_plot_threads(session_id) -> list[PlotThread]`
- `add_plot_thread(thread_data, session_id) -> None`
- `update_plot_thread(thread_id, updates, session_id) -> None`
- `get_active_threads(session_id) -> list[PlotThread]`

**Estimated:** 1 hour (dataclass + repository methods)

---

### 2.2 KnowledgeEntry Dataclass

**File:** `src/domain/entities/entity_parser.py` (add after PlotThread)

**Purpose:** Track world-building facts, lore, established canon

**Fields needed:**
```python
@dataclass(frozen=True)
class KnowledgeEntry:
    id: str  # e.g., "knowledge_magic_system"
    category: str  # "world_rules", "history", "culture", "technology", "magic"
    fact: str  # The actual knowledge statement
    details: str  # Elaboration and context
    source_memory_ids: Sequence[str]  # Where this knowledge came from
    related_entities: Sequence[str]  # Characters/locations related
    confidence: float  # 0.0-1.0, how certain is this fact?
    tags: Sequence[str]  # ["magic_system", "established_canon", "important"]
    contradicts: Sequence[str] | None  # IDs of facts this contradicts
    timestamp: str  # When extracted
    message_index: int  # When this was established
```

**Repository methods needed:**
- `get_knowledge_entries(session_id, category=None) -> list[KnowledgeEntry]`
- `add_knowledge_entry(entry_data, session_id) -> None`
- `search_knowledge(query: str, session_id) -> list[KnowledgeEntry]`
- `get_contradicting_knowledge(entry_id, session_id) -> list[KnowledgeEntry]`

**Estimated:** 1 hour (dataclass + repository methods)

---

### 2.3 Contradiction Dataclass

**File:** `src/domain/entities/entity_parser.py` (add after KnowledgeEntry)

**Purpose:** Track narrative inconsistencies that need resolution

**Fields needed:**
```python
@dataclass(frozen=True)
class Contradiction:
    id: str  # e.g., "contradiction_alice_age"
    type: str  # "fact", "characterization", "timeline", "world_rule"
    description: str  # What's contradictory
    statement_a: str  # First conflicting statement
    statement_b: str  # Second conflicting statement
    source_a: str  # Memory ID or knowledge ID for statement A
    source_b: str  # Memory ID or knowledge ID for statement B
    severity: str  # "minor", "moderate", "major"
    status: str  # "detected", "acknowledged", "resolved", "retconned", "ignored"
    affected_entities: Sequence[str]  # Characters/locations affected
    resolution_notes: str | None  # How it was resolved
    detected_at: str  # ISO timestamp
    resolved_at: str | None  # ISO timestamp (if resolved)
    message_index: int  # When detected
```

**Repository methods needed:**
- `get_contradictions(session_id, status=None) -> list[Contradiction]`
- `add_contradiction(contradiction_data, session_id) -> None`
- `resolve_contradiction(contradiction_id, resolution, session_id) -> None`
- `get_unresolved_contradictions(session_id) -> list[Contradiction]`

**Estimated:** 1 hour (dataclass + repository methods)

---

### 2.4 ResponseClassification Dataclass

**File:** `src/domain/entities/entity_parser.py` (add after Contradiction)

**Purpose:** Metadata about Claude's response for analytics/tracking

**Fields needed:**
```python
@dataclass(frozen=True)
class ResponseClassification:
    message_index: int  # Which response this is
    scene_type: str  # "action", "dialogue", "introspection", "description", "transition"
    tone: str  # "serious", "lighthearted", "tense", "romantic", "mysterious"
    pacing: str  # "fast", "medium", "slow"
    character_focus: Sequence[str]  # Which characters were prominent
    location: str  # Where scene takes place
    time_progression: str  # "none", "minutes", "hours", "days", "weeks"
    plot_threads_advanced: Sequence[str]  # Which threads progressed
    emotional_beats: Sequence[str]  # ["tension", "relief", "revelation"]
    word_count: int
    response_quality_score: float | None  # 0.0-1.0 (optional self-assessment)
    timestamp: str
```

**Repository methods needed:**
- `get_response_classification(message_index, session_id) -> ResponseClassification | None`
- `add_response_classification(classification_data, session_id) -> None`
- `get_scene_type_distribution(session_id) -> dict[str, int]`

**Estimated:** 0.5 hours (dataclass + repository methods)

---

### 2.5 Repository Extensions

**File:** `src/domain/entities/entity_repository.py`

**Need to add methods for new entity types:**

```python
# PlotThread methods
def get_plot_threads(self, session_id: str = "main") -> list[dict]:
    """Load all plot threads for session."""

def add_plot_thread(self, thread_data: dict, session_id: str = "main") -> None:
    """Add new plot thread."""

def update_plot_thread(self, thread_id: str, updates: dict, session_id: str = "main") -> None:
    """Update existing plot thread."""

# KnowledgeEntry methods
def get_knowledge_entries(
    self, session_id: str = "main", category: str | None = None
) -> list[dict]:
    """Load knowledge entries, optionally filtered by category."""

def add_knowledge_entry(self, entry_data: dict, session_id: str = "main") -> None:
    """Add new knowledge entry."""

# Contradiction methods
def get_contradictions(
    self, session_id: str = "main", status: str | None = None
) -> list[dict]:
    """Load contradictions, optionally filtered by status."""

def add_contradiction(self, contradiction_data: dict, session_id: str = "main") -> None:
    """Add new contradiction."""

def resolve_contradiction(
    self, contradiction_id: str, resolution: str, session_id: str = "main"
) -> None:
    """Mark contradiction as resolved."""

# ResponseClassification methods
def get_response_classification(
    self, message_index: int, session_id: str = "main"
) -> dict | None:
    """Get classification for specific response."""

def add_response_classification(
    self, classification_data: dict, session_id: str = "main"
) -> None:
    """Add response classification."""
```

**Storage format:**
- `state/plot_threads.json` - Array of PlotThread objects
- `state/knowledge.json` - Array of KnowledgeEntry objects
- `state/contradictions.json` - Array of Contradiction objects
- `state/response_classifications.json` - Array of ResponseClassification objects

**Estimated:** 2 hours (implement all repository methods)

---

## 3. Agent Implementations ❌ NEEDS IMPLEMENTATION

### Status: Need to implement (~30-40 hours total)

Each agent follows this structure:

```python
class SomeAgent:
    def __init__(self, rp_dir, log_file, llm_client=None, entity_repo=None):
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.llm_client = llm_client  # Secondary LLM
        self.entity_repo = entity_repo

    def execute(self, context: dict) -> dict:
        """Execute agent logic."""
        if not self.llm_client:
            return {"success": False, "error": "No LLM client"}

        # 1. Build prompt from context
        prompt = self._build_prompt(context)

        # 2. Call LLM
        response = self.llm_client.send_message(
            user_message=prompt,
            max_tokens=2048,
            temperature=0.0,
        )

        # 3. Parse response (JSON)
        results = self._parse_response(response.content)

        # 4. Save via repository
        self._save_results(results)

        return {"success": True, "data": results}

    def _build_prompt(self, context: dict) -> str:
        """Build LLM prompt."""
        pass

    def _parse_response(self, content: str) -> dict:
        """Parse LLM JSON response."""
        pass

    def _save_results(self, results: dict) -> None:
        """Save to repository."""
        pass
```

---

### 3.1 Background Agents (Run AFTER Claude Responds)

These analyze Claude's response and extract structured data.

#### 3.1.1 MemoryCreationAgent

**File:** `src/automation/agents/background/memory_creation_agent.py`

**Purpose:** Extract memorable moments from Claude's response

**Input context:**
```python
{
    "response_text": str,  # Claude's response
    "user_message": str,  # What user said
    "characters_in_scene": list[str],  # Detected characters
    "location": str,  # Current location
    "chapter": str,  # Current chapter
    "message_index": int,  # Response number
    "session_id": str,
}
```

**LLM prompt template:**
```
Analyze this roleplay response and extract memorable moments for each character.

USER MESSAGE: {user_message}
RESPONSE: {response_text}
CHARACTERS: {characters_in_scene}
LOCATION: {location}

For each character, identify:
- Important events they experienced
- Significant dialogue they said
- Emotional moments
- Decisions they made
- Relationship changes

Respond with JSON:
{
  "memories": [
    {
      "character": "Alice",
      "summary": "Brief summary of what happened",
      "details": "More detailed description",
      "tags": ["action", "emotion", "decision"],
      "quoted_dialogue": ["exact quotes from response"],
      "relationships": {
        "Alice-Bob": {
          "type": "friendship",
          "change": "grew_closer",
          "notes": "Shared vulnerable moment"
        }
      }
    }
  ]
}
```

**Parsing logic:**
- Extract JSON from response
- Validate required fields
- Create MemoryEntry objects
- Handle missing/malformed data gracefully

**Repository operations:**
```python
for memory in memories:
    self.entity_repo.append_memory_entry(
        character_name=memory["character"],
        entry={
            "id": f"mem_{uuid4().hex[:8]}",
            "summary": memory["summary"],
            "details": memory["details"],
            "tags": memory["tags"],
            "quoted_dialogue": memory["quoted_dialogue"],
            "relationships": memory.get("relationships", {}),
            "location": context["location"],
            "chapter": context["chapter"],
            "timestamp": datetime.now().isoformat(),
            "message_index": context["message_index"],
        }
    )
```

**Estimated:** 4-6 hours (prompt engineering + parsing + testing)

---

#### 3.1.2 RelationshipAnalysisAgent

**File:** `src/automation/agents/background/relationship_analysis_agent.py`

**Purpose:** Detect relationship changes between characters

**Input context:**
```python
{
    "response_text": str,
    "user_message": str,
    "characters_in_scene": list[str],
    "existing_relationships": dict,  # Current relationship states
    "session_id": str,
}
```

**LLM prompt template:**
```
Analyze this response for relationship changes between characters.

RESPONSE: {response_text}
CHARACTERS: {characters_in_scene}
CURRENT RELATIONSHIPS:
{existing_relationships}

Identify:
- New relationships formed
- Existing relationships that changed
- Relationship type (friendship, romance, rivalry, mentor, family, etc.)
- Direction of feelings (mutual, one-sided)
- Intensity/closeness (1-10)
- Recent developments

Respond with JSON:
{
  "relationships": [
    {
      "pair": ["Alice", "Bob"],
      "type": "romantic_interest",
      "direction": "Alice→Bob",
      "intensity": 7,
      "change": "confessed_feelings",
      "notes": "Alice revealed her feelings during conversation",
      "mutual": false
    }
  ]
}
```

**Parsing logic:**
- Extract relationship changes
- Compare with existing relationships
- Identify new vs updated relationships
- Track directionality (A→B vs A↔B)

**Repository operations:**
```python
# Relationships stored in MemoryEntry.relationships field
# AND/OR separate relationship tracking file
for rel in relationships:
    # Update character memory logs with relationship data
    # Or maintain separate relationship graph
```

**Estimated:** 4-6 hours

---

#### 3.1.3 PlotThreadDetectionAgent

**File:** `src/automation/agents/background/plot_thread_detection_agent.py`

**Purpose:** Identify and track narrative threads/storylines

**Input context:**
```python
{
    "response_text": str,
    "user_message": str,
    "existing_threads": list[PlotThread],
    "characters_in_scene": list[str],
    "recent_memories": list[MemoryEntry],  # Last 10 memories for context
    "message_index": int,
    "session_id": str,
}
```

**LLM prompt template:**
```
Analyze this response for plot threads and narrative developments.

RESPONSE: {response_text}
EXISTING THREADS:
{existing_threads}
RECENT CONTEXT:
{recent_memories}

Identify:
- New plot threads starting
- Existing threads progressing
- Threads that resolved
- Thread priority/importance

Respond with JSON:
{
  "new_threads": [
    {
      "title": "Alice's Secret Identity",
      "description": "Alice is hiding something about her past",
      "participants": ["Alice", "Bob"],
      "priority": 8,
      "tags": ["mystery", "character_backstory"]
    }
  ],
  "thread_updates": [
    {
      "thread_id": "thread_001",
      "status": "active",
      "progress": "Clues revealed about Alice's past",
      "priority_change": 0
    }
  ]
}
```

**Parsing logic:**
- Create PlotThread objects for new threads
- Update existing thread statuses
- Track progression/resolution

**Repository operations:**
```python
for thread in new_threads:
    self.entity_repo.add_plot_thread({
        "id": f"thread_{uuid4().hex[:8]}",
        "title": thread["title"],
        "description": thread["description"],
        # ... rest of fields
    }, session_id)

for update in thread_updates:
    self.entity_repo.update_plot_thread(
        update["thread_id"],
        updates={"status": update["status"], ...},
        session_id
    )
```

**Estimated:** 6-8 hours (complex logic)

---

#### 3.1.4 KnowledgeExtractionAgent

**File:** `src/automation/agents/background/knowledge_extraction_agent.py`

**Purpose:** Extract world-building facts and lore

**Input context:**
```python
{
    "response_text": str,
    "user_message": str,
    "existing_knowledge": list[KnowledgeEntry],
    "session_id": str,
}
```

**LLM prompt template:**
```
Extract world-building facts and lore from this response.

RESPONSE: {response_text}
EXISTING KNOWLEDGE:
{existing_knowledge}

Identify NEW facts about:
- World rules (magic, physics, technology)
- History and past events
- Culture and society
- Geography
- Organizations and factions

Only extract facts that are:
- Explicitly stated or strongly implied
- New information (not duplicating existing knowledge)
- Potentially important for narrative consistency

Respond with JSON:
{
  "knowledge": [
    {
      "category": "magic_system",
      "fact": "Magic requires verbal incantations",
      "details": "Alice explained that all spells need spoken words to work",
      "confidence": 0.9,
      "tags": ["magic", "established_canon"]
    }
  ]
}
```

**Parsing logic:**
- Extract knowledge entries
- Check for duplicates against existing knowledge
- Detect potential contradictions

**Repository operations:**
```python
for entry in knowledge:
    self.entity_repo.add_knowledge_entry({
        "id": f"know_{uuid4().hex[:8]}",
        "category": entry["category"],
        "fact": entry["fact"],
        # ... rest
    }, session_id)
```

**Estimated:** 4-6 hours

---

#### 3.1.5 ContradictionDetectionAgent

**File:** `src/automation/agents/background/contradiction_detection_agent.py`

**Purpose:** Detect narrative inconsistencies

**Input context:**
```python
{
    "response_text": str,
    "existing_knowledge": list[KnowledgeEntry],
    "recent_memories": list[MemoryEntry],
    "character_entities": dict[str, CharacterEntity],
    "session_id": str,
}
```

**LLM prompt template:**
```
Check this response for contradictions with established facts.

RESPONSE: {response_text}
ESTABLISHED KNOWLEDGE:
{existing_knowledge}
RECENT MEMORIES:
{recent_memories}
CHARACTER PROFILES:
{character_entities}

Identify contradictions:
- Factual inconsistencies (world rules violated)
- Character inconsistencies (acting out of character)
- Timeline issues (events in wrong order)
- Previous statements contradicted

Only flag genuine contradictions, not:
- Character growth/change
- Intentional mystery/reveals
- Different perspectives

Respond with JSON:
{
  "contradictions": [
    {
      "type": "fact",
      "description": "Magic used without verbal incantation",
      "statement_a": "All magic requires spoken words (from knowledge_003)",
      "statement_b": "Alice cast spell silently in this response",
      "severity": "moderate",
      "source_a": "knowledge_003",
      "source_b": "current_response"
    }
  ]
}
```

**Parsing logic:**
- Extract contradictions
- Map to source IDs (knowledge/memory IDs)
- Classify severity

**Repository operations:**
```python
for contradiction in contradictions:
    self.entity_repo.add_contradiction({
        "id": f"contra_{uuid4().hex[:8]}",
        "type": contradiction["type"],
        # ... rest
        "status": "detected",
    }, session_id)
```

**Estimated:** 6-8 hours (complex analysis)

---

#### 3.1.6 ResponseAnalyzerAgent

**File:** `src/automation/agents/background/response_analyzer_agent.py`

**Purpose:** Classify scene type, tone, pacing

**Input context:**
```python
{
    "response_text": str,
    "user_message": str,
    "characters_in_scene": list[str],
    "location": str,
    "message_index": int,
    "session_id": str,
}
```

**LLM prompt template:**
```
Classify this response's narrative characteristics.

RESPONSE: {response_text}

Analyze:
- Scene type (action, dialogue, introspection, description, transition)
- Tone (serious, lighthearted, tense, romantic, mysterious, humorous)
- Pacing (fast, medium, slow)
- Time progression (none, minutes, hours, days, weeks)
- Emotional beats (tension, relief, revelation, conflict, resolution, etc.)
- Character focus (which characters were prominent)
- Plot threads advanced (which storylines progressed)

Respond with JSON:
{
  "scene_type": "dialogue",
  "tone": "serious",
  "pacing": "medium",
  "time_progression": "minutes",
  "character_focus": ["Alice", "Bob"],
  "emotional_beats": ["tension", "revelation"],
  "plot_threads_advanced": ["thread_001", "thread_005"],
  "word_count": 450
}
```

**Parsing logic:**
- Extract classification data
- Create ResponseClassification object

**Repository operations:**
```python
self.entity_repo.add_response_classification({
    "message_index": context["message_index"],
    "scene_type": classification["scene_type"],
    # ... rest
    "timestamp": datetime.now().isoformat(),
}, session_id)
```

**Estimated:** 3-4 hours (simpler than others)

---

### 3.2 Immediate Agents (Run BEFORE Claude Responds)

These analyze user's message and prepare context for Claude.

#### 3.2.1 QuickEntityAnalysisAgent

**File:** `src/automation/agents/immediate/quick_entity_analysis_agent.py`

**Purpose:** Identify entities mentioned in user message

**Input context:**
```python
{
    "user_message": str,
    "available_entities": list[str],  # All known entity names
    "session_id": str,
}
```

**Note:** This might NOT need LLM! You already have `entity_service.detect_mentions()`.

**Decision:**
- Option A: Use existing `detect_mentions()` (keyword-based, fast, free)
- Option B: Use LLM for semantic matching (slower, costs money, better accuracy)

**If using LLM:**
```
Identify which entities are mentioned or relevant to this message.

USER MESSAGE: {user_message}
AVAILABLE ENTITIES: {available_entities}

Include entities that are:
- Directly mentioned by name
- Referenced indirectly ("my sister" → Alice if context suggests it)
- Contextually relevant (message is about location Alice is in)

Respond with JSON:
{
  "mentioned_entities": ["Alice", "Bob", "Riverside_Cafe"],
  "contextually_relevant": ["Downtown"]
}
```

**Estimated:** 2-3 hours (might skip LLM entirely)

---

#### 3.2.2 FactExtractionAgent

**File:** `src/automation/agents/immediate/fact_extraction_agent.py`

**Purpose:** Pull relevant facts about entities in scene

**Input context:**
```python
{
    "user_message": str,
    "entities_in_scene": list[str],
    "entity_data": dict[str, CharacterEntity | LocationEntity],
    "knowledge_base": list[KnowledgeEntry],
    "session_id": str,
}
```

**LLM prompt template:**
```
Extract the most relevant facts to include in Claude's context.

USER MESSAGE: {user_message}
ENTITIES IN SCENE: {entities_in_scene}

ENTITY PROFILES:
{entity_data}

KNOWLEDGE BASE:
{knowledge_base}

Select 5-10 most relevant facts to provide to Claude, focusing on:
- Information directly relevant to user's message
- Character traits that inform how they'd respond
- World rules that apply to current situation
- Recent developments in relationships

Respond with JSON:
{
  "relevant_facts": [
    {
      "entity": "Alice",
      "fact_type": "personality",
      "fact": "Alice is naturally curious and asks lots of questions",
      "relevance": "User asked about investigation, Alice would be interested"
    }
  ]
}
```

**Parsing logic:**
- Extract facts
- Format for prompt injection

**Output:**
```python
return {
    "success": True,
    "facts_for_injection": [
        "Alice (personality): Curious, asks many questions",
        "Bob (relationship): Alice trusts Bob deeply",
        # ...
    ]
}
```

**Estimated:** 4-5 hours

---

#### 3.2.3 MemoryExtractionAgent

**File:** `src/automation/agents/immediate/memory_extraction_agent.py`

**Purpose:** Find relevant memories for current context

**Input context:**
```python
{
    "user_message": str,
    "entities_in_scene": list[str],
    "all_memories": dict[str, list[MemoryEntry]],  # Per-character memories
    "session_id": str,
}
```

**LLM prompt template:**
```
Find the most relevant memories for this conversation context.

USER MESSAGE: {user_message}
CHARACTERS: {entities_in_scene}

AVAILABLE MEMORIES (last 50 per character):
{all_memories}

Select 5-10 memories that:
- Are directly relevant to what user is asking/doing
- Provide important context Claude should remember
- Inform how characters would respond
- Avoid redundancy (don't select similar memories)

Prioritize:
1. Recent memories (last 5-10 responses)
2. Memories directly related to current topic
3. Emotionally significant moments
4. Unresolved plot threads

Respond with JSON:
{
  "relevant_memories": [
    {
      "character": "Alice",
      "memory_id": "mem_abc123",
      "summary": "Alice confessed feelings to Bob",
      "relevance": "User asking about their relationship status"
    }
  ]
}
```

**Parsing logic:**
- Extract memory IDs
- Look up full memory details
- Format for prompt injection

**Output:**
```python
return {
    "success": True,
    "memories_for_injection": [
        "Alice (recent): Confessed feelings to Bob in garden",
        "Bob (recent): Seemed surprised but didn't reject her",
        # ...
    ]
}
```

**Estimated:** 4-5 hours

---

#### 3.2.4 PlotThreadExtractionAgent

**File:** `src/automation/agents/immediate/plot_thread_extraction_agent.py`

**Purpose:** Identify active plot threads relevant to current message

**Input context:**
```python
{
    "user_message": str,
    "entities_in_scene": list[str],
    "plot_threads": list[PlotThread],
    "session_id": str,
}
```

**LLM prompt template:**
```
Identify which active plot threads are relevant to this message.

USER MESSAGE: {user_message}
CHARACTERS: {entities_in_scene}

ACTIVE PLOT THREADS:
{plot_threads}

Select plot threads that:
- Involve characters in current scene
- Relate to user's message topic
- Are still active/unresolved
- Would inform Claude's response

Respond with JSON:
{
  "relevant_threads": [
    {
      "thread_id": "thread_001",
      "title": "Alice's Secret Identity",
      "relevance": "User asking about Alice's past",
      "priority": 8
    }
  ]
}
```

**Parsing logic:**
- Extract thread IDs
- Look up full thread details
- Format for prompt injection

**Output:**
```python
return {
    "success": True,
    "threads_for_injection": [
        "Active thread: Alice's Secret Identity (high priority)",
        "Active thread: Investigation of mysterious events (medium priority)",
        # ...
    ]
}
```

**Estimated:** 4-5 hours

---

## 4. Prompt Templates & Parsing ❌ NEEDS IMPLEMENTATION

### Status: Part of agent implementation

Each agent needs:

1. **System prompt template** - Instructions for LLM
2. **User prompt template** - Formatted context data
3. **Response schema** - JSON structure LLM should return
4. **Parser logic** - Extract + validate JSON from LLM response
5. **Error handling** - Handle malformed/incomplete responses

**Common patterns:**

```python
class PromptBuilder:
    @staticmethod
    def build_memory_prompt(context: dict) -> str:
        return f"""Analyze this roleplay response...

RESPONSE: {context['response_text']}
...
Respond with JSON:
{{"memories": [...]}}
"""

class ResponseParser:
    @staticmethod
    def parse_memory_response(content: str) -> list[dict]:
        import json
        import re

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")

        data = json.loads(json_match.group())

        # Validate required fields
        if "memories" not in data:
            raise ValueError("Missing 'memories' field")

        return data["memories"]
```

**Estimated:** Included in agent implementation time

---

## 5. Integration Points ❌ NEEDS DESIGN

### Status: Need to design flow (~4-6 hours)

**Where do agents run in the main conversation flow?**

### 5.1 Background Agent Flow (After Claude Responds)

**File:** Likely `src/automation/services/agent_coordinator.py` or new orchestration layer

**Current flow:**
```
User sends message
  ↓
Automation system (triggers, templates, immediate agents)
  ↓
Primary LLM (Claude responds)
  ↓
Response sent to user
  ↓
??? Background agents run here ???
```

**Proposed flow:**
```python
# In message_handler or bridge_service
async def handle_user_message(user_message: str) -> str:
    # 1. Run immediate agents (enhance prompt)
    immediate_context = await agent_coordinator.run_immediate_agents(
        user_message=user_message,
        session_id=current_session,
    )

    # 2. Build enhanced prompt
    enhanced_prompt = prompt_builder.build(
        user_message=user_message,
        facts=immediate_context.get("facts", []),
        memories=immediate_context.get("memories", []),
        plot_threads=immediate_context.get("plot_threads", []),
    )

    # 3. Call primary LLM (Claude)
    response = await primary_llm_client.send_message(enhanced_prompt)

    # 4. Send response to user immediately
    send_to_user(response.content)

    # 5. Run background agents asynchronously (don't block user)
    asyncio.create_task(
        agent_coordinator.run_background_agents(
            user_message=user_message,
            response_text=response.content,
            session_id=current_session,
        )
    )

    return response.content
```

**Key decisions:**
- Run background agents async (don't block user)
- Run immediate agents sync (must complete before Claude responds)
- Cache immediate agent results (5-10 second TTL)
- Handle agent failures gracefully (log but don't break conversation)

**Estimated:** 3-4 hours (design + implementation)

---

### 5.2 Prompt Injection Strategy

**Where exactly do agent results go into Claude's prompt?**

**Current prompt structure:**
```
[System Message]
You are roleplaying as...

[Character Cards] - From entity loader

[Recent Conversation History] - Last N messages

[User Message] - Current input
```

**Enhanced prompt structure:**
```
[System Message]
You are roleplaying as...

[Character Cards] - From entity loader

[Relevant Facts] ← FROM FactExtractionAgent
- Alice (personality): Curious and investigative
- Bob (background): Former detective
...

[Recent Memories] ← FROM MemoryExtractionAgent
- Alice (recent): Confessed feelings to Bob
- Bob (recent): Discovered clue about mystery
...

[Active Plot Threads] ← FROM PlotThreadExtractionAgent
- HIGH PRIORITY: Investigation of mysterious events
- MEDIUM PRIORITY: Alice and Bob's developing relationship
...

[Recent Conversation History] - Last N messages

[User Message] - Current input
```

**Implementation:**
```python
class PromptBuilder:
    def build_enhanced_prompt(
        self,
        user_message: str,
        character_cards: list[str],
        conversation_history: list[dict],
        agent_context: dict,
    ) -> str:
        sections = [
            self._build_system_message(),
            self._build_character_cards(character_cards),
        ]

        # Add agent-extracted context
        if agent_context.get("facts"):
            sections.append(self._build_facts_section(agent_context["facts"]))

        if agent_context.get("memories"):
            sections.append(self._build_memories_section(agent_context["memories"]))

        if agent_context.get("plot_threads"):
            sections.append(self._build_threads_section(agent_context["plot_threads"]))

        sections.append(self._build_conversation_history(conversation_history))
        sections.append(user_message)

        return "\n\n".join(sections)
```

**Estimated:** 2-3 hours

---

### 5.3 Caching Strategy

**Problem:** Immediate agents take time (~1-2 seconds), user waits

**Solution:** Cache agent results briefly

```python
class AgentResultCache:
    def __init__(self, ttl_seconds: int = 10):
        self.cache: dict[str, tuple[dict, float]] = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> dict | None:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: dict) -> None:
        self.cache[key] = (value, time.time())
```

**Usage:**
```python
# Check cache first
cache_key = f"{session_id}:{user_message_hash}"
cached_context = agent_cache.get(cache_key)

if cached_context:
    immediate_context = cached_context
else:
    immediate_context = await run_immediate_agents(...)
    agent_cache.set(cache_key, immediate_context)
```

**Estimated:** 1 hour

---

## 6. Testing ❌ NEEDS IMPLEMENTATION

### Status: Need comprehensive test suite (~10-15 hours)

### 6.1 Unit Tests (Per Agent)

**Pattern:**
```python
# tests/automation/agents/background/test_memory_creation_agent.py

def test_memory_creation_agent_with_mock_llm():
    """Test agent with mock LLM response."""

    # Setup
    mock_llm = MockLLMClient()
    mock_llm.set_response('{"memories": [...]}')

    agent = MemoryCreationAgent(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        llm_client=mock_llm,
        entity_repo=mock_repo,
    )

    # Execute
    result = agent.execute({
        "response_text": "Alice walked into the room...",
        "characters_in_scene": ["Alice", "Bob"],
        # ...
    })

    # Assert
    assert result["success"] is True
    assert len(result["data"]["memories"]) > 0

    # Verify repository called
    mock_repo.append_memory_entry.assert_called()
```

**Test coverage per agent:**
- ✅ Successful execution with valid LLM response
- ✅ Handling malformed JSON
- ✅ Handling missing LLM client
- ✅ Handling missing entity repository
- ✅ Parsing edge cases (empty arrays, null fields)
- ✅ Repository operations called correctly

**Estimated:** 1 hour per agent × 10 = 10 hours

---

### 6.2 Integration Tests

**Test full pipeline:**
```python
def test_full_agent_pipeline_e2e():
    """Test immediate → LLM → background agent flow."""

    # 1. Run immediate agents
    immediate_result = coordinator.run_immediate_agents(
        user_message="Alice, tell me about your past",
        session_id="test",
    )

    assert immediate_result["facts"] is not None
    assert immediate_result["memories"] is not None

    # 2. Simulate LLM response
    response_text = "Alice hesitated, then began to speak..."

    # 3. Run background agents
    background_result = coordinator.run_background_agents(
        user_message="Alice, tell me about your past",
        response_text=response_text,
        session_id="test",
    )

    assert background_result["memories_created"] > 0
    assert background_result["plot_threads_updated"] >= 0
```

**Estimated:** 3-5 hours

---

### 6.3 Cost Tracking Tests

**Verify LLM costs:**
```python
def test_agent_costs_within_budget():
    """Ensure agents don't exceed cost budget."""

    agent = MemoryCreationAgent(llm_client=real_deepseek_client, ...)

    result = agent.execute(context)

    # Check token usage
    assert result["usage"]["input_tokens"] < 1000
    assert result["usage"]["output_tokens"] < 500

    # Estimate cost (DeepSeek ~$0.0001/1K tokens)
    total_tokens = result["usage"]["input_tokens"] + result["usage"]["output_tokens"]
    estimated_cost = (total_tokens / 1000) * 0.0001

    assert estimated_cost < 0.001  # Less than 0.1 cent per call
```

**Estimated:** 2 hours

---

## 7. Total Build Scope Summary

### By Component

| Component | Complexity | Est. Hours | Priority |
|-----------|------------|------------|----------|
| **1. Infrastructure** | Low | 4-6 | 🔴 Critical |
| **2. Data Structures** | Low-Medium | 4-6 | 🔴 Critical |
| **3. Background Agents** (6) | Medium-High | 27-38 | 🟡 High |
| **4. Immediate Agents** (4) | Medium | 14-18 | 🟡 High |
| **5. Integration/Wiring** | Medium | 6-10 | 🔴 Critical |
| **6. Testing** | Medium | 10-15 | 🟢 Medium |
| **TOTAL** | | **65-93 hours** | |

### By Priority

#### Phase 1: Foundation (Must Have) - 14-22 hours
1. ✅ Infrastructure (Secondary LLM) - 4-6 hours
2. ✅ Data structures (all 4 entities + repository) - 4-6 hours
3. ✅ Integration wiring (prompt injection, caching) - 6-10 hours

#### Phase 2: First Agent (Proof of Concept) - 6-8 hours
4. ✅ MemoryCreationAgent (background) - 4-6 hours
5. ✅ Basic tests - 2 hours

#### Phase 3: Core Agents (High Value) - 20-28 hours
6. ✅ RelationshipAnalysisAgent - 4-6 hours
7. ✅ PlotThreadDetectionAgent - 6-8 hours
8. ✅ MemoryExtractionAgent (immediate) - 4-5 hours
9. ✅ FactExtractionAgent (immediate) - 4-5 hours
10. ✅ Tests - 2-4 hours

#### Phase 4: Additional Agents (Nice to Have) - 25-35 hours
11. ⚪ KnowledgeExtractionAgent - 4-6 hours
12. ⚪ ContradictionDetectionAgent - 6-8 hours
13. ⚪ ResponseAnalyzerAgent - 3-4 hours
14. ⚪ QuickEntityAnalysisAgent (immediate) - 2-3 hours
15. ⚪ PlotThreadExtractionAgent (immediate) - 4-5 hours
16. ⚪ Comprehensive tests - 6-9 hours

---

## 8. Decision Points

### 8.1 Agent Grouping Strategy

**Option A: Individual Agents (Current Plan)**
- ✅ Modular, easy to test
- ✅ Can enable/disable individually
- ❌ More LLM calls (higher cost)
- **Cost:** ~$0.01/message (10 agents × $0.001)

**Option B: Unified Agent (Single Call)**
- ✅ Cheaper (1 LLM call)
- ❌ Harder to test
- ❌ All-or-nothing (can't disable parts)
- **Cost:** ~$0.001/message (1 agent)

**Option C: Grouped Agents (Hybrid) - RECOMMENDED**
- ✅ Balance of cost and modularity
- ✅ Logical groupings
- **Cost:** ~$0.003/message (3 agents)

**Groups:**
1. **Memory & Relationships** - MemoryCreationAgent + RelationshipAnalysisAgent
2. **Plot & Knowledge** - PlotThreadDetectionAgent + KnowledgeExtractionAgent + ContradictionDetectionAgent
3. **Response Analysis** - ResponseAnalyzerAgent
4. **Context Extraction** (Immediate) - All 4 immediate agents in one call

### 8.2 When to Run Agents?

**Option A: Every Response (Thoroughness)**
- ✅ Complete analysis
- ❌ Expensive ($0.01/message)
- ❌ Slower

**Option B: Selective (Based on Response Type)**
- ✅ Cheaper
- ✅ Faster
- ❌ More complex logic
- Example: Only run MemoryCreation if response > 200 words

**Option C: User-Configurable per Agent**
- ✅ Most flexible
- ❌ Complex UI
- ❌ More maintenance

### 8.3 LLM Provider for Agents?

**Option A: DeepSeek via OpenRouter (RECOMMENDED)**
- ✅ Cheapest (~$0.0001/1K tokens)
- ✅ Good quality for analysis
- ❌ Slower than OpenAI

**Option B: GPT-3.5-turbo via OpenAI**
- ✅ Fast
- ✅ Good quality
- ❌ ~10x more expensive than DeepSeek

**Option C: Claude Haiku**
- ✅ Best quality
- ❌ ~50x more expensive than DeepSeek

---

## 9. Quick Start Checklist

### Week 1: Foundation
- [ ] Implement secondary LLM infrastructure
- [ ] Add PlotThread, KnowledgeEntry, Contradiction, ResponseClassification dataclasses
- [ ] Extend entity repository with new methods
- [ ] Test infrastructure end-to-end

### Week 2: First Agent
- [ ] Implement MemoryCreationAgent
- [ ] Write prompt template
- [ ] Implement parsing logic
- [ ] Write unit tests
- [ ] Test with real LLM (verify costs)

### Week 3: Core Agents
- [ ] Implement RelationshipAnalysisAgent
- [ ] Implement PlotThreadDetectionAgent
- [ ] Design integration flow (where agents run)
- [ ] Implement prompt injection

### Week 4: Immediate Agents
- [ ] Implement MemoryExtractionAgent
- [ ] Implement FactExtractionAgent
- [ ] Implement caching strategy
- [ ] Integration tests

### Week 5+: Remaining Agents
- [ ] Implement remaining 6 agents
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation

---

## 10. Files to Create

**New files needed:**

```
src/domain/entities/
  entity_parser.py (modify - add 4 new dataclasses)

src/domain/entities/
  entity_repository.py (modify - add repository methods)

src/automation/agents/background/
  __init__.py
  memory_creation_agent.py
  relationship_analysis_agent.py
  plot_thread_detection_agent.py
  knowledge_extraction_agent.py
  contradiction_detection_agent.py
  response_analyzer_agent.py

src/automation/agents/immediate/
  __init__.py
  quick_entity_analysis_agent.py
  fact_extraction_agent.py
  memory_extraction_agent.py
  plot_thread_extraction_agent.py

tests/automation/agents/background/
  test_memory_creation_agent.py
  test_relationship_analysis_agent.py
  test_plot_thread_detection_agent.py
  test_knowledge_extraction_agent.py
  test_contradiction_detection_agent.py
  test_response_analyzer_agent.py

tests/automation/agents/immediate/
  test_quick_entity_analysis_agent.py
  test_fact_extraction_agent.py
  test_memory_extraction_agent.py
  test_plot_thread_extraction_agent.py

tests/automation/agents/integration/
  test_full_agent_pipeline.py
  test_prompt_injection.py
  test_agent_caching.py
```

**Total new files:** ~30

---

## Next Steps

Want to:
1. Start with Phase 1 (Foundation) - Infrastructure + Data Structures?
2. Review and refine the agent designs first?
3. Make decisions on the open questions (grouping strategy, when to run, etc.)?
4. Something else?
