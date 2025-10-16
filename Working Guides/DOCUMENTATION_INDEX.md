# RP Claude Code - Documentation Index

Master index and navigation guide for all project documentation.

---

## QUICK START

**New to the project?** Start here:
1. Read: [AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md) - Understand what agents do
2. Read: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Understand overall flow
3. Read: [COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md) - Understand what reads/writes what

**Need to add/fix something?** Go to the relevant documentation:
- Adding an agent? → [AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md)
- Modifying file operations? → [COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md)
- Understanding infrastructure? → [SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md)

---

## DOCUMENTATION FILES

### 1. AGENT_DOCUMENTATION.md
**Purpose**: Complete reference for all 10 agents and agent system behavior

**Contains**:
- **Background Agents** (6): What they do, inputs, outputs
  - Response Analyzer
  - Memory Creation
  - Relationship Analysis
  - Plot Thread Detection
  - Knowledge Extraction
  - Contradiction Detection
- **Immediate Agents** (4): What they do, inputs, outputs
  - Quick Entity Analysis
  - Fact Extraction
  - Memory Extraction
  - Plot Thread Extraction
- **Agent System Behavior**:
  - Result caching
  - Write queue integration
  - Timeout & error handling
  - Priority system
  - Configuration
  - Execution guarantees
- **Orchestration**:
  - Agent Coordinator
  - Agent Factory

**When to use**:
- Understanding what agents do
- Seeing agent data flow
- Adding new agents
- Configuring agent behavior
- Understanding caching
- Debugging agent issues

**Key sections**:
- Quick reference table of all agents
- Detailed agent breakdown
- Integration notes for developers

---

### 2. SYSTEM_ARCHITECTURE.md
**Purpose**: Complete system design and architecture documentation

**Contains**:
- **Core Components**: FileManager, FSWriteQueue, FileChangeTracker, EntityManager, StateTemplates
- **File Management System**: Directory structure, state files, IPC communication
- **Entity Management**: Entity cards, memories, locations, relationships
- **State Management**: All state files and their purposes
- **Automation System**: Orchestrator V2, Pipeline, Context, Events, Configuration
- **Client/API Layer**: Claude API, DeepSeek API
- **TUI System**: Terminal UI, TUI Bridge
- **Complete Request/Response Cycle**: Detailed timeline with specific file operations
- **Data Flow Diagrams**: Visual representations
- **Performance Optimization Strategies**: Caching, selective loading, parallelization, debouncing
- **Error Handling & Resilience**: How system recovers from failures
- **Design Patterns**: Pipeline, Factory, Event Bus, Dependency Injection, Write Queue, Context Object
- **Key Design Patterns**: Used throughout the system

**When to use**:
- Understanding overall system design
- Seeing complete request/response flow
- Understanding why things are designed certain ways
- Performance considerations
- Error handling strategies
- Design pattern examples

**Key sections**:
- 400+ lines of comprehensive documentation
- Complete execution timeline
- Visual data flow diagrams
- Component dependency graph
- Performance optimization details

---

### 3. COMPONENT_DATA_FLOW.md
**Purpose**: Quick reference for what components read and write

**Contains**:
- **Quick Reference Table**: All components at a glance
- **State Files Matrix**: Who reads/writes each state file
- **Entity System Matrix**: Who reads/writes entity files
- **IPC Files**: TUI communication format
- **Agent System**: Complete immediate and background agent data flow
- **Pipeline Stages**: Each stage and operations
- **Write Queue Behavior**: Debouncing explanation
- **Modification Checklist**: When modifying components
- **Debugging Tips**: Common issues and solutions
- **Data Modification Patterns**: How to properly add/update data
- **Performance Notes**: Bottlenecks and optimization opportunities
- **Key Files Reference**: Quick lookup table

**When to use**:
- Quickly finding what reads/writes a file
- Debugging why something isn't updating
- Planning modifications
- Understanding dependencies
- Quick lookup without reading full docs

**Key sections**:
- One-page reference tables
- "Who reads/writes what" matrix
- Component modification checklist
- Debugging guide

---

### 4. SUPPORTING_COMPONENTS.md
**Purpose**: Reference for all non-agent infrastructure components

