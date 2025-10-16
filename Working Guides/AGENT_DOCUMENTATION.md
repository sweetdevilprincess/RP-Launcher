# RP Claude Code - Agent Documentation

## Quick Reference
This document outlines all agents in the RP Claude Code system, what they do, where they pull data from, and where they send results.

**Location**: `src/automation/agents/`
- **Background Agents**: `background/` (runs after response generation)
- **Immediate Agents**: `immediate/` (runs before response generation)

---

## BACKGROUND AGENTS
*Run after Response N while user types Message N+1 (hidden processing, ~2-15 seconds each)*

### 1. Response Analyzer
**Location**: `src/automation/agents/background/response_analyzer.py`

**What It Does**:
Analyzes Claude's response for scene classification, pacing analysis, and character tracking. Extracts structured information about story progression.

**Pulls From**:
- Claude's response text
- Response number
- Previous scene types (from state)
- Current RP directory state

**Sends To**:
- Scene type (dialogue, action, introspection, transition, world_building)
- Pacing level (fast, medium, slow)
- Tension level (1-10)
- Character tracking data
- Location changes
- Timeline data
- `state/agent_analysis.json` (cache)

---

### 2. Memory Creation Agent
**Location**: `src/automation/agents/background/memory_creation.py`

**What It Does**:
Extracts memorable moments from responses to build persistent character memory banks. Identifies significant events, revelations, and emotional beats.

**Pulls From**:
- Claude's response text
- Response number
- Chapter identifier (optional)

**Sends To**:
- Memory records with: title, characters involved, location, type (revelation, conflict, first_meeting, character_moment, relationship_development, plot_event)
- Significance score (1-10), emotional tone, key quotes
- Output directory: `memories/{character_name}/`
- `state/agent_analysis.json` (cache)

---

### 3. Relationship Analysis Agent
**Location**: `src/automation/agents/background/relationship_analysis.py`

**What It Does**:
Tracks character interactions and relationship score changes. Monitors relationship tier transitions (enemy → stranger → friend, etc.).

**Pulls From**:
- Claude's response text
- Response number
- Characters in scene
- `relationships/{character_name}_preferences.json`
- `state/relationships.json` (current state)

**Sends To**:
- Relationship changes with: character pair, tier classification
- Score delta, trigger event, tier transitions
- Updates: `state/relationships.json`
- `state/agent_analysis.json` (cache)

---

### 4. Plot Thread Detection Agent
**Location**: `src/automation/agents/background/plot_thread_detection.py`

**What It Does**:
Detects new plot threads, tracks mentions of existing threads, and identifies resolved threads. Manages plot lifecycle and consequence countdowns.

**Pulls From**:
- Claude's response text
- Response number
- Chapter identifier
- `state/plot_threads_master.md` (existing threads)

**Sends To**:
- New threads: ID, title, priority (high/medium/low), time sensitivity, characters
- Mentioned threads: existing thread updates
- Resolved threads: closure information
- Updates: `state/plot_threads_master.md`
- `state/agent_analysis.json` (cache)

---

### 5. Knowledge Extraction Agent
**Location**: `src/automation/agents/background/knowledge_extraction.py`

**What It Does**:
Extracts world-building facts from responses including setting details, geography, organizations, and cultural information.

**Pulls From**:
- Claude's response text
- Response number
- Chapter identifier
- `state/knowledge_base.md` (existing facts)

**Sends To**:
- Facts with: category (setting, locations, organizations, cultural, geography, items, history)
- Subject, fact statement, confidence level (high/medium/low)
- Updates: `state/knowledge_base.md`
- `state/agent_analysis.json` (cache)

---

### 6. Contradiction Detection Agent (Optional)
**Location**: `src/automation/agents/background/contradiction_detection.py`

**What It Does**:
Quality assurance agent that fact-checks new responses against established canon. Detects contradictions.

**Pulls From**:
- Claude's response text
- Response number
- `state/knowledge_base.md` (established facts)
- `state/story_facts.json`
- `entities/*.md` (first 10 files)

**Sends To**:
- Contradictions with: category, subject, established fact, new claim, severity (minor/moderate/major)
- Verification count
- `state/agent_analysis.json` (cache)

---

## IMMEDIATE AGENTS
*Run before Response N+1 to gather context (parallel execution, ~3 second user latency)*

### 7. Quick Entity Analysis Agent
**Location**: `src/automation/agents/immediate/quick_entity_analysis.py`

