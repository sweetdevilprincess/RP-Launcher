# TUI Settings Gap Analysis
**Date:** 2025-01-05
**Purpose:** Identify which configuration parameters are missing from the TUI

---

## Already Implemented in TUI ✅

### LLM Setup Section
- ✅ Primary provider (dropdown)
- ✅ Primary API key (password input)
- ✅ Primary model (text input)
- ✅ Primary temperature (slider 0-200)
- ✅ Primary max_tokens (text input)
- ✅ Primary prompt_caching (switch)
- ✅ Proxy configuration (switch + 3 fields)
- ✅ Secondary LLM (switch + full config)

### Performance Section
- ✅ Enable streaming (switch)
- ✅ Enable caching (switch)
- ✅ Max cache size (text input)
- ✅ Request timeout (text input)

### Appearance Section
- ✅ Theme (dropdown - 5 options)
- ✅ Font size (dropdown - 3 options)
- ✅ Show timestamps (switch)

### Paths Section
- ✅ RPs root directory (text input)
- ✅ Templates directory (text input)
- ✅ Logs directory (text input)

### Advanced Section
- ✅ Log level (dropdown - DEBUG/INFO/WARNING/ERROR)
- ✅ IPC Bridge host (text input)
- ✅ IPC Bridge port (text input)
- ✅ Enable debug mode (switch)

### Testing Section
- ✅ Enable testing mode (switch)
- ✅ Mock response delay (text input)

### Automation Section
- ✅ Enable agents (switch)
- ✅ Auto-generate preferences (switch)
- ✅ Auto-generation frequency (dropdown)

### Modules Section
- ✅ Module enable/disable toggles
- ✅ Module status display
- ✅ Module dependencies display
- ✅ IPC integration (GET_MODULES, TOGGLE_MODULE)

### Data Section
- ✅ Auto backup (switch)
- ✅ Backup frequency (dropdown)
- ✅ Backup now button
- ✅ Export data button

---

## Missing from TUI ❌

### 1. System Configuration (5 parameters)

**Location:** `system` config section

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `backup_frequency` | Integer | 10 | ❌ |
| `max_backups` | Integer | 20 | ❌ |
| `performance_tracking` | Boolean | false | ❌ |
| `auto_save` | Boolean | true | ❌ |

**Note:** `log_level` is already in Advanced section ✅

**Recommended Location:** New subsection in "Advanced" or "Data" section

---

### 2. Session Manager Configuration (4 parameters)

**Location:** `modules.session_manager.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `auto_checkpoint_frequency` | Integer | 10 | ❌ |
| `keep_archived` | Integer | 20 | ❌ |
| `compression` | Boolean | false | ❌ |
| `auto_branch_on_restore` | Boolean | true | ❌ |

**Recommended Location:** New "Session Management" section or subsection in "Data"

---

### 3. Agent Coordinator Configuration (7 parameters)

**Location:** `modules.agent_coordinator.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `max_concurrent_agents` | Integer | 6 | ❌ |
| `timeout` | Integer | 60 | ❌ |
| `cache_enabled` | Boolean | true | ❌ |
| `immediate_workers` | Integer | 4 | ❌ |
| `background_workers` | Integer | 6 | ❌ |
| `retry_enabled` | Boolean | true | ❌ |
| `max_retries` | Integer | 2 | ❌ |

**Recommended Location:** Expand "Automation" section with "Agent Settings" subsection

---

### 4. Entity Manager Configuration (3 parameters)

**Location:** `modules.entity_manager.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `auto_generate_threshold` | Integer | 3 | ❌ |
| `track_mentions` | Boolean | true | ❌ |
| `use_repository` | Boolean | true | ❌ |

**Note:** `auto_generate_threshold` partially covered by "Auto-generation frequency" but not exactly the same

**Recommended Location:** Expand "Automation" section or new "Entity System" section

---

### 5. Automation Orchestrator Configuration (4 parameters)

**Location:** `modules.automation_orchestrator.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `auto_start` | Boolean | false | ❌ |
| `use_triggers` | Boolean | true | ❌ |
| `use_templates` | Boolean | true | ❌ |
| `fallback_enabled` | Boolean | true | ❌ |

**Recommended Location:** Expand "Automation" section

---

### 6. File Manager Configuration (2 parameters)

**Location:** `modules.file_manager.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `backup_on_write` | Boolean | true | ❌ |
| `use_write_queue` | Boolean | true | ❌ |

**Recommended Location:** "Advanced" section or "Data" section

---

### 7. Proxy Client Configuration (3 parameters)

**Location:** `modules.proxy_client.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `timeout` | Integer | 30 | ❌ |
| `retry_attempts` | Integer | 3 | ❌ |
| `use_proxy` | Boolean | false | ✅ Already in LLM Setup |

