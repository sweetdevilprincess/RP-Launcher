# Agent System Implementation Plan
**Date:** 2025-10-28
**Status:** Ready to Implement
**Estimated Effort:** 36-48 hours total

---

## Executive Summary

This document outlines the complete implementation plan for connecting automation agents to the secondary LLM system. The LLM routing infrastructure is **already complete** - we just need to create the agents and wire them into the pipeline.

**What's Done:**
- ✅ Dual LLM client architecture (primary + secondary)
- ✅ LLM routing functions (`call_primary_llm`, `call_secondary_llm`)
- ✅ Provider-agnostic router (works with ANY LLM)
- ✅ Settings UI for secondary provider/temperature
- ✅ Agent execution pipeline (strategies, coordinator, executor)

**What's Missing:**
- ❌ Base agent class with LLM access
- ❌ 10 concrete agent implementations
- ❌ Bridge wiring through the pipeline

---

## Current State Analysis

### LLM Router - ALREADY IMPLEMENTED ✅

**File:** `src/infrastructure/llm/llm_router.py`

The router is complete and functional:

```python
def call_primary_llm(bridge, user_message, *, cached_context=None, **kwargs) -> LLMResponse:
    """Call primary LLM for main conversation."""
    if not bridge.primary_client:
        raise RuntimeError("No primary LLM configured")
    return bridge.primary_client.send_message(user_message, cached_context, **kwargs)

def call_secondary_llm(bridge, user_message, *, cached_context=None, **kwargs) -> LLMResponse:
    """Call secondary LLM for automation agents.

    Routes to primary if use_secondary_for_automation is False.
    Routes to secondary if toggle ON.
    """
    use_secondary = bridge.llm_routing.get("use_secondary_for_automation", False)

    if not use_secondary or not bridge.secondary_client:
        return call_primary_llm(bridge, user_message, cached_context, **kwargs)

    return bridge.secondary_client.send_message(user_message, cached_context, **kwargs)
```

**Key Features:**
- Provider-agnostic (works with Claude API, OpenAI, OpenRouter, etc.)
- Automatic routing based on `use_secondary_for_automation` toggle
- Fallback to primary if secondary not configured
- Fully tested and working

**Exported in:** `src/infrastructure/llm/__init__.py`

**No changes needed to the router!**

---

### Agent Execution Pipeline - ALREADY BUILT ✅

**Files:**
- `src/automation/services/agent_coordinator.py` - Orchestrates pipeline
- `src/automation/services/agent_executor.py` - Concurrent execution with retry
- `src/automation/services/agent_factory.py` - Creates agent instances
- `src/automation/agents/immediate_agent_strategy.py` - Pre-response agents
- `src/automation/agents/background_agent_strategy.py` - Post-response agents
- `src/automation/agents/registry.py` - Strategy creation

**Flow:**
```
AutomationService
    ↓
AgentRunner (coordinates strategies)
    ↓
ImmediateAgentStrategy → Creates agents → Executes concurrently → Formats results
BackgroundAgentStrategy → Creates agents → Executes concurrently → Saves to files
```

**Current Agent Instantiation:**
```python
# immediate_agent_strategy.py line 299
# background_agent_strategy.py line 266
agent = agent_class(rp_dir=rp_dir, log_file=None)  # ← No LLM access!
```

**Problem:** Agents are created but have NO way to call the LLM.

---

## What Needs to Be Built

### 1. Base Agent Class (**NEW FILE**)

**File:** `src/automation/agents/base_agent.py`

**Purpose:** Provide common functionality for all agents, especially LLM access via the router.

**Full Implementation:**

```python
"""Base Agent Class - Provides LLM access for automation agents."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any

from ...infrastructure.llm import call_secondary_llm


class BaseAgent(ABC):
    """Abstract base class for all automation agents.

    Provides:
    - LLM access via secondary provider (or primary if toggle OFF)
    - Common error handling and logging
    - Template method pattern for agent execution

    All agents inherit from BaseAgent and implement:
    1. get_agent_id() - Unique identifier
    2. execute() - Main agent logic
    """

    def __init__(
        self,
        rp_dir: Path,
        log_file: Optional[Path] = None,
        bridge: "BridgeService" = None
    ):
        """Initialize base agent.

        Args:
            rp_dir: RP directory path
            log_file: Optional log file for agent activity
            bridge: Bridge service instance (provides LLM access)
        """
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.bridge = bridge

    @abstractmethod
    def get_agent_id(self) -> str:
        """Get unique agent identifier.

        Returns:
            Agent ID like 'memory_creation', 'fact_extraction', etc.
        """
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        """Execute agent logic and return result.

        This method should:
        1. Build LLM prompt from provided context
        2. Call LLM via self.call_llm()
        3. Parse LLM response
        4. Save results (if needed)
        5. Return formatted output

        Args:
            *args: Agent-specific arguments
            **kwargs: Agent-specific keyword arguments

        Returns:
            Result string (usually JSON)
        """
        pass

    def call_llm(self, prompt: str, *, temperature: float = 0.0, **kwargs) -> str:
        """Call secondary LLM for automation tasks.

        This method uses call_secondary_llm() which:
        - Routes to secondary provider if toggle ON
        - Falls back to primary if toggle OFF
        - Uses configured temperature for secondary provider

        Args:
            prompt: The prompt to send to LLM
            temperature: Temperature override (default 0.0 for analysis)
            **kwargs: Additional arguments for LLM client

        Returns:
            LLM response content as string

        Raises:
            RuntimeError: If no LLM is configured
        """
        if not self.bridge:
            raise RuntimeError(f"[{self.get_agent_id()}] No bridge configured - cannot access LLM")

        response = call_secondary_llm(
            self.bridge,
            user_message=prompt,
            temperature=temperature,
            **kwargs
        )

        return response.content

    def _log(self, message: str) -> None:
        """Log a message to the log file if configured.

        Args:
            message: Message to log
        """
        if self.log_file:
            from ...automation.core import log_to_file
            log_to_file(self.log_file, f"[{self.get_agent_id()}] {message}")
```

