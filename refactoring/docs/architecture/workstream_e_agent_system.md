# Workstream E: Agent System Refactoring

**Status**: ✅ Complete (Phases 1-6)
**Date**: 2025-10-20
**Branch**: `feature/refactor-e-agent-system`

---

## Overview

Workstream E refactors the monolithic `AgentCoordinator` into modular, testable components following clean architecture principles. The agent system operates at the **individual agent level** and is designed to be called by Workstream D's strategy-level orchestration.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Workstream D: Strategy Level                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐    │
│  │ Agent        │  │ Agent        │  │ Fallback      │    │
│  │ Registry     │  │ Runner       │  │ Trigger       │    │
│  │ (strategies) │  │ (strategies) │  │ Strategy      │    │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘    │
│         │                  │                    │            │
│         └──────────────────┼────────────────────┘            │
│                            ↓                                 │
└────────────────────────────│─────────────────────────────────┘
                             │
┌────────────────────────────│─────────────────────────────────┐
│  Workstream E: Individual Agent Level                        │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         AgentCoordinator (Facade)                     │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                            │
│    ┌────────────┼────────────┬────────────┬─────────────┐  │
│    ↓            ↓            ↓            ↓             ↓  │
│  ┌─────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────┐│
│  │Agent│  │ Agent   │  │ Agent    │  │ Agent   │  │Retry │││
│  │Cata-│  │ Factory │  │ Executor │  │Format-  │  │Policy│││
│  │log  │  │         │  │          │  │ ter     │  │      │││
│  └─────┘  └─────────┘  └──────────┘  └─────────┘  └──────┘││
│     │          │             │             │           │    │
│     └──────────┴─────────────┴─────────────┴───────────┘    │
│                            │                                 │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Individual Agents (QuickEntityAnalysis, etc.)        │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## Components

### Phase 1: Retry Infrastructure

**Location**: `refactoring/src/infrastructure/retry/`

#### RetryPolicy

Configurable retry behavior with multiple backoff strategies:
- **Exponential**: `delay = initial * (multiplier ** attempt)`
- **Linear**: `delay = initial + (increment * attempt)`
- **Fixed**: `delay = constant`

Features:
- Jitter support (randomize delays to avoid thundering herd)
- Max delay cap
- Exception filtering (which exceptions trigger retries)

#### RetryExecutor

Executes functions with retry logic:
- Tracks attempt count and total delay
- Logs retry events via LoggingService
- Returns `RetryResult` with success/failure info

#### Predefined Policies

```python
AGENT_RETRY_POLICY = RetryPolicy(
    max_attempts=2,
    backoff_strategy=BackoffStrategy.FIXED,
    initial_delay_seconds=0.5,
    jitter=0.0,  # Predictable for user-facing
)

BACKGROUND_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    initial_delay_seconds=2.0,
    max_delay_seconds=60.0,
    jitter=0.2,  # More variance for background
)
```

---

### Phase 2: Agent Execution Contracts

**Location**: `refactoring/src/automation/contracts/agent_contracts.py`

#### AgentType

```python
class AgentType(Enum):
    IMMEDIATE = "immediate"   # Pre-response (3s latency)
    BACKGROUND = "background" # Post-response (hidden)
```

#### AgentMetadata

```python
@dataclass(frozen=True)
class AgentMetadata:
    agent_id: str
    description: str
    agent_type: AgentType
    priority: int = 5              # 1=highest, 10=lowest
    timeout_seconds: float = 10.0
    enabled: bool = True
```

#### AgentExecutionResult

```python
@dataclass(frozen=True)
class AgentExecutionResult:
    agent_id: str
    success: bool
    content: Optional[str] = None     # JSON output
    duration_ms: int = 0
    error: Optional[str] = None
    is_balance_error: bool = False
    attempts: int = 1
```

#### AgentExecutionStats

```python
@dataclass(frozen=True)
class AgentExecutionStats:
    agents_registered: int
    agents_executed: int
    agents_succeeded: int
    agents_failed: int
    balance_errors: int
    total_duration_ms: int
    max_duration_ms: int
    avg_duration_ms: int

    @property
    def success_rate(self) -> float:
        return self.agents_succeeded / self.agents_executed
```

---

### Phase 3: Core Components

#### 3.1 AgentCatalog

**Location**: `refactoring/src/automation/services/agent_catalog.py`

Thread-safe catalog for agent discovery and metadata management.

**Renamed from `AgentRegistry`** to avoid collision with Workstream D's strategy-level `AgentRegistry`.

