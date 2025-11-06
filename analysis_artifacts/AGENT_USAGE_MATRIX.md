# Agent Usage Matrix - Complete Agent System Analysis

**Purpose:** Document all agents registered in the system, their execution context, and data dependencies
**Analysis Date:** Phase 1.5
**Status:** Based on refactored agent system in `/refactoring/src/automation/agents/`

---

## Agent System Overview

### Strategy Architecture

The agent system uses a **strategy pattern** with 3 possible strategies:

1. **ImmediateAgentStrategy** - Pre-response context gathering (runs BEFORE LLM)
2. **BackgroundAgentStrategy** - Post-response analysis (runs AFTER LLM)
3. **FallbackTriggerStrategy** - Legacy trigger system (fallback if agents disabled)

**Execution Flow:**
```
User sends message
  │
  ├─> ImmediateAgentStrategy.execute()
  │    ├─> Runs immediate agents in parallel (max 4 workers)
  │    ├─> Timeout: 3-5 seconds per agent
  │    └─> Results injected into prompt
  │
  ├─> Enhanced prompt sent to LLM (Claude/etc.)
  │
  └─> LLM response received
       │
       └─> BackgroundAgentStrategy.execute_post_response()
            ├─> Runs background agents in parallel (max 4 workers)
            ├─> No strict timeout (can take longer)
            └─> Results written to state files
```

---

## Registered Agents (10 Total)

### Immediate Agents (3)

Run BEFORE LLM call to gather context for prompt injection.

| Agent ID | Class | File | Purpose | Timeout | Status |
|----------|-------|------|---------|---------|--------|
| `fact_extraction` | `FactExtractionAgent` | `immediate/fact_extraction_agent.py` | Extract relevant facts about entities mentioned in message | 3-5s | ✓ Refactored |
| `memory_extraction` | `MemoryExtractionAgent` | `immediate/memory_extraction_agent.py` | Find relevant character memories based on message | 3-5s | ✓ Refactored |
| `plot_thread_extraction` | `PlotThreadExtractionAgent` | `immediate/plot_thread_extraction_agent.py` | Identify active plot threads relevant to message | 3-5s | ✓ Refactored |

### Background Agents (7)

Run AFTER LLM response to analyze and extract information.

| Agent ID | Class | File | Purpose | Status |
|----------|-------|------|---------|--------|
| `response_analyzer` | `ResponseAnalyzerAgent` | `implementations/response_analyzer_agent.py` | Scene classification and pacing analysis | ✓ Refactored |
| `time_tracking` | `TimeTrackingAgent` | `implementations/time_tracking_agent.py` | Track narrative time progression | ✓ Refactored |
| `memory_creation` | `MemoryCreationAgent` | `implementations/memory_creation_agent.py` | Extract memorable moments from response | ✓ Refactored |
| `plot_thread_detection` | `PlotThreadDetectionAgent` | `implementations/plot_thread_detection_agent.py` | Detect plot changes and developments | ✓ Refactored |
| `relationship_analysis` | `RelationshipAnalysisAgent` | `implementations/relationship_analysis_agent.py` | Analyze character dynamics and relationships | ✓ Refactored |
| `knowledge_extraction` | `KnowledgeExtractionAgent` | `implementations/knowledge_extraction_agent.py` | Extract world-building facts and lore | ✓ Refactored |
| `contradiction_synthesis` | `ContradictionSynthesisAgent` | `implementations/contradiction_synthesis_agent.py` | Detect inconsistencies and synthesize explanations | ✓ Refactored |

---

## Agent Instantiation Flow

### Factory Creation Path