**Key Features:**
- Uses `call_secondary_llm()` router automatically
- Respects secondary provider toggle
- Falls back to primary if needed
- Temperature defaults to 0.0 for consistent analysis
- Logging support
- Abstract template for all agents

---

### 2. Agent Implementations (10 NEW FILES)

#### Pattern for All Agents

```python
from .base_agent import BaseAgent
import json

class SomeAgent(BaseAgent):
    """Agent description."""

    def get_agent_id(self) -> str:
        return "agent_name"

    def execute(self, context_arg1: str, context_arg2: str, **kwargs) -> str:
        """Execute agent logic."""
        try:
            # Step 1: Build prompt
            prompt = self._build_prompt(context_arg1, context_arg2)

            # Step 2: Call LLM (uses secondary via router!)
            response = self.call_llm(prompt, temperature=0.0)

            # Step 3: Parse response
            result = self._parse_response(response)

            # Step 4: Save results (optional)
            self._save_results(result)

            # Step 5: Return formatted output
            return json.dumps({"success": True, "data": result})

        except Exception as e:
            self._log(f"Error: {e}")
            return json.dumps({"success": False, "error": str(e)})

    def _build_prompt(self, arg1, arg2) -> str:
        """Build LLM prompt from context."""
        return f"""Analyze this data:

ARG1: {arg1}
ARG2: {arg2}

Respond with JSON:
{{"key": "value"}}
"""

    def _parse_response(self, content: str) -> dict:
        """Parse LLM JSON response."""
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")
        return json.loads(json_match.group())

    def _save_results(self, results: dict) -> None:
        """Save to repository (if needed)."""
        pass
```

---

#### Background Agents (Run AFTER Claude Responds)

##### 2.1 MemoryCreationAgent

**File:** `src/automation/agents/implementations/memory_creation_agent.py`

**Purpose:** Extract memorable moments from Claude's response and save to character memory logs.

**UPDATED 2025-10-29**: Clarifications based on existing codebase analysis and requirements.

---

**Agent Receives (from background_agent_strategy):**
```python
execute(
    user_message: str,       # User's input
    message_number: int,     # Current message index
    claude_response: str     # Claude's response to analyze (in kwargs)
)
```

**Agent Reads from Session State (Populated by ResponseAnalyzerAgent):**
- `characters_in_scene` - From session state `scene_context.characters_in_scene`
- `location` - From session state `scene_context.location`
- `chapter` - From session state `scene_context.chapter`
- `session_id` - Automatically handled by FixtureEntityRepository (for timeline branching)

**Fallback Strategy:**
- Agents run concurrently, so ResponseAnalyzerAgent may not finish first
- If session state is empty (first run), extract via LLM as fallback
- Eventually ResponseAnalyzerAgent populates session state and fallback is unused

---

**LLM Prompt:**
```
Analyze this roleplay response and extract memorable moments for each character.

USER MESSAGE: {user_message}
CLAUDE'S RESPONSE: {claude_response}
CHARACTERS DETECTED: {characters_in_scene}

For each character, identify:
- Important events they experienced
- Significant dialogue they said or heard
- Emotional moments
- Decisions they made
- Character development

DO NOT include relationship changes here - those are tracked separately.

Respond with JSON:
{
  "memories": [
    {
      "character": "Alice",
      "summary": "Brief 1-sentence summary",
      "details": "More detailed description",
      "tags": ["Alice", "Bob", "emotion_tag", "action_tag", "descriptor"],
      "quoted_dialogue": ["\"Exact quote with quotes\"", "\"Another quote\""]
    }
  ]
}
```

**Tag Format (IMPORTANT):**
Tags should include:
1. **Character names** mentioned in the memory (e.g., "Alice", "Bob")
2. **Descriptive tags** for categorization

**TODO**: Define standardized emotion tags to ensure consistency:
- Emotions: `happy`, `sad`, `angry`, `fearful`, `surprised`, `disgusted`, `anxious`, etc.
- Actions: `combat`, `dialogue`, `decision`, `discovery`, `revelation`, etc.
- Consider using a predefined tag taxonomy to prevent tag sprawl

---