**Key Methods**:
```python
register_agent(metadata: AgentMetadata, agent_class: Type)
get_agent_metadata(agent_id: str) -> Optional[AgentMetadata]
get_agent_class(agent_id: str) -> Optional[Type]
list_agents(agent_type: Optional[AgentType] = None, enabled_only: bool = False) -> List[AgentMetadata]
list_agent_ids(...) -> List[str]
count_agents(...) -> int
```

**Thread Safety**: Uses `threading.RLock()` for concurrent access.

#### 3.2 AgentFactory

**Location**: `refactoring/src/automation/services/agent_factory.py`

Creates agent instances from catalog metadata with conditional logic.

**Key Methods**:
```python
create_agent(agent_id: str) -> BaseAgent
create_agents(agent_ids: List[str], context: Dict[str, Any]) -> List[BaseAgent]
create_immediate_agents(context: Optional[Dict] = None) -> List[BaseAgent]
create_background_agents(context: Optional[Dict] = None) -> List[BaseAgent]
```

**Conditional Creation**:
- `fact_extraction` requires `tier2_entities`
- `memory_extraction` requires `scene_participants`
- `relationship_analysis` requires `characters_in_scene`
- `contradiction_detection` requires `enable_contradiction_detection`

#### 3.3 AgentExecutor

**Location**: `refactoring/src/automation/services/agent_executor.py`

Executes agents concurrently with timeout and retry handling.

**Renamed from `AgentRunner`** to avoid collision with Workstream D's strategy-level `AgentRunner`.

**Key Methods**:
```python
run_immediate_agents(agents: List, context: Dict, timeout: float = 10.0) -> List[AgentExecutionResult]
run_background_agents(agents: List, context: Dict, timeout: float = 60.0) -> List[AgentExecutionResult]
```

**Features**:
- **Separate thread pools**: 4 workers (immediate), 6 workers (background)
- **Retry integration**: Uses `AGENT_RETRY_POLICY` or `BACKGROUND_RETRY_POLICY`
- **Timeout enforcement**: Per-agent and global timeouts
- **Partial success**: Returns results even if some agents fail
- **Exception filtering**: Retries connection errors, timeouts, rate limits (not balance errors)

**Thread Pool Management**:
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(agent.execute, ...): agent for agent in agents}
    for future in as_completed(futures, timeout=10.0):
        result = future.result()
```

#### 3.4 AgentFormatter

**Location**: `refactoring/src/automation/services/agent_formatter.py`

Formats agent results for different output targets using strategy pattern.

**Strategies**:
1. **JsonCacheFormatter**: For `agent_analysis.json` (background agents)
2. **PromptInjectionFormatter**: For Claude prompt (~300-400 tokens, immediate agents)

**Key Methods**:
```python
format_for_cache(results: List[AgentExecutionResult], response_number: int) -> dict
format_for_prompt(results: List[AgentExecutionResult]) -> str
```

**JSON Cache Schema**:
```json
{
  "version": "1.0",
  "meta": {
    "resp_num": 42,
    "updated": "2025-10-20T...",
    "status": "fresh",
    "agents_run": 6,
    "agents_ok": 5,
    "agents_fail": 1
  },
  "background": {
    "response_analyzer": {...},
    "memory_creation": {...}
  },
  "immediate": {
    "quick_entity_analysis": {...}
  },
  "stats": {
    "bg_dur": 12500,
    "total_dur": 15000
  }
}
```

---

### Phase 4: AgentCoordinator

**Location**: `refactoring/src/automation/services/agent_coordinator.py`

Thin facade orchestrating the complete agent execution pipeline.

**Pipeline Flow**:
```
AgentCatalog → AgentFactory → AgentExecutor → AgentFormatter
```

**Key Methods**:
```python
register_agent(metadata: AgentMetadata, agent_class: Type)
run_immediate_agents(message: str, response_number: int, ...) -> str
run_background_agents(response_text: str, response_number: int, ...) -> dict
save_to_cache(cache_data: dict, cache_file: Optional[Path] = None)
load_from_cache(cache_file: Optional[Path] = None) -> Optional[dict]
get_catalog_stats() -> Dict[str, int]
```

**Usage Example**:
```python
from refactoring.src.automation.services import AgentCoordinator
from refactoring.src.automation.contracts import AgentMetadata, AgentType

coordinator = AgentCoordinator(
    rp_dir=Path("/path/to/rp"),
    log_file=Path("/path/to/hook.log"),
    logger=my_logger
)