**What It Does**:
Quickly identifies entities mentioned in user's message. Classifies them into tiers for optimized context loading.

**Pulls From**:
- User's message
- Message number
- Available entity cards: `entities/*.md`
- Available locations: `locations/*.md`

**Sends To**:
- Tier 1 entities (scene participants - full load)
- Tier 2 entities (mentioned but absent - facts only)
- Tier 3 count (entities to skip)
- Relevant locations
- New entities requiring cards
- `state/agent_analysis.json` (cache)

---

### 8. Fact Extraction Agent
**Location**: `src/automation/agents/immediate/fact_extraction.py`

**What It Does**:
Extracts 5 key facts from Tier 2 entity cards (mentioned but absent). Optimizes token usage by ~97%.

**Pulls From**:
- User's message (for context)
- Tier 2 entity list
- Full entity cards: `entities/{name}.md`

**Sends To**:
- For each entity: 5 most important facts (one sentence each)
- Structured format: `{"entities": {"EntityName": {"facts": [...]}}}`
- `state/agent_analysis.json` (cache)

---

### 9. Memory Extraction Agent
**Location**: `src/automation/agents/immediate/memory_extraction.py`

**What It Does**:
Extracts 2-5 most relevant memories per scene participant from their memory banks. Optimizes token usage by ~96%.

**Pulls From**:
- User's message (for relevance context)
- Scene participants list
- Memory files: `memories/{character}/*.md`
- Total memory availability per character

**Sends To**:
- For each character: 2-5 relevant memories with ID, title, when/where, significance
- Prioritized by: JUST HAPPENED > FOUNDATIONAL > RELEVANT TO TOPIC
- `state/agent_analysis.json` (cache)

---

### 10. Plot Thread Extraction Agent
**Location**: `src/automation/agents/immediate/plot_thread_extraction.py`

**What It Does**:
Extracts 2-5 most relevant plot threads from master file for current conversation. Optimizes token usage by ~85%.

**Pulls From**:
- User's message (for relevance context)
- Message number
- `state/plot_threads_master.md` (master plot threads)

**Sends To**:
- Total active threads count
- Loaded threads (2-5 most relevant): ID, title, priority, last mentioned, countdown
- Monitored threads (tracked but not loaded)
- Prioritized by: CRITICAL > HIGH > MEDIUM > LOW
- `state/agent_analysis.json` (cache)

---

## AGENT SYSTEM BEHAVIOR & INTEGRATION

### Result Caching

All agent results are cached to `state/agent_analysis.json` during each cycle. This means:
- Immediate agents cache their results after execution
- Background agents cache their results after execution
- **Same cycle**: Agents can read results from other agents if needed
- **Next cycle**: Previous cycle's results available for context
- Cache is overwritten each cycle (not persistent between cycles)

**Implication**: When adding new agents, they can rely on results from parallel agents being available in the cache.

---

### Write Queue Integration

All agents write to files through the **FSWriteQueue** system (debounced 500ms per file):

- Agent writes are **not immediate** - they're queued
- Multiple agents can write to the same file in parallel
- FSWriteQueue batches them into a **single disk write**
- Write happens 500ms after the last write to that file

**Example**:
```
Response 42:
- Memory Creation agent writes: memories/Alice/mem_001.md → queued
- Memory Creation agent writes: memories/Alice/mem_002.md → queued (same file timer resets)
- Relationship Analysis agent writes: state/relationships.json → queued (different file)

After 500ms:
- Only 1 write to memories/Alice/ (contains both memories)
- Only 1 write to state/relationships.json
- Reduces disk I/O by ~50%
```

**Implication**: When developing, understand that file changes from agents won't appear on disk immediately - they're delayed by up to 500ms. For testing, use the write queue's `flush()` method to force immediate writes.

---

### Timeout & Error Handling

**Immediate Agents**:
- **Timeout**: 3-5 seconds (configurable per agent)
- **Failure behavior**: Agent skipped, pipeline continues
- **Partial results**: Used if some agents succeed, others fail
- **Pipeline continues**: Never blocks response generation

**Background Agents**:
- **Timeout**: 15-30 seconds total (all run in parallel)
- **Failure behavior**: Failed agent results not included
- **Fallback system**: Trigger-based fallback available if agents fail
- **Pipeline continues**: Failures don't block next cycle

**Implication**: When adding new agents, assume they might fail and design fallbacks. Timeouts prevent one slow agent from blocking everything.