**Existing Memory Structure** (from `entity_parser.py`):
```python
@dataclass(frozen=True)
class MemoryEntry:
    id: str                          # UUID like "mem_abc12345"
    summary: str                     # Brief 1-sentence summary
    details: str                     # Detailed description
    tags: Sequence[str]              # Character names + descriptive tags
    quoted_dialogue: Sequence[str]   # Exact quotes with quote marks
    relationships: Mapping[str, Any] # DEPRECATED - use RelationshipAnalysisAgent
    location: str                    # Where it happened
    chapter: str                     # Chapter reference
    timestamp: str | None            # ISO 8601 format
    message_index: int = 0           # For timeline filtering
```

**Note on Relationships Field:**
- The `relationships` field exists in MemoryEntry for backward compatibility
- **DO NOT populate this field** - it should be empty `{}`
- Relationship tracking is handled by `RelationshipAnalysisAgent`
- Each character has separate `relationships.json` file tracking their relationships

---

**Save Logic:**
```python
from uuid import uuid4

for memory in llm_response["memories"]:
    character = memory["character"]

    memory_entry = {
        "id": f"mem_{uuid4().hex[:8]}",
        "summary": memory["summary"],
        "details": memory["details"],
        "tags": memory["tags"],  # Characters + descriptive tags
        "quoted_dialogue": memory.get("quoted_dialogue", []),
        "relationships": {},  # Empty - tracked separately
        "location": extracted_location or "Unknown",
        "chapter": extracted_chapter or "",
        "timestamp": self.get_timestamp(),  # ISO format
        "message_index": message_number
    }

    # Save to state/entities/{character}/memory.json
    # This appends to existing array or creates new file
    self.append_to_entity_json(character, memory_entry, "memory.json")
```

---

**Timeline Branching Support:**

The existing repository (`entity_repository.py:200-272`) already handles timeline branching:
- Memories saved to: `{character}_memories.json` (main timeline)
- Or: `{character}_memories_{session_id}.json` (branched timeline)
- Uses **Copy-on-Write**: branched timelines inherit parent memories up to branch point
- `session_state_service.get_current_timeline()` provides session_id

---

**⚠️ CRITICAL PATH DISCREPANCY:**

**BaseAgent helpers** save to:
```
rp_dir/state/entities/{character}/memory.json
rp_dir/state/entities/{character}/memory_{session_id}.json
```

**Repository expects** files at:
```
rp_dir/entities/{character_slug}_memories.json
rp_dir/entities/{character_slug}_memories_{session_id}.json
```

**Resolution Required:**
1. **Option A**: Agent should use `FixtureEntityRepository.append_memory_entry()` directly instead of BaseAgent helpers
2. **Option B**: Update BaseAgent helpers to save to repository-expected location
3. **Option C**: Update repository to read from new location

**Recommendation**: Use Option A - call repository directly for proper timeline branching:
```python
# In agent execute():
from src.domain.entities import FixtureEntityRepository

repository = FixtureEntityRepository(rp_dir=self.rp_dir)
repository.append_memory_entry(character, memory_entry)
```

This ensures:
- Timeline branching works correctly
- Copy-on-Write inheritance works
- Files saved to correct location
- Session state service integration works

---

**File Storage (Actual):**
- Main timeline: `rp_dir/entities/{character_slug}_memories.json`
- Branched timeline: `rp_dir/entities/{character_slug}_memories_{session_id}.json`
- Format: JSON with `{"character": "...", "entries": [...]}`
- Repository handles array appending and timeline logic

---

**Return Value:**
```python
return f"Created {len(memories)} memories for {num_characters} characters"
```

---

**Implementation Checklist:**
- [ ] Read chapter/location/characters from session state (populated by ResponseAnalyzerAgent)
- [ ] Fallback to LLM extraction if session state is empty (first run)
- [ ] Query LLM with prompt (temperature=0.0 for consistency)
- [ ] Parse JSON response
- [ ] Generate UUID for each memory entry
- [ ] Populate all required fields (relationships = empty dict)
- [ ] Save using `FixtureEntityRepository.append_memory_entry()` (not BaseAgent helpers!)
- [ ] Pass `session_state_service` to repository for timeline branching
- [ ] Handle errors gracefully (log and continue)
- [ ] Return summary of memories created

---

**Resolved via ResponseAnalyzerAgent Implementation:**
1. ✅ Standardized emotion/action tag taxonomy defined in MemoryCreationAgent
2. ✅ Location comes from session state `scene_context.location`
3. ✅ Chapter comes from session state `scene_context.chapter`
4. ✅ Characters come from session state `scene_context.characters_in_scene`

**Estimated:** 4-6 hours

---

##### 2.2 RelationshipAnalysisAgent

**File:** `src/automation/agents/background/relationship_analysis_agent.py`

**Purpose:** Detect relationship changes between characters.

**Prompt:**
```
Analyze this response for relationship changes between characters.

RESPONSE: {response_text}
CHARACTERS: {characters_in_scene}

Identify:
- New relationships formed
- Existing relationships that changed
- Relationship type (friendship, romance, rivalry, mentor, family, etc.)
- Direction of feelings (mutual, one-sided)
- Value -100 to 100

Respond with JSON:
{
  "relationships": [
    {
      "pair": ["Alice", "Bob"],
      "type": "romantic_interest",
      "direction": "Alice→Bob",
      "value": 25,
      "change": "confessed_feelings",
      "mutual": false
    }
  ]
}
```