**Contains**:
- **API Clients**: DeepSeek, Claude API, Claude SDK
- **Configuration System**: ConfigContainer, typed configuration
- **Context & Data Flow**: AutomationContext, context propagation
- **Event System**: EventBus, event types
- **Pipeline Architecture**: PipelineStage, builder, stages
- **Prompt Building**: PromptBuilder, PromptTemplateManager
- **Performance & Profiling**: PerformanceProfiler, @profile decorator
- **Initialization & Setup**: RPInitializer
- **Strategies & Helpers**: File loading, consistency checklist
- **Fallback System**: Trigger system
- **Integration Points**: How components work together
- **Component Dependencies**: Complete dependency graph
- **Common Operations**: How to do common tasks

**When to use**:
- Understanding infrastructure components
- Adding new configuration options
- Understanding event system
- Working with pipelines
- Performance profiling
- Setting up new RP
- Understanding fallback systems

**Key sections**:
- API client references
- Configuration management
- Event system details
- Pipeline architecture
- Common operations guide

---

### 5. AGENT_DEVELOPMENT_GUIDE.md
**Purpose**: Step-by-step guide for building and integrating agents

**Contains**:
- Agent architecture overview
- The 5-method pattern (required template)
- BaseAgent class reference
- JSON output schemas for all agent types
- Step-by-step: Create a new agent (7 steps)
- Complete integration checklist
- Real code examples from 3 production agents
- Quick reference template (copy-paste ready)
- 7 common patterns with code snippets
- Debugging and testing guide
- Performance tips

**When to use**:
- Creating a new agent
- Understanding agent patterns
- Debugging agent issues
- Seeing code examples
- Following checklist for integration

**Key sections**:
- The 5-method pattern (required for all)
- JSON schemas for every agent type
- Step-by-step creation process
- Copy-paste template

---

### 6. AUDIT_FINDINGS.md
**Purpose**: Codebase health report and findings from comprehensive audit

**Contains**:
- Executive summary of codebase health (95% active)
- Orchestrator V1 vs V2 analysis
- Backup files identified
- Legacy configuration code
- Missing/removed modules verification
- Export consistency verification
- Priority 1-3 recommendations (effort estimates)
- Version decision matrix
- Testing recommendations

**When to use**:
- Understanding codebase health
- Planning cleanup work
- Making architectural decisions (V1 vs V2)
- Understanding legacy issues

**Key sections**:
- Cleanup recommendations
- Decision matrix for Orchestrator
- Known issues and status

---

### 7. PROMPT_TEMPLATES_GUIDE.md
**Purpose**: Complete reference for genre-specific narrative templates system

**Contains**:
- 11 built-in genre templates (action, thriller, etc.)
- JSON template structure breakdown
- 4 configuration modes (auto, composite, modular, layered)
- How the template injection system works
- How to create new templates
- How to create combination templates
- Debugging and troubleshooting
- Integration with automation system
- Best practices

**When to use**:
- Customizing writing style for your RP
- Understanding genre guidance system
- Creating new genre templates
- Debugging template loading issues
- Setting up ROLEPLAY_OVERVIEW.md

**Key sections**:
- All 11 genres explained
- JSON structure
- 4 configuration modes with examples
- How to create and test templates

---

### 8. RP_DIRECTORY_MAP.md
**Purpose**: Comprehensive reference for all files in `/RPs/{RP Name}/` directories and component interactions

**Contains**:
- **Complete Directory Structure**: All folders and their purposes
- **State Directory Reference**: All 22 state files with read/write information
- **Component File Operations**: Detailed breakdown of what each component reads and writes
- **Interaction Patterns**: IPC communication, tiered loading, migration patterns
- **Special Directories**: Entity system, relationships, memories, chapters
- **Initialization & Setup**: Complete RP setup process
- **Component Interaction Flow**: Full message processing flow diagram
- **Debugging Guide**: Common issues and inspection commands
- **Summary Tables**: Quick reference for who reads/writes what

**When to use**:
- Understanding where RP files are stored
- Debugging file read/write issues
- Understanding data flow for RP directories
- Finding which components interact with specific files
- Setting up new RP directory structures
- Tracing file operations during development

**Key sections**:
- Complete state files matrix with line references
- File reads/writes by component
- IPC communication patterns
- Directory structure reference
- Debugging checklist