# Register agents
coordinator.register_agent(
    metadata=AgentMetadata(
        agent_id="quick_entity_analysis",
        description="Identify entities in message",
        agent_type=AgentType.IMMEDIATE,
        priority=1,
        timeout_seconds=5.0
    ),
    agent_class=QuickEntityAnalysisAgent
)

# Run immediate agents
prompt_context = coordinator.run_immediate_agents(
    message="The user's message",
    response_number=42,
    loaded_entities=["Alice", "Bob"]
)

# Run background agents
cache_data = coordinator.run_background_agents(
    response_text="Claude's response",
    response_number=42,
    characters_in_scene=["Alice"]
)

# Save to cache
coordinator.save_to_cache(cache_data)
```

---

### Phase 5: Testing Infrastructure

**Location**: `refactoring/tests/`

#### Test Stubs

**Location**: `refactoring/tests/automation/stubs/stub_agents.py`

Stub agents for testing without DeepSeek API calls:
- `StubImmediateAgent`: Returns mock immediate agent JSON
- `StubBackgroundAgent`: Returns mock background agent JSON
- `SlowAgent`: Times out (for timeout testing)
- `FailingAgent`: Always raises exception
- `TransientFailureAgent`: Fails N times then succeeds (retry testing)
- `InsufficientBalanceAgent`: Raises balance error (non-retryable)

#### Unit Tests

**Location**: `refactoring/tests/infrastructure/test_retry_policy.py`

Tests for retry policy:
- Immediate success (no retries)
- Retry after transient failures
- Exhausted retries
- Non-retryable exceptions
- Exponential/linear/fixed backoff timing
- Max delay capping
- Jitter behavior

**Running Tests**:
```bash
cd refactoring
pytest tests/ -v
```

---

## Integration with Workstream D

### Strategy-Level vs Individual-Level

**Workstream D** operates at the **strategy level**:
- `AgentRegistry`: Loads and configures agent **strategies**
- `AgentRunner`: Executes agent **strategies** sequentially
- Strategies: `BackgroundAgentStrategy`, `ImmediateAgentStrategy`, `FallbackTriggerStrategy`

**Workstream E** operates at the **individual agent level**:
- `AgentCatalog`: Catalogs individual **agents**
- `AgentExecutor`: Executes individual **agents** concurrently
- Agents: `QuickEntityAnalysisAgent`, `MemoryCreationAgent`, etc.

### Integration Point

Workstream D's strategies **call** Workstream E's components:

```python
# In background_agent_strategy.py (Workstream D)
from refactoring.src.automation.services import AgentCoordinator

class BackgroundAgentStrategy:
    def execute(self, agent_context: AgentContext, prompt: str) -> AutomationResult:
        # Use Workstream E's coordinator
        coordinator = AgentCoordinator(...)

        cache_data = coordinator.run_background_agents(
            response_text=prompt,
            response_number=agent_context.response_number,
            ...
        )

        return AutomationResult(success=True, ...)
```

### Parameter Mapping

Workstream D provides `AgentContext`:
```python
@dataclass(frozen=True)
class AgentContext:
    message: str
    response_number: int
    loaded_entities: List[str]
    characters_in_scene: List[str]
    chapter: Optional[str]
    previous_scenes: List[str]
```

Workstream E maps to individual agent parameters:
```python
# AgentExecutor._extract_agent_args()
param_mappings = {
    "quick_entity_analysis": ("message", "message_number"),
    "memory_creation": ("response_text", "response_number", "chapter"),
    # ...
}
```

---

## File Structure

```
refactoring/
├── src/
│   ├── infrastructure/
│   │   └── retry/
│   │       ├── retry_policy.py       # RetryPolicy, RetryExecutor
│   │       └── __init__.py
│   │
│   └── automation/
│       ├── contracts/
│       │   ├── agent_contracts.py    # AgentMetadata, AgentExecutionResult
│       │   └── __init__.py
│       │
│       └── services/
│           ├── agent_catalog.py      # AgentCatalog (discovery)
│           ├── agent_factory.py      # AgentFactory (creation)
│           ├── agent_executor.py     # AgentExecutor (execution)
│           ├── agent_formatter.py    # AgentFormatter (formatting)
│           ├── agent_coordinator.py  # AgentCoordinator (facade)
│           └── __init__.py
│
├── tests/
│   ├── automation/
│   │   └── stubs/
│   │       ├── stub_agents.py        # Test stubs
│   │       └── __init__.py
│   │
│   └── infrastructure/
│       └── test_retry_policy.py      # Retry tests
│
└── docs/
    └── architecture/
        └── workstream_e_agent_system.md  # This file