**Estimated:** 4-6 hours

---

##### 2.3 PlotThreadDetectionAgent

**File:** `src/automation/agents/background/plot_thread_detection_agent.py`

**Purpose:** Identify and track narrative threads/storylines.

**Prompt:**
```
Analyze this response for plot threads and narrative developments.

RESPONSE: {response_text}
EXISTING THREADS: {existing_threads}

Identify:
- New plot threads starting
- Existing threads progressing
- Threads that resolved
- Thread priority/importance (1-10)

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
      "progress": "Clues revealed about Alice's past"
    }
  ]
}
```

**Estimated:** 6-8 hours (more complex)

---

##### 2.4 KnowledgeExtractionAgent

**File:** `src/automation/agents/background/knowledge_extraction_agent.py`

**Purpose:** Extract world-building facts and lore.

**Prompt:**
```
Extract world-building facts and lore from this response.

RESPONSE: {response_text}
EXISTING KNOWLEDGE: {existing_knowledge}

Identify NEW facts about:
- World rules (magic, physics, technology)
- History and past events
- Culture and society
- Geography
- Organizations and factions

Only extract facts that are:
- Explicitly stated or strongly implied
- New information (not duplicating existing)
- Important for narrative consistency

Respond with JSON:
{
  "knowledge": [
    {
      "category": "magic_system",
      "fact": "Magic requires verbal incantations",
      "details": "Alice explained that all spells need spoken words",
      "confidence": 0.9,
      "tags": ["magic", "established_canon"]
    }
  ]
}
```

**Estimated:** 4-6 hours

---

##### 2.5 ContradictionDetectionAgent

**File:** `src/automation/agents/background/contradiction_detection_agent.py`

**Purpose:** Detect narrative inconsistencies.

**Prompt:**
```
Check this response for contradictions with established facts.

RESPONSE: {response_text}
ESTABLISHED KNOWLEDGE: {existing_knowledge}
RECENT MEMORIES: {recent_memories}

Identify contradictions:
- Factual inconsistencies (world rules violated)
- Character inconsistencies (acting out of character)
- Timeline issues
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
      "statement_a": "All magic requires spoken words",
      "statement_b": "Alice cast spell silently",
      "severity": "moderate",
      "source_a": "knowledge_003"
    }
  ]
}
```

**Estimated:** 6-8 hours (complex analysis)

---

##### 2.6 ResponseAnalyzerAgent ✅ IMPLEMENTED

**File:** `src/automation/agents/implementations/response_analyzer_agent.py`

**Status:** COMPLETE - Implemented 2025-10-30

**Purpose:** Classify scene type, tone, pacing, and extract scene metadata.

**What It Does:**
- Analyzes Claude's response for scene classification (type, pacing, tension)
- Extracts characters actively in the scene
- Detects current location and chapter
- Tracks time progression
- Provides narrative variety alerts
- **Updates session state** with scene context for other agents to use

**Session State Integration:**
- Writes to timeline-specific file: `state/scene_context_{session_id}.json`
- Other agents read from session state via `session_state_service.get_scene_context()`
- Follows same pointer pattern as arcs/relationships/plot_threads

**LLM Prompt (Implemented):**
```
Analyze this roleplay response and extract scene metadata and narrative characteristics.

USER MESSAGE: {user_message}
CLAUDE'S RESPONSE: {claude_response}

PREVIOUS SCENE CONTEXT:
- Chapter: {previous_chapter}
- Location: {previous_location}
- Recent Scene Types: {previous_scenes}

Extract the following information:

1. Scene Classification: type, pacing, tension (1-10), word count
2. Characters: in_scene, mentioned, new_characters
3. Location & Chapter: current location, location_changed, chapter
4. Time Progression: elapsed, timestamp, day_chapter
5. Narrative Alerts: variety, tension_flat, recommendations

Respond with JSON ONLY.
```

**Output Format (scene_context_{session_id}.json):**
```json
{
  "chapter": "Chapter 3: Secrets Revealed",
  "location": "The Rusty Anchor Tavern",
  "characters_in_scene": ["Alice", "Bob"],
  "last_updated_message": 42,
  "scene_analysis": {
    "type": "dialogue",
    "pace": "medium",
    "tension": 6,
    "word_count": 450
  },
  "time_context": {
    "elapsed": "30 minutes",
    "timestamp": "Tuesday 3:00 PM",
    "day_chapter": "Day 3"
  },
  "previous_location": "City Streets",
  "alerts": {
    "variety": "good",
    "tension_flat": false
  }
}
```

**Implementation Time:** ~7 hours

---

#### Immediate Agents (Run BEFORE Claude Responds)

##### 2.7 QuickEntityAnalysisAgent

**File:** `src/automation/agents/immediate/quick_entity_analysis_agent.py`

**Purpose:** Identify entities mentioned in user message.

**Note:** Might not need LLM - `entity_service.detect_mentions()` already exists!

**Decision:** Start with existing keyword-based detection, add LLM only if needed.

**Estimated:** 2-3 hours (or skip entirely)

---

##### 2.8 FactExtractionAgent

