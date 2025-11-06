# File Locations Quick Reference

**Last Updated**: 2025-10-17
**Purpose**: Quick lookup for file locations across the project

---

## At a Glance

**See full structure:** @Claude Instructions/PROJECT_STRUCTURE.md

---

## Documentation Files

### Main Documentation (Working Guides/)

```
Working Guides/
├── PROJECT_STRUCTURE.md           ← Directory tree & file reference
├── DOCUMENTATION_INDEX.md         ← Navigation hub
├── AGENT_DOCUMENTATION.md         ← Agent reference
├── SYSTEM_ARCHITECTURE.md         ← System design
├── COMPONENT_DATA_FLOW.md         ← Quick reference matrix
├── SUPPORTING_COMPONENTS.md       ← Infrastructure components
├── AGENT_DEVELOPMENT_GUIDE.md     ← Build new agents
├── AUDIT_FINDINGS.md              ← Codebase audit
├── PROMPT_TEMPLATES_GUIDE.md      ← Genre templates
├── LAUNCHER_DOCUMENTATION.md      ← Launcher system
├── TUI_BRIDGE_DOCUMENTATION.md    ← TUI bridge backend
├── ROLEPLAY_OVERVIEW_GUIDE.md     ← RP editing
├── RP_DIRECTORY_MAP.md            ← RP structure
├── SETUP_FOLDER_AUDIT.md          ← Setup folder analysis
└── RP_DIRECTORY_OBSOLESCENCE_AUDIT.md ← RP audit
```

### Project Instructions (Claude Instructions/)

```
Claude Instructions/
├── CLAUDE.md                      ← Project instructions (MAIN)
├── GUIDELINES.md                  ← Critical guidelines
├── DOCUMENTATION.md               ← Documentation structure
├── WORKFLOWS.md                   ← Development workflows
├── SESSION_PROTOCOL.md            ← Working session protocol
├── FILE_REFERENCE.md              ← This file
└── PROJECT_STRUCTURE.md           ← Directory tree (also here)
```

### Version History

```
docs/changelogs/
├── CHANGELOG_2025-10-15.md
├── CHANGELOG_2025-10-16_1.0.1.md
└── CHANGELOG_2025-10-16_1.0.2.md  ← Current
```

### Additional Documentation

```
docs/
├── guides/                        ← How-to guides (15+ files)
├── reference/                     ← Reference documentation
├── planned_features/              ← Roadmap
├── refactoring/                   ← Refactoring notes
└── archive/                       ← Deprecated documentation
```

---

## Source Code Files

### Main Entry Points

```
Project Root/
├── launch_rp_tui.py               ← Main launcher script
├── package.json                   ← Node configuration
├── requirements.txt               ← Python dependencies
└── LICENSE
```

### Core Source Code (src/)

```
src/
├── automation/
│   ├── orchestrator.py            ← Main orchestrator (V1 - active)
│   ├── agent_coordinator.py       ← Agent coordination
│   ├── core.py                    ← Core automation logic
│   ├── agents/
│   │   ├── base_agent.py          ← Agent base class
│   │   ├── agent_factory.py       ← Agent registration
│   │   ├── background/            ← Background agents (6 agents)
│   │   └── immediate/             ← Immediate agents (4 agents)
│   └── [other automation modules]
│
├── clients/
│   ├── claude_api.py              ← Claude API client
│   ├── claude_sdk.py              ← Claude SDK integration
│   └── deepseek.py                ← DeepSeek API client
│
├── rp_client_tui.py               ← TUI interface
├── entity_manager.py              ← Entity management
├── file_manager.py                ← File operations
├── fs_write_queue.py              ← File write queue system
└── [other core modules]
```

### Agents by Type

**Background Agents** (run asynchronously):
```
src/automation/agents/background/
├── contradiction_detection.py
├── knowledge_extraction.py
├── memory_creation.py
├── plot_thread_detection.py
├── relationship_analysis.py
└── response_analyzer.py
```

**Immediate Agents** (run immediately):
```
src/automation/agents/immediate/
├── fact_extraction.py
├── memory_extraction.py
├── plot_thread_extraction.py
└── quick_entity_analysis.py
```

---

## Configuration Files

### Active Configuration

```
config/
├── config.json                    ← Active config
├── automation_config.json.template ← Template
└── README.md
```

### Guidelines

```
config/guidelines/                 ← Writing guidelines (10 markdown files)
├── DeepSeek_Update_Format_Guide.md
├── NPC_Interaction_Rules.md
├── POV_and_Writing_Checklist.md
├── Prose_Quality_Checklist.md
├── SESSION_INSTRUCTIONS.md
├── Story Guidelines.md
├── Writing_Style_Guide.md
└── [more guidelines]
```

