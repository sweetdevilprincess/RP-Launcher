# RP Claude Code - Project Structure Reference

**Last Updated**: 2025-10-17
**Version**: 1.1.0
**Purpose**: Complete directory tree and structure reference for the entire RP Claude Code project

---

## Quick Navigation

- [Root Level](#root-level)
- [Source Code (`src/`)](#source-code-src)
- [Configuration (`config/`)](#configuration-config)
- [Documentation (`docs/`)](#documentation-docs)
- [Roleplay Projects (`RPs/`)](#roleplay-projects-rps)
- [Setup Utilities (`setup/`)](#setup-utilities-setup)
- [Working Guides](#working-guides)
- [Key Files at Root](#key-files-at-root)

---

## Complete Directory Tree

```
RP Claude Code/
|-- src/
|   |-- automation/
|   |   |-- agents/
|   |   |   |-- background/
|   |   |   `-- immediate/
|   |   |-- config/
|   |   |-- helpers/
|   |   |-- orchestrator_v2_simplified.py
|   |   |-- agent_coordinator.py
|   |   `-- background_tasks.py
|   |-- core/
|   |   |-- base.py
|   |   |-- config.py
|   |   `-- module_manager.py
|   |-- modules/
|   |   |-- agents/
|   |   |   `-- agent_coordinator_module.py
|   |   |-- automation/
|   |   |   `-- orchestrator_module.py
|   |   |-- entities/
|   |   |   `-- entity_manager_module.py
|   |   |-- files/
|   |   |   |-- file_manager_module.py
|   |   |   `-- fs_write_queue_module.py
|   |   |-- session/
|   |   |   `-- session_manager_module.py
|   |   |-- tasks/
|   |   |   `-- background_task_queue_module.py
|   |   `-- updates/
|   |       `-- update_checker_module.py
|   |-- clients/
|   |-- utils/
|   |-- entity_manager.py
|   |-- file_manager.py
|   |-- fs_write_queue.py
|   |-- session_manager.py
|   |-- tui_bridge.py
|   `-- ...
|-- Working Guides/
|-- docs/
|-- config/
`-- RPs/
```

(node_modules/ omitted for brevity)

---

## Root Level

### Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | **PROJECT INSTRUCTIONS** - Read this first! Contains all guidelines, documentation structure, and development workflows |
| `README.md` | Project overview and getting started |
| `LICENSE` | Open source license |
| `launch_rp_tui.py` | Main entry point - launches the TUI application |
| `requirements.txt` | Python package dependencies |
| `package.json` | Node.js configuration and scripts |

---

## Source Code (`src/`)

### Main Components

#### `automation/` - Automation runtime
Drives tiered file loading, agent orchestration, prompt assembly, and background analysis cycles.

**Key files:**
- `orchestrator_v2_simplified.py` - Production orchestrator with tiered loaders and DeepSeek agent hooks
- `agent_coordinator.py` - Concurrent agent runner + cache writer
- `background_tasks.py` - Threaded queue for long-running work (entity card generation, etc.)
- `helpers/prompt_builder.py` - Prompt assembly, template wiring, and Claude thinking controls
- `agents/` - 10 DeepSeek analysis agents split into `background/` and `immediate/`

**Module integration:** `modules/automation/orchestrator_module.py`, `modules/agents/agent_coordinator_module.py`

**See:** `AGENT_DOCUMENTATION.md`, `SYSTEM_ARCHITECTURE.md`

#### `core/` + `modules/` - Module system
`core/` defines the Module API and dynamic configuration; `modules/` wraps legacy components so they can be dependency-managed.

**Key files:**
- `core/base.py` - Lifecycle contract for every module
- `core/module_manager.py` - Dependency resolution, initialization ordering, and status reporting
- `core/config.py` - Module-aware configuration loader (`state/automation_config.json`)
- `modules/**/_module.py` - Wrappers for file manager, session manager, entity manager, orchestrator, and utilities

#### `clients/` - API Clients
Integrations with different AI models.

**Key files:**
- `claude_api.py` - Claude API integration
- `claude_sdk.py` - Claude SDK wrapper
- `deepseek.py` - DeepSeek API integration

#### `rp_client_tui.py`
The Terminal User Interface (TUI) for interacting with RPs.

#### `entity_manager.py`
Manages characters, locations, items, and other entities in RPs.

#### `file_manager.py`
Handles file operations and organization.

#### `fs_write_queue.py`
Write queue system to manage file writes safely and efficiently.

---

## Configuration (`config/`)

### Structure

```
config/
├── guidelines/              # 10 markdown guidelines for story writing
├── templates/               # Entity and scene templates
│   ├── prompts/             # 11 genre-specific JSON prompt templates
│   └── [various templates]
├── config.json              # Active configuration
└── [template files]
```

### Key Templates

- **Genre prompts** (11 types):
  - `action.json`, `comedy.json`, `dark_romance.json`
  - `horror.json`, `mystery.json`, `thriller.json`
  - And 5 more combinations

- **Entity templates**:
  - `TEMPLATE_ENTITY_CHARACTER.md`
  - `TEMPLATE_ENTITY_LOCATION.md`
  - `TEMPLATE_ENTITY_ITEM.md`
  - `TEMPLATE_ENTITY_EVENT.md`

- **Story templates**:
  - `TEMPLATE_STORY_GENOME.md`
  - `TEMPLATE_ROLEPLAY_OVERVIEW.md`
  - `TEMPLATE_SCENE_NOTES.md`

---

## Documentation (`docs/`)

### Structure by Purpose

| Directory | Purpose |
|-----------|---------|
| `guides/` | How-to guides (15+ markdown files) |
| `changelogs/` | Version history and release notes |
| `reference/` | SDK docs and reference material |
| `planned_features/` | Roadmap and future features |
| `refactoring/` | Refactoring notes and plans |
| `archive/` | Deprecated/archived documentation |

### Key Documentation

- **AGENT_CACHE_FORMAT.md** - Agent caching specification
- **AUTOMATION_GUIDE.md** - How to use automation
- **QUICK_START.md** - Getting started guide
- **SYSTEM_OVERVIEW.md** - System architecture overview

---

## Roleplay Projects (`RPs/`)

### Structure

Each RP follows this template:

```
RP_NAME/
├── RP_NAME.md                      # Main story file
├── AUTHOR'S_NOTES.md               # Author notes
├── STORY_GENOME.md                 # Plot/structure
├── SCENE_NOTES.md                  # Scene tracking
├── NAMING_CONVENTIONS.md           # Naming rules
├── characters/                     # Character profiles
├── chapters/                       # Story chapters
├── entities/                       # All entities (characters, locations, items)
├── locations/                      # Location descriptions
├── memories/                       # Story memories
├── relationships/                  # Relationship tracking
├── sessions/                       # Session logs
├── exports/                        # Export formats (epub, pdf, wiki)
├── backups/                        # Story backups
├── config/                         # RP-specific configuration
└── state/                          # RP state files
    ├── automation_config.json      # Automation settings
    ├── current_state.md            # Current story state
    ├── entity_tracker.json         # Entity tracking
    ├── relationship_tracker.json   # Relationships
    ├── plot_threads_master.md      # Plot threads
    ├── knowledge_base.md           # World facts
    ├── memory_index.json           # Memory index
    ├── file_tracking.json          # File changes
    └── hook.log                    # Debug logs
```

### Current RPs

1. **Example RP** - Minimal example for reference
2. **Lilith and Silas** - Production RP (active)
3. **Lily** - RP instance
4. **RP 2** - RP instance

---

## Setup Utilities (`setup/`)

### Purpose
Pre-configured templates and scripts for quickly starting new RPs.

### Structure

```
setup/
├── templates/
│   ├── starter_packs/
│   │   ├── fantasy_adventure/     # Fantasy template
│   │   └── minimal/               # Minimal template
│   └── examples/
├── scripts/
├── guides/
└── CHECKLIST.md
```

---

## Working Guides (Documentation Hub)

**Location:** `Working Guides/` directory

**Primary Navigation:**
1. Start with: `DOCUMENTATION_INDEX.md`
2. Then read: `SYSTEM_ARCHITECTURE.md`
3. Reference: `COMPONENT_DATA_FLOW.md`

**All 13 Working Guides:**

| Document | Purpose |
|----------|---------|
| `DOCUMENTATION_INDEX.md` | Navigation hub - START HERE |
| `AGENT_DOCUMENTATION.md` | Reference for all 10 agents |
| `SYSTEM_ARCHITECTURE.md` | System design and data flow |
| `COMPONENT_DATA_FLOW.md` | Quick reference matrix |
| `SUPPORTING_COMPONENTS.md` | Infrastructure components |
| `AGENT_DEVELOPMENT_GUIDE.md` | Build new agents (5-method pattern) |
| `AUDIT_FINDINGS.md` | Codebase audit results |
| `PROMPT_TEMPLATES_GUIDE.md` | Genre template system |
| `LAUNCHER_DOCUMENTATION.md` | Launcher system |
| `TUI_BRIDGE_DOCUMENTATION.md` | TUI bridge backend |
| `ROLEPLAY_OVERVIEW_GUIDE.md` | RP overview editing |
| `RP_DIRECTORY_MAP.md` | RP file structure |
| `SETUP_FOLDER_AUDIT.md` | Setup folder analysis |

---

## Node Modules

### Main Dependencies

- **@anthropic-ai/claude-agent-sdk** - Claude Agent SDK
  - Includes ripgrep binaries (x64-win32, arm64-darwin, etc.)
  - Includes JetBrains plugin libraries

- **@img/sharp-win32-x64** - Image processing

- **zod** - TypeScript validation library

---

## State Files (Inside Each RP's `state/` directory)

### Files

| File | Purpose | Format |
|------|---------|--------|
| `automation_config.json` | Agent configuration | JSON |
| `current_state.md` | Current story state | Markdown |
| `entity_tracker.json` | Entity tracking | JSON |
| `relationship_tracker.json` | Character relationships | JSON |
| `plot_threads_master.md` | Active plot threads | Markdown |
| `knowledge_base.md` | World facts and lore | Markdown |
| `memory_index.json` | Story memories index | JSON |
| `file_tracking.json` | File change tracking | JSON |
| `response_counter.json` | Response count tracking | JSON |
| `hook.log` | Debug and operation logs | Text |
| `tui_active.flag` | TUI active indicator | Flag |
| `claude_session_active.flag` | Session indicator | Flag |

---

## How to Navigate This Structure

### "I need to understand the system"
1. Read: `Working Guides/DOCUMENTATION_INDEX.md`
2. Then: `Working Guides/SYSTEM_ARCHITECTURE.md`
3. Reference: `Working Guides/COMPONENT_DATA_FLOW.md`

### "I need to add an agent"
1. Read: `Working Guides/AGENT_DEVELOPMENT_GUIDE.md`
2. Look at examples in: `src/automation/agents/background/` or `immediate/`
3. Follow the 5-method template

### "I need to understand the RP structure"
1. Read: `Working Guides/RP_DIRECTORY_MAP.md`
2. Look at: `RPs/Example RP/` or any production RP
3. Reference: `setup/templates/`

### "I need to modify configuration"
1. Check: `config/config.json`
2. Read: `config/CLAUDE.md` or `config/README.md`
3. See templates in: `config/templates/`

### "I need to understand automation"
1. Read: `docs/guides/AUTOMATION_GUIDE.md`
2. Reference: `Working Guides/AGENT_DOCUMENTATION.md`
3. See: `src/automation/orchestrator.py`

---

## Key Principles for Working With This Structure

1. **Documentation First** - Always read CLAUDE.md at session start
2. **State Isolation** - Each RP has isolated state in its own `state/` directory
3. **Config Templates** - Always use templates, don't hand-write configs
4. **Agent Registry** - All agents must be registered in `agent_factory.py`
5. **File Tracking** - Use `FSWriteQueue` for all file writes
6. **Version Control** - Update changelogs in `docs/changelogs/` with changes

---

## Related Documentation

For more details, see:
- **Project Instructions**: `CLAUDE.md`
- **Navigation Hub**: `Working Guides/DOCUMENTATION_INDEX.md`
- **System Design**: `Working Guides/SYSTEM_ARCHITECTURE.md`
- **Data Flow Reference**: `Working Guides/COMPONENT_DATA_FLOW.md`
- **RP Structure**: `Working Guides/RP_DIRECTORY_MAP.md`

---

**Last Generated**: 2025-10-17
**Version**: 1.0.0
**Status**: Ready for linking from CLAUDE.md