**File:** `src/automation/agents/immediate/fact_extraction_agent.py`

**Purpose:** Pull relevant facts about entities for Claude's context.

**Prompt:**
```
Extract the most relevant facts to include in Claude's context.

USER MESSAGE: {user_message}
ENTITIES IN SCENE: {entities_in_scene}
ENTITY PROFILES: {entity_data}
KNOWLEDGE BASE: {knowledge_base}

Select 5-10 most relevant facts focusing on:
- Information directly relevant to user's message
- Character traits that inform how they'd respond
- World rules that apply to current situation
- Recent relationship developments

Respond with JSON:
{
  "relevant_facts": [
    {
      "entity": "Alice",
      "fact_type": "personality",
      "fact": "Alice is naturally curious",
      "relevance": "User asked about investigation"
    }
  ]
}
```

**Output:** List of facts formatted for prompt injection.

**Estimated:** 4-5 hours

---

##### 2.9 MemoryExtractionAgent

**File:** `src/automation/agents/immediate/memory_extraction_agent.py`

**Purpose:** Find relevant memories for current context.

**Prompt:**
```
Find the most relevant memories for this conversation context.

USER MESSAGE: {user_message}
CHARACTERS: {entities_in_scene}
AVAILABLE MEMORIES (last 50 per character): {all_memories}

Select 5-10 memories that:
- Are directly relevant to what user is asking/doing
- Provide important context Claude should remember
- Inform how characters would respond
- Avoid redundancy

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
      "relevance": "User asking about relationship status"
    }
  ]
}
```

**Output:** List of memories formatted for prompt injection.

**Estimated:** 4-5 hours

---

##### 2.10 PlotThreadExtractionAgent

**File:** `src/automation/agents/immediate/plot_thread_extraction_agent.py`

**Purpose:** Identify active plot threads relevant to current message.

**Prompt:**
```
Identify which active plot threads are relevant to this message.

USER MESSAGE: {user_message}
CHARACTERS: {entities_in_scene}
ACTIVE PLOT THREADS: {plot_threads}

Select threads that:
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

**Output:** List of threads formatted for prompt injection.

**Estimated:** 4-5 hours

---

### 3. Wire Bridge Through Pipeline (5 FILE MODIFICATIONS)

#### 3.1 Update factory.py

**File:** `src/automation/factory.py`

**Change:** Add `bridge` parameter and pass to strategies

```python
# Line 118 - Update function signature
def create_automation_service(
    rp_dir: Path,
    *,
    bridge: "BridgeService" = None,  # ← ADD THIS
    config_service: ConfigService | None = None,
    logger: LoggingService | None = None,
    **overrides: Any,
) -> AutomationService:
    """Create automation service with bridge access for agents.

    Args:
        rp_dir: RP directory path
        bridge: Bridge service instance (provides LLM access to agents)  # ← ADD THIS
        config_service: Optional config service
        logger: Optional logger
        **overrides: Optional dependency overrides
    """

    # ... existing code ...

    # Line 251 - Pass bridge to agent registry
    if "agent_runner" in overrides:
        agent_runner = overrides["agent_runner"]
    else:
        agent_registry = AgentRegistry(config=config_service, logger=logger)
        strategies = agent_registry.create_strategies(bridge=bridge)  # ← ADD bridge=bridge
        agent_runner = AgentRunner(strategies=strategies, logger=logger)
```

---

#### 3.2 Update registry.py

**File:** `src/automation/agents/registry.py`

**Change:** Accept and pass bridge to strategies

```python
# Line 38 - Update signature
def create_strategies(self, bridge=None) -> list[AgentStrategy]:  # ← ADD bridge=None
    """Create and order agent strategies based on configuration.

    Args:
        bridge: Bridge service instance (provides LLM access to agents)  # ← ADD THIS

    Returns:
        Ordered list of agent strategies to execute
    """
    self._logger.debug("agent_registry.create_strategies.start")

    strategies: list[AgentStrategy] = []

    # Load agent configuration
    agents_config = self._config.get("agents", {})
    fallback_config = self._config.get("fallback", {})

    use_agents = self._should_use_agents(agents_config, fallback_config)

    if use_agents:
        # Line 57 - Pass bridge to immediate strategy
        immediate_strategy = self._create_immediate_strategy(agents_config, bridge)  # ← ADD bridge
        if immediate_strategy:
            strategies.append(immediate_strategy)

        # Line 63 - Pass bridge to background strategy
        background_strategy = self._create_background_strategy(agents_config, bridge)  # ← ADD bridge
        if background_strategy:
            strategies.append(background_strategy)

    # ... rest unchanged ...

# Line 115 - Update method signature
def _create_immediate_strategy(
    self, agents_config: dict[str, Any], bridge=None  # ← ADD bridge=None
) -> ImmediateAgentStrategy | None:
    """Create immediate agent strategy if configured.

    Args:
        agents_config: Agent configuration section
        bridge: Bridge service instance  # ← ADD THIS
    """
    # ... existing code ...

    return ImmediateAgentStrategy(
        logger=self._logger,
        enabled_agents=enabled_agents,
        max_workers=4,
        bridge=bridge,  # ← ADD THIS
    )