**Note:** `use_proxy` is in LLM Setup section. Timeout/retry are missing.

**Recommended Location:** Expand proxy section in "LLM Setup" or move to "Advanced"

---

### 8. FS Write Queue Configuration (2 parameters)

**Location:** `modules.fs_write_queue.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `flush_interval` | Integer | 5 | ❌ |
| `max_queue_size` | Integer | 100 | ❌ |

**Recommended Location:** "Advanced" section (expert settings)

---

### 9. Background Task Queue Configuration (2 parameters)

**Location:** `modules.background_task_queue.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `max_workers` | Integer | 4 | ❌ |
| `shutdown_timeout` | Integer | 30 | ❌ |

**Recommended Location:** "Advanced" section (expert settings)

---

### 10. Update Checker Configuration (2 parameters)

**Location:** `modules.update_checker.config`

| Parameter | Type | Default | Missing |
|-----------|------|---------|---------|
| `check_interval` | Integer | 86400 | ❌ |
| `auto_check` | Boolean | false | ❌ |

**Recommended Location:** "Advanced" section

---

### 11. Individual Agent Configurations (15 parameters)

**Background Agents (7 agents):**

| Agent | Config Path | Parameters | Missing |
|-------|-------------|------------|---------|
| response_analyzer | `agents.background.response_analyzer` | enabled (bool) | ❌ |
| time_tracking | `agents.background.time_tracking` | enabled (bool) | ❌ |
| memory_creation | `agents.background.memory_creation` | enabled (bool) | ❌ |
| relationship_analysis | `agents.background.relationship_analysis` | enabled (bool) | ❌ |
| knowledge_extraction | `agents.background.knowledge_extraction` | enabled (bool) | ❌ |
| plot_thread_detection | `agents.background.plot_thread_detection` | enabled (bool) | ❌ |
| contradiction_synthesis | `agents.background.contradiction_synthesis` | enabled (bool) | ❌ |

**Immediate Agents (4 agents):**

| Agent | Config Path | Parameters | Missing |
|-------|-------------|------------|---------|
| memory_extraction | `agents.immediate.memory_extraction` | enabled (bool), timeout_seconds (int) | ❌ |
| fact_extraction | `agents.immediate.fact_extraction` | enabled (bool), timeout_seconds (int) | ❌ |
| plot_thread_extraction | `agents.immediate.plot_thread_extraction` | enabled (bool), timeout_seconds (int) | ❌ |
| quick_entity_analysis | `agents.immediate.quick_entity_analysis` | enabled (bool), timeout_seconds (int) | ❌ |

**Note:** Automation section has "Enable agents" toggle, but no individual agent control

**Recommended Location:** Expand "Automation" section with agent subsections

---

### 12. LLM Provider Configurations (10 parameters)

**Claude SDK:**
- ❌ `model` (covered by primary_model in general LLM section)
- ❌ `temperature` (covered by primary_temperature)
- ❌ `max_tokens` (covered by primary_max_tokens)

**Claude API:**
- ✅ `use_prompt_caching` (covered)
- ❌ `thinking_budget_tokens`

**OpenAI:**
- ❌ `endpoint` (responses vs chat_completions)

**OpenRouter:**
- ❌ `site_url`
- ❌ `app_name`

**Recommended Location:** Provider-specific subsections under "LLM Setup"

---

## Summary Statistics

### Coverage Analysis

| Category | Total Parameters | Implemented | Missing | Coverage |
|----------|-----------------|-------------|---------|----------|
| **High-Level Settings** | 28 | 28 | 0 | 100% ✅ |
| **Module Configurations** | 31 | 0 | 31 | 0% ❌ |
| **Agent Configurations** | 15 | 0 | 15 | 0% ❌ |
| **Provider Details** | 6 | 1 | 5 | 17% ⚠️ |
| **TOTAL** | 80 | 29 | 51 | 36% |

### What's Well Covered ✅
- LLM provider selection and credentials
- Basic LLM parameters (model, temperature, max_tokens)
- Proxy configuration
- System paths
- Module enable/disable toggles
- Appearance and theme
- Testing mode

### What's Missing ❌
- **Per-module configuration** (31 parameters)
- **Per-agent configuration** (15 parameters)
- **Advanced system settings** (5 parameters)

---

## Proposed Implementation Plan

### Phase 1: Agent Configuration UI (Highest Priority)
**Impact:** Users frequently want to enable/disable individual agents

