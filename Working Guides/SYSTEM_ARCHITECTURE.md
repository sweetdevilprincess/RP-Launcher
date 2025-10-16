# RP Claude Code - Complete System Architecture

Comprehensive documentation of all major components, their inputs, outputs, and dependencies.

---

## TABLE OF CONTENTS

1. [Core Components](#core-components)
2. [File Management System](#file-management-system)
3. [Entity Management](#entity-management)
4. [State Management](#state-management)
5. [Automation System](#automation-system)
6. [Client/API Layer](#client-api-layer)
7. [TUI System](#tui-system)
8. [Data Flow Diagrams](#data-flow-diagrams)
9. [Complete System Overview](#complete-system-overview)

---

## CORE COMPONENTS

### 1. File Manager
**Location**: `src/file_manager.py`

**Purpose**: Centralized file operations for the entire system. Handles JSON, Markdown, and directory management with consistent error handling.

**Reads From**:
- Any JSON files: `*.json`
- Any Markdown files: `*.md`
- Directory structures

**Writes To**:
- JSON files with auto-formatting
- Markdown files
- Creates directories as needed
- IPC files for TUI communication

**Key Methods**:
- `read_json()` - Read JSON with defaults
- `write_json()` - Write JSON with formatting
- `update_json()` - Merge JSON updates
- `read_markdown()` - Parse markdown files
- `list_files()` - List files by pattern
- `write_ipc_input()` - Write messages to TUI bridge
- `read_ipc_response()` - Read responses from TUI bridge

**Dependencies**:
- None (core utility)

**Used By**:
- Entity Manager
- File Change Tracker
- Orchestrators
- All other file operations

---

### 2. Filesystem Write Queue
**Location**: `src/fs_write_queue.py`

**Purpose**: Debounced file write queue that prevents excessive disk I/O. Each file has its own debounce timer.

**Reads From**:
- Files being written to (to check existing state)

**Writes To**:
- All project files (JSON, markdown, state files)

**Key Methods**:
- `write_text()` - Queue text write with debounce
- `write_json()` - Queue JSON write with debounce
- `flush()` - Force immediate write
- `shutdown()` - Graceful shutdown with final flush

**Configuration**:
- `debounce_ms` - Milliseconds to wait (default 500ms)
- Per-file independent timers

**Dependencies**:
- None (core utility)

**Used By**:
- File Change Tracker
- Background agents
- Core automation
- Any component writing files

---

### 3. File Change Tracker
**Location**: `src/file_change_tracker.py`

**Purpose**: Tracks file modification times to detect when files have been updated (especially DeepSeek-generated content). Sends notifications to Claude when changes occur.

**Reads From**:
- File modification times (filesystem)
- Previous tracking data: `state/file_changes.json`
- Modified files themselves (to notify about changes)

**Writes To**:
- Tracking file: `state/file_changes.json` (via write queue)
- Update notifications (formatted as messages)

**Key Methods**:
- `check_files_for_updates()` - Check list of files for changes
- Returns tuple: (update_notifications, updated_files)

**Usage Example**:
When entity cards, memories, or plot threads are updated externally (by DeepSeek), this tracker detects it and notifies Claude.

**Dependencies**:
- FileManager (indirect)
- FSWriteQueue (for saving tracking data)

**Used By**:
- Orchestrator V2 (to check for external changes)

---

### 4. Entity Manager
**Location**: `src/entity_manager.py`

**Purpose**: Manages entity cards (characters, locations, organizations). Loads, parses, indexes, and retrieves entity information with trigger-based lookups.

**Reads From**:
- Entity card files: `entities/*.md` (primary) or `characters/*.md` (legacy)
- File Manager for reading markdown
- DeepSeek API for entity parsing (optional)

**Writes To**:
- Internal index (in-memory EntityCard objects)
- Trigger map for fast lookups
- Files indexed by type (characters, locations, organizations)

**Key Data Structures**:
```
EntityCard:
- name: Entity name
- entity_type: CHARACTER, LOCATION, ORGANIZATION, UNKNOWN
- file_path: Path to markdown file
- triggers: Keywords that trigger this entity
- full_content: Complete markdown content
- personality_core: Extracted personality section
- metadata: Parsed metadata fields
- sections: Dict of parsed sections
```

**Key Methods**:
- `scan_and_index()` - Scan directories and parse all entities
- `get_entity()` - Retrieve entity by name
- `get_entities_by_type()` - Get all entities of a type
- `get_entity_by_trigger()` - Find entity by keyword
- `get_entity_facts()` - Extract key facts from entity card

**Dependencies**:
- FileManager (for reading markdown)
- StateTemplates (for default metadata)
- DeepSeek API (optional, for parsing)

**Used By**:
- Quick Entity Analysis agent (immediate)
- Fact Extraction agent (immediate)
- Orchestrator V2 (initialization)

---

### 5. State Templates
**Location**: `src/state_templates.py`

**Purpose**: Provides markdown templates for all state management files. Ensures consistency in state file structure.

**Reads From**:
- None (generator only)

**Writes To**:
- Templates returned as strings (caller writes to file)

**Templates Provided**:
- `plot_threads_master()` - Master plot threads file template
- `knowledge_base()` - Knowledge base template
- `story_facts()` - Story facts template
- `relationships()` - Relationships tracking template
- `current_state()` - Current state template
- etc.

**Each Template Includes**:
- Metadata section
- Instructions
- Main content area
- Statistics sections

**Dependencies**:
- None

**Used By**:
- Initialization scripts
- Orchestrator V2
- Background agents
- Manual setup processes

---

## FILE MANAGEMENT SYSTEM

**Detailed Reference:** For comprehensive information about all files in `/RPs/{RP Name}/` directories, component interactions, and file operation debugging, see [RP_DIRECTORY_MAP.md](RP_DIRECTORY_MAP.md).

### Directory Structure for Data

```
RP_PROJECT/
├── state/                          # Core state files
│   ├── response_counter.json       # Current response number
│   ├── automation_config.json      # Automation settings
│   ├── current_state.md            # Current story state
│   ├── file_changes.json           # File change tracking
│   ├── agent_analysis.json         # Agent results cache
│   ├── relationships.json          # Character relationships
│   ├── plot_threads_master.md      # All plot threads
│   ├── knowledge_base.md           # World facts
│   ├── story_facts.json            # Verified story facts
│   └── hook.log                    # Automation logs
│
├── entities/                       # Character, location, organization cards
│   ├── CharacterName.md
│   ├── LocationName.md
│   └── ...
│
├── memories/                       # Character memory banks
│   ├── CharacterName/
│   │   ├── memory_ID.md
│   │   └── ...
│   └── ...
│
├── locations/                      # Location details
│   ├── LocationName.md
│   └── ...
│
├── relationships/                  # Character preference/relationship data
│   ├── CharacterName_preferences.json
│   └── ...
│
├── CLAUDE.md                       # Project instructions (read by Claude)
├── CURRENT_STATUS.md              # Status file (updated by automation)
└── (other files)
```

### IPC Communication Files (TUI Bridge)

```
state/
├── rp_client_input.json           # Input FROM TUI TO Bridge
├── rp_client_response.json        # Response FROM Bridge TO TUI
├── rp_client_ready.flag           # Bridge ready signal
├── rp_client_done.flag            # Bridge done signal
└── tui_active.flag                # TUI active signal
```

---

## ENTITY MANAGEMENT

### Entity Cards

Entity cards are markdown files that store information about characters, locations, and organizations.

**Location**: `entities/*.md`

**Entity Card Sections** (parsed by EntityManager):
- **Name**: Entity name (filename)
- **Type**: CHARACTER, LOCATION, ORGANIZATION
- **Triggers**: Keywords that trigger this entity
- **Description**: What/who this entity is
- **Personality Core** (for characters): Core traits and values
- **Relationships**: How this entity relates to others
- **History**: Background information
- **Current Status**: Current state/location
- **Other sections**: As needed

**Example Character Card Structure**:
```markdown
---
name: Character Name
type: character
triggers:
  - trigger1
  - trigger2
---

# Character Name

## Description
Who this character is...

## Personality Core
Core traits and values...

## Relationships
- Character A: Description
- Character B: Description

## History
Background...

## Current Status
Where they are now...
```

### Memories

Character memories are stored in individual markdown files in their memory bank.

**Location**: `memories/{CharacterName}/*.md`

**Memory File Structure**:
```markdown
---
id: MEMORY-{uuid}
title: Memory Title
characters_involved:
  - CharacterName1
  - CharacterName2
location: LocationName
type: revelation|conflict|first_meeting|character_moment|relationship_development|plot_event
significance: 1-10
emotional_tone: positive|negative|neutral|mixed
when_happened: ResponseNumber or timeframe
---

# Memory Title

## Summary
Brief description of the memory...

## Key Quote
"Important quote from the scene"

## Tags
- tag1
- tag2

## Why Significant
Why this memory matters...
```

---

## STATE MANAGEMENT

### Core State Files

#### response_counter.json
Tracks the current response number.

```json
{
  "current": 42,
  "chapter": 3,
  "last_updated": "2025-10-16T12:30:00"
}
```

#### automation_config.json
Automation system configuration (loaded by core.py).

```json
{
  "agents": {
    "background": {
      "response_analyzer": {"enabled": true, "priority": 1},
      ...
    },
    "immediate": {
      "quick_entity_analysis": {"enabled": true, "timeout_seconds": 5},
      ...
    }
  },
  "fallback": {
    "use_trigger_system": true,
    "trigger_system_primary": false
  },
  "auto_story_arc": true,
  "arc_frequency": 50
}
```

#### current_state.md
Current story state (chapter, time, location, characters, situation).

```markdown
# Current Story State

**Chapter**: 3
**Response**: 42
**In-World Time**: 3:45 PM, Day 5
**Location**: The Tavern
**Characters Present**:
- Character A
- Character B

**Current Situation**:
Description of what's happening...

**Recent Events**:
- Event 1
- Event 2

**Pending Threads**:
- Thread 1
- Thread 2
```

#### relationships.json
Current relationship state between characters.

```json
{
  "CharA_CharB": {
    "tier": "friend",
    "score": 75,
    "history": [
      {"response": 10, "change": 5, "reason": "Good conversation"},
      ...
    ]
  }
}
```

#### plot_threads_master.md
Master file tracking all plot threads (see AGENT_DOCUMENTATION.md for details).

#### knowledge_base.md
World-building facts organized by category.

---

## AUTOMATION SYSTEM

### Orchestrator V2 (Modern Pipeline Architecture)
**Location**: `src/automation/orchestrator_v2.py`

**Purpose**: Modern orchestrator using pipeline architecture. Central hub coordinating all automation.

**Initialization**:
- Creates state directories
- Loads configuration
- Initializes Entity Manager
- Initializes Template Manager
- Initializes File Change Tracker
- Initializes Performance Profiler

**Key Methods**:
- `run_automation(message: str)` - Run automation with simple mode (no caching)
- `run_automation_cached()` - Run with caching enabled
- Internal methods handle:
  - Pipeline execution
  - Immediate agents (pre-response)
  - Background agents (post-response)
  - File updates
  - Performance profiling

**Reads From**:
- `state/automation_config.json` - Configuration
- `state/response_counter.json` - Current response number
- Entity cards: `entities/*.md`
- Memory files: `memories/{char}/*.md`
- Relationship data: `state/relationships.json`
- Plot threads: `state/plot_threads_master.md`
- Knowledge base: `state/knowledge_base.md`
- Agent analysis cache: `state/agent_analysis.json`

**Writes To**:
- Entity index (in-memory, IndexedEntityManager)
- Memory banks (via agents)
- Relationship updates (via agents)
- Plot thread updates (via agents)
- Knowledge base updates (via agents)
- All via write queue for debouncing

**Dependencies**:
- AutomationContext (data flow)
- ConfigContainer (configuration)
- PipelineBuilder (pipeline creation)
- EventBus (event publishing)
- EntityManager
- FileChangeTracker
- PerformanceProfiler

**Used By**:
- TUI Bridge (main integration point)
- Initialization scripts

---

### Automation Pipeline System
**Location**: `src/automation/pipeline/`

**Components**:
- `base.py` - Base stage class
- `builder.py` - Pipeline builder
- `stages.py` - All pipeline stages
- `__init__.py` - Exports

**How It Works**:
1. Pipeline is built with stages
2. Each stage processes context
3. Context passed to next stage
4. Results accumulated

**Key Pipeline Stages**:
- `LoadEntitiesStage` - Load entity cards
- `ImmediateAgentsStage` - Run immediate agents
- `ResponseStage` - Generate Claude response
- `BackgroundAgentsStage` - Run background agents
- `FileUpdateStage` - Update files with results

---

### Automation Context
**Location**: `src/automation/context/automation_context.py`

**Purpose**: Data flow container passed through pipeline. Holds all context needed for automation.

**Contains**:
```python
class AutomationContext:
    rp_dir: Path                      # RP directory
    message: str                      # User message
    response_count: int              # Current response number
    entities: IndexedEntityManager    # All entities
    agent_results: dict              # Results from agents
    response: Optional[str]          # Generated response
    timestamp: datetime              # When automation ran
    performance_metrics: dict        # Performance data
```

**Data Flow**: `Context → Stage → (modified) Context → Stage → ...`

---

### Event System
**Location**: `src/automation/events/`

**Purpose**: Decoupled event publishing for monitoring and logging.

**Event Types**:
- `ResponseGeneratedEvent` - New response generated
- `ErrorEvent` - Error occurred
- `ProfilingEvent` - Performance data
- `StatusUpdateEvent` - Status change

**EventBus**:
- Centralized event publishing
- Subscribers can listen to events
- Used for logging, monitoring, debugging

---

### Configuration Container
**Location**: `src/automation/config/config_container.py`

**Purpose**: Typed configuration management for automation settings.

**Loads From**: `state/automation_config.json`

**Provides**:
- Typed access to configuration
- Defaults if config missing
- Validation of config values

---

### Core Automation Module
**Location**: `src/automation/core.py`

**Provides**:
- `log_to_file()` - Log to hook.log
- `load_config()` - Load automation config with defaults
- `get_response_count()` - Get current response number
- `save_response_count()` - Save response counter

**These are utility functions used throughout automation.**

---

### Story Generation
**Location**: `src/automation/story_generation.py`

**Purpose**: DeepSeek API integration for story generation.

**Class**: `StoryGenerator`

**Key Methods**:
- `generate_story_arc_instructions()` - Generate story arc updates
- `generate_entity_cards()` - Generate new entity cards
- `generate_chapter_summary()` - Summarize chapter

**Reads From**:
- Story context
- Current responses
- Knowledge base

**Writes To**:
- Via DeepSeek API calls
- Results saved to appropriate files

**Dependencies**:
- DeepSeek API client
- FileManager

---

### Background Task Queue
**Location**: `src/automation/background_tasks.py`

**Purpose**: Execute long-running tasks (entity generation, etc.) without blocking main loop.

**Class**: `BackgroundTaskQueue`

**Features**:
- ThreadPoolExecutor for concurrent execution
- Automatic retry with exponential backoff
- Task persistence to prevent loss on crash
- Special handling for API rate limits (402 errors)

**Usage**:
```python
queue = BackgroundTaskQueue(max_workers=4)
queue.enqueue_task(function, *args, **kwargs)
```

**Used By**:
- Orchestrator V2 (for entity generation, story arcs, etc.)

---

## CLIENT/API LAYER

### Claude API Client
**Location**: `src/clients/claude_api.py`

**Purpose**: Direct Anthropic API client with prompt caching support for efficient RP conversations.

**Class**: `ClaudeAPIClient`

**Key Features**:
- Prompt caching for TIER_1 files
- Extended thinking modes (5 levels)
- Temperature/sampling control
- Conversation history support
- Token usage tracking

**Thinking Modes**:
- `disabled` - No extended thinking
- `think` - Quick planning (5K tokens)
- `think hard` - Feature design (10K tokens)
- `megathink` - Standard reasoning (10K tokens)
- `think harder` - Complex bugs (25K tokens)
- `ultrathink` - Maximum reasoning (31999 tokens)

**Method**: `send_message()`

**Parameters**:
- `user_message` - User's message
- `cached_context` - Static context to cache (TIER_1 files)
- `conversation_history` - Previous messages
- `max_tokens` - Max response length
- `temperature` - Sampling temperature
- `thinking_mode` - Thinking mode preset
- `thinking_budget` - Custom thinking tokens

**Returns**:
```python
{
    "content": "response text",
    "thinking": "thinking process (if available)",
    "usage": {
        "input_tokens": ...,
        "output_tokens": ...,
        "cache_creation_input_tokens": ...,
        "cache_read_input_tokens": ...
    },
    "raw_response": anthropic_response_object
}
```

**Dependencies**:
- Anthropic API (requires ANTHROPIC_API_KEY env var)

**Used By**:
- TUI Bridge
- Test scripts

---

### DeepSeek API Client
**Location**: `src/clients/deepseek.py` (referenced but not fully shown)

**Purpose**: DeepSeek API integration via OpenRouter for entity/story generation.

**Requires**:
- OPENROUTER_API_KEY environment variable

**Used For**:
- Entity card generation
- Story arc generation
- Chapter summaries
- Contradiction detection
- Other story analysis

---

## TUI SYSTEM

### RP Client TUI
**Location**: `src/rp_client_tui.py`

**Purpose**: Terminal UI for roleplay interaction. Uses Textual framework for rich terminal interface.

**Features**:
- Multi-line text input
- Real-time context display
- Quick reference overlays (Ctrl+M memory, Ctrl+A arcs, etc.)
- Response preview
- Status indicators
- File-based communication (no Claude Code cost)

**Key Components**:
- TextArea for message input
- Response display area
- Context panel (chapter, time, location)
- Status indicators

**Communication**:
- Reads user input
- Writes to: `state/rp_client_input.json`
- Reads response from: `state/rp_client_response.json`
- Uses flag files for synchronization

**Dependencies**:
- Textual framework
- Rich library for rendering

---

### TUI Bridge
**Location**: `src/tui_bridge.py`

**Purpose**: Connects TUI to Claude Code. Monitors for user input, runs automation, sends responses back.

**Flow**:
1. Monitor for input: `state/rp_client_input.json`
2. Parse user message
3. Run automation (via OrchestratorV2)
4. Generate Claude response
5. Write response: `state/rp_client_response.json`
6. Signal done

**Components**:
- Input monitoring loop
- Claude API client integration
- Automation orchestration
- IPC file management

**Key Methods**:
- `main()` - Main bridge loop
- Internal methods for:
  - Reading/writing IPC files
  - Running automation
  - Generating responses
  - Error handling

**Integration Points**:
- Reads: TUI input files
- Uses: ClaudeAPIClient
- Uses: AutomationOrchestratorV2
- Writes: Response files
- Writes: Log file

**Used By**:
- Started manually or via launcher script

---

## DATA FLOW DIAGRAMS

### Complete Request/Response Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│ USER TYPES MESSAGE IN TUI (rp_client_tui.py)                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ TUI Writes to: state/rp_client_input.json                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ TUI BRIDGE DETECTS INPUT (tui_bridge.py)                        │
│ - Reads: rp_client_input.json                                   │
│ - Creates: AutomationContext                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR V2 RUN AUTOMATION (orchestrator_v2.py)             │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ PIPELINE STAGE 1: Load & Index                          │    │
│ │ - Load entities from: entities/*.md                     │    │
│ │ - Check for file changes: state/file_changes.json       │    │
│ │ - Output: Indexed entities in context                   │    │
│ └─────────────────────────────────────────────────────────┘    │
│                     │                                            │
│                     ▼                                            │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ PIPELINE STAGE 2: Immediate Agents (Parallel)          │    │
│ │ - Quick Entity Analysis                                 │    │
│ │   Reads: Current user message, entity cards             │    │
│ │   Outputs: Tier 1/2/3 entities, relevant locations      │    │
│ │                                                         │    │
│ │ - Fact Extraction                                       │    │
│ │   Reads: Tier 2 entities, entity cards                  │    │
│ │   Outputs: Key facts for each Tier 2 entity             │    │
│ │                                                         │    │
│ │ - Memory Extraction                                     │    │
│ │   Reads: Scene participants, memory files               │    │
│ │   Outputs: 2-5 relevant memories per character          │    │
│ │                                                         │    │
│ │ - Plot Thread Extraction                                │    │
│ │   Reads: User message, plot_threads_master.md           │    │
│ │   Outputs: 2-5 relevant plot threads                    │    │
│ │                                                         │    │
│ │ Results cached: state/agent_analysis.json               │    │
│ └─────────────────────────────────────────────────────────┘    │
│                     │                                            │
│                     ▼                                            │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ PIPELINE STAGE 3: Generate Response                     │    │
│ │ - Build prompt with automation results                  │    │
│ │ - Send to Claude via API with cached context            │    │
│ │ - Store response in context                             │    │
│ └─────────────────────────────────────────────────────────┘    │
│                     │                                            │
│                     ▼                                            │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ PIPELINE STAGE 4: Background Agents (Parallel)          │    │
│ │ - Response Analyzer                                     │    │
│ │   Reads: Response, response_counter                     │    │
│ │   Writes: Scene classification, pacing, tension         │    │
│ │                                                         │    │
│ │ - Memory Creation                                       │    │
│ │   Reads: Response                                       │    │
│ │   Writes: memories/{character}/*.md                     │    │
│ │                                                         │    │
│ │ - Relationship Analysis                                 │    │
│ │   Reads: Response, relationships.json                   │    │
│ │   Writes: relationships.json (updated)                  │    │
│ │                                                         │    │
│ │ - Plot Thread Detection                                 │    │
│ │   Reads: Response, plot_threads_master.md               │    │
│ │   Writes: plot_threads_master.md (updated)              │    │
│ │                                                         │    │
│ │ - Knowledge Extraction                                  │    │
│ │   Reads: Response                                       │    │
│ │   Writes: state/knowledge_base.md (updated)             │    │
│ │                                                         │    │
│ │ - Contradiction Detection (optional)                    │    │
│ │   Reads: Response, knowledge_base.md                    │    │
│ │   Writes: Contradiction alerts                          │    │
│ │                                                         │    │
│ │ Results cached: state/agent_analysis.json               │    │
│ └─────────────────────────────────────────────────────────┘    │
│                     │                                            │
│                     ▼                                            │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ PIPELINE STAGE 5: Update Files                          │    │
│ │ - Write updated state files                             │    │
│ │ - Queue writes via FSWriteQueue (debounced)             │    │
│ │ - Increment response counter                            │    │
│ └─────────────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ TUI BRIDGE WRITES RESPONSE                                       │
│ Writes to: state/rp_client_response.json                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ TUI READS RESPONSE (rp_client_tui.py)                           │
│ - Displays response to user                                     │
│ - Updates context (chapter, time, location)                     │
│ - Ready for next message                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### File Read/Write Dependencies

```
IMMEDIATE AGENTS (Before Response)
    ↓
    ├─→ Quick Entity Analysis
    │   Reads: entities/*.md, locations/*.md
    │
    ├─→ Fact Extraction
    │   Reads: entities/*.md
    │
    ├─→ Memory Extraction
    │   Reads: memories/{char}/*.md
    │
    └─→ Plot Thread Extraction
        Reads: state/plot_threads_master.md


RESPONSE GENERATION
    ↓
    Uses cached results from immediate agents


BACKGROUND AGENTS (After Response)
    ↓
    ├─→ Response Analyzer
    │   Writes: state/agent_analysis.json
    │
    ├─→ Memory Creation
    │   Writes: memories/{char}/*.md (NEW FILES)
    │
    ├─→ Relationship Analysis
    │   Reads: state/relationships.json
    │   Writes: state/relationships.json (UPDATED)
    │
    ├─→ Plot Thread Detection
    │   Reads: state/plot_threads_master.md
    │   Writes: state/plot_threads_master.md (UPDATED)
    │
    ├─→ Knowledge Extraction
    │   Reads: state/knowledge_base.md
    │   Writes: state/knowledge_base.md (UPDATED)
    │
    └─→ Contradiction Detection (Optional)
        Reads: state/knowledge_base.md, entities/*.md


FILE WRITE QUEUE (All Writes)
    ↓
    Debounces writes by 500ms per file
    Actual write to disk happens after debounce period
```

---

### Component Dependencies Graph

```
TUI Bridge (tui_bridge.py)
    ├─→ Claude API Client (clients/claude_api.py)
    ├─→ Orchestrator V2 (orchestrator_v2.py)
    │   ├─→ Pipeline System (pipeline/)
    │   │   ├─→ Automation Context (context/automation_context.py)
    │   │   ├─→ Config Container (config/config_container.py)
    │   │   └─→ Event Bus (events/event_bus.py)
    │   ├─→ Entity Manager (entity_manager.py)
    │   │   └─→ File Manager (file_manager.py)
    │   ├─→ File Change Tracker (file_change_tracker.py)
    │   │   └─→ FSWriteQueue (fs_write_queue.py)
    │   ├─→ Performance Profiler (profiling.py)
    │   └─→ Core Automation (core.py)
    │       └─→ FSWriteQueue (fs_write_queue.py)
    │
    ├─→ File Manager (file_manager.py)
    └─→ FSWriteQueue (fs_write_queue.py)


AGENTS (automation/agents/)
    ├─→ Agent Coordinator (agent_coordinator.py)
    │   ├─→ Entity Manager (entity_manager.py)
    │   ├─→ File Manager (file_manager.py)
    │   └─→ FSWriteQueue (fs_write_queue.py)
    │
    ├─→ Agent Factory (agent_factory.py)
    │   └─→ Agent Base Class (base_agent.py)
    │
    ├─→ Each Agent (background/*.py, immediate/*.py)
    │   ├─→ File Manager
    │   ├─→ FSWriteQueue
    │   └─→ DeepSeek API (for some agents)


BACKGROUND TASKS
    ├─→ Background Task Queue (background_tasks.py)
    ├─→ Story Generator (story_generation.py)
    │   └─→ DeepSeek API Client (clients/deepseek.py)
    └─→ File Manager
```

---

## COMPLETE SYSTEM OVERVIEW

### Execution Timeline for One User Message

```
TIME    COMPONENT              ACTION
────────────────────────────────────────────────────────────────
T+0     TUI                    User types message and presses Enter
        TUI                    Writes to: state/rp_client_input.json
                              Sets: rp_client_ready.flag

T+0.1   TUI Bridge            Detects input file
        TUI Bridge            Reads: rp_client_input.json
        TUI Bridge            Creates: AutomationContext

T+0.2   Orchestrator V2       Creates Pipeline
        Pipeline              Stage 1: Load Entities
                             - Reads: entities/*.md, locations/*.md
                             - Indexes all entities
                             - Output: indexed_entities in context

T+0.3   Pipeline              Stage 2: Immediate Agents (Parallel)
        4 Agents              All run in parallel via ThreadPoolExecutor
        (5 seconds total)     - Quick Entity Analysis: 3 sec
                             - Fact Extraction: 2 sec
                             - Memory Extraction: 2 sec
                             - Plot Thread Extraction: 2 sec
                             Output: agent_results in context
                             Cached: state/agent_analysis.json

T+5.3   Pipeline              Stage 3: Generate Response
        Claude API            Build prompt with agent results
        Claude API            Send to Claude (with cached context)
        Claude API            Receive response (10-30 sec depending on length)

T+15-35 Pipeline              Stage 4: Background Agents (Parallel)
        TUI                   User sees response immediately
        (15-30 seconds)       6 agents run in background:
                             - Response Analyzer: 15 sec
                             - Memory Creation: 5 sec
                             - Relationship Analysis: 5 sec
                             - Plot Thread Detection: 5 sec
                             - Knowledge Extraction: 3 sec
                             - Contradiction Detection: 2 sec

T+30-45 Background Queue      Background tasks (if any)
        DeepSeek API          Story arc generation (if needed)
        DeepSeek API          Entity card generation (if needed)

T+45+   All                   All writes flushed from FSWriteQueue
        FSWriteQueue          Final debounce period expires
        (500ms after last)    All modified files written to disk

NEXT    TUI                   Ready for next message
```

### Data Consistency & Debouncing

To prevent file corruption and reduce disk I/O:

1. **FSWriteQueue Debouncing**:
   - Each file has independent 500ms debounce timer
   - Multiple writes to same file within 500ms = only one disk write
   - Reduces I/O from ~10-15 writes to ~5-8 writes per cycle

2. **Atomic Operations**:
   - JSON files: write to temp, rename (atomic)
   - Markdown files: full file rewrite
   - Read-modify-write done atomically

3. **File Modification Tracking**:
   - FileChangeTracker monitors modification times
   - Next cycle can detect external changes
   - Supports manual edits to files while system running

---

### Key Design Patterns

1. **Pipeline Pattern**:
   - Stage-based processing
   - Context flows through stages
   - Each stage transforms context
   - Clean separation of concerns

2. **Factory Pattern**:
   - AgentFactory creates agents
   - Registry of all agent types
   - Conditional agent creation

3. **Event Bus Pattern**:
   - Decoupled event publishing
   - Subscribers listen to events
   - Used for logging, monitoring

4. **Dependency Injection**:
   - ConfigContainer holds configuration
   - Components request what they need
   - Reduces tight coupling

5. **Write Queue Pattern**:
   - Debounced file writes
   - Per-file independent timers
   - Thread-safe operation

6. **Context Object Pattern**:
   - AutomationContext flows through pipeline
   - Contains all needed data
   - Immutable approach (create new context for each stage)

---

### Performance Optimization Strategies

1. **Prompt Caching**:
   - Large static context (TIER_1 files) cached by Claude API
   - Reused across requests
   - Reduces input token costs

2. **Selective Loading**:
   - Quick Entity Analysis classifies entities into tiers
   - Tier 1: Full card loaded
   - Tier 2: Only key facts loaded (97% token reduction)
   - Tier 3: Skipped entirely
   - Similar strategy for memories and plot threads

3. **Background Processing**:
   - Immediate agents run before response (3 sec user latency)
   - Background agents run after response (hidden 15-30 sec)
   - User sees response immediately while analysis happens

4. **Agent Parallelization**:
   - All immediate agents run in parallel
   - All background agents run in parallel
   - ThreadPoolExecutor with 4 workers
   - Near-linear scaling for multiple agents

5. **Debounced Writes**:
   - FSWriteQueue prevents excessive disk I/O
   - Per-file independent timers
   - Typically reduces writes by 40-50%

6. **Caching**:
   - Agent results cached in state/agent_analysis.json
   - Reused within same cycle
   - Prevents redundant analysis

---

### Error Handling & Resilience

1. **Agent Timeouts**:
   - Each agent has timeout (3-5 seconds)
   - Failed agents don't block pipeline
   - Partial results used (better than nothing)

2. **Fallback Systems**:
   - Trigger system available if agents fail
   - Legacy entity tracking available
   - Graceful degradation

3. **Crash Recovery**:
   - Background tasks persist to disk
   - Can resume after crash
   - Response counter saved atomically

4. **API Rate Limiting**:
   - Special handling for 402 "Low Balance" errors
   - Automatic retry with backoff
   - Background task queue manages retry

---

This architecture supports a complex multi-agent roleplay system while maintaining performance, reliability, and ease of debugging.