# Line 146 - Update method signature
def _create_background_strategy(
    self, agents_config: dict[str, Any], bridge=None  # ← ADD bridge=None
) -> BackgroundAgentStrategy | None:
    """Create background agent strategy if configured.

    Args:
        agents_config: Agent configuration section
        bridge: Bridge service instance  # ← ADD THIS
    """
    # ... existing code ...

    return BackgroundAgentStrategy(
        logger=self._logger,
        enabled_agents=enabled_agents,
        max_workers=4,
        bridge=bridge,  # ← ADD THIS
    )
```

---

#### 3.3 Update immediate_agent_strategy.py

**File:** `src/automation/agents/immediate_agent_strategy.py`

**Changes:**

```python
# Line 46 - Add bridge parameter to __init__
def __init__(
    self,
    *,
    logger: LoggingService,
    max_workers: int = 4,
    enabled_agents: dict[str, dict[str, any]] | None = None,
    default_timeout: int = 5,
    bridge: "BridgeService" = None,  # ← ADD THIS
) -> None:
    """Initialize immediate agent strategy.

    Args:
        logger: Logging service
        max_workers: Maximum concurrent agents
        enabled_agents: Dict mapping agent IDs to config
        default_timeout: Default timeout in seconds
        bridge: Bridge service instance (provides LLM access)  # ← ADD THIS
    """
    self._logger = logger
    self._max_workers = max_workers
    self._enabled_agents = enabled_agents or {}
    self._default_timeout = default_timeout
    self.bridge = bridge  # ← ADD THIS

# Line 299 - Pass bridge when creating agents
def _execute_single_agent(
    self, agent_id: str, agent_class: type, agent_context: AgentContext, timeout: int, rp_dir
) -> dict[str, any]:
    """Execute a single immediate agent."""
    # ... existing code ...

    # CHANGE THIS LINE:
    # OLD: agent = agent_class(rp_dir=rp_dir, log_file=None)
    # NEW:
    agent = agent_class(
        rp_dir=rp_dir,
        log_file=None,
        bridge=self.bridge  # ← ADD THIS
    )

    # ... rest unchanged ...
```

---

#### 3.4 Update background_agent_strategy.py

**File:** `src/automation/agents/background_agent_strategy.py`

**Changes:**

```python
# Line 48 - Add bridge parameter to __init__
def __init__(
    self,
    *,
    logger: LoggingService,
    max_workers: int = 4,
    enabled_agents: dict[str, bool] | None = None,
    bridge: "BridgeService" = None,  # ← ADD THIS
) -> None:
    """Initialize background agent strategy.

    Args:
        logger: Logging service
        max_workers: Maximum concurrent agents
        enabled_agents: Dict mapping agent IDs to enabled status
        bridge: Bridge service instance (provides LLM access)  # ← ADD THIS
    """
    self._logger = logger
    self._max_workers = max_workers
    self._enabled_agents = enabled_agents or {}
    self.bridge = bridge  # ← ADD THIS

# Line 266 - Pass bridge when creating agents
def _execute_single_agent(
    self, agent_id: str, agent_class: type, agent_context: AgentContext, rp_dir
) -> dict[str, any]:
    """Execute a single background agent."""
    # ... existing code ...

    # CHANGE THIS LINE:
    # OLD: agent = agent_class(rp_dir=rp_dir, log_file=None)
    # NEW:
    agent = agent_class(
        rp_dir=rp_dir,
        log_file=None,
        bridge=self.bridge  # ← ADD THIS
    )

    # ... rest unchanged ...
```

---

#### 3.5 Update bridge_service.py

**File:** `src/presentation/bridge/bridge_service.py`

**Change:** Pass `self` to automation service factory

```python
# Line 119
def _initialize_services(self) -> None:
    """Initialize refactored automation services."""
    print("[INIT] Initializing services...")

    # Automation service (using factory) - PASS BRIDGE
    self.automation_service = create_automation_service(
        self.rp_dir,
        bridge=self  # ← ADD THIS - Pass bridge reference for agent LLM access
    )
    print("[OK] Automation service initialized")

    # ... rest unchanged ...