```
BridgeService._initialize_services()
  │
  └─> create_automation_service(rp_dir, bridge=self)
       [File: src/automation/factory.py]
       │
       ├─> Create dependencies (config, paths, file manager, etc.)
       │
       ├─> AgentRegistry(config, logger, bridge)
       │    [File: src/automation/agents/registry.py]
       │
       ├─> agent_registry.create_strategies(rp_dir=rp_dir)
       │    │
       │    ├─> _should_use_agents(agents_config, fallback_config)
       │    │    └─> Checks if any immediate/background agents enabled
       │    │
       │    ├─> IF use_agents:
       │    │    │
       │    │    ├─> _create_immediate_strategy(agents_config, rp_dir)
       │    │    │    │
       │    │    │    └─> ImmediateAgentStrategy(
       │    │    │             logger,
       │    │    │             enabled_agents={...},
       │    │    │             max_workers=4,
       │    │    │             rp_dir,
       │    │    │             bridge
       │    │    │        )
       │    │    │
       │    │    └─> _create_background_strategy(agents_config, rp_dir)
       │    │         │
       │    │         └─> BackgroundAgentStrategy(
       │    │                  logger,
       │    │                  enabled_agents={...},
       │    │                  max_workers=4,
       │    │                  rp_dir,
       │    │                  bridge
       │    │             )
       │    │
       │    └─> ELSE (agents disabled):
       │         └─> _create_trigger_strategy(fallback_config)
       │              └─> FallbackTriggerStrategy(...)
       │
       ├─> AgentRunner(strategies=[...], logger)
       │    [File: src/automation/services/agent_runner.py]
       │
       └─> AutomationService(..., agent_runner, ...)
            [File: src/automation/services/automation_service.py]
```

---

## Agent Execution Context

### ImmediateAgentStrategy Context

**AgentContext fields provided:**
- `message`: User's message being sent
- `response_number`: Current response count
- `loaded_entities`: Entities detected by tier loading
- `characters_in_scene`: Characters mentioned in message
- `in_scene_entities`: Entities actively in scene (full cards loaded)
- `referenced_entities`: Entities mentioned but not in scene
- `chapter`: None (TODO)
- `previous_scenes`: [] (not needed for immediate)

**Data Sources:**
- User message (from IPC request)
- AutomationContext (from prompt builder)
- Tier loading results (entity detection)

**Execution:**
- Concurrent via ThreadPoolExecutor (max 4 workers)
- Individual timeouts per agent (3-5 seconds)
- Failures logged but don't block (best-effort)

**Results:**
- Injected into prompt as formatted text
- Cached in AutomationResult.cached_context

### BackgroundAgentStrategy Context

**Method:** `execute_post_response(user_message, claude_response, message_number, rp_dir)`

**Parameters provided to each agent:**
- `user_message`: Original user message
- `claude_response`: LLM's generated response
- `message_number`: Current response count
- `rp_dir`: RP directory path

**AgentContext fields (minimal):**
- `message`: User message
- `response_number`: Message number
- `loaded_entities`: []
- `characters_in_scene`: []
- `chapter`: None (TODO)
- `previous_scenes`: [] (TODO)

**Execution:**
- Concurrent via ThreadPoolExecutor (max 4 workers)
- No strict timeouts (can run longer)
- Failures logged but don't block

**Results:**
- Written to state files by each agent
- Dict mapping agent_id → result dict returned

---

## Data Flow Matrix

### Immediate Agents - Data Dependencies

| Agent | Reads From | Writes To | LLM Access |
|-------|-----------|-----------|------------|
| FactExtractionAgent | - User message<br>- Entity files<br>- Knowledge base | None (read-only) | No |
| MemoryExtractionAgent | - User message<br>- Character memory files<br>- Characters in scene | None (read-only) | No |
| PlotThreadExtractionAgent | - User message<br>- Plot threads master<br>- Active plot threads | None (read-only) | No |

### Background Agents - Data Dependencies

| Agent | Reads From | Writes To | LLM Access |
|-------|-----------|-----------|------------|
| ResponseAnalyzerAgent | - User message<br>- Claude response<br>- Session state | - Scene metadata<br>- Pacing analysis files | Optional (via bridge) |
| TimeTrackingAgent | - Claude response<br>- Current session state<br>- Time tracking state | - Time tracking state<br>- Session state updates | No |
| MemoryCreationAgent | - User message<br>- Claude response<br>- Character files | - Character memory files<br>- Memory logs | Yes (via bridge) |
| PlotThreadDetectionAgent | - User message<br>- Claude response<br>- Plot threads master | - Plot threads master<br>- Plot thread updates | Yes (via bridge) |
| RelationshipAnalysisAgent | - Claude response<br>- Character files<br>- Relationship graph | - Relationship graph<br>- Character relationship files | Yes (via bridge) |
| KnowledgeExtractionAgent | - Claude response<br>- Knowledge base<br>- World lore files | - Knowledge base<br>- World lore files | Yes (via bridge) |
| ContradictionSynthesisAgent | - Claude response<br>- Knowledge base<br>- Plot threads<br>- Character states | - Contradiction log<br>- Synthesis notes<br>- Knowledge base updates | Yes (via bridge) |

