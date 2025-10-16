# RP Claude Code - Supporting Components Documentation

Complete reference for all non-agent components, utilities, and infrastructure systems.

---

## TABLE OF CONTENTS

1. [API Clients](#api-clients)
2. [Configuration System](#configuration-system)
3. [Context & Data Flow](#context--data-flow)
4. [Event System](#event-system)
5. [Pipeline Architecture](#pipeline-architecture)
6. [Prompt Building](#prompt-building)
7. [Performance & Profiling](#performance--profiling)
8. [Initialization & Setup](#initialization--setup)
9. [Strategies & Helpers](#strategies--helpers)
10. [Status & Time Tracking](#status--time-tracking)
11. [Fallback System (Triggers)](#fallback-system-triggers)

---

## API CLIENTS

### DeepSeek API Client
**Location**: `src/clients/deepseek.py`

**Purpose**: Calls DeepSeek API via OpenRouter for text generation (entity cards, story arcs, summaries).

**Default Configuration**:
- **Model**: `deepseek/deepseek-chat-v3.1`
- **Temperature**: 0.3 (deterministic)
- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
- **Timeout**: 60 seconds

**API Key Resolution** (in order):
1. Environment: `DEEPSEEK_API_KEY`
2. Environment: `OPENROUTER_API_KEY`
3. Global config: `config.json` (TUI settings)
4. RP-specific: `state/secrets.json`
5. Current dir: `state/secrets.json`

**Exception Types**:
- `DeepSeekError` - Base exception
- `MissingAPIKeyError` - No key found
- `InsufficientBalanceError` - 402 error (low balance)

**Key Functions**:
- `call_deepseek(prompt: str, rp_dir: Path) -> str` - Main API call
- `_load_api_key(rp_dir: Path) -> str` - Load and resolve key

**Usage**:
```python
from src.clients import deepseek_client

try:
    response = deepseek_client.call_deepseek(
        prompt="Generate an entity card for...",
        rp_dir=rp_dir
    )
except deepseek_client.MissingAPIKeyError:
    print("Set OPENROUTER_API_KEY")
except deepseek_client.InsufficientBalanceError:
    # Handled by background task queue with retry
    pass
```

**Used By**:
- Story Generator (arc generation, summaries)
- Background agents (entity parsing)
- Entity Manager (optional parsing)

---

### Claude API Client (Main)
**Location**: `src/clients/claude_api.py`

**Purpose**: Direct Anthropic API integration with prompt caching and extended thinking.

**Thinking Modes** (5 levels):
| Mode | Budget | Use Case |
|------|--------|----------|
| disabled | 0 | Quick responses, no thinking |
| think | 5000 | Quick planning, simple tasks |
| think hard | 10000 | Feature design, debugging |
| megathink | 10000 | Standard reasoning (default) |
| think harder | 25000 | Complex bugs, architecture |
| ultrathink | 31999 | Maximum reasoning |

**Key Features**:
- **Prompt Caching**: Cache TIER_1 files across requests
- **Cache Metrics**: Track cache creation and read tokens
- **Extended Thinking**: Multiple reasoning levels
- **Temperature Control**: Sampling control (0-1)
- **Conversation History**: Multi-turn conversations

**Main Method**: `send_message()`

**Parameters**:
- `user_message` - User's message
- `cached_context` - Static context to cache (TIER_1 files)
- `conversation_history` - Previous [{"role": "user"/"assistant", "content": "..."}]
- `max_tokens` - Max response length
- `temperature` - Sampling temperature
- `thinking_mode` - Thinking preset
- `thinking_budget` - Override thinking tokens

**Returns**:
```python
{
    "content": str,           # Response text
    "thinking": str,          # Thinking process (if available)
    "usage": {
        "input_tokens": int,
        "output_tokens": int,
        "cache_creation_input_tokens": int,
        "cache_read_input_tokens": int
    },
    "raw_response": object    # Full API response
}
```

**Used By**:
- TUI Bridge (main integration point)
- Test scripts

---

### Claude SDK Client
**Location**: `src/clients/claude_sdk.py` (exists but not fully examined)

**Purpose**: Alternative SDK-based client (mentioned but appears to be legacy).

---

## CONFIGURATION SYSTEM

### Config Container
**Location**: `src/automation/config/config_container.py`

**Purpose**: Typed configuration objects replacing plain dictionaries. Provides validation, defaults, and type safety.

**Configuration Classes** (dataclasses):

```python
@dataclass
class AgentConfig:
    enabled: bool = True
    priority: int = 5
    timeout_seconds: int = 10
    retry_count: int = 0
    fallback_enabled: bool = True

@dataclass
class ImmediateAgentsConfig:
    enabled: bool = True
    quick_entity_analysis: AgentConfig
    fact_extraction: AgentConfig
    memory_extraction: AgentConfig
    plot_thread_extraction: AgentConfig

@dataclass
class BackgroundAgentsConfig:
    enabled: bool = True
    response_analyzer: AgentConfig (priority=1)
    memory_creation: AgentConfig (priority=2)
    relationship_analysis: AgentConfig (priority=3)
    plot_thread_detection: AgentConfig (priority=4)
    knowledge_extraction: AgentConfig (priority=5)
    contradiction_detection: AgentConfig (priority=6, enabled=False by default)

@dataclass
class FallbackConfig:
    enabled: bool = True
    timeout_threshold: int = 10
    error_threshold: int = 3
    use_simple_context: bool = True

@dataclass
class ConfigContainer:
    agents: AgentsConfig
    fallback: FallbackConfig
    # ... other config fields
```

**Benefits**:
- Type-safe configuration access
- IDE autocomplete support
- Validation at load time
- Clear defaults
- Easy to extend

**Loaded From**: `state/automation_config.json`

**Usage**:
```python
config = load_config_container(Path("state/automation_config.json"))
# Type-safe access:
config.agents.background.memory_creation.enabled  # bool
config.fallback.timeout_threshold  # int
```

---

## CONTEXT & DATA FLOW

### Automation Context
**Location**: `src/automation/context/automation_context.py`

**Purpose**: Immutable context object that flows through the automation pipeline. Replaces parameter sprawl with a single, typed data structure.

**Key Properties**:

```python
@dataclass(frozen=True)
class AutomationContext:
    # Core inputs
    message: str                              # User message
    rp_dir: Path                             # RP directory path

    # Configuration
    config: Dict[str, Any]                   # Config dict

    # Computed values
    response_count: int                      # Current response number
    should_generate_arc: bool                # Generate story arc this cycle?
    total_minutes: int                       # In-world time
    activities_desc: str                     # Activities summary

    # File collections
    tier1_files: Dict[str, str]             # TIER_1: cached context
    tier2_files: Dict[str, str]             # TIER_2: entity facts
    tier3_files: List[Path]                 # TIER_3: skipped
    escalated_files: List[Path]             # Escalated priority files

    # Entity data
    loaded_entities: List[str]              # Loaded entity names
    entities_with_cores: List[str]          # Entities with personality core

    # Agent results
    agent_context: Optional[str]            # All agent results combined
    cached_background_context: Optional[str]  # Cached from previous cycle
    immediate_agent_context: Optional[str]  # Current cycle immediate results

    # File updates
    file_updates: List[Dict]                # External file changes
    update_notification: str                # Notification text

    # Profiling
    profiler: Optional[Any]                 # Profiler instance
    profiling_enabled: bool                 # Enable profiling?
```

**Key Methods**:

- `with_update(**kwargs) -> AutomationContext`: Return new context with updates (immutable pattern)
- `merge_agent_context() -> str`: Combine cached and immediate agent contexts
- `state_dir` property: Convenience property for state directory

**Usage**:
```python
# Create context
context = AutomationContext(
    message="User message",
    rp_dir=Path("/path/to/rp")
)

# Update (immutable - returns new context)
new_context = context.with_update(response_count=42, should_generate_arc=True)

# Access properties
context.state_dir  # Returns: rp_dir / "state"
context.arc_frequency  # From config
```

**Data Flow**:
1. Context created with user message
2. Passed through pipeline stages
3. Each stage reads from and updates context
4. Final context contains all results

---

## EVENT SYSTEM

### Event Bus & Events
**Location**: `src/automation/events/`

**Purpose**: Decoupled event publishing for logging, monitoring, and debugging.

**Base Event Class**:
```python
class Event:
    """Base class for all events."""
    timestamp: datetime
    component: Optional[str]
```

**Event Types**:

#### FileLoadedEvent
- **When**: File loaded from disk
- **Data**: filename, file_path, tier, size_bytes

#### AgentStartedEvent
- **When**: Agent begins execution
- **Data**: agent_id, agent_type, parameters

#### AgentCompletedEvent
- **When**: Agent finishes execution
- **Data**: agent_id, agent_type, execution_time, success, result, error

#### PipelineStageEvent
- **When**: Pipeline stage executes
- **Data**: stage_name, stage_type (started/completed/failed/skipped), execution_time, result, error

#### ConfigurationChangedEvent
- **When**: Configuration is modified
- **Data**: config_file, changed_keys, old_values, new_values

#### ErrorEvent
- **When**: Error occurs
- **Data**: error_type, error_message, component, stack_trace, recoverable

#### ResponseGeneratedEvent
- **When**: Response generated
- **Data**: response_number, response_length, model, cache_mode

**EventBus**:
```python
class EventBus:
    def publish(event: Event) -> None
    def subscribe(event_type: Type, handler: Callable) -> None
    def unsubscribe(event_type: Type, handler: Callable) -> None
```

**Usage**:
```python
from src.automation.events import publish, subscribe
from src.automation.events.automation_events import ResponseGeneratedEvent

# Publish event
publish(ResponseGeneratedEvent(
    response_number=42,
    response_length=500,
    model="claude-sonnet",
    cache_mode=True
))

# Subscribe to events
def on_response_generated(event: ResponseGeneratedEvent):
    print(f"Response {event.response_number} generated")

subscribe(ResponseGeneratedEvent, on_response_generated)
```

---

## PIPELINE ARCHITECTURE

### Pipeline Base Classes
**Location**: `src/automation/pipeline/base.py`

**Purpose**: Core pipeline architecture for composing automation stages in sequence.

**Pipeline Context**:
```python
@dataclass
class PipelineContext:
    automation_context: AutomationContext  # Wrapped context
    stage_results: Dict[str, Any]         # Results from each stage
    errors: List[str]                     # Errors during execution
    warnings: List[str]                   # Warnings
    skip_remaining: bool                  # Skip remaining stages?

    def record_result(stage_name: str, result: Any)
    def add_error(error: str)
    def add_warning(warning: str)
    def update_automation_context(**kwargs)
```

**Pipeline Stage** (ABC):
```python
class PipelineStage(ABC):
    def __init__(self, name: str, log_file: Optional[Path])

    @abstractmethod
    def execute(context: PipelineContext) -> bool
        # Return True for success, False for failure
```

**Pipeline Result**:
```python
@dataclass
class PipelineResult:
    success: bool
    context: PipelineContext
    stages_executed: List[str]
    stages_skipped: List[str]
    execution_time: float

    def to_automation_result() -> AutomationResult
```

**Example Stage**:
```python
class LoadEntitiesStage(PipelineStage):
    def execute(self, context: PipelineContext) -> bool:
        try:
            # Load and index entities
            self.entity_manager.scan_and_index()
            context.record_result("loaded_entities", ...)
            return True
        except Exception as e:
            context.add_error(str(e))
            return False
```

### Pipeline Builder
**Location**: `src/automation/pipeline/builder.py`

**Purpose**: Builds pipelines from stages.

**Usage**:
```python
from src.automation.pipeline.builder import PipelineBuilder

builder = PipelineBuilder()
builder.add_stage(LoadEntitiesStage(...))
builder.add_stage(ImmediateAgentsStage(...))
builder.add_stage(ResponseStage(...))
builder.add_stage(BackgroundAgentsStage(...))
builder.add_stage(FileUpdateStage(...))

pipeline = builder.build()
result = pipeline.execute(context)
```

### Pipeline Stages
**Location**: `src/automation/pipeline/stages.py`

**Standard Pipeline Stages**:

1. **LoadEntitiesStage**
   - Loads and indexes entity cards
   - Output: entities in context

2. **ImmediateAgentsStage**
   - Runs all 4 immediate agents in parallel
   - Output: agent results in cache

3. **ResponseStage**
   - Calls Claude API with agent context
   - Output: response in context

4. **BackgroundAgentsStage**
   - Runs all 6 background agents in parallel
   - Output: file updates queued

5. **FileUpdateStage**
   - Applies all file updates
   - Output: files written via FSWriteQueue

---

## PROMPT BUILDING

### Prompt Builder
**Location**: `src/automation/helpers/prompt_builder.py`

**Purpose**: Unified prompt building for both cached and non-cached modes. Eliminates 90% code duplication.

**Key Method**: `build_prompt()`

**Parameters**:
- `tier1_files` - TIER_1 files (cached context)
- `tier2_files` - TIER_2 files (entity facts)
- `tier3_files` - TIER_3 files (skipped)
- `escalated_files` - Escalated priority files
- `message` - User message
- `response_count` - Current response number
- `total_minutes` - In-world time
- `activities_desc` - Activities summary
- `should_generate_arc` - Generate arc injection?
- `agent_context` - Agent analysis context
- `loaded_entities` - Entity names for consistency checklist
- `update_notification` - File update notification
- `cache_mode` - Return tuple for caching?

**Returns**:
- If `cache_mode=False`: Single string (enhanced_prompt)
- If `cache_mode=True`: Tuple (cached_context, dynamic_prompt)

**Sections Built**:
1. TIER_1 (cached in Claude)
2. TIER_2 (entity facts)
3. TIER_3 (referenced entities)
4. Escalated files
5. Agent context (immediate agent results)
6. Consistency checklist
7. Story arc injection (if enabled)
8. Update notifications
9. User message

**Used By**:
- Orchestrator V2
- Response generation stage

---

### Prompt Template Manager
**Location**: `src/automation/prompt_templates.py`

**Purpose**: Genre-specific narrative guidance templates for different story types.

**Template Modes**:
1. **auto** - Smart detection from ROLEPLAY_OVERVIEW.md
2. **composite** - Pre-made genre combinations
3. **modular** - Mix sections from different genres
4. **layered** - Primary genre + secondary highlights

**Configuration**:
```json
{
  "narrative_template": {
    "mode": "auto|composite|modular|layered",
    "primary_genre": "fantasy|scifi|romance|etc",
    "secondary_genres": [],
    "sections": []
  }
}
```

**Key Method**: `generate_narrative_instructions() -> str`

**Returns**: Formatted narrative instructions (empty if error or mode not found)

**Used By**:
- Prompt Builder (optional injection)
- Story generation

---

## PERFORMANCE & PROFILING

### Performance Profiler
**Location**: `src/automation/profiling.py`

**Purpose**: Tracks precise timing of automation operations to identify bottlenecks.

**Key Methods**:
```python
class PerformanceProfiler:
    def start(operation: str)                    # Start timing
    def end(operation: str) -> float             # End timing, return elapsed
    def measure(operation: str) -> ContextManager # Context manager
    def get_timing(operation: str) -> Optional[float]
    def report(title: str) -> str               # Generate report
```

**Usage**:
```python
profiler = PerformanceProfiler()

# Manual timing
profiler.start("entity_loading")
load_entities()
elapsed = profiler.end("entity_loading")

# Context manager
with profiler.measure("agent_execution"):
    run_agents()

# Report
print(profiler.report("Automation Performance"))
```

**Tracks**:
- Operation name
- Start time (perf_counter for precision)
- Elapsed time (in seconds)
- Call stack (nested operations)

---

### Profiling Decorator
**Location**: `src/automation/decorators/profiling.py`

**Purpose**: Clean decorator pattern replacing repetitive profiling boilerplate.

**Decorator**: `@profile(name: str = None, log: bool = True)`

**Usage**:
```python
from src.automation.decorators import profile

@profile("response_generation")
def generate_response(self, message: str):
    # Automatically profiled
    return response

@profile(log=False)
def quick_check(self):
    # Profiled but not logged
    pass
```

**ProfileContext**:
```python
class ProfileContext:
    def __init__(self, name, profiler, enabled, log_file)

    # Use with: ProfileContext(...).__enter__()/__exit__()
```

**Benefits**:
- Eliminates 11+ instances of boilerplate
- Automatic start/end timing
- Optional logging
- Works with or without profiler

---

## INITIALIZATION & SETUP

### RP Initializer
**Location**: `src/initialize_rp.py`

**Purpose**: Initialize complete directory structure and state files for new RP.

**Main Class**: `RPInitializer`

**Key Method**: `initialize(rp_name: str = None, skip_existing: bool = True)`

**Creates**:

1. **Directory Structure**:
   - `chapters/` - Story chapters
   - `entities/` - Entity cards
   - `locations/` - Location details
   - `memories/` - Character memories
   - `relationships/` - Relationship data
   - `state/` - State files
   - `ROLEPLAY_OVERVIEW.md` - RP overview

2. **State Files**:
   - `state/response_counter.json` - Response count
   - `state/automation_config.json` - Agent configuration
   - `state/current_state.md` - Current state
   - `state/relationships.json` - Character relationships
   - `state/plot_threads_master.md` - Plot threads
   - `state/knowledge_base.md` - World facts

3. **Initial Content**:
   - `Chapter_1.md` - First chapter template
   - `ROLEPLAY_OVERVIEW.md` - RP metadata

**Usage**:
```python
from src.initialize_rp import RPInitializer

initializer = RPInitializer(Path("RPs/MyRP"))
initializer.initialize(
    rp_name="My Roleplay",
    skip_existing=True
)
```

---

## STRATEGIES & HELPERS

### File Loading Strategy
**Location**: `src/automation/strategies/file_loading.py`

**Purpose**: Strategy pattern for file loading operations.

**Strategies**:
- Different loading approaches for different scenarios
- Configurable via strategy pattern
- Allows testing different loading strategies

---

### Consistency Checklist
**Location**: `src/automation/consistency_checklist.py`

**Purpose**: Generate consistency checklist for loaded entities to prevent contradictions.

**Function**: `generate_consistency_checklist(loaded_entities, entity_manager) -> str`

**Output**: Checklist format for Claude to review consistency

---

### Prompt Helper Module
**Location**: `src/automation/helpers/prompt_builder.py`

**Supporting Functions**:
- Prompt section building
- TIER organization
- Context merging
- Template injection

---

## STATUS & TIME TRACKING

### Status Manager
**Location**: `src/automation/status.py`

**Purpose**: Generates and updates `CURRENT_STATUS.md` with real-time system status.

**Key Features**:
- Updates status file every response
- Shows current location, chapter, response count
- Tracks story arc progress
- Lists loaded entities
- Quick command reference

**Template Fields**:
- Timestamp
- Current location
- Chapter number
- Response count
- Story arc progress (visual progress bar)
- Entity count
- Loaded entities this response
- Automation settings (entity cards, arcs)
- Quick command reference

**Used By**:
- Orchestrator V1 (status updates)
- Orchestrator V2 (status updates)

**Output**: `CURRENT_STATUS.md` (project root)

---

### Time Tracker
**Location**: `src/automation/time_tracking.py`

**Purpose**: Calculates in-world time based on activities described in messages.

**Key Methods**:
- `calculate_time(message, state_file)` - Parse message for time-based activities
- Detects time-indicating phrases (morning, evening, later, etc.)
- Updates timing based on activities mentioned
- Maintains timeline consistency

**Reads From**:
- User message (activity descriptions)
- `Timing.txt` or timing guidelines

**Writes To**:
- Returns time deltas
- Updates current_state.md timing

**Used By**:
- Orchestrator V1 (time calculation)
- Orchestrator V2 (time calculation)

---

## FALLBACK SYSTEM (TRIGGERS)

### Trigger System
**Location**: `src/trigger_system/trigger_system.py`

**Purpose**: Fallback entity/memory detection system using keyword triggers if agents fail.

**Trigger-Based Detection**:
- Keyword matching for entity mentions
- Trigger patterns in entity cards
- Fallback when agents timeout/fail

**Configuration**:
- Triggers enabled/disabled via config
- Can be primary or fallback system
- Configurable timeout threshold

**Used By**:
- Orchestrator V2 (fallback if agents fail)
- Consistency checking

**See**: `src/trigger_system/README.md` for detailed trigger system documentation

---

## UTILITY MODULES

### Version Module
**Location**: `src/version.py`

**Purpose**: Version tracking for the system.

**Exports**: Version string for UI and logging

---

### Update Checker
**Location**: `src/update_checker.py`

**Purpose**: Check for system updates.

**Key Functions**:
- Check for new versions
- Notify user of updates
- Download/apply updates (optional)

---

### Generate Preferences
**Location**: `src/generate_preferences.py`

**Purpose**: Generate user preferences for DeepSeek analysis.

**Creates**: Character preference files for relationship analysis.

---

## INTEGRATION POINTS

### How Components Work Together

```
┌─────────────────────────────────────────────┐
│ User Input (TUI Bridge)                     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ AutomationContext Created                   │
│ - User message                              │
│ - Configuration loaded                      │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Pipeline Execution                          │
├─────────────────────────────────────────────┤
│ 1. Load Entities Stage                      │
│    - EntityManager scans entities           │
│ 2. Immediate Agents Stage                   │
│    - 4 agents analyze user message          │
│    - Results cached to state/agent_analysis │
│ 3. Response Stage                           │
│    - PromptBuilder builds prompt            │
│    - PromptTemplateManager injects template │
│    - Claude API Client calls Claude         │
│    - Profiler tracks execution time         │
│ 4. Background Agents Stage                  │
│    - 6 agents analyze response              │
│ 5. File Update Stage                        │
│    - FSWriteQueue debounces writes          │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Events Published                            │
│ - ResponseGeneratedEvent                    │
│ - AgentCompletedEvent (for each agent)      │
│ - PipelineStageEvent (for each stage)       │
│ - ProfilingEvent (performance data)         │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ TUI Bridge Returns Response                 │
└─────────────────────────────────────────────┘
```

---

## COMPONENT DEPENDENCIES

```
Orchestrator V2
    ├─ ConfigContainer (load configuration)
    ├─ AutomationContext (data flow)
    ├─ Pipeline (stages, execution)
    ├─ EntityManager (entity loading)
    ├─ FileChangeTracker (detect updates)
    ├─ PerformanceProfiler (track timing)
    ├─ EventBus (publish events)
    └─ PromptBuilder (build prompts)
        ├─ PromptTemplateManager
        └─ ConsistencyChecklist

Claude API Client
    └─ Anthropic SDK

DeepSeek API Client
    └─ OpenRouter API

TUI Bridge
    ├─ Claude API Client
    ├─ Orchestrator V2
    └─ FileManager

Pipeline
    ├─ PipelineStage (abstract base)
    ├─ Each Specific Stage
    ├─ PipelineBuilder
    └─ EventBus (publish events)

Agents
    ├─ BaseAgent (abstract)
    ├─ EntityManager
    ├─ FileManager
    ├─ FSWriteQueue
    └─ DeepSeek API Client

Background Task Queue
    ├─ StoryGenerator (generates stories)
    ├─ DeepSeek API Client
    └─ FSWriteQueue
```

---

## COMMON OPERATIONS

### Add a New Configuration Option
1. Add to `state/automation_config.json`
2. Update `ConfigContainer` dataclass
3. Access via `config.your_new_field`

### Add Profiling to a Method
1. Add `@profile("method_name")` decorator
2. Decorator handles start/end timing
3. Results in performance report

### Add a New Event
1. Create class in `src/automation/events/automation_events.py`
2. Extend `Event` base class
3. Publish via `publish(YourEvent(...))`
4. Subscribe via `subscribe(YourEvent, handler_func)`

### Add a New Pipeline Stage
1. Create class extending `PipelineStage`
2. Implement `execute(context: PipelineContext) -> bool`
3. Update pipeline builder to include stage
4. Document in pipeline documentation

### Initialize New RP Directory
```python
from src.initialize_rp import RPInitializer
initializer = RPInitializer(Path("RPs/NewRP"))
initializer.initialize()
```

---

This documentation should provide complete reference for all supporting infrastructure and make it easier to extend the system!
