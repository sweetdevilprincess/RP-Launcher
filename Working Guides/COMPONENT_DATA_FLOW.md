# RP Claude Code - Component Data Flow Reference

**Last Updated**: 2025-10-17  
**Version**: 1.1.0

Quick reference guide showing what each component reads and writes.

**Note:** For detailed information about file operations within `/RPs/{RP Name}/` directories, see [RP_DIRECTORY_MAP.md](RP_DIRECTORY_MAP.md). That document provides comprehensive file interaction details, state file references, and debugging guidance specific to RP operations.

---

## QUICK REFERENCE TABLE

| Component | Location | Reads From | Writes To | Purpose |
|-----------|----------|-----------|-----------|---------|
| **Module Manager** | `src/core/module_manager.py` | Module registry, `state/automation_config.json` | Module lifecycle state (in-memory) | Registers modules, resolves dependencies, coordinates start/stop |
| **Config Loader** | `src/core/config.py` | `state/automation_config.json`, defaults | `state/automation_config.json` (save/reset) | Merges default + per-RP config for modules |
| **FileManagerModule** | `src/modules/files/file_manager_module.py` | All RP files (JSON, Markdown, directories) | All RP files via `FileManager` | Centralized read/write helper for modules |
| **FSWriteQueueModule** | `src/modules/files/fs_write_queue_module.py` | Pending write registry | Deferred writes to disk (debounced) | Buffers and flushes filesystem writes |
| **SessionManagerModule** | `src/modules/session/session_manager_module.py` | `sessions/**/*.json` | `sessions/**/*.json` | Retry, branching, checkpoint lifecycle |
| **EntityManagerModule** | `src/modules/entities/entity_manager_module.py` | `entities/*.md`, `memories/`, `relationships/` | In-memory indices, generated cards via FileManager | Entity lookup, mention detection, preference helpers |
| **BackgroundTaskQueueModule** | `src/modules/tasks/background_task_queue_module.py` | Task queue persistence (`state/background_tasks.json`) | Same (plus logs) | Runs long tasks without blocking automation loop |
| **AgentCoordinatorModule** | `src/modules/agents/agent_coordinator_module.py` | DeepSeek agent definitions, cached results | `state/agent_analysis.json` | Executes DeepSeek agents concurrently + caches output |
| **OrchestratorModule** | `src/modules/automation/orchestrator_module.py` + `src/automation/orchestrator_v2_simplified.py` | Tiered state files, agent cache, triggers, counters | `CURRENT_STATUS.md`, `hook.log`, `state/agent_analysis.json` (when saving) | Builds Claude prompt, coordinates automation pass |
| **File Change Tracker** | `src/file_change_tracker.py` | Filesystem mtimes, `state/file_tracking.json` | `state/file_tracking.json` | Detects external edits and surfaces diffs |
| **Immediate Agents (4)** | `src/automation/agents/immediate/` | Entity cards, memories, plot threads, user message | `state/agent_analysis.json` (`immediate` block) | Supplies quick context before Claude reply |
| **Background Agents (6)** | `src/automation/agents/background/` | Claude response, state files | `state/agent_analysis.json` (`background` block), state files via FileManager | Post-response analysis; updates lore, memories, relationships |
| **TUI Bridge** | `src/tui_bridge.py` | TUI flags, ModuleManager status, `state/*` | `state/rp_client_input.json`, `hook.log`, module commands | Loads ModuleManager, relays messages between TUI and Claude |
| **TUI (Textual)** | `src/rp_client_tui.py` | `state/rp_client_response.json`, `CURRENT_STATUS.md` | `state/rp_client_input.json`, control flags | Operator-facing UI for sessions |
| **Claude API Client** | `src/clients/claude_api.py` | Conversation history from SessionManager | Claude responses to `state/rp_client_response.json` | Anthropic API integration (API mode) |
| **DeepSeek Client** | `src/clients/deepseek.py` | Agent prompts from automation | JSON/text analysis back to agents | DeepSeek analysis + generation support |
---

## STATE FILES - WHO READS AND WRITES

### response_counter.json
- **Read By**:
- OrchestratorModule / `AutomationOrchestratorV2` (initialization)
  - Core automation functions
  - All agents (when needed)
- **Written By**:
- `automation.core.increment_counter` (invoked by OrchestratorModule after each response)
  - Via FSWriteQueueModule