```

---

## Migration Guide

### From Legacy AgentCoordinator

**Legacy (src/automation/agent_coordinator.py)**:
```python
coordinator = AgentCoordinator(rp_dir, log_file, max_workers=4)
coordinator.add_agent("my_agent", agent_func, *args)
context = coordinator.run_all_agents(timeout=30)
```

**Refactored (refactoring/src/automation/services/agent_coordinator.py)**:
```python
coordinator = AgentCoordinator(
    rp_dir=rp_dir,
    log_file=log_file,
    logger=logger,
    immediate_workers=4,
    background_workers=6
)
coordinator.register_agent(metadata, agent_class)
prompt_context = coordinator.run_immediate_agents(...)
cache_data = coordinator.run_background_agents(...)
```

### Key Differences

1. **Registration**: Now uses `AgentMetadata` instead of manual `add_agent()`
2. **Execution**: Split into `run_immediate_agents()` and `run_background_agents()`
3. **Formatting**: Automatic via `AgentFormatter` (no manual `_format_context()`)
4. **Thread Pools**: Separate pools for immediate vs background
5. **Retry**: Built-in retry policies
6. **Type Safety**: Frozen dataclasses for immutability

---

## Performance Characteristics

### Immediate Agents
- **Thread Pool**: 4 workers
- **Timeout**: 10 seconds (global)
- **Retry Policy**: 2 attempts, 0.5s fixed delay, no jitter
- **User-Facing Latency**: ~3 seconds typical
- **Agents**: QuickEntityAnalysis, FactExtraction, MemoryExtraction, PlotThreadExtraction

### Background Agents
- **Thread Pool**: 6 workers
- **Timeout**: 60 seconds (global)
- **Retry Policy**: 3 attempts, exponential backoff (2s → 4s → 8s max 60s), 20% jitter
- **Hidden from User**: Runs after response sent
- **Agents**: ResponseAnalyzer, MemoryCreation, RelationshipAnalysis, PlotThreadDetection, KnowledgeExtraction, ContradictionDetection

### Scalability
- **Parallel Execution**: All agents in a stage run concurrently
- **Partial Success**: Pipeline continues even if some agents fail
- **Resource Limits**: Thread pool sizes prevent resource exhaustion
- **Graceful Degradation**: Timeouts prevent blocking

---

## Future Enhancements

### Workstream D Coordination
- ✅ Contracts aligned with `AgentContext`
- ✅ Naming conflicts resolved (AgentCatalog/AgentExecutor)
- 🔄 Waiting for Workstream D to finalize `AutomationContext` fields
- 🔄 Parameter mapping can be improved after Workstream D integration

### Testing
- ✅ Basic retry policy tests
- ✅ Stub agents for testing
- 🔄 Full integration tests with AgentCoordinator
- 🔄 Mock agents for specific scenarios
- 🔄 Performance benchmarks

### Features
- 🔄 Agent result caching (beyond JSON file)
- 🔄 Agent dependency graphs (Agent A needs Agent B's result)
- 🔄 Dynamic thread pool sizing
- 🔄 Agent telemetry and metrics
- 🔄 Hot reloading of agent configurations

---

## Changelog

**2025-10-20**: Workstream E Complete (Phases 1-6)
- Phase 1: Retry infrastructure
- Phase 2: Agent contracts (minimal, awaiting Workstream D)
- Phase 3: AgentCatalog, AgentFactory, AgentExecutor, AgentFormatter
- Phase 4: AgentCoordinator facade
- Phase 5: Test stubs and retry tests
- Phase 6: Documentation (this file)
- Renamed: AgentRegistry → AgentCatalog, AgentRunner → AgentExecutor
- Coordinated with Workstream D on naming and contracts

---

## Questions & Support

### For Workstream D Team
- Strategy imports: Update after agents refactored into `refactoring/src/automation/agents/`
- Contract finalization: Coordinate on `AutomationContext` fields
- Integration testing: Validate strategy → executor flow

### For Future Developers
- Adding new agents: Follow `BaseAgent` pattern, register in catalog
- Modifying retry behavior: Update `AGENT_RETRY_POLICY` or `BACKGROUND_RETRY_POLICY`
- Changing thread pools: Adjust `immediate_workers` / `background_workers` in coordinator
- Custom formatters: Implement `FormatterStrategy` protocol

---

**Status**: ✅ Ready for Integration
**Next**: Coordinate with Workstream D for full pipeline integration
