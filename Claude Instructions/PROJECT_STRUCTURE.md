# RP Claude Code - Project Structure Reference

**Last Updated**: 2025-10-17
**Version**: 1.0.0
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
C:\Users\green\Desktop\RP Claude Code\
│
├── Claude Instructions/                     # Claude Code project instructions (modular)
│   ├── CLAUDE.md                            # Main project instructions
│   ├── GUIDELINES.md                        # Critical guidelines
│   ├── DOCUMENTATION.md                     # Documentation structure
│   ├── WORKFLOWS.md                         # Development workflows
│   ├── SESSION_PROTOCOL.md                  # Session protocol
│   ├── FILE_REFERENCE.md                    # File locations
│   └── PROJECT_STRUCTURE.md                 # This file
│
├── src/                                    # Main source code
│   ├── automation/                         # Automation system
│   │   ├── agents/                         # Agent implementations
│   │   │   ├── background/                 # Background agents
│   │   │   │   ├── __init__.py
│   │   │   │   ├── contradiction_detection.py
│   │   │   │   ├── knowledge_extraction.py
│   │   │   │   ├── memory_creation.py
│   │   │   │   ├── plot_thread_detection.py
│   │   │   │   ├── relationship_analysis.py
│   │   │   │   └── response_analyzer.py
│   │   │   ├── immediate/                  # Immediate agents
│   │   │   │   ├── __init__.py
│   │   │   │   ├── fact_extraction.py
│   │   │   │   ├── memory_extraction.py
│   │   │   │   ├── plot_thread_extraction.py
│   │   │   │   └── quick_entity_analysis.py
│   │   │   ├── __init__.py
│   │   │   ├── agent_factory.py             # Agent registration
│   │   │   ├── base_agent.py                # Agent base class
│   │   │   └── AGENT_DEVELOPMENT_GUIDE.md   # Agent development docs
│   │   ├── config/                          # Automation config
│   │   │   ├── __init__.py
│   │   │   └── config_container.py
│   │   ├── context/                         # Context management
│   │   │   ├── __init__.py
│   │   │   └── automation_context.py
│   │   ├── decorators/                      # Python decorators
│   │   │   ├── __init__.py
│   │   │   └── profiling.py
│   │   ├── events/                          # Event system
│   │   │   ├── __init__.py
│   │   │   ├── automation_events.py
│   │   │   └── event_bus.py
│   │   ├── helpers/                         # Helper utilities
│   │   │   ├── __init__.py
│   │   │   └── prompt_builder.py
│   │   ├── pipeline/                        # Pipeline architecture
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── builder.py
│   │   │   └── stages.py
│   │   ├── registry/                        # Component registry
│   │   │   ├── __init__.py
│   │   │   └── registry.py
│   │   ├── strategies/                      # Strategy patterns
│   │   │   ├── __init__.py
│   │   │   └── file_loading.py
│   │   ├── __init__.py
│   │   ├── agent_coordinator.py             # Agent coordination
│   │   ├── background_tasks.py              # Background task handling
│   │   ├── consistency_checklist.py         # Consistency checking
│   │   ├── core.py                          # Core automation logic
│   │   ├── file_loading.py                  # File loading strategy
│   │   ├── orchestrator.py                  # V1 orchestrator (active)
│   │   ├── orchestrator_v2.py               # V2 orchestrator (experimental)
│   │   ├── profiling.py                     # Performance profiling
│   │   ├── prompt_templates.py              # Prompt template management
│   │   ├── status.py                        # Status tracking
│   │   ├── story_generation.py              # Story generation logic
│   │   ├── time_tracking.py                 # Time tracking
│   │   └── triggers.py                      # Trigger system (fallback)
│   │
│   ├── clients/                             # API clients
│   │   ├── utils/                           # Client utilities
│   │   │   ├── __init__.py
│   │   │   └── python_fix.py
│   │   ├── __init__.py
│   │   ├── claude.py                        # Claude API client
│   │   ├── claude_api.py                    # Claude API wrapper
│   │   ├── claude_sdk.py                    # Claude SDK integration
│   │   ├── claude_sdk_bridge.mjs            # SDK bridge (JavaScript)
│   │   └── deepseek.py                      # DeepSeek API client
│   │
│   ├── trigger_system/                      # Trigger system (legacy)
│   │   ├── __init__.py
│   │   ├── trigger_system.py
│   │   └── README.md
│   │
│   ├── __init__.py
│   ├── entity_manager.py                    # Entity management
│   ├── file_change_tracker.py               # File change tracking
│   ├── file_manager.py                      # File operations
│   ├── fs_write_queue.py                    # File system write queue
│   ├── generate_preferences.py              # Preference generation
│   ├── initialize_rp.py                     # RP initialization
│   ├── rp_client_tui.py                     # TUI interface
│   ├── state_templates.py                   # State file templates
│   ├── tui_bridge.py                        # TUI bridge (active)
│   ├── tui_bridge.py.bak                    # TUI bridge backup
│   ├── tui_bridge_old.py                    # TUI bridge (legacy)
│   ├── update_checker.py                    # Update checking
│   └── version.py                           # Version information
│
├── config/                                  # Configuration files
│   ├── guidelines/                          # Writing guidelines
│   │   ├── DeepSeek_Update_Format_Guide.md
│   │   ├── NPC_Interaction_Rules.md
│   │   ├── POV_and_Writing_Checklist.md
│   │   ├── Prose_Quality_Checklist.md
│   │   ├── Session_End_Protocol.md
│   │   ├── SESSION_INSTRUCTIONS.md
│   │   ├── Story Guidelines.md
│   │   ├── Time_Tracking_Guide.md
│   │   ├── Timing.txt
│   │   └── Writing_Style_Guide.md
│   │
│   ├── templates/                           # Content templates
│   │   ├── prompts/                         # Genre prompt templates (11 JSON files)
│   │   │   ├── action.json
│   │   │   ├── comedy.json
│   │   │   ├── dark_romance.json
│   │   │   ├── dark_romance_thriller.json
│   │   │   ├── grimdark.json
│   │   │   ├── grimdark_horror.json
│   │   │   ├── horror.json
│   │   │   ├── mystery.json
│   │   │   ├── slice_of_life.json
│   │   │   ├── slice_of_life_comedy.json
│   │   │   └── thriller.json
│   │   ├── AUTOMATION_CONFIG_README.md
│   │   ├── TEMPLATE_AUTHORS_NOTES.md
│   │   ├── TEMPLATE_automation_config.json
│   │   ├── TEMPLATE_ENTITY_CHARACTER.md
│   │   ├── TEMPLATE_ENTITY_EVENT.md
│   │   ├── TEMPLATE_ENTITY_ITEM.md
│   │   ├── TEMPLATE_ENTITY_LOCATION.md
│   │   ├── TEMPLATE_ROLEPLAY_OVERVIEW.md
│   │   ├── TEMPLATE_SCENE_NOTES.md
│   │   ├── TEMPLATE_STORY_GENOME.md
│   │   └── TEMPLATE_user_memory.md
│   │
│   ├── CLAUDE.md                            # Project config docs
│   ├── config.json                          # Active configuration
│   ├── config.json.template                 # Config template
│   ├── automation_config.json.template      # Automation config template
│   ├── proxy_prompt.txt                     # Proxy mode prompt
│   └── README.md
│
├── docs/                                    # Documentation
│   ├── guides/                              # How-to guides
│   │   ├── AGENT_CACHE_FORMAT.md
│   │   ├── AGENT_CACHE_JSON_FORMAT.md
│   │   ├── AGENT_CACHE_SPEC.md
│   │   ├── AGENT_COORDINATION.md
│   │   ├── AUTOMATION_GUIDE.md
│   │   ├── FILE_LOADING_TIERS.md
│   │   ├── LAUNCHER_GUIDE.md
│   │   ├── PROMPT_CACHING_GUIDE.md
│   │   ├── PROXY_MODE_GUIDE.md
│   │   ├── QUICK_START.md
│   │   ├── README_TUI.md
│   │   ├── SYSTEM_OVERVIEW.md
│   │   ├── TAILWIND_WARM_THEMES.md
│   │   ├── TUI_THEMING_GUIDE.md
│   │   └── UPDATE_CHECKER.md
│   │
│   ├── changelogs/                          # Version history
│   │   ├── CHANGELOG_2025-10-15.md
│   │   ├── CHANGELOG_2025-10-16_1.0.1.md
│   │   └── CHANGELOG_2025-10-16_1.0.2.md
│   │
│   ├── reference/                           # Reference documentation
│   │   ├── SDK/                             # SDK documentation
│   │   │   ├── QUICKSTART_SDK.md
│   │   │   ├── README_SDK.md
│   │   │   └── SDK_SUMMARY.md
│   │   └── RP_FOLDER_STRUCTURE.md
│   │
│   ├── archive/                             # Archived documentation
│   │   ├── CONCURRENT_DEEPSEEK.md
│   │   ├── GIT_REVIEW_REPORT.md
│   │   └── RELEASE_CHECKLIST_v1.0.0.md
│   │
│   ├── planned_features/                    # Future roadmap
│   │   ├── ROADMAP.md
│   │   ├── search_and_organization.md
│   │   ├── story_continuity.md
│   │   ├── technical_improvements.md
│   │   ├── timeline_and_pacing.md
│   │   ├── version_control.md
│   │   └── WRITER_AGENT.md
│   │
│   ├── refactoring/                         # Refactoring documentation
│   │   └── REFACTORING_2025-10-14.md
│   │
│   ├── COMMUNITY_SHOWCASE_WIKI.md           # Community docs
│   ├── OBSOLESCENCE_ANALYSIS.md             # Obsolete features analysis
│   ├── THINKING_MODES.md                    # Thinking mode documentation
│   ├── WIKI_QUICK_REFERENCE.md              # Quick reference
│   ├── WIKI_SETUP_GUIDE.md                  # Setup documentation
│   └── WIKI_STRUCTURE.md                    # Documentation structure
│
├── RPs/                                     # Roleplay projects
│   ├── config/
│   │   └── config.json                      # RPs configuration
│   │
│   ├── Example RP/                          # Example RP
│   │   ├── CURRENT_STATUS.md
│   │   ├── entities/
│   │   ├── locations/
│   │   ├── memories/
│   │   ├── relationships/
│   │   ├── sessions/
│   │   └── state/                           # RP state files
│   │
│   ├── Lilith and Silas/                    # Production RP
│   │   ├── Lilith and Silas.md              # Main story file
│   │   ├── NAMING_CONVENTIONS.md
│   │   ├── Story_Genome.md
│   │   ├── Scene_Notes.md
│   │   ├── backups/                         # Story backups
│   │   ├── chapters/                        # Story chapters
│   │   ├── characters/                      # Character files
│   │   ├── config/                          # RP-specific config
│   │   ├── entities/                        # Entities (characters, locations, items)
│   │   ├── exports/                         # Export formats (epub, pdf, wiki)
│   │   ├── locations/
│   │   ├── memories/                        # Story memories
│   │   ├── relationships/                   # Relationship tracking
│   │   ├── sessions/                        # Session logs
│   │   └── state/                           # RP state files
│   │
│   ├── Lily/                                # RP instance
│   │   └── [Same structure as above]
│   │
│   └── RP 2/                                # RP instance
│       └── [Same structure as above]
│
├── setup/                                   # Setup utilities
│   ├── guides/                              # Setup guides
│   │   └── 02_CREATING_YOUR_FIRST_RP.md
│   │
│   ├── scripts/                             # Setup scripts
│   │
│   ├── templates/                           # Starter templates
│   │   ├── examples/
│   │   └── starter_packs/                   # Pre-built templates
│   │       ├── fantasy_adventure/
│   │       └── minimal/
│   │
│   ├── CHECKLIST.md                         # Setup checklist
│   ├── README.md
│   └── quick_setup.py
│
├── Working Guides/                          # Development documentation
│   ├── AGENT_DEVELOPMENT_GUIDE.md           # Agent development (5-method pattern)
│   ├── AGENT_DOCUMENTATION.md               # Agent reference (10 agents)
│   ├── AUDIT_FINDINGS.md                    # Codebase audit
│   ├── COMPONENT_DATA_FLOW.md               # Data flow matrix
│   ├── DOCUMENTATION_INDEX.md               # Navigation hub
│   ├── LAUNCHER_DOCUMENTATION.md            # Launcher system
│   ├── PROMPT_TEMPLATES_GUIDE.md            # Genre templates
│   ├── ROLEPLAY_OVERVIEW_EDITING_GUIDE.md   # RP editing
│   ├── ROLEPLAY_OVERVIEW_GUIDE.md           # RP guide
│   ├── RP_DIRECTORY_MAP.md                  # RP structure
│   ├── RP_DIRECTORY_OBSOLESCENCE_AUDIT.md   # RP audit
│   ├── SETUP_FOLDER_AUDIT.md                # Setup audit
│   ├── SUPPORTING_COMPONENTS.md             # Infrastructure
│   ├── SYSTEM_ARCHITECTURE.md               # System design
│   └── TUI_BRIDGE_DOCUMENTATION.md          # TUI bridge
│
├── node_modules/                            # Node dependencies
│   ├── @anthropic-ai/
│   │   └── claude-agent-sdk/
│   ├── @img/
│   │   └── sharp-win32-x64/
│   └── zod/                                 # Zod validation library
│
├── CLAUDE.md                                # Project instructions (in root for easy access)
├── LICENSE                                  # License file
├── README.md                                # Project README
├── launch_rp_tui.py                         # Main launcher script
├── package.json                             # Node package config
├── package-lock.json                        # Node dependencies lock
└── requirements.txt                         # Python dependencies
```

---

## Root Level

### Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | **PROJECT INSTRUCTIONS** - Master file that imports from Claude Instructions/ folder |
| `README.md` | Project overview and getting started |
| `LICENSE` | Open source license |
| `launch_rp_tui.py` | Main entry point - launches the TUI application |
| `requirements.txt` | Python package dependencies |
| `package.json` | Node.js configuration and scripts |

---

## Claude Instructions (Project Instructions Organization)

**Location**: `Claude Instructions/` folder

**Purpose**: Organized project instructions using modular documents with @import syntax

**Files:**
- `CLAUDE.md` - Main file (imports others)
- `GUIDELINES.md` - Critical guidelines
- `DOCUMENTATION.md` - Documentation structure
- `WORKFLOWS.md` - Development workflows
- `SESSION_PROTOCOL.md` - Session protocol
- `FILE_REFERENCE.md` - File locations
- `PROJECT_STRUCTURE.md` - This file

**See:** Root-level CLAUDE.md which imports from this folder

---

## Source Code (`src/`)

### Main Components

#### `automation/` - The Automation System
The heart of the system. Handles agent orchestration, story generation, and background processing.

**Key files:**
- `orchestrator.py` - Main orchestrator (active version)
- `agent_coordinator.py` - Agent coordination and scheduling
- `core.py` - Core automation logic
- `agents/` - 10 built-in agents (background and immediate)
- `pipeline/` - Pipeline architecture for processing

**See:** `AGENT_DOCUMENTATION.md`, `SYSTEM_ARCHITECTURE.md`

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
- **Project Instructions**: Claude Instructions/CLAUDE.md (or @Claude Instructions/CLAUDE.md)
- **Navigation Hub**: `Working Guides/DOCUMENTATION_INDEX.md`
- **System Design**: `Working Guides/SYSTEM_ARCHITECTURE.md`
- **Data Flow Reference**: `Working Guides/COMPONENT_DATA_FLOW.md`
- **RP Structure**: `Working Guides/RP_DIRECTORY_MAP.md`

---

**Last Generated**: 2025-10-17
**Version**: 1.0.0
**Status**: Moved to Claude Instructions folder