- **Used For**: Tracking current response number

### automation_config.json
- **Read By**:
- OrchestratorModule / `AutomationOrchestratorV2` (initialization)
- ConfigLoader / ModuleManager
  - Core automation
- **Written By**:
  - Manual setup only
- **Used For**: Agent configuration, feature flags

### current_state.md
- **Read By**:
  - TUI (display context)
  - Agents (context)
- **Written By**:
  - Background agents (updates)
  - Via FSWriteQueueModule
- **Used For**: Current story state

### agent_analysis.json
- **Read By**:
  - OrchestratorModule / `AutomationOrchestratorV2` (when assembling prompt context)
  - AgentCoordinatorModule (reuse cached background runs)
- **Written By**:
  - AgentCoordinatorModule (after agents run)
  - Via FSWriteQueueModule
- **Used For**: Cache agent results

### relationships.json
- **Read By**:
  - Relationship Analysis agent
  - Memory extraction (context)
- **Written By**:
  - Relationship Analysis agent
  - Via FSWriteQueueModule
- **Used For**: Track character relationships

### plot_threads_master.md
- **Read By**:
  - Plot Thread Detection agent (background)
  - Plot Thread Extraction agent (immediate)
  - Orchestrator (initialization)
- **Written By**:
  - Plot Thread Detection agent
  - Via FSWriteQueueModule
- **Used For**: Manage all plot threads

### knowledge_base.md
- **Read By**:
  - Knowledge Extraction agent
  - Contradiction Detection agent
- **Written By**:
  - Knowledge Extraction agent
  - Via FSWriteQueueModule
- **Used For**: World-building facts

### file_changes.json
- **Read By**:
  - File Change Tracker
- **Written By**:
  - File Change Tracker
  - Via FSWriteQueueModule
- **Used For**: Track file modifications

### hook.log
- **Read By**:
  - Manual inspection only
- **Written By**:
  - All components (logging)
  - Direct write (not queued)
- **Used For**: Debug logging

---

## ENTITY SYSTEM - WHO READS AND WRITES

### entities/*.md (Entity Cards)
- **Read By**:
  - Entity Manager (scan_and_index)
  - Quick Entity Analysis agent
  - Fact Extraction agent
  - Contradiction Detection agent
  - Various other agents
- **Written By**:
  - Story Generator (via DeepSeek)
  - Manual creation
- **Used For**: Store character/location/org info

### memories/{character}/*.md (Memory Files)
- **Read By**:
  - Memory Extraction agent (immediate)
  - Various agents needing context
- **Written By**:
  - Memory Creation agent (background)
  - Via FSWriteQueueModule
- **Used For**: Character memory banks

### locations/*.md (Location Details)
- **Read By**:
  - Quick Entity Analysis agent
  - Various agents
- **Written By**:
  - Story Generator (via DeepSeek)
  - Manual creation
- **Used For**: Location information

### relationships/{character}_preferences.json
- **Read By**:
  - Relationship Analysis agent
- **Written By**:
  - Manual setup
- **Used For**: Character preferences

---

## IPC FILES - TUI COMMUNICATION

### state/rp_client_input.json
- **Written By**: TUI (rp_client_tui.py)
- **Read By**: TUI Bridge (tui_bridge.py)
- **Flow**: TUI → Bridge
- **Format**:
  ```json
  {
    "message": "User's input message",
    "timestamp": "ISO timestamp"
  }
  ```

### state/rp_client_response.json
- **Written By**: TUI Bridge (tui_bridge.py)
- **Read By**: TUI (rp_client_tui.py)
- **Flow**: Bridge → TUI
- **Format**:
  ```json
  {
    "response": "Claude's response",
    "analysis": "Agent analysis results",
    "timestamp": "ISO timestamp"
  }
  ```

### state/rp_client_ready.flag
- **Set By**: TUI (when input ready)
- **Checked By**: TUI Bridge (before reading input)
- **Purpose**: Synchronization signal

### state/rp_client_done.flag
- **Set By**: TUI Bridge (when response ready)
- **Checked By**: TUI (before reading response)
- **Purpose**: Synchronization signal

### state/tui_active.flag
- **Set By**: TUI (on startup)
- **Checked By**: TUI Bridge (before starting)
- **Purpose**: Ensure TUI is running

---

## AGENT SYSTEM - DATA FLOW

### Immediate Agents (Before Response)
Run in parallel, all within ~3 seconds