---

## Agent Configuration

### Configuration Location

**File:** `{rp_dir}/config/automation_config.json` (or `config.json`)

**Structure:**
```json
{
  "agents": {
    "immediate": {
      "fact_extraction": {
        "enabled": true,
        "timeout_seconds": 5
      },
      "memory_extraction": {
        "enabled": true,
        "timeout_seconds": 5
      },
      "plot_thread_extraction": {
        "enabled": false,
        "timeout_seconds": 5
      }
    },
    "background": {
      "response_analyzer": {
        "enabled": true
      },
      "time_tracking": {
        "enabled": true
      },
      "memory_creation": {
        "enabled": true
      },
      "plot_thread_detection": {
        "enabled": true
      },
      "relationship_analysis": {
        "enabled": false
      },
      "knowledge_extraction": {
        "enabled": true
      },
      "contradiction_synthesis": {
        "enabled": false
      }
    }
  },
  "fallback": {
    "use_trigger_system": true,
    "trigger_system_primary": false
  }
}
```

### Configuration Loading

**Loaded by:**
- `ConfigLoader(rp_dir).load()` in `create_automation_service()`
- `AgentRegistry` reads `config.get("agents", {})`

**Determines:**
- Which agents are instantiated
- Which strategy is used (agents vs trigger fallback)
- Timeout values for immediate agents
- Max workers (currently hardcoded to 4)

---

## Agent Base Class

**File:** `src/automation/agents/base_agent.py`

**All agents inherit from BaseAgent or implement agent interface**

**Common Interface:**
- `execute(context: AgentContext) -> dict`
- `get_timeout() -> int`
- `get_priority() -> int`

**→ TRACE:** Base agent implementation if needed for Phase 2

---

## Agent Runner

**File:** `src/automation/services/agent_runner.py`

**Purpose:** Executes strategies in order

**Initialization:**
```python
agent_runner = AgentRunner(
    strategies=[immediate_strategy, background_strategy],
    logger=logger
)
```

**Methods:**
- `run_immediate(context) -> AutomationResult`
- `run_background(user_message, claude_response, message_number)`

**→ TRACE:** AgentRunner implementation for Phase 2

---

## Automation Service Integration

**File:** `src/automation/services/automation_service.py`

**AutomationService uses agent_runner:**
- Pre-response: Calls `agent_runner.run_immediate(context)`
- Post-response: Calls `agent_runner.run_background(...)`

**→ TRACE:** AutomationService implementation for Phase 2

---

## Bridge Integration for Agent LLM Access

### Bridge Reference Passed to Agents

**Flow:**
1. `BridgeService` passes `self` to `create_automation_service(bridge=self)`
2. Factory passes `bridge` to `AgentRegistry`
3. `AgentRegistry` passes `bridge` to strategies
4. Strategies pass `bridge` to individual agent instances

**Agents Using Bridge:**
- MemoryCreationAgent
- PlotThreadDetectionAgent
- RelationshipAnalysisAgent
- KnowledgeExtractionAgent
- ContradictionSynthesisAgent

**Usage Pattern:**
```python
# In agent
if self.bridge and self.bridge.secondary_client:
    llm_client = self.bridge.secondary_client
    response = llm_client.call_llm(prompt, ...)
```

**LLM Routing:**
- Immediate agents: Rarely use LLM (read-only context gathering)
- Background agents: May use secondary LLM client for analysis
- Bridge provides: `primary_client`, `secondary_client`

---

## File System Paths Used by Agents

### Common Paths (via StatePaths)