**Add to Automation Section:**
```
Automation Settings
  [✓] Enable automation agents (master switch)
  [✓] Auto-generate entity preferences
  [Dropdown] Auto-generation frequency

  ▼ Background Agents (run after Claude responds)
    [✓] Response Analyzer - Extract scene metadata
    [✓] Time Tracking - Track in-world time
    [✓] Memory Creation - Extract memorable moments
    [✓] Relationship Analysis - Track character relationships
    [✓] Knowledge Extraction - Extract world facts
    [✓] Plot Thread Detection - Identify narrative threads
    [ ] Contradiction Synthesis - Detect story contradictions

  ▼ Immediate Agents (run before Claude responds)
    [✓] Memory Extraction - timeout: [5] seconds
    [✓] Fact Extraction - timeout: [5] seconds
    [✓] Plot Thread Extraction - timeout: [5] seconds
    [ ] Quick Entity Analysis - timeout: [3] seconds
```

### Phase 2: Session & Data Configuration (High Priority)
**Impact:** Users want control over checkpoints and backups

**Expand Data Section:**
```
Data Management
  System Backups:
    [✓] Auto-save state changes
    Backup frequency: [10] responses
    Max backups to keep: [20]

  Session Checkpoints:
    Auto-checkpoint every: [10] responses (0 = disabled)
    Max archived sessions: [20]
    [✓] Enable compression for archives
    [✓] Auto-branch when restoring checkpoint
```

### Phase 3: Agent Coordinator Configuration (Medium Priority)
**Impact:** Power users want performance tuning

**Expand Automation Section:**
```
Agent System Performance:
  Max concurrent agents: [6]
  Agent timeout: [60] seconds
  Immediate agent workers: [4]
  Background agent workers: [6]
  [✓] Enable result caching
  [✓] Enable automatic retry
  Max retry attempts: [2]
```

### Phase 4: Advanced Module Configuration (Low Priority)
**Impact:** Expert users only

**Expand Advanced Section:**
```
Advanced Module Configuration
  ▼ Entity Manager
    Auto-generate threshold: [3] mentions
    [✓] Track entity mentions
    [✓] Use repository pattern

  ▼ File Manager
    [✓] Backup files before writing
    [✓] Use async write queue

  ▼ Write Queue
    Flush interval: [5] seconds
    Max queue size: [100] operations

  ▼ Task Queue
    Max workers: [4]
    Shutdown timeout: [30] seconds

  ▼ Update Checker
    Check interval: [86400] seconds (24h)
    [✓] Auto-check on startup
```

### Phase 5: Provider-Specific Configuration (Low Priority)
**Impact:** Mostly covered, missing edge cases

**Expand LLM Setup:**
```
Provider-Specific Settings
  ▼ Claude API
    [✓] Use prompt caching
    Extended thinking budget: [5000] tokens

  ▼ OpenAI
    API endpoint: (●) Responses ( ) Chat Completions

  ▼ OpenRouter
    Site URL: [____________________] (optional)
    App name: [RP Launcher__________]
```

---

## Implementation Notes

### IPC Protocol Extensions Needed

```python
# Get module configuration
GET_MODULE_CONFIG
Request: {module_id: "agent_coordinator"}
Response: {
    config: {
        max_concurrent_agents: 6,
        timeout: 60,
        ...
    }
}

# Set module configuration parameter
SET_MODULE_CONFIG
Request: {
    module_id: "agent_coordinator",
    param: "timeout",
    value: 120
}
Response: {success: true, requires_restart: true}

# Get agent configuration
GET_AGENT_CONFIG
Request: {agent_type: "background", agent_id: "memory_creation"}
Response: {config: {enabled: true}}

# Set agent configuration
SET_AGENT_CONFIG
Request: {
    agent_type: "background",
    agent_id: "memory_creation",
    param: "enabled",
    value: false
}
Response: {success: true, requires_restart: false}
```

### UI Component Reuse

The existing settings overlay already has all necessary widgets:
- ✅ `Switch` for boolean toggles
- ✅ `Slider` for numeric ranges
- ✅ `Input` for text/numbers
- ✅ `Select` for dropdowns
- ✅ `Collapsible` for grouping
- ✅ IPC communication infrastructure
- ✅ Save/load functionality
- ✅ Real-time field enable/disable

**Just need to add new sections and wire up IPC handlers!**

---

## Conclusion

The TUI has **excellent coverage of high-level settings** (36%), but is **missing detailed per-module/per-agent configuration** (64%).

**Next Steps:**
1. ✅ Prioritize agent configuration (Phase 1) - most user-facing
2. ✅ Add session/data configuration (Phase 2) - high user demand
3. ⚠️ Consider if Phases 3-5 needed (expert users can edit config.json)
4. ✅ Implement IPC handlers for module/agent config CRUD
5. ✅ Extend settings overlay with new sections

**Recommendation:** Focus on Phases 1-2 (agents + session/data). Phases 3-5 are "nice to have" but expert users can edit config.json directly.