---

### Agent Priority System

**Background Agents** have explicit priorities:
```
Priority 1: Response Analyzer (scene classification)
Priority 2: Memory Creation (memories)
Priority 3: Relationship Analysis (relationships)
Priority 4: Plot Thread Detection (plot threads)
Priority 5: Knowledge Extraction (facts)
Priority 6: Contradiction Detection (optional quality check)
```

**Purpose**: If system is under resource constraints, higher priority agents run first.

**Immediate Agents**: All run in parallel (no priority ordering), but have timeout limits.

**Implication**: When adding new background agents, assign an appropriate priority number in `automation_config.json`.

---

### Agent Configuration

All agents are configured in `state/automation_config.json`:

```json
{
  "agents": {
    "background": {
      "response_analyzer": {"enabled": true, "priority": 1},
      "memory_creation": {"enabled": true, "priority": 2},
      ...
    },
    "immediate": {
      "quick_entity_analysis": {"enabled": true, "timeout_seconds": 5},
      ...
    }
  }
}
```

**Implication**: New agents must be registered here to be discovered and executed.

---

### Execution Guarantees

1. **Sequential stages**: Immediate → Response → Background (always in order)
2. **Parallel within stage**: All agents in a stage run concurrently
3. **No cross-cycle blocking**: Background agents don't block next message
4. **Atomic response**: Claude's response is atomic - all or nothing
5. **Partial analysis**: Agent failures don't prevent analysis of other aspects

---

## ORCHESTRATION & COORDINATION

### Agent Coordinator
**Location**: `src/automation/agent_coordinator.py`

**What It Does**:
Multi-agent orchestration system that manages concurrent agent execution, collects results, handles timeouts and failures.

**Manages**:
- Parallel agent execution (ThreadPoolExecutor)
- Result aggregation and caching
- Performance metrics tracking
- Cache → prompt format conversion

---

### Agent Factory
**Location**: `src/automation/agents/agent_factory.py`

**What It Does**:
Factory pattern for creating agents. Maintains registry of all 10 agents and handles conditional creation.

**Manages**:
- Agent registry and configurations
- Conditional agent creation (checks if data exists)
- Batch agent creation
- Agent-to-coordinator registration

---

## Data Flow Summary

```
USER MESSAGE
    ↓
[IMMEDIATE AGENTS - Parallel, ~3 seconds]
├→ Quick Entity Analysis
├→ Fact Extraction (if Tier 2 entities exist)
├→ Memory Extraction (for scene participants)
└→ Plot Thread Extraction (relevant threads)
    ↓
CLAUDE RESPONSE GENERATED
    ↓
[BACKGROUND AGENTS - Parallel, hidden, ~15-30 seconds]
├→ Response Analyzer
├→ Memory Creation
├→ Relationship Analysis
├→ Plot Thread Detection
├→ Knowledge Extraction
└→ Contradiction Detection (optional)
    ↓
CACHE to state/agent_analysis.json
    ↓
FILE UPDATES
├→ memories/{character}/*.md (new memories)
├→ state/relationships.json (relationship changes)
├→ state/plot_threads_master.md (new/resolved threads)
├→ state/knowledge_base.md (new facts)
└→ state/story_facts.json (verified facts)
    ↓
NEXT USER MESSAGE → Back to immediate agents
```

---

## File Organization

```
src/automation/agents/
├── __init__.py
├── base_agent.py                 (base class for all agents)
├── agent_factory.py              (creates agents)
├── background/                   (background agents)
│   ├── response_analyzer.py
│   ├── memory_creation.py
│   ├── relationship_analysis.py
│   ├── plot_thread_detection.py
│   ├── knowledge_extraction.py
│   ├── contradiction_detection.py
│   └── __init__.py
└── immediate/                    (immediate agents)
    ├── quick_entity_analysis.py
    ├── fact_extraction.py
    ├── memory_extraction.py
    ├── plot_thread_extraction.py
    └── __init__.py
```

---

## Quick Stats

- **Total Agents**: 10
- **Background Agents**: 6 (post-response processing)
- **Immediate Agents**: 4 (pre-response context gathering)
- **Central Cache**: `state/agent_analysis.json`
- **Execution Model**: Parallel ThreadPoolExecutor
- **User Latency**: ~3 seconds (immediate agents only)
- **Hidden Processing**: ~15-30 seconds (background agents)
