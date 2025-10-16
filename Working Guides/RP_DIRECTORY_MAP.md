# RP Directory Map

**Complete Reference for `/RPs/{RP Name}/` Directory Structure and File Interactions**

This document provides a detailed, comprehensive map of all files, directories, and components that read from and write to the RP project directories. Use this as a reference when understanding data flow and debugging file operations.

---

## Quick Navigation

- [Directory Structure](#directory-structure)
- [State Directory Files](#state-directory-files)
- [Files Read By Components](#files-read-by-components)
- [Files Written By Components](#files-written-by-components)
- [Interaction Patterns](#interaction-patterns)
- [Special Directories](#special-directories)
- [Initialization & Setup](#initialization--setup)
- [Component Interaction Flow](#component-interaction-flow)
- [Debugging Guide](#debugging-guide)

---

## Directory Structure

### Root RP Directory

```
/RPs/
├── config/                          # Shared configuration
│   └── config.json                  # Global RP configuration
│
└── {RP Name}/                       # Individual RP projects
    ├── chapters/                    # Story chapters (read by FileLoader, StoryGenerator)
    │   ├── chapter_001.md
    │   ├── chapter_002.txt
    │   └── ...
    │
    ├── characters/                  # Character sheets (legacy support)
    │   ├── {{user}}.md             # Player character (read by FileLoader TIER_1)
    │   └── {char_name}.md          # NPCs (optional legacy format)
    │
    ├── entities/                    # Entity cards (PRIMARY LOCATION)
    │   ├── [CHAR] Name.md          # Characters (managed by EntityManager)
    │   ├── [LOC] Name.md           # Locations
    │   ├── [ORG] Name.md           # Organizations
    │   └── ...
    │
    ├── locations/                   # Location files (optional)
    │   └── {location}.md
    │
    ├── memories/                    # Character memories (written by MemoryCreationAgent)
    │   ├── character_name_memories.md
    │   └── ...
    │
    ├── relationships/               # Relationship preference files (written by EntityManager)
    │   ├── character_name_preferences.json
    │   └── ...
    │
    ├── sessions/                    # Session logs and history
    ├── backups/                     # Backup files
    ├── config/                      # Per-RP configuration
    ├── exports/                     # Generated exports
    │   ├── wiki/
    │   ├── epub/
    │   └── pdf/
    │
    ├── state/                       # CRITICAL STATE FILES (see below)
    │   └── [All state management files]
    │
    ├── {RP Name}.md                 # RP metadata file
    ├── AUTHOR'S_NOTES.md            # Author guidelines (read by FileLoader TIER_1)
    ├── STORY_GENOME.md              # Plot skeleton (read by FileLoader TIER_1)
    ├── NAMING_CONVENTIONS.md        # Naming rules (read by FileLoader TIER_1)
    ├── SCENE_NOTES.md               # Scene descriptions (read by FileLoader TIER_1)
    └── CURRENT_STATUS.md            # Current RP status
```

---

## State Directory Files

### Location
`/RPs/{RP Name}/state/`

### Complete State Files Reference

| File Name | Type | Purpose | Read By | Written By | Line Reference | Created By |
|-----------|------|---------|---------|-----------|-----------------|-----------|
| **response_counter.json** | JSON | Current response number counter | `automation/core.py` | `file_manager.py:354-374` | Line 354-374 | `initialize_rp.py:112` |
| **response_counter.txt** | TEXT | Legacy counter format (auto-deleted after migration) | `automation/core.py` | `fs_write_queue.py` | `file_manager.py:340-348` | Legacy |
| **current_state.md** | Markdown | Current RP story position | `file_loading.py` (TIER_1) | Manual / Claude | `automation/file_loading.py:66` | `initialize_rp.py:107` |
| **story_arc.md** | Markdown | Generated story arc summary | `file_loading.py` (TIER_1) | `story_generation.py:142` | `automation/story_generation.py:22` | `initialize_rp.py:107` |
| **automation_config.json** | JSON | Automation system settings & agent config | `automation/core.py` | `initialize_rp.py:111` | `initialize_rp.py:111` | `initialize_rp.py:111` |
| **entity_tracker.json** | JSON | Index of all entities in RP | Agent system | `initialize_rp.py:108` | `initialize_rp.py:108` | `initialize_rp.py:108` |
| **relationship_tracker.json** | JSON | Index of relationship files | Agent system | `initialize_rp.py:109` | `initialize_rp.py:109` | `initialize_rp.py:109` |
| **memory_index.json** | JSON | Index of memory files | Agent system | `initialize_rp.py:110` | `initialize_rp.py:110` | `initialize_rp.py:110` |
| **file_tracking.json** | JSON | File change tracking for optimization | `file_change_tracker.py` | `file_change_tracker.py` | `file_change_tracker.py:~190` | `initialize_rp.py:112` |
| **plot_threads_master.md** | Markdown | Active plot threads | Background agents | Background agents | `state_templates.py:16-75` | `initialize_rp.py:104` |
| **plot_threads_archive.md** | Markdown | Resolved/concluded plot threads | Background agents | Background agents | `state_templates.py:template` | `initialize_rp.py:105` |
| **knowledge_base.md** | Markdown | World knowledge and facts extracted | Background agents | `knowledge_extraction.py` | `state_templates.py:78+` | `initialize_rp.py:106` |
| **hook.log** | TEXT | Execution logs and debugging output | Monitoring / Debugging | `automation/core.py:24-36` | `automation/core.py:log_to_file` | `initialize_rp.py` |
| **rp_client_input.json** | JSON | TUI input message (IPC) | `tui_bridge.py:197` | `file_manager.py:100-120` | `file_manager.py:100-120` | TUI (`rp_client_tui.py`) |
| **rp_client_response.json** | JSON | Claude response output (IPC) | `rp_client_tui.py` | `file_manager.py:157-187` | `file_manager.py:157-187` | `tui_bridge.py:231` |
| **rp_client_ready.flag** | FLAG | Signal that bridge is ready for input | `rp_client_tui.py` | `tui_bridge.py` | `tui_bridge.py` | Bridge startup |
| **rp_client_done.flag** | FLAG | Signal that response is complete | `rp_client_tui.py` | `tui_bridge.py:232` | `tui_bridge.py:232` | After response |
| **session_triggers.json** | JSON | Active characters/triggers for session | `tui_bridge.py` | `file_manager.py:290-310` | `file_manager.py:290-310` | Session initialization |
| **session_triggers.txt** | TEXT | Legacy trigger format (auto-deleted) | `tui_bridge.py` | `fs_write_queue.py` | Legacy | Legacy |
| **claude_session_active.flag** | FLAG | Claude session is active marker | `tui_bridge.py` | `tui_bridge.py:205-209` | `tui_bridge.py:205-209` | Session start |
| **tui_active.flag** | FLAG | TUI process is running | `launch_rp_tui.py` | `launch_rp_tui.py:195-218` | `launch_rp_tui.py:195-218` | TUI startup |
| **agent_analysis.md** | Markdown | Agent analysis cache and results | `agent_coordinator.py` | `agent_coordinator.py` | `tui_bridge.py:221` | Agents (background) |

**Total State Files: 22 (including legacy)**

---

## Files Read By Components

### FileManager (`src/file_manager.py`)

**Purpose:** Central file I/O handler for all RP operations

**Reads:**

| File Pattern | Method | Lines | Purpose |
|-------------|--------|-------|---------|
| `{rp_dir}/**/*.json` | `read_json()` | 34-56 | Load JSON state files |
| `{rp_dir}/**/*.md` | `read_markdown()` | 393-412 | Load markdown files |
| `state/rp_client_input.json` | `read_ipc_input()` | 122-156 | Get user message from TUI |
| `state/rp_client_response.json` | `read_ipc_response()` | 189-222 | Read response status |
| `state/session_triggers.json` | `read_session_triggers()` | 226-288 | Load active characters |

**Writes:**

| File Pattern | Method | Lines | Purpose |
|-------------|--------|-------|---------|
| `{rp_dir}/**/*.json` | `write_json()` | 58-74 | Save JSON state files |
| `{rp_dir}/**/*.md` | `write_markdown()` | 414-429 | Save markdown files |
| `state/rp_client_input.json` | `write_ipc_input()` | 100-120 | Send user message to bridge |
| `state/rp_client_response.json` | `write_ipc_response()` | 157-187 | Send Claude response to TUI |
| `state/session_triggers.json` | `write_session_triggers()` | 290-310 | Update active characters |
| `state/response_counter.json` | Increment logic | 354-389 | Update response count |

---

### EntityManager (`src/entity_manager.py`)

**Purpose:** Manages entity cards (characters, locations, organizations) and preferences

**Reads:**

| File Pattern | Method | Lines | Purpose |
|-------------|--------|-------|---------|
| `entities/*.md` | `scan_and_index()` | 72-88 | Index all entities |
| `entities/[CHAR] *.md` | Character load | 100+ | Load character entities |
| `relationships/{character}_preferences.json` | `load_preferences()` | 567-613 | Load preference profile |
| Personality cores | `extract_personality()` | 220-237 | Extract character traits |
| `characters/{{user}}.md` | Player character | 68 | Load player character |

**Writes:**

| File Pattern | Method | Lines | Purpose |
|-------------|--------|-------|---------|
| `entities/[CHAR] {name}.md` | `create_entity_card()` | 500-508 | Create character card |
| `entities/[LOC] {name}.md` | `create_entity_card()` | 502+ | Create location card |
| `relationships/{character}_preferences.json` | `create_preference_file()` | 548-583 | Create preference profile |
| Preference files | `auto_generate_preferences()` | 585-709 | Generate traits from card |

---

### FileLoader (`src/automation/file_loading.py`)

**Purpose:** Loads RP files in tiered strategy for efficiency

**Reads TIER_1 (Every Response - Cached):**

| File | Lines | Purpose | Frequency |
|------|-------|---------|-----------|
| `{rp_dir}/AUTHOR'S_NOTES.md` | 62 | Author guidelines | Every response |
| `{rp_dir}/STORY_GENOME.md` | 63 | Plot skeleton | Every response |
| `{rp_dir}/NAMING_CONVENTIONS.md` | 64 | Naming rules | Every response |
| `{rp_dir}/SCENE_NOTES.md` | 65 | Scene descriptions | Every response |
| `state/current_state.md` | 66 | Current story position | Every response |
| `state/story_arc.md` | 67 | Story arc summary | Every response |
| `characters/{{user}}.md` | 68 | Player character | Every response |
| `chapters/` (first file) | 74-76 | Initial chapter context | Every response |

**Reads TIER_2 (Every 4th Response - Periodic):**

| File | Lines | Purpose | Frequency |
|------|-------|---------|-----------|
| `../config/guidelines/*.md` | 120-126 | Global writing guidelines | Every 4th response |
| RP overview files | 130 | General RP context | Every 4th response |

**Reads TIER_3 (Conditional - Entity Mentions):**

| File | Lines | Purpose | Trigger |
|------|-------|---------|---------|
| `entities/[CHAR] {mentioned}.md` | Conditional | Character details | When entity mentioned |
| `entities/[LOC] {mentioned}.md` | Conditional | Location details | When location mentioned |
| `relationships/{character}_preferences.json` | Conditional | Preference profile | When relevant |

**Method Reference:**
- Safe loading: `_load_file_safe()` - Lines 34-50
- Error handling: Gracefully skips missing files, logs to hook.log

---

### StoryGenerator (`src/automation/story_generation.py`)

**Purpose:** Generates and maintains story arc summaries

**Reads:**

| File | Lines | Purpose |
|------|-------|---------|
| `state/current_state.md` | 86 (comment) | Context for arc generation |
| `state/story_arc.md` | 87 (comment) | Previous arc for continuity |
| `chapters/` folder | 85 (comment) | Historical context |

**Writes:**

| File | Lines | Purpose |
|------|-------|---------|
| `state/story_arc.md` | 142 | Updated story arc summary |
| Via `_write_queue.write_text()` | 18-22 | Debounced write system |

---

### FileChangeTracker (`src/file_change_tracker.py`)

**Purpose:** Tracks file modifications for optimization

**Reads:**

| File | Lines | Purpose |
|------|-------|---------|
| `entities/*.md` | 67 | Track entity changes |
| `state/current_state.md` | 73 | Track state changes |
| `state/story_arc.md` | 74 | Track arc changes |

**Writes:**

| File | Lines | Purpose |
|------|-------|---------|
| `state/file_changes.json` | Tracking | Record file modifications |

---

### TUI Bridge (`src/tui_bridge.py`)

**Purpose:** Bridges TUI interface with automation system

**Reads:**

| File | Lines | Purpose |
|------|-------|---------|
| `state/rp_client_input.json` | 197 | User input message (IPC) |
| Input file support | 191-192 | Supports .txt and .json |
| `config/config.json` | 118 | Load RP configuration |
| State files (via FileManager) | 105+ | Access RP state |

**Writes:**

| File | Lines | Purpose |
|------|-------|---------|
| `state/rp_client_response.json` | 231 | Send response to TUI (IPC) |
| Done flag | 232 | Signal completion |
| Via orchestrator | 105 | Trigger background tasks |

---

### Automation Agents (Background) (`src/automation/agents/background/`)

**Purpose:** Parallel analysis and content extraction

**Read From:**

- `state/current_state.md` - Story context
- `entities/` - Entity references
- `chapters/` - Historical context
- `relationships/` - Character preferences

**Write To:**

- `state/plot_threads_master.md` - Plot thread updates
- `state/plot_threads_archive.md` - Resolved threads
- `state/knowledge_base.md` - Extracted knowledge
- `memories/` - Memory files
- `relationships/` - Relationship updates
- `state/agent_analysis.md` - Analysis cache

**Individual Agents:**

1. **MemoryCreationAgent** - Extracts memorable moments → `memories/`
2. **ResponseAnalyzer** - Analyzes responses → `state/agent_analysis.md`
3. **RelationshipAnalysis** - Analyzes relationships → `relationships/`
4. **KnowledgeExtraction** - Extracts world facts → `state/knowledge_base.md`
5. **PlotThreadDetection** - Detects plot threads → `state/plot_threads_master.md`
6. **ContradictionDetection** - Finds inconsistencies → `state/hook.log`

---

## Files Written By Components

### Write Queue System (`src/fs_write_queue.py`)

**Purpose:** Centralized, debounced file writing to prevent disk thrashing

**Global Instance:**
```python
_write_queue = get_write_queue()  # Line 20-22
```

**Methods:**

| Method | Lines | Purpose | Default Debounce |
|--------|-------|---------|-------------------|
| `write_text()` | 88-103 | Write text files | 500ms |
| `write_json()` | 105-122 | Write JSON files | 500ms |
| `flush()` | Per-file | Force immediate write | N/A |

**Used By:**

- `automation/core.py:169` - Response counter updates
- `automation/triggers.py` - Trigger history
- `automation/story_generation.py:22` - Story arc updates
- `automation/status.py` - Status updates
- `automation/time_tracking.py` - Time tracking updates

**Key Feature:** Each file has independent debounce timer, allowing multiple files to be written independently while preventing rapid successive writes to same file.

---

### FileManager Write Operations

**See [FileManager - Reads](#filemanager-srcfile_managerpy) section above for write methods**

Key write locations:
- All JSON writes: Lines 58-74
- All Markdown writes: Lines 414-429
- IPC response: Lines 157-187
- Session triggers: Lines 290-310
- Response counter: Lines 354-389

---

### EntityManager Write Operations

**See [EntityManager - Reads](#entitymanager-srcentity_managerpy) section above for write methods**

Key write locations:
- Entity cards: Lines 500-508
- Preference files: Lines 548-583
- Preference generation: Lines 585-709

---

### Initialization System (`src/initialize_rp.py`)

**Purpose:** Creates complete RP directory structure on first setup

**Creates All Directories:**
- `chapters/`, `characters/`, `entities/`, `locations/`, `memories/`, `relationships/`, `sessions/`, `backups/`, `exports/`, `config/`, `state/`

**Creates All State Files (Lines 103-125):**
- `state/plot_threads_master.md` - Line 104
- `state/plot_threads_archive.md` - Line 105
- `state/knowledge_base.md` - Line 106
- `state/current_state.md` - Line 107
- `state/entity_tracker.json` - Line 108
- `state/relationship_tracker.json` - Line 109
- `state/memory_index.json` - Line 110
- `state/automation_config.json` - Line 111
- `state/file_tracking.json` - Line 112

---

## Interaction Patterns

### IPC Communication Pattern (TUI ↔ Bridge)

**Sequence:**

```
1. TUI writes user input to state/rp_client_input.json
2. TUI creates state/rp_client_ready.flag
3. Bridge detects flag, reads state/rp_client_input.json
4. Bridge processes message with FileLoader + Agents
5. Bridge writes response to state/rp_client_response.json
6. Bridge creates state/rp_client_done.flag
7. TUI detects done.flag, reads response
8. TUI displays response, waits for next input
9. Cycle repeats
```

**Critical Files:**

| File | Set By | Read By | Purpose |
|------|--------|---------|---------|
| `state/rp_client_input.json` | TUI | Bridge | User message |
| `state/rp_client_response.json` | Bridge | TUI | Claude response |
| `state/rp_client_ready.flag` | Bridge | TUI | Ready for input signal |
| `state/rp_client_done.flag` | Bridge | TUI | Response complete signal |

---

### Tiered File Loading Strategy

**Why:** Optimize performance by loading frequently-needed files every time, less-critical files periodically

**TIER_1 - Every Response (Always Cached)**
- Author notes, naming conventions, scene notes
- Current story position
- Player character sheet
- Story arc summary
- First chapter context

**TIER_2 - Every 4th Response (Periodic)**
- Global writing guidelines
- RP overview files

**TIER_3 - Conditional (On Demand)**
- Entity cards when mentioned
- Relationship files when relevant
- Location files when needed

**Implementation:** `src/automation/file_loading.py`
- Safe loading: `_load_file_safe()` handles missing files gracefully
- Response counter used to determine tier: `response_num % 4 == 0` for TIER_2

---

### Migration Pattern (Legacy Support)

System automatically migrates old file formats to new ones:

**Examples:**

| Old Format | New Format | Migration Handler | Auto-Delete |
|-----------|-----------|-------------------|-------------|
| `response_counter.txt` | `response_counter.json` | FileManager | Yes (after migration) |
| `session_triggers.txt` | `session_triggers.json` | FileManager | Yes (after migration) |
| `characters/` files | `entities/[CHAR]` files | EntityManager | Manual migration |

**Implementation:** Each read method checks for legacy format, migrates if found, then deletes old file

---

### Write Queue Debouncing

**Problem Solved:** Rapid successive file writes cause disk thrashing

**Solution:** Per-file debounce timers

**How It Works:**

1. Call `write_queue.write_text("path", "content")`
2. If no pending timer for "path", create 500ms timer
3. If timer already exists, reset to 500ms
4. When timer expires, write to disk
5. If multiple writes within 500ms window, only final content written

**Example Scenario:**
```
t=0ms    : write_json("response_counter.json", {"count": 1})  → Timer starts
t=100ms  : write_json("response_counter.json", {"count": 2})  → Timer resets
t=200ms  : write_json("response_counter.json", {"count": 3})  → Timer resets
t=600ms  : Timer expires, writes {"count": 3} to disk (only 1 disk write)
```

**Benefits:**
- Reduces disk I/O by 50-80% for frequently-updated files
- Prevents file corruption from concurrent writes
- Improves overall system performance

---

## Special Directories

### `/state/` - Core Operations Hub

**Contains:** 22 critical state management files

**Access Pattern:**
- **High Frequency Reads:** `current_state.md`, `story_arc.md` (every response)
- **Periodic Writes:** Response counter (every response, debounced)
- **IPC Files:** `rp_client_input.json`, `rp_client_response.json` (per user interaction)
- **Background Updates:** Plot threads, knowledge base, agent analysis (background agents)

**Initialization:** See `initialize_rp.py` lines 103-125

---

### `/entities/` - Entity System Hub

**Purpose:** Centralized location for all character, location, organization cards

**Naming Convention:**
- `[CHAR] {name}.md` - Character entities
- `[LOC] {name}.md` - Location entities
- `[ORG] {name}.md` - Organization entities

**File Format:** Markdown with frontmatter

**Read By:**
- EntityManager: `scan_and_index()` (lines 72-88)
- FileLoader: TIER_3 conditional loading
- TUI: For display and reference
- Agents: For context during analysis

**Written By:**
- EntityManager: `create_entity_card()` (lines 500-508)
- Agents: Auto-creation of new entities

**Access Pattern:**
- Scanned during initialization
- Cached in memory
- Referenced by name during responses
- Updated when new entities mentioned

---

### `/relationships/` - Character Preferences Hub

**Purpose:** Store relationship preferences and personality matching

**File Format:** `{character_name}_preferences.json`

**JSON Structure:**
```json
{
  "character_name": "Name",
  "like_traits": [
    {"trait": "trait_name", "points": 10}
  ],
  "dislike_traits": [
    {"trait": "trait_name", "points": -5}
  ],
  "hate_traits": [
    {"trait": "trait_name", "points": -20}
  ]
}
```

**Created By:**
- EntityManager: `create_preference_file()` (lines 548-583)
- EntityManager: `auto_generate_preferences()` (lines 585-709)

**Read By:**
- EntityManager: `load_preferences()` (lines 567-613)
- FileLoader: TIER_3 conditional loading

**Access Pattern:**
- Created when entity card created
- Updated when personality traits identified
- Consulted during relationship analysis

---

### `/memories/` - Character Memory Hub

**Purpose:** Store extracted memories and moments from story

**File Format:** `{character_name}_memories.md`

**Content:** Markdown list of memorable moments

**Written By:**
- MemoryCreationAgent: Extracts and creates memories
- Agents: Auto-creation of memory entries

**Read By:**
- Background agents for context
- FileLoader for TIER_3 conditional loading

**Access Pattern:**
- Created during first mention of character
- Updated after each significant moment
- Consulted for character consistency

---

### `/chapters/` - Story History Hub

**Purpose:** Store story chapter files

**File Format:** Markdown or text files (`chapter_001.md`, `chapter_002.txt`)

**Read By:**
- FileLoader: First file loaded in TIER_1
- StoryGenerator: For historical context
- Agents: For story continuity

**Access Pattern:**
- Chronological loading
- Referenced for backstory
- Scanned for entity mentions

---

## Initialization & Setup

### Complete RP Setup Process (`initialize_rp.py`)

**Called:** When creating new RP project

**Creates Directory Structure:**

```python
directories = [
    'chapters', 'characters', 'entities', 'locations',
    'memories', 'relationships', 'sessions', 'backups',
    'exports', 'config', 'state'
]
```

**Creates All State Files (Lines 103-125):**

```python
state_files = {
    'plot_threads_master.md': StateTemplates.plot_threads_template(),
    'plot_threads_archive.md': StateTemplates.plot_threads_template(),
    'knowledge_base.md': StateTemplates.knowledge_base_template(),
    'current_state.md': StateTemplates.current_state_template(),
    'entity_tracker.json': {},
    'relationship_tracker.json': {},
    'memory_index.json': {},
    'automation_config.json': automation_defaults,
    'file_tracking.json': {}
}
```

**State File Templates:**
- `plot_threads_master.md` - Initial empty plot threads
- `plot_threads_archive.md` - Initial empty archive
- `knowledge_base.md` - Initial empty knowledge base
- `current_state.md` - Initial story position placeholder
- JSON files - Empty objects or default configurations

---

## Component Interaction Flow

### Complete Message Processing Flow

```
TUI (rp_client_tui.py)
  │
  ├─ User types message
  │
  ├─ Writes to: state/rp_client_input.json
  │
  ├─ Creates: state/rp_client_ready.flag
  │
  └─ Waits for response
     │
     v
Bridge (tui_bridge.py)
  │
  ├─ Detects: state/rp_client_ready.flag
  │
  ├─ Reads: state/rp_client_input.json
  │
  ├─ Invokes: AutomationOrchestrator
  │
  └─ Returns: orchestrator results
     │
     ├─ Reads from FileLoader:
     │  ├─ TIER_1: current_state.md, story_arc.md, AUTHOR'S_NOTES.md, etc.
     │  ├─ TIER_2: (if response_num % 4 == 0) guidelines, overview
     │  └─ TIER_3: entity cards, preferences, memories (conditional)
     │
     ├─ Runs: Immediate Agents (5-second timeout, hidden)
     │  ├─ quick_entity_analysis.py
     │  ├─ fact_extraction.py
     │  ├─ memory_extraction.py
     │  └─ plot_thread_extraction.py
     │
     ├─ Generates: Claude prompt with all loaded context
     │
     ├─ Calls: Claude API
     │
     ├─ Receives: Claude response
     │
     ├─ Writes: state/rp_client_response.json
     │
     ├─ Creates: state/rp_client_done.flag
     │
     └─ Starts: Background Agents (parallel, while user reads)
        ├─ response_analyzer.py → state/agent_analysis.md
        ├─ memory_creation.py → memories/
        ├─ relationship_analysis.py → relationships/
        ├─ plot_thread_detection.py → state/plot_threads_master.md
        ├─ knowledge_extraction.py → state/knowledge_base.md
        └─ contradiction_detection.py → state/hook.log
        │
        └─ Updates State Files:
           ├─ Increments: state/response_counter.json
           ├─ Updates: state/current_state.md (optional)
           ├─ Updates: state/story_arc.md (via StoryGenerator)
           └─ Updates: Various entity/relationship/memory files
     │
     v
TUI (rp_client_tui.py)
  │
  ├─ Detects: state/rp_client_done.flag
  │
  ├─ Reads: state/rp_client_response.json
  │
  ├─ Displays: Claude response
  │
  └─ Waits for next user input
```

---

## Debugging Guide

### Common File Operation Issues

**Problem: Response counter not updating**
- Check: `state/response_counter.json` exists
- Check: `hook.log` for write queue errors
- Check: Write queue debounce (500ms) - may need to wait
- Check: File permissions on state directory

**Problem: Entities not found**
- Check: `entities/` directory exists and has files
- Check: File naming follows `[TYPE] Name.md` convention
- Check: `state/entity_tracker.json` contains the entity
- Check: FileLoader TIER_3 conditional loading triggered
- Check: `hook.log` for scanning errors

**Problem: Preferences not being used**
- Check: `relationships/` directory has `{character}_preferences.json`
- Check: JSON structure matches expected format
- Check: Character name matches between files
- Check: EntityManager.load_preferences() called correctly
- Check: `hook.log` for preference load errors

**Problem: IPC Communication stalled**
- Check: `state/rp_client_ready.flag` exists
- Check: `state/rp_client_input.json` contains valid JSON
- Check: Bridge process running and monitoring flags
- Check: `state/rp_client_done.flag` created after processing
- Check: `hook.log` for bridge errors

**Problem: Memory not being persisted**
- Check: `memories/` directory exists
- Check: MemoryCreationAgent creating files (check `hook.log`)
- Check: File naming follows `{character}_memories.md`
- Check: File permissions on memories directory
- Check: Write queue flushing properly

### Inspection Commands

**View current state:**
```bash
cat state/current_state.md
```

**Check response counter:**
```bash
cat state/response_counter.json
```

**Check active entities:**
```bash
ls -la entities/
```

**View recent logs:**
```bash
tail -50 state/hook.log
```

**Check file changes tracking:**
```bash
cat state/file_changes.json
```

**Monitor state directory:**
```bash
watch -n 1 'ls -la state/ | grep -E "(json|md|flag)$"'
```

### Key Files for Debugging

| File | Purpose | How to Use |
|------|---------|-----------|
| `state/hook.log` | System logs | `tail -f state/hook.log` |
| `state/response_counter.json` | Current position | Check if incrementing |
| `state/rp_client_input.json` | Last user input | Verify message received |
| `state/rp_client_response.json` | Last response | Verify Claude output |
| `state/file_changes.json` | What changed | Track modifications |
| `automation_config.json` | Agent settings | Verify agent configuration |

---

## Summary Table

### Quick Reference - Who Reads/Writes What

| Component | Reads | Writes | Location |
|-----------|-------|--------|----------|
| **FileManager** | JSON, Markdown, IPC | JSON, Markdown, IPC, counters | `src/file_manager.py` |
| **EntityManager** | Entity cards, preferences | Entity cards, preferences | `src/entity_manager.py` |
| **FileLoader** | TIER_1/2/3 files | - (read only) | `src/automation/file_loading.py` |
| **StoryGenerator** | Story context | `state/story_arc.md` | `src/automation/story_generation.py` |
| **Background Agents** | Entity/chapter/state files | `state/`, `memories/`, `relationships/` | `src/automation/agents/background/` |
| **TUI Bridge** | Input, config, state | Response, flags, output | `src/tui_bridge.py` |
| **WriteQueue** | - | All text/JSON writes (debounced) | `src/fs_write_queue.py` |
| **Initialize** | - | Complete RP structure | `src/initialize_rp.py` |
| **FileChangeTracker** | Monitored files | `state/file_changes.json` | `src/file_change_tracker.py` |

---

## Related Documentation

- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - Overall system design and request flow
- **[COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md)** - High-level component interaction matrix
- **[SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md)** - File handling and I/O systems
- **[AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md)** - Background agent details
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Navigation hub

---

**Last Updated:** 2025-10-16
**Version:** 1.0.0
**Status:** Complete and current

For questions about specific file interactions, check the relevant section above or search for the component name.