```

---

## Implementation Phases

### Phase 1: Foundation + First Agent (8-12 hours)

**Goal:** Get ONE agent working end-to-end with secondary LLM

**Tasks:**
1. Create `base_agent.py` with LLM router access (1 hour)
2. Wire bridge through pipeline (2 hours):
   - Update `factory.py`
   - Update `registry.py`
   - Update strategy files
   - Update `bridge_service.py`
3. Implement `MemoryCreationAgent` (4-6 hours):
   - Write agent class
   - Design prompt template
   - Implement JSON parsing
   - Test with secondary LLM
4. Test end-to-end (1-2 hours):
   - Verify secondary LLM is called
   - Verify temperature is applied
   - Verify fallback to primary works
   - Verify results are saved

**Deliverable:** ONE working agent that uses secondary LLM via router

**Success Criteria:**
- ✅ MemoryCreationAgent executes successfully
- ✅ Uses secondary LLM if toggle ON
- ✅ Falls back to primary if toggle OFF
- ✅ Respects temperature configuration
- ✅ Parses and saves results

---

### Phase 2: Core Agents (16-20 hours)

**Goal:** Implement 4 most valuable agents

**Tasks:**
5. Implement `RelationshipAnalysisAgent` (4-6 hours)
6. Implement `PlotThreadDetectionAgent` (6-8 hours)
7. Implement `MemoryExtractionAgent` (4-5 hours)
8. Implement `FactExtractionAgent` (4-5 hours)
9. Test all 5 agents together (2 hours)

**Deliverable:** 5 agents providing useful context/analysis

**Success Criteria:**
- ✅ All 5 agents execute without errors
- ✅ Background agents save results correctly
- ✅ Immediate agents format output for prompt injection
- ✅ Agents handle edge cases gracefully
- ✅ LLM costs are reasonable (<$0.01 per message)

---

### Phase 3: Remaining Agents (12-16 hours)

**Goal:** Complete the 10-agent system

**Tasks:**
10. Implement `KnowledgeExtractionAgent` (4-6 hours)
11. Implement `ContradictionDetectionAgent` (6-8 hours)
12. Implement `ResponseAnalyzerAgent` (3-4 hours)
13. Implement `QuickEntityAnalysisAgent` (2-3 hours) - or skip if not needed
14. Implement `PlotThreadExtractionAgent` (4-5 hours)
15. Full integration testing (2-3 hours)
16. Performance tuning and optimization (2-3 hours)

**Deliverable:** Complete 10-agent system

**Success Criteria:**
- ✅ All 10 agents working
- ✅ Agents run concurrently without conflicts
- ✅ Results formatted correctly
- ✅ Error handling robust
- ✅ Documentation complete

---

## File Structure

### New Files to Create (11)

```
src/automation/agents/
  base_agent.py                                    # NEW - Base class with LLM access

src/automation/agents/background/
  __init__.py                                      # NEW
  memory_creation_agent.py                         # NEW
  relationship_analysis_agent.py                   # NEW
  plot_thread_detection_agent.py                   # NEW
  knowledge_extraction_agent.py                    # NEW
  contradiction_detection_agent.py                 # NEW
  response_analyzer_agent.py                       # NEW

src/automation/agents/immediate/
  __init__.py                                      # NEW
  quick_entity_analysis_agent.py                   # NEW (optional)
  fact_extraction_agent.py                         # NEW
  memory_extraction_agent.py                       # NEW
  plot_thread_extraction_agent.py                  # NEW
```

### Files to Modify (5)

```
src/automation/factory.py                         # Add bridge parameter
src/automation/agents/registry.py                 # Pass bridge to strategies
src/automation/agents/immediate_agent_strategy.py # Pass bridge to agents
src/automation/agents/background_agent_strategy.py # Pass bridge to agents
src/presentation/bridge/bridge_service.py         # Pass self to factory
```

---

## Testing Strategy

### Unit Tests (Per Agent)

**Pattern:**
```python
# tests/automation/agents/background/test_memory_creation_agent.py

def test_memory_creation_with_mock_llm(tmp_path):
    """Test agent with mock LLM response."""

    # Setup mock LLM
    mock_bridge = Mock()
    mock_bridge.primary_client.send_message.return_value = Mock(
        content='{"memories": [{"character": "Alice", "summary": "Test"}]}'
    )

    # Create agent
    agent = MemoryCreationAgent(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        bridge=mock_bridge
    )

    # Execute
    result = agent.execute(
        response_text="Alice walked into the room...",
        user_message="What does Alice do?",
        characters_in_scene=["Alice"],
        location="Living Room",
        chapter="Chapter 1",
        message_index=5,
        session_id="test"
    )

    # Assert
    result_data = json.loads(result)
    assert result_data["success"] is True
    assert len(result_data["data"]["memories"]) == 1
```

**Coverage per agent:**
- ✅ Successful execution with valid LLM response
- ✅ Handling malformed JSON
- ✅ Handling missing bridge
- ✅ Parsing edge cases (empty arrays, null fields)
- ✅ Error handling

---

### Integration Tests

```python
def test_immediate_agent_flow(test_rp_dir):
    """Test immediate agents enhance prompt correctly."""

    # Create bridge with secondary LLM
    bridge = create_test_bridge(test_rp_dir)

    # Create automation service with bridge
    automation = create_automation_service(test_rp_dir, bridge=bridge)

    # Run automation pipeline
    context = AutomationContext(
        message="Alice, tell me about your past",
        rp_dir=test_rp_dir
    )
    result = automation.run(context)

    # Verify immediate agents ran and enhanced prompt
    assert result.success
    assert result.enhanced_prompt is not None
    assert "Alice" in result.enhanced_prompt
    # Check that agent context was injected
    assert "<!-- IMMEDIATE AGENT CONTEXT -->" in result.enhanced_prompt

def test_background_agent_flow(test_rp_dir):
    """Test background agents analyze response correctly."""

    # ... similar pattern for background agents
