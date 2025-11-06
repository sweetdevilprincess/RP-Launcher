# Agent LLM Infrastructure Status

**Date:** 2025-10-24
**Discovery:** Complete scope of missing agent LLM infrastructure

---

## TL;DR

You have:
- ✅ Primary LLM infrastructure (Claude/OpenAI/OpenRouter for main conversation)
- ✅ Agent execution pipeline (Catalog, Factory, Executor, Coordinator)
- ✅ Data storage (MemoryEntry, EntityRepository, relationships)
- ✅ UI placeholders for secondary LLM settings

You DON'T have:
- ❌ Secondary LLM client for agents (cheap DeepSeek/etc)
- ❌ Configuration for agent LLM
- ❌ Any agent implementations that analyze responses
- ❌ Wiring between agent pipeline and LLM client

---

## Current State

### What Works Now

#### Primary LLM (Main Conversation)
**Location**: `bridge_service.py`, `message_handler.py`
- User sends message → Claude responds
- Cost: ~$0.01-0.05 per message
- Provider: Configured in settings (Claude/OpenAI/OpenRouter)
- Status: ✅ **FULLY FUNCTIONAL**

#### Agent Execution Pipeline
**Location**: `src/automation/services/`
- AgentCatalog - Registry ✅
- AgentFactory - Creates agents ✅
- AgentExecutor - Runs concurrently ✅
- AgentCoordinator - Orchestrates ✅
- Status: ✅ **FULLY FUNCTIONAL** (but has no agents to run)

#### Data Storage
**Location**: `src/domain/entities/`
- MemoryEntry dataclass ✅
- MemoryLog with timeline support ✅
- FixtureEntityRepository ✅
- Relationship tracking (in memories) ✅
- Status: ✅ **FULLY FUNCTIONAL**

---

## What's Missing

### 1. Secondary LLM Infrastructure ❌

#### Configuration Schema
**File**: `src/infrastructure/config/defaults.py`
**Status**: Missing

```python
# NEEDS TO BE ADDED
class AgentLLMConfig(TypedDict):
    """Secondary LLM configuration for agent analysis."""
    enabled: bool
    provider: str  # "openrouter", "openai", etc.
    model: str     # "deepseek/deepseek-chat-v3"
    api_key: str
    temperature: float
    max_tokens: int
    timeout: int

AGENT_LLM_DEFAULTS: AgentLLMConfig = {
    "enabled": True,
    "provider": "openrouter",
    "model": "deepseek/deepseek-chat-v3",
    "api_key": "",  # User must provide
    "temperature": 0.0,  # Deterministic analysis
    "max_tokens": 2048,
    "timeout": 30,
}
```

#### Client Initialization
**File**: `src/automation/factory.py` or `bridge_service.py`
**Status**: Missing

```python
# NEEDS TO BE ADDED
def create_agent_llm_client(config: dict) -> LLMClient:
    """Create LLM client specifically for agent analysis.

    Uses cheaper models (DeepSeek) for cost-effective analysis.
    """
    agent_config = config.get("agent_llm", {})

    if not agent_config.get("enabled", True):
        return None  # Agents disabled

    provider = agent_config.get("provider", "openrouter")

    # Create appropriate client
    if provider == "openrouter":
        from src.infrastructure.llm import OpenRouterClient
        return OpenRouterClient(
            api_key=agent_config.get("api_key"),
            model=agent_config.get("model", "deepseek/deepseek-chat-v3"),
            temperature=agent_config.get("temperature", 0.0),
        )
    # ... other providers
```

#### Dependency Injection
**File**: `src/automation/services/agent_factory.py`
**Status**: Signature needs to be updated

```python
# CURRENT (line 53)
def __init__(
    self,
    *,
    catalog: AgentCatalog,
    rp_dir: Path,
    log_file: Path,
    logger: LoggingService | None = None,
):

# NEEDS TO BECOME
def __init__(
    self,
    *,
    catalog: AgentCatalog,
    rp_dir: Path,
    log_file: Path,
    agent_llm_client: LLMClient | None,  # ← ADD THIS
    entity_repo: FixtureEntityRepository,  # ← ADD THIS
    logger: LoggingService | None = None,
):
    self.agent_llm_client = agent_llm_client
    self.entity_repo = entity_repo
```

**File**: `src/automation/services/agent_factory.py:103`
**Status**: Agent construction needs to be updated

```python
# CURRENT
agent = agent_class(self.rp_dir, self.log_file)

# NEEDS TO BECOME
agent = agent_class(
    rp_dir=self.rp_dir,
    log_file=self.log_file,
    llm_client=self.agent_llm_client,  # ← ADD THIS
    entity_repo=self.entity_repo,      # ← ADD THIS
)
```

---

### 2. Agent Implementations ❌

All 10 agents are missing:

#### Background Agents (Run after Claude responds)
**Location**: `src/automation/agents/background/` (doesn't exist yet)

1. **MemoryCreationAgent** ❌
   - Analyzes response for memorable moments
   - Creates MemoryEntry objects
   - Saves via EntityRepository
   - Cost: ~$0.001 per response

2. **RelationshipAnalysisAgent** ❌
   - Detects relationship changes
   - Updates relationships field in memories
   - Cost: ~$0.001 per response

3. **PlotThreadDetectionAgent** ❌
   - Identifies plot developments
   - Tracks storylines
   - Cost: ~$0.001 per response

4. **KnowledgeExtractionAgent** ❌
   - Extracts world-building facts
   - Saves lore/knowledge
   - Cost: ~$0.001 per response

5. **ContradictionDetectionAgent** ❌
   - Finds narrative inconsistencies
   - Compares with established facts
   - Cost: ~$0.001 per response

6. **ResponseAnalyzerAgent** ❌
   - Classifies scene type
   - Analyzes pacing
   - Cost: ~$0.001 per response

#### Immediate Agents (Run before Claude responds)
**Location**: `src/automation/agents/immediate/` (doesn't exist yet)

7. **QuickEntityAnalysisAgent** ❌
   - Identifies entities mentioned in user message
   - Triggers entity loading
   - Cost: ~$0.0005 per message

8. **FactExtractionAgent** ❌
   - Pulls relevant facts about entities
   - Injects into prompt
   - Cost: ~$0.0005 per message

9. **MemoryExtractionAgent** ❌
   - Finds relevant memories
   - Injects into prompt
   - Cost: ~$0.0005 per message

10. **PlotThreadExtractionAgent** ❌
    - Identifies active plot threads
    - Provides narrative continuity
    - Cost: ~$0.0005 per message

---

## Cost Analysis

### Current System (No Agents)
- Primary LLM: ~$0.03 per message
- Agent LLM: $0 (not implemented)
- **Total: ~$0.03 per message**

### With All Agents (Individual Approach)
- Primary LLM: ~$0.03 per message
- 10 Agent calls: ~$0.01 total ($0.001 each)
- **Total: ~$0.04 per message**

### With Grouped Agents (Hybrid Approach - Recommended)
- Primary LLM: ~$0.03 per message
- 3 Agent calls: ~$0.003 total
- **Total: ~$0.033 per message**

### With Unified Agent (Single Call)
- Primary LLM: ~$0.03 per message
- 1 Agent call: ~$0.001
- **Total: ~$0.031 per message**

---

## UI Status

### Settings Page
**File**: `src/presentation/tui/components/llm_settings_page.py`
**Status**: ✅ UI exists, ❌ not wired to backend

```python
# Lines 193-208: Secondary LLM section exists in UI
yield Static("Secondary LLM (Optional)", classes="section-title")
yield Static("Used for automation purposes...", ...)
yield Input(id="secondary-api-key", password=True)
yield Input(id="secondary-model", ...)
```

**Problem**: These fields exist but:
- Not saved to config
- Not loaded from config
- Not used to create agent LLM client

---

## Implementation Roadmap

### Phase 1: Secondary LLM Infrastructure (4-6 hours)
1. Add AgentLLMConfig to defaults.py
2. Create create_agent_llm_client() function
3. Update AgentFactory signature
4. Update AgentCoordinator to pass agent_llm_client
5. Wire settings UI to config backend
6. Test with mock agent

### Phase 2: First Agent (Memory Creation) (6-8 hours)
1. Create MemoryCreationAgent class
2. Build prompt template
3. Implement LLM calling
4. Parse JSON response
5. Create MemoryEntry objects
6. Save via EntityRepository
7. Write comprehensive tests
8. Document usage

### Phase 3: Remaining Agents (30-40 hours)
1. Relationship Analysis (6-8 hours)
2. Response Analyzer (4-6 hours)
3. Plot Thread Detection (6-8 hours)
4. Knowledge Extraction (6-8 hours)
5. Contradiction Detection (6-8 hours)
6. Quick Entity Analysis (4-6 hours)
7. Fact Extraction (4-6 hours)
8. Memory Extraction (4-6 hours)
9. Plot Thread Extraction (4-6 hours)

**Total Estimated Effort: 40-54 hours**

---

## Architecture Decisions Still Needed

### 1. Agent Grouping Strategy
- **Option A**: Individual (10 separate agents, 10 LLM calls)
- **Option B**: Unified (1 agent, 1 LLM call)
- **Option C**: Hybrid (3 groups, 3 LLM calls) ← **RECOMMENDED**

### 2. Agent LLM Provider
- DeepSeek via OpenRouter (cheapest)
- GPT-3.5 via OpenAI (faster)
- Claude Haiku (best quality for price)
- User configurable

### 3. Agent Execution Timing
- All agents every response? (expensive but thorough)
- Selective based on response type? (cheaper but complex)
- User configurable per agent? (most flexible)

---

## Key Files to Modify

1. `src/infrastructure/config/defaults.py` - Add agent LLM config
2. `src/automation/factory.py` - Add create_agent_llm_client()
3. `src/automation/services/agent_factory.py` - Update constructor
4. `src/automation/services/agent_coordinator.py` - Pass agent_llm_client
5. `src/presentation/tui/components/llm_settings_page.py` - Wire to backend
6. `src/automation/agents/background/` - Create directory, add 6 agents
7. `src/automation/agents/immediate/` - Create directory, add 4 agents

---

## Summary

You have excellent infrastructure (pipeline, storage, execution) but are missing:
1. Secondary LLM client configuration and initialization
2. All 10 agent implementations

This is actually **GOOD** because:
- Clean slate - build it right from the start
- Modern architecture - no legacy baggage
- Proper separation - primary vs agent LLM
- Testable and flexible

**Estimated total work: 40-54 hours** to complete full agent system.