---

### 9. LAUNCHER_DOCUMENTATION.md (NEW)
**Purpose**: Complete reference for the RP Launcher system (`launch_rp_tui.py`)

**Contains**:
- **Architecture**: Three-process system (Launcher → Bridge → TUI)
- **Quick Start**: How to launch RPs with examples
- **Detailed Usage**: Each component explained (Launcher, Bridge, TUI)
- **F-Key Commands**: All 10 F-keys with detailed explanations
  - F1: Help
  - F2: Character Sheet + Memory
  - F3: Story Overview (Arc + Genome)
  - F4: Entities
  - F5: Scene Notes
  - F6: Module Toggles
  - F7: Status
  - F8: Settings
  - F10: Restart Bridge
- **Features**: Python management, process cleanup, update checking
- **Configuration**: Launcher settings and RP automation config
- **Troubleshooting**: Common issues and solutions
- **Advanced Usage**: Debug mode, development workflows
- **Process Communication**: IPC via JSON files explained

**When to use**:
- Learning how to use the launcher
- Understanding what each F-key does
- Configuring launcher settings
- Debugging launcher issues
- Troubleshooting frozen TUI or bridge problems
- Understanding how launcher processes work
- Developing custom features

**Key sections**:
- Complete F-key reference (10 keys documented)
- Process architecture diagrams
- Keyboard shortcuts
- Configuration options
- Troubleshooting guide
- Process communication details

---

### 10. TUI_BRIDGE_DOCUMENTATION.md (NEW)
**Purpose**: Complete reference for the TUI Bridge backend system (`tui_bridge.py`)

**Contains**:
- **Architecture**: Bridge process and three-process system
- **Operating Modes**:
  - SDK Mode (default, no API key needed)
  - API Mode (direct Anthropic API with key)
  - Mode selection logic and fallback behavior
- **Initialization & Configuration**: Startup sequence, config files
- **Message Processing Flow**: Complete request-response cycle with timing
- **SDK Mode Details**: Node.js bridge, streaming, architecture
- **API Mode Details**: Direct API calls, HTTP communication
- **Prompt Caching**: How both modes implement caching (50-90% savings)
- **Extended Thinking**: 6 thinking modes and configuration
- **Background Automation**: Non-blocking agent processing
- **IPC Communication**: File-based inter-process communication
- **Session Management**: Continuous vs fresh sessions
- **Error Handling**: Error scenarios and recovery
- **Configuration**: Global and per-RP settings

**When to use**:
- Understanding how the bridge backend works
- Choosing between SDK and API mode
- Configuring API key for API mode
- Understanding prompt caching benefits
- Configuring extended thinking modes
- Debugging bridge issues
- Understanding background automation
- Setting up per-RP configurations

**Key sections**:
- SDK vs API mode comparison
- Complete message processing flow
- Prompt caching explanation and benefits
- Error handling and recovery
- IPC communication protocol
- Session management
- Configuration reference

---

## NAVIGATION BY TASK

### I want to...

#### Understand the System
1. Read: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Complete design
2. Reference: [COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md) - Quick lookup
3. Deep dive: [SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md) - Infrastructure details

#### Add a New Agent
1. Reference: [AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md) - Agent requirements
2. Reference: [SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md) - Agent system
3. Steps:
   - Create file in `src/automation/agents/background/` or `immediate/`
   - Extend BaseAgent
   - Register in AgentFactory.registry
   - Add to automation_config.json
   - Update AGENT_DOCUMENTATION.md

#### Fix File Read/Write Issues
1. Reference: [RP_DIRECTORY_MAP.md](RP_DIRECTORY_MAP.md) - File interaction details (RP-specific)
2. Reference: [COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md) - Who reads/writes what
3. Check: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md#complete-request-response-cycle) - Data flow
4. Steps:
   - Find which component should update the file
   - Check if using FSWriteQueue
   - Check if file permissions correct
   - Check if state directory exists
   - Trace through COMPONENT_DATA_FLOW matrix
   - Use RP_DIRECTORY_MAP debugging guide for RP-specific issues