```

---

## Cost Analysis

### Per-Agent Cost Estimates (using DeepSeek via OpenRouter)

**Pricing:** ~$0.0001 per 1K tokens

**Background Agents:**
- MemoryCreationAgent: ~500 input + 300 output = 800 tokens = $0.00008
- RelationshipAnalysisAgent: ~400 input + 200 output = 600 tokens = $0.00006
- PlotThreadDetectionAgent: ~600 input + 400 output = 1000 tokens = $0.0001
- KnowledgeExtractionAgent: ~500 input + 300 output = 800 tokens = $0.00008
- ContradictionDetectionAgent: ~700 input + 300 output = 1000 tokens = $0.0001
- ResponseAnalyzerAgent: ~300 input + 200 output = 500 tokens = $0.00005

**Total per message (all 6 background agents):** ~$0.00047 ≈ **$0.0005 per response**

**Immediate Agents:**
- FactExtractionAgent: ~600 input + 200 output = 800 tokens = $0.00008
- MemoryExtractionAgent: ~700 input + 300 output = 1000 tokens = $0.0001
- PlotThreadExtractionAgent: ~500 input + 200 output = 700 tokens = $0.00007

**Total per message (all 3 immediate agents):** ~$0.00025 ≈ **$0.00025 per message**

**Grand Total:** **~$0.00075 per message** (less than 0.1 cent!)

**Cost at scale:**
- 100 messages: $0.075 (7.5 cents)
- 1000 messages: $0.75 (75 cents)
- 10,000 messages: $7.50

**Extremely affordable with DeepSeek!**

---

## Decision Points

### 1. Agent Grouping

**Decision:** Individual agents (current plan)

**Rationale:**
- Modular and testable
- Can enable/disable individually
- Cost is negligible with DeepSeek ($0.00075/message)
- Easier to debug and maintain

---

### 2. When to Run Agents

**Decision:** Every response (for Phase 1-2)

**Rationale:**
- Complete analysis
- Cost is negligible
- Can optimize later if needed

**Future optimization:**
- Add config option to run agents selectively
- Skip agents based on response type/length

---

### 3. LLM Provider for Agents

**Decision:** Use secondary provider (user-configurable)

**Rationale:**
- Respects user's choice
- Can be same as primary (single-key mode)
- Can be different (dual-key mode for cost optimization)
- Automatically falls back to primary if secondary not configured

**Recommended for testing:** DeepSeek via OpenRouter (cheapest + good quality)

---

## Next Steps

### Immediate Actions (Phase 1):

1. **Create base_agent.py**
   - Copy template from section 1 above
   - Test imports work

2. **Wire bridge through pipeline**
   - Update 5 files as documented
   - Test bridge reference propagates correctly

3. **Implement MemoryCreationAgent**
   - Use pattern from section 2.1
   - Test with mock LLM first
   - Test with real secondary LLM

4. **Verify end-to-end**
   - Run full conversation flow
   - Check secondary LLM is called
   - Verify temperature applied
   - Test fallback to primary

### Success Criteria for Phase 1:

- [ ] base_agent.py created and imports successfully
- [ ] Bridge wired through all 5 files
- [ ] MemoryCreationAgent implemented
- [ ] Agent executes with secondary LLM
- [ ] Temperature configuration respected
- [ ] Fallback to primary works when toggle OFF
- [ ] Results saved correctly

---

## Reference: Key Code Locations

**LLM Router:**
- Implementation: `src/infrastructure/llm/llm_router.py`
- Export: `src/infrastructure/llm/__init__.py`

**Bridge:**
- Service: `src/presentation/bridge/bridge_service.py`
- LLM clients: `bridge.primary_client`, `bridge.secondary_client`
- Routing config: `bridge.llm_routing`

**Agent Pipeline:**
- Factory: `src/automation/factory.py`
- Registry: `src/automation/agents/registry.py`
- Strategies: `src/automation/agents/immediate_agent_strategy.py`, `background_agent_strategy.py`
- Executor: `src/automation/services/agent_executor.py`

**Legacy Base Agent (for reference):**
- Old implementation: `src/automation/agents/base_agent.py` (uses DeepSeek directly)
- NOTE: We're creating a NEW base agent with router access

---

## Appendix: Agent Import Locations

**Current strategy imports (need to be updated when agents are created):**

```python
# immediate_agent_strategy.py line 19
try:
    from src.automation.agents import (
        FactExtractionAgent,
        MemoryExtractionAgent,
        PlotThreadExtractionAgent,
        QuickEntityAnalysisAgent,
    )
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

# background_agent_strategy.py line 19
try:
    from src.automation.agents import (
        ContradictionDetectionAgent,
        KnowledgeExtractionAgent,
        MemoryCreationAgent,
        PlotThreadDetectionAgent,
        RelationshipAnalysisAgent,
        ResponseAnalyzerAgent,
    )
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
```

**These imports will work once we create the agent files!**

---

## Total Effort Summary

| Phase | Tasks | Est. Hours | Deliverable |
|-------|-------|------------|-------------|
| **Phase 1** | Foundation + 1 agent | 8-12 | Working MemoryCreationAgent |
| **Phase 2** | Core 4 agents | 16-20 | 5 agents total |
| **Phase 3** | Remaining 5 agents | 12-16 | Complete system |
| **TOTAL** | All components | **36-48** | 10-agent system |

---

**Document Status:** Complete and ready for implementation
**Last Updated:** 2025-10-28
**Next Action:** Begin Phase 1 - Create base_agent.py