- `{rp_dir}/state/` - State files
- `{rp_dir}/state/session_state.json` - Session state
- `{rp_dir}/state/plot_threads_master.md` - Plot threads
- `{rp_dir}/state/knowledge_base.md` - World knowledge
- `{rp_dir}/characters/` - Character files
- `{rp_dir}/characters/{character_name}.md` - Character sheets
- `{rp_dir}/entities/` - Entity definitions
- `{rp_dir}/logs/` - Agent logs

### Agent-Specific Output Files

**ResponseAnalyzerAgent:**
- `state/scene_metadata/scene_{number}.json`
- `state/pacing_analysis.json`

**TimeTrackingAgent:**
- `state/time_tracking.json`

**MemoryCreationAgent:**
- `characters/{character_name}_memories.md`
- `state/memory_log.json`

**PlotThreadDetectionAgent:**
- `state/plot_threads_master.md` (updates)
- `state/plot_thread_updates_{number}.json`

**RelationshipAnalysisAgent:**
- `state/relationships.json`
- `characters/{character_name}_relationships.md`

**KnowledgeExtractionAgent:**
- `state/knowledge_base.md` (updates)
- `state/world_lore/{topic}.md`

**ContradictionSynthesisAgent:**
- `state/contradictions_log.json`
- `state/synthesis_notes.md`

---

## Performance Characteristics

### Immediate Agents

- **Total Time Budget:** 3-5 seconds per agent
- **Concurrency:** Max 4 agents in parallel
- **Best Case:** 3-5 seconds (all parallel)
- **Worst Case:** 15-25 seconds (4 batches of 4 agents)
- **Actual:** ~3-5 seconds (only 3 immediate agents exist)

**Impact:**
- Adds 3-5 seconds latency before LLM call
- User sees "processing" delay
- Results improve prompt quality

### Background Agents

- **Total Time Budget:** No hard limit
- **Concurrency:** Max 4 agents in parallel
- **Execution:** Async after LLM response
- **Best Case:** Seconds (no LLM calls)
- **Worst Case:** Minutes (multiple LLM calls to secondary model)
- **Actual:** Varies by agent and LLM usage

**Impact:**
- No user-facing latency (async)
- May delay next request if still running
- File writes may overlap with user actions

---

## Agent Availability Flags

### Import Guards

Both strategies use try/except to handle missing agents:

**ImmediateAgentStrategy:**
```python
try:
    from .immediate import (
        FactExtractionAgent,
        MemoryExtractionAgent,
        PlotThreadExtractionAgent,
    )
    FACT_EXTRACTION_AVAILABLE = True
    # etc.
except ImportError:
    FACT_EXTRACTION_AVAILABLE = False
    class FactExtractionAgent: pass  # Stub
```

**Graceful Degradation:**
- If agents can't be imported, strategy returns empty results
- Logs warning about unavailability
- System continues without agent functionality

---

## Next Traces Required (Phase 2)

### For Complete Agent Understanding:

1. **BaseAgent** - Agent interface/base class
   - File: `src/automation/agents/base_agent.py`

2. **Individual Agent Implementations:**
   - Immediate agents (3 files)
   - Background agents (7 files)

3. **AgentRunner** - Strategy executor
   - File: `src/automation/services/agent_runner.py`

4. **AutomationService** - Top-level orchestrator
   - File: `src/automation/services/automation_service.py`

5. **AgentContext** - Context object structure
   - File: `src/automation/contracts/agent_contracts.py`

---

## Summary

**Agent System Architecture:**
- **10 agents total** (3 immediate + 7 background)
- **2 strategies** (immediate + background)
- **1 fallback strategy** (legacy triggers)
- **Factory-based creation** with dependency injection
- **Configuration-driven enablement**
- **Bridge integration** for secondary LLM access
- **Concurrent execution** with ThreadPoolExecutor
- **Graceful degradation** on import failures

**Key Files:**
- `automation/factory.py` - Service creation
- `automation/agents/registry.py` - Strategy selection
- `automation/agents/immediate_agent_strategy.py` - Pre-response agents
- `automation/agents/background_agent_strategy.py` - Post-response agents
- 10 agent implementation files

**Data Flow:**
- Immediate: Context gathering → Prompt injection
- Background: Response analysis → File writes

---

**Analysis Complete:** Phase 1.5 - Agent System Traced
**Next Step:** Phase 2 - Layer-by-Layer File Analysis