#### Modify Configuration
1. Reference: [SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md#configuration-system) - ConfigContainer
2. Steps:
   - Add to state/automation_config.json
   - Update ConfigContainer dataclass
   - Access via config.your_field
   - Document the change

#### Add Performance Profiling
1. Reference: [SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md#performance--profiling) - Profiling guide
2. Steps:
   - Add `@profile("operation_name")` decorator
   - Or use `with profiler.measure("operation_name"):`
   - Call profiler.report() to see results

#### Debug Entity/Memory/Thread Issues
1. Reference: [AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md) - Which agent handles what
2. Reference: [COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md#debugging-tips) - Debugging guide
3. Check: `state/agent_analysis.json` - Agent results cache
4. Check: `state/hook.log` - Debug logs

#### Understand Request/Response Flow
1. Read: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md#complete-request-response-cycle) - Timeline
2. Reference: [COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md#complete-request-response-cycle) - Data flow

#### Add Event Handling
1. Reference: [SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md#event-system) - Event system
2. Steps:
   - Create event class in automation_events.py
   - Extend Event base class
   - Publish via `publish(YourEvent(...))`
   - Subscribe via `subscribe(YourEvent, handler_func)`

#### Initialize New RP
1. Reference: [SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md#rp-initializer) - RPInitializer
2. Code:
   ```python
   from src.initialize_rp import RPInitializer
   initializer = RPInitializer(Path("RPs/NewRP"))
   initializer.initialize()
   ```

---

## FILE ORGANIZATION REFERENCE

### Documentation Files (Project Root)
```
RP_PROJECT/
├── CLAUDE.md                           ← THIS FILE
├── Working Guides
│	├── DOCUMENTATION_INDEX.md          ← You are here (navigation hub)
│	├── AGENT_DOCUMENTATION.md          ← Agent reference
│	├── SYSTEM_ARCHITECTURE.md          ← Complete design
│	├── COMPONENT_DATA_FLOW.md          ← Quick reference
│	├── SUPPORTING_COMPONENTS.md        ← Infrastructure
│	├── AGENT_DEVELOPMENT_GUIDE.md      ← Build agents
│	├── AUDIT_FINDINGS.md               ← Codebase health
│	├── PROMPT_TEMPLATES_GUIDE.md       ← Genre templates
│	├── RP_DIRECTORY_MAP.md             ← RP file interactions
└── CHANGELOG_2025_10_16_1.0.1.md   ← Version history
```

### Source Code Files
```
src/
├── file_manager.py                 ← File operations
├── fs_write_queue.py              ← Debounced writes
├── file_change_tracker.py         ← Change detection
├── entity_manager.py              ← Entity management
├── state_templates.py             ← State templates
├── tui_bridge.py                  ← TUI integration
├── rp_client_tui.py              ← Terminal UI
├── initialize_rp.py               ← RP setup
│
├── clients/
│   ├── claude_api.py             ← Claude API client
│   ├── claude_sdk.py             ← SDK client (legacy)
│   └── deepseek.py               ← DeepSeek API client
│
└── automation/
    ├── orchestrator_v2.py        ← Main orchestrator
    ├── core.py                   ← Core utilities
    ├── story_generation.py       ← Story generation
    ├── background_tasks.py       ← Background jobs
    ├── consistency_checklist.py  ← Consistency checks
    ├── profiling.py              ← Performance tracking
    ├── prompt_templates.py       ← Template manager
    ├── time_tracking.py          ← Time tracking
    ├── triggers.py               ← Trigger system
    │
    ├── agent_coordinator.py      ← Agent orchestration
    ├── agents/
    │   ├── agent_factory.py
    │   ├── base_agent.py
    │   ├── background/           ← Background agents
    │   └── immediate/            ← Immediate agents
    │
    ├── pipeline/
    │   ├── base.py              ← Pipeline base classes
    │   ├── builder.py           ← Pipeline builder
    │   ├── stages.py            ← Pipeline stages
    │   └── __init__.py
    │
    ├── context/
    │   ├── automation_context.py ← Context classes
    │   └── __init__.py
    │
    ├── events/
    │   ├── automation_events.py ← Event types
    │   ├── event_bus.py         ← Event bus
    │   └── __init__.py
    │
    ├── config/
    │   ├── config_container.py  ← Configuration
    │   └── __init__.py
    │
    ├── decorators/
    │   ├── profiling.py         ← @profile decorator
    │   └── __init__.py
    │
    ├── helpers/
    │   ├── prompt_builder.py    ← Prompt building
    │   └── __init__.py
    │
    ├── strategies/
    │   └── file_loading.py      ← File loading strategy
    │
    └── registry/
        └── registry.py           ← Component registry
```

### State Files
```
state/
├── response_counter.json          ← Response count
├── automation_config.json         ← Agent configuration
├── current_state.md              ← Current story state
├── relationships.json            ← Character relationships
├── plot_threads_master.md        ← Plot threads
├── knowledge_base.md             ← World facts
├── agent_analysis.json           ← Agent results cache
├── file_changes.json             ← File change tracking
├── hook.log                      ← Debug logs
├── rp_client_input.json          ← TUI input
├── rp_client_response.json       ← TUI response
├── rp_client_ready.flag          ← Sync flag
├── rp_client_done.flag           ← Sync flag
└── tui_active.flag               ← Sync flag
```

### Changelogs
```
docs/changelogs
├── CHANGELOG_2025-10-16_1.0.1.md       ← Current changelog
```

---

## CROSS-REFERENCES

### Components by Category

**File Operations**:
- FileManager - `src/file_manager.py`
- FSWriteQueue - `src/fs_write_queue.py`
- FileChangeTracker - `src/file_change_tracker.py`
- See: COMPONENT_DATA_FLOW.md

**Entity Management**:
- EntityManager - `src/entity_manager.py`
- Entity files - `entities/*.md`
- See: SYSTEM_ARCHITECTURE.md#entity-management

**State Management**:
- StateTemplates - `src/state_templates.py`
- State files - `state/*.json`, `state/*.md`
- See: SYSTEM_ARCHITECTURE.md#state-management

**Agents**:
- Background agents - `src/automation/agents/background/`
- Immediate agents - `src/automation/agents/immediate/`
- AgentCoordinator - `src/automation/agent_coordinator.py`
- AgentFactory - `src/automation/agents/agent_factory.py`
- See: AGENT_DOCUMENTATION.md

**Automation**:
- OrchestratorV2 - `src/automation/orchestrator_v2.py`
- Pipeline - `src/automation/pipeline/`
- ConfigContainer - `src/automation/config/config_container.py`
- See: SUPPORTING_COMPONENTS.md

**API & Clients**:
- Claude API - `src/clients/claude_api.py`
- DeepSeek API - `src/clients/deepseek.py`
- See: SUPPORTING_COMPONENTS.md#api-clients

**UI**:
- TUI Bridge - `src/tui_bridge.py`
- TUI Client - `src/rp_client_tui.py`
- See: SYSTEM_ARCHITECTURE.md#tui-system

---

## DOCUMENTATION CONVENTIONS

### Icons Used
- 📋 **Reference**: Look here for detailed reference
- ⚡ **Quick**: Quick reference / fast lookup
- 🔧 **How-to**: Step-by-step instructions
- ⚠️ **Warning**: Important gotcha or limitation
- 💡 **Tip**: Helpful suggestion
- 🔗 **Link**: Cross-reference to another section

### Format Conventions
- `code` - File paths, class names, method names
- **Bold** - Important concepts
- > Quote - Configuration examples
- Code blocks - Code examples

### Sections in Each Doc
1. **Purpose** - Why this exists
2. **Location** - Where to find it
3. **Key Methods/Functions** - What it does
4. **Inputs/Outputs** - Data flow
5. **Configuration** - How to configure
6. **Usage** - Code examples
7. **Dependencies** - What it needs
8. **Used By** - What uses this component

---

## MAINTENANCE & UPDATES

### When to Update Documentation

- **Added a new agent**: Update AGENT_DOCUMENTATION.md
- **Modified agent behavior**: Update AGENT_DOCUMENTATION.md and SYSTEM_ARCHITECTURE.md
- **Added new state file**: Update SYSTEM_ARCHITECTURE.md and COMPONENT_DATA_FLOW.md
- **Added new component**: Update SUPPORTING_COMPONENTS.md
- **Changed data flow**: Update COMPONENT_DATA_FLOW.md and SYSTEM_ARCHITECTURE.md
- **Added configuration option**: Update SUPPORTING_COMPONENTS.md#configuration-system
- **Added new event type**: Update SUPPORTING_COMPONENTS.md#event-system

### Documentation Standards

Each component should have:
1. **Clear Purpose** - What problem does it solve?
2. **File Location** - Where is it in the project?
3. **Key Methods/Classes** - What are the public APIs?
4. **Inputs** - What data does it read?
5. **Outputs** - What data does it write?
6. **Usage Examples** - How to use it?
7. **Dependencies** - What else does it need?
8. **Who Uses It** - What components depend on it?

---

## QUICK LOOKUP TABLE

| Need to find... | Check... |
|-----------------|----------|
| What an agent does | AGENT_DOCUMENTATION.md |
| How to add an agent | AGENT_DEVELOPMENT_GUIDE.md (complete guide) |
| Agent development template | AGENT_DEVELOPMENT_GUIDE.md#quick-reference-template |
| Request/response flow | SYSTEM_ARCHITECTURE.md#complete-request-response-cycle |
| Who reads/writes a file | COMPONENT_DATA_FLOW.md |
| RP file structure and interactions | RP_DIRECTORY_MAP.md |
| What components interact with RP directories | RP_DIRECTORY_MAP.md#files-read-by-components |
| RP state files reference | RP_DIRECTORY_MAP.md#state-directory-files |
| IPC communication pattern | RP_DIRECTORY_MAP.md#interaction-patterns |
| State file purposes | SYSTEM_ARCHITECTURE.md#state-management |
| Configuration options | SUPPORTING_COMPONENTS.md#configuration-system |
| Event system | SUPPORTING_COMPONENTS.md#event-system |
| Pipeline architecture | SUPPORTING_COMPONENTS.md#pipeline-architecture |
| API clients | SUPPORTING_COMPONENTS.md#api-clients |
| Performance profiling | SUPPORTING_COMPONENTS.md#performance--profiling |
| File operations | COMPONENT_DATA_FLOW.md |
| Debugging tips | COMPONENT_DATA_FLOW.md#debugging-tips |
| Directory structure | SYSTEM_ARCHITECTURE.md#file-management-system |
| Design patterns | SYSTEM_ARCHITECTURE.md#key-design-patterns |
| Genre-specific writing guidance | PROMPT_TEMPLATES_GUIDE.md |
| 11 available genre templates | PROMPT_TEMPLATES_GUIDE.md#available-genres |
| Setting up templates for RP | PROMPT_TEMPLATES_GUIDE.md#how-to-use |
| Creating custom templates | PROMPT_TEMPLATES_GUIDE.md#creating-a-new-template |
| Codebase health status | AUDIT_FINDINGS.md |
| Cleanup recommendations | AUDIT_FINDINGS.md#recommendations |
| How to use the launcher | LAUNCHER_DOCUMENTATION.md |
| What each F-key does | LAUNCHER_DOCUMENTATION.md#f-key-commands |
| Launcher troubleshooting | LAUNCHER_DOCUMENTATION.md#troubleshooting |
| Launcher architecture | LAUNCHER_DOCUMENTATION.md#architecture |
| Launcher configuration | LAUNCHER_DOCUMENTATION.md#configuration |
| How the bridge works | TUI_BRIDGE_DOCUMENTATION.md |
| SDK mode vs API mode | TUI_BRIDGE_DOCUMENTATION.md#operating-modes |
| Prompt caching and benefits | TUI_BRIDGE_DOCUMENTATION.md#prompt-caching |
| Extended thinking modes | TUI_BRIDGE_DOCUMENTATION.md#extended-thinking |
| Bridge configuration | TUI_BRIDGE_DOCUMENTATION.md#configuration |
| Message processing flow | TUI_BRIDGE_DOCUMENTATION.md#message-processing-flow |

---

## FEEDBACK & IMPROVEMENTS

This documentation is meant to make the project easier to work with. If:
- Something is unclear
- A section is missing
- A code example doesn't work
- Documentation is out of date

**Please update the relevant documentation file** to keep it accurate and helpful for future development!

---

**Last Updated**: 2025-10-16
**Version**: 1.0
**Status**: Complete initial documentation set