#### Quick Entity Analysis
- **Reads**: User message, entity cards
- **Writes**: Tier 1/2/3 classifications
- **Cache**: state/agent_analysis.json
- **Purpose**: Classify entities for optimization

#### Fact Extraction
- **Reads**: Tier 2 entities, entity cards
- **Writes**: Key facts for each entity
- **Cache**: state/agent_analysis.json
- **Purpose**: Extract important facts (97% token reduction)

#### Memory Extraction
- **Reads**: Scene participants, memories/{char}/*.md
- **Writes**: 2-5 relevant memories per character
- **Cache**: state/agent_analysis.json
- **Purpose**: Gather relevant memories (96% token reduction)

#### Plot Thread Extraction
- **Reads**: User message, plot_threads_master.md
- **Writes**: 2-5 relevant plot threads
- **Cache**: state/agent_analysis.json
- **Purpose**: Load relevant threads (85% token reduction)

### Background Agents (After Response)
Run in parallel, hidden, ~15-30 seconds total

#### Response Analyzer
- **Reads**: Response, response counter
- **Writes**: Scene classification, pacing, tension
- **Updates**: state/agent_analysis.json
- **Purpose**: Analyze response quality

#### Memory Creation
- **Reads**: Response, response counter
- **Writes**: memories/{character}/*.md (new files)
- **Updates**: Via FSWriteQueueModule
- **Purpose**: Extract and store memories

#### Relationship Analysis
- **Reads**: Response, state/relationships.json
- **Writes**: Updated state/relationships.json
- **Updates**: Via FSWriteQueueModule
- **Purpose**: Track relationship changes

#### Plot Thread Detection
- **Reads**: Response, state/plot_threads_master.md
- **Writes**: Updated state/plot_threads_master.md
- **Updates**: Via FSWriteQueueModule
- **Purpose**: Track new/resolved threads

#### Knowledge Extraction
- **Reads**: Response, state/knowledge_base.md
- **Writes**: Updated state/knowledge_base.md
- **Updates**: Via FSWriteQueueModule
- **Purpose**: Extract world facts

#### Contradiction Detection (Optional)
- **Reads**: Response, state/knowledge_base.md, entities/*.md
- **Writes**: Contradiction alerts
- **Updates**: state/agent_analysis.json
- **Purpose**: Fact-check against canon

---

## ORCHESTRATION FLOW

### Automation Pass (module-managed order)

1. **Tiered Loader + Status Prep**
   - Controlled by: OrchestratorModule (`AutomationOrchestratorV2`)
   - Reads: tiered core files (`state/current_state.md`, entity index, templates, counters)
   - Writes: `CURRENT_STATUS.md`, `hook.log` snapshots

2. **Immediate Agents**
   - Runs via: AgentCoordinatorModule (immediate agent set)
   - Reads: user message, entity cards, memories, plot threads
   - Writes: `state/agent_analysis.json` (`immediate` block)

3. **Claude Response**
   - Uses: Claude API client or SDK (configured in TUI Bridge)
   - Reads: assembled prompt (base context + agent output)
   - Writes: `state/rp_client_response.json`, active session log via SessionManagerModule

4. **Background Agents**
   - Runs via: AgentCoordinatorModule (background agent set)
   - Reads: Claude response, knowledge base, relationships, memories, plot threads
   - Writes: `state/agent_analysis.json` (`background` block), state files through FileManagerModule + FSWriteQueueModule

5. **File Flush & Change Tracking**
   - FSWriteQueueModule flushes pending writes
   - FileChangeTracker updates `state/file_tracking.json` for external visibility

---

## WRITE QUEUE BEHAVIOR

All writes go through FSWriteQueueModule for debouncing:

```
Multiple writes to same file within 500ms
            ↓
         Queued
            ↓
    500ms after last write
            ↓
     Single disk write
```

Example in one cycle:
- Memory Creation wants to write: `memories/Alice/mem_001.md`
- Relationship Analysis wants to write: `state/relationships.json`
- Plot Detection wants to write: `state/plot_threads_master.md`
- Each file gets ONE write after debounce

---

## COMPONENT MODIFICATION CHECKLIST

Use this when modifying components:

### Adding a New Agent
- [ ] Create file in `src/automation/agents/background/` or `immediate/`
- [ ] Extend `BaseAgent` class
- [ ] Implement `run()` method
- [ ] Register in `AgentFactory.registry`
- [ ] Add to config in `automation_config.json`
- [ ] Update `AGENT_DOCUMENTATION.md`

### Adding a New State File
- [ ] Add template to `StateTemplates` class
- [ ] Decide read/write permissions
- [ ] Document in this file
- [ ] Update initialization logic
- [ ] Ensure FSWriteQueueModule compatible

### Modifying File Manager
- [ ] Affects all file operations
- [ ] Test with all file types
- [ ] Update error handling
- [ ] Test IPC communication

### Modifying FSWriteQueueModule
- [ ] Affects all writes system-wide
- [ ] Test debounce behavior
- [ ] Test concurrent writes
- [ ] Test shutdown handling

### Registering a New Module
- [ ] Implement an `RPModule` subclass in `src/modules/<domain>/`
- [ ] Declare `name`, `dependencies`, and lifecycle hooks (`initialize/start/stop/cleanup`)
- [ ] Register it with `ModuleManager` (see `tui_bridge.py` bootstrap sequence)
- [ ] Add defaults to `core/config.py` and update documentation (`SYSTEM_ARCHITECTURE.md`)
- [ ] Verify it appears in `/modules status` and survives start/stop cycles

---

## DEBUGGING TIPS

### Agent Results Not Updating
- Check: `state/agent_analysis.json` for cache
- Check: agent logs in `state/hook.log`
- Check: FSWriteQueueModule debounce settings
- Solution: Clear cache, restart

### Files Not Changing
- Check: FSWriteQueueModule debounce (may still be pending)
- Check: File permissions
- Check: State directory exists
- Solution: Force flush or wait 500ms+

### Entity Cards Not Recognized
- Check: `entities/` directory structure
- Check: EntityManager scan results in log
- Check: Entity file format (markdown)
- Solution: Rescan via EntityManager initialization

### Response Not Saved
- Check: `state/rp_client_response.json`
- Check: Response file permissions
- Check: TUI bridge log
- Solution: Check disk space, permissions

---

## Data Modification Patterns

### To Add/Update Entity Card
```
1. Manual edit entities/{name}.md
2. OR DeepSeek generates via Story Generator
3. EntityManager re-indexes on next cycle
4. Agents see updated card
```

### To Add Memory
```
1. Memory Creation agent runs after response
2. Generates memories/{char}/mem_ID.md
3. Queued via FSWriteQueueModule
4. Flushed after 500ms
5. Memory Extraction uses next cycle
```

### To Update Relationships
```
1. Relationship Analysis reads response
2. Updates state/relationships.json
3. Queued via FSWriteQueueModule
4. Flushed after 500ms
5. Next agent analysis uses updated values
```

### To Add Plot Thread
```
1. Plot Thread Detection reads response
2. Identifies new thread
3. Updates state/plot_threads_master.md
4. Queued via FSWriteQueueModule
5. Plot Thread Extraction uses next cycle
```

---

## Performance Notes

### Slow Areas to Watch
- Entity indexing (scan_and_index): O(n) where n = entity count
- Memory extraction: O(m*k) where m = characters, k = memories
- Plot thread matching: O(t*w) where t = threads, w = words in response
- DeepSeek API calls: 30-60 seconds depending on request

### Optimization Opportunities
- Cache entity index between cycles (already done)
- Use bloom filters for quick entity matching
- Batch DeepSeek API calls
- Pre-compile regex patterns for detection

### Bottlenecks
- DeepSeek API calls (external dependency)
- Markdown file parsing (for large entity cards)
- Entity mention detection (word matching)
- File I/O (mitigated by FSWriteQueueModule)

---

## Key Files to Know

| When You Need To | File |
|-----------------|------|
| Understand overall flow | `SYSTEM_ARCHITECTURE.md` (this directory) |
| Add/modify agent | `src/automation/agents/` and `AGENT_DOCUMENTATION.md` |
| Handle files | `src/file_manager.py` |
| Understand module system | `src/core/module_manager.py`, `src/modules/` |
| Configure automation | `state/automation_config.json` |
| Check state | `state/current_state.md` |
| Debug issues | `state/hook.log` |
| Understand entities | `entities/*.md` |
| Track relationships | `state/relationships.json` |
| Manage plot | `state/plot_threads_master.md` |

---

This reference should help you quickly understand what changes what and prevent missed dependencies!