### Templates

```
config/templates/
├── prompts/                       ← Genre templates (11 JSON files)
│   ├── action.json
│   ├── comedy.json
│   ├── dark_romance.json
│   ├── horror.json
│   ├── mystery.json
│   ├── thriller.json
│   └── [more genres]
├── TEMPLATE_ENTITY_CHARACTER.md
├── TEMPLATE_STORY_GENOME.md
├── TEMPLATE_ROLEPLAY_OVERVIEW.md
└── [more templates]
```

---

## Roleplay Projects

### Directory Structure

Each RP follows this structure:

```
RPs/PROJECT_NAME/
├── PROJECT_NAME.md                ← Main story file
├── STORY_GENOME.md                ← Plot/structure
├── SCENE_NOTES.md                 ← Scene tracking
├── AUTHOR'S_NOTES.md              ← Author notes
├── characters/                    ← Character profiles
├── chapters/                      ← Story chapters
├── entities/                      ← All entities
├── locations/                     ← Location descriptions
├── memories/                      ← Story memories
├── relationships/                 ← Relationships
├── sessions/                      ← Session logs
├── exports/                       ← Export formats
├── backups/                       ← Backups
├── config/                        ← RP config
└── state/                         ← RP state files
```

### Specific RPs

```
RPs/
├── config/config.json             ← RPs configuration
├── Example RP/                    ← Reference example
├── Lilith and Silas/              ← Production RP
├── Lily/                          ← RP instance
└── RP 2/                          ← RP instance
```

### State Files (Inside Each RP's state/)

```
state/
├── automation_config.json         ← Agent configuration
├── current_state.md               ← Story state
├── entity_tracker.json            ← Entity tracking
├── relationship_tracker.json      ← Relationships
├── plot_threads_master.md         ← Plot threads
├── knowledge_base.md              ← World facts
├── memory_index.json              ← Memory index
├── file_tracking.json             ← File changes
├── response_counter.json          ← Response counts
└── hook.log                       ← Debug logs
```

---

## Setup Templates

### Starter Packs

```
setup/templates/starter_packs/
├── fantasy_adventure/             ← Fantasy template
├── minimal/                       ← Minimal template
└── examples/                      ← Examples
```

---

## Dependencies

### Node Modules

```
node_modules/
├── @anthropic-ai/
│   └── claude-agent-sdk/          ← Claude Agent SDK
├── @img/
│   └── sharp-win32-x64/           ← Image processing
└── zod/                           ← Validation library
```

---

## Quick Path Lookups

### "I need to find..."

| What | Where |
|------|-------|
| Agent examples | `src/automation/agents/background/` or `immediate/` |
| Main docs | `Working Guides/` |
| Configuration | `config/` or `RPs/PROJECT/state/` |
| RP stories | `RPs/PROJECT_NAME/PROJECT_NAME.md` |
| Character files | `RPs/PROJECT_NAME/characters/` |
| State files | `RPs/PROJECT_NAME/state/` |
| Genre templates | `config/templates/prompts/` |
| Setup guides | `docs/guides/` |
| Writing guidelines | `config/guidelines/` |
| Version history | `docs/changelogs/` |

---

## Documentation by Task

### "I want to add an agent"

**Read these:**
- `Working Guides/AGENT_DEVELOPMENT_GUIDE.md`
- `Working Guides/AGENT_DOCUMENTATION.md`

**Create file in:**
- `src/automation/agents/background/` or `immediate/`

**Update these:**
- `src/automation/agents/agent_factory.py`
- `config/templates/TEMPLATE_automation_config.json`
- `Working Guides/AGENT_DOCUMENTATION.md`
- `docs/changelogs/CHANGELOG_[DATE].md`

### "I want to understand the system"

**Read these (in order):**
1. `Working Guides/PROJECT_STRUCTURE.md`
2. `Working Guides/SYSTEM_ARCHITECTURE.md`
3. `Working Guides/COMPONENT_DATA_FLOW.md`

### "I want to understand an RP"

**Read these:**
- `Working Guides/RP_DIRECTORY_MAP.md`
- `RPs/Example RP/` (structure)
- `RPs/PROJECT_NAME/PROJECT_NAME.md` (story)

### "I want to know who reads/writes what"

**Check this:**
- `Working Guides/COMPONENT_DATA_FLOW.md`

### "I need quick help on X"

**Check:**
- @Claude Instructions/DOCUMENTATION.md for doc navigation
- @Claude Instructions/WORKFLOWS.md for task workflows
- @Claude Instructions/GUIDELINES.md for standards

---

## Reference

**For detailed file structure:** @Claude Instructions/PROJECT_STRUCTURE.md

---

**Last Updated**: 2025-10-17
**Status**: Active file reference
