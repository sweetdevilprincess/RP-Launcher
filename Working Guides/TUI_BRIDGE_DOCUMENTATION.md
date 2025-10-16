# TUI Bridge Documentation

Complete reference for the TUI Bridge system (`tui_bridge.py`) - the backend process that connects the TUI interface to Claude and manages automation.

**Version**: Current (2025-10-16)
**Status**: Complete system documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Operating Modes](#operating-modes)
4. [Initialization & Configuration](#initialization--configuration)
5. [Message Processing Flow](#message-processing-flow)
6. [SDK Mode Details](#sdk-mode-details)
7. [API Mode Details](#api-mode-details)
8. [Prompt Caching](#prompt-caching)
9. [Extended Thinking](#extended-thinking)
10. [Background Automation](#background-automation)
11. [IPC Communication](#ipc-communication)
12. [Session Management](#session-management)
13. [Error Handling](#error-handling)
14. [Configuration](#configuration)

---

## Overview

The TUI Bridge is a backend worker process that:

- **Monitors for user input** via IPC (JSON files)
- **Processes messages** with automation system
- **Calls Claude** via SDK or API
- **Manages prompt caching** for token efficiency
- **Runs background agents** for analysis
- **Maintains sessions** across multiple messages
- **Returns responses** to TUI via IPC

**Location**: `src/tui_bridge.py` (461 lines)

**Launch**: Automatically started by launcher (`launch_rp_tui.py`)

**Can also run manually**: `python src/tui_bridge.py "RP Name"`

---

## Architecture

### Process Model

```
┌──────────────────┐
│   Launcher       │
│  (Python)        │
└────────┬─────────┘
         │ Starts bridge process
         ▼
┌──────────────────────────────────────┐
│     TUI Bridge (src/tui_bridge.py)    │
│      (Separate Python Process)        │
│                                       │
│  • FileManager (IPC)                 │
│  • Automation Orchestrator            │
│  • SDK or API Client                 │
│  • Conversation Manager               │
│  • Background Task Queue              │
└──────┬─────────────────────┬──────────┘
       │                     │
       │ Reads/Writes       │ Calls
       │ JSON files         │
       ▼                     ▼
    TUI (stdin)      Claude SDK / API
    (IPC files)      (Node.js or REST)
```

### Three-Process System (Launcher Level)

```
1. Launcher (launch_rp_tui.py)
   └─ Starts Bridge process
      └─ Bridge (tui_bridge.py)
         └─ Starts Node.js SDK bridge (if SDK mode)
   └─ Starts TUI process
      └─ TUI (rp_client_tui.py)
         └─ Communicates with Bridge via IPC
```

---

## Operating Modes

### 1. SDK Mode (Default)

**When Used**: When no API key is available or configured

**How It Works**:
- Python wrapper around Claude Code SDK bridge (Node.js)
- Persistent Node.js process for SDK communication
- Communicates via JSON over stdin/stdout
- No API key required (uses Claude Code/SDK)

**Features**:
- ✅ Streaming responses
- ✅ Prompt caching (via Claude API behind the scenes)
- ✅ Extended thinking modes
- ✅ Session management
- ✅ Real-time response display

**Requirements**:
- Node.js 18+ installed
- `npm install` run in `src/` directory
- Claude Code SDK available

**Performance**: High - streams responses in real-time

**Cost**: Depends on Claude Code/SDK configuration

**Location**: `src/clients/claude_sdk.py` and `src/clients/claude_sdk_bridge.mjs`

---

### 2. API Mode (Alternative)

**When Used**: When Anthropic API key is available and configured

**How It Works**:
- Direct HTTP calls to Anthropic Claude API
- Maintains conversation history locally
- Manages prompt caching directly
- Requires API key

**Features**:
- ✅ Direct API control
- ✅ Prompt caching with explicit cache stats
- ✅ Extended thinking modes
- ✅ Full conversation history management
- ✅ Token counting and optimization

**Requirements**:
- Anthropic API key (`ANTHROPIC_API_KEY` environment variable)
- OR API key configured in settings (F8) → saved to config.json

**Performance**: Good - HTTP calls with wait time for responses

**Cost**: Direct - pay per token used, visible in responses

**Location**: `src/clients/claude_api.py`

---

### Mode Selection Logic

```
Bridge Startup (tui_bridge.py lines 108-176):

1. Default: use_sdk_mode = True
2. Check config for "use_api_mode" flag
3. If API mode requested:
   a. Try to load API key
   b. If key found → Initialize API client
   c. If key NOT found → Fall back to SDK mode
   d. If error → Fall back to SDK mode
4. Initialize selected mode
5. Print startup message with mode
```

**Priority**:
1. Check global config: `config/config.json`
2. Override with local config: `state/config.json`
3. Check `use_api_mode` flag
4. If not set or false: Use SDK (default)
5. If set and key available: Use API
6. If set but key missing: Use SDK (fallback)

---

## Initialization & Configuration

### Startup Sequence

**Lines 78-182 in tui_bridge.py**:

1. **Verify Arguments** (Lines 79-92)
   - Check RP folder name provided
   - Verify RP folder exists

2. **Initialize Services** (Lines 101-106)
   - Create FileManager for IPC
   - Initialize AutomationOrchestrator for background tasks

3. **Load Configuration** (Lines 116-160)
   - Load global config (`config/config.json`)
   - Load local config (`state/config.json`) - overrides global
   - Check for `use_api_mode` flag
   - Load thinking mode configuration

4. **Initialize Client** (Lines 141-175)
   - If API mode: Initialize ClaudeAPIClient
   - Else: Initialize ClaudeSDKClient
   - Handle fallback scenarios

5. **Print Status** (Lines 177-181)
   - Show mode (SDK or API)
   - Show RP directory being monitored
   - Indicate ready for input

### Configuration Files

**Global Config**: `config/config.json`
```json
{
  "use_api_mode": false,              // false = SDK, true = API
  "thinking_mode": "megathink",       // or: disabled, think, think_hard, think_harder, ultrathink
  "thinking_budget": null,            // Custom budget (optional)
  "use_proxy": false,                 // Proxy mode for custom prompts
  "check_for_updates": true,          // Update checking
  "update_check_interval": 86400      // 24 hours
}
```

**Local Config** (per-RP): `{RP}/state/config.json`
- Overrides global config for this RP
- Same keys as global

---

## Message Processing Flow

### Complete Request-Response Cycle

**Lines 184-400+ in tui_bridge.py**:

```
1. Wait for Input (Lines 184-239)
   ├─ Check if TUI is still active (tui_active.flag)
   ├─ Check for ready flag (rp_client_ready.flag)
   └─ Read message from rp_client_input.json

2. Process Special Commands (Lines 204-239)
   └─ If "/new" command:
      ├─ Clear session flags
      ├─ Clear conversation history
      ├─ Clear agent cache
      └─ Send "Session reset" response

3. Run Automation (Lines 241-299)
   ├─ Call run_automation_with_caching()
   ├─ Load TIER_1, TIER_2, TIER_3 files
   ├─ Run immediate agents (5-10 second timeout)
   ├─ Extract entities, facts, plot threads
   └─ Generate dynamic prompt

4. Apply Advanced Features
   ├─ If proxy mode: Inject custom prompt
   ├─ If thinking mode: Set budget
   └─ If caching: Prepare cached context

5. Call Claude (API or SDK)
   ├─ Send prompt to Claude
   ├─ Get response
   ├─ Receive cache stats (if API mode)
   └─ Collect usage metrics

6. Update History (Lines 283-286 for API, SDK handles internally)
   ├─ Add user message to history
   ├─ Add assistant response to history
   └─ Persist history to file

7. Queue Background Tasks (Lines 290-325)
   ├─ Analyze response
   ├─ Extract memories
   ├─ Detect plot threads
   ├─ Find contradictions
   ├─ Extract knowledge
   └─ Analyze relationships

8. Send Response to TUI (Lines 327-345)
   ├─ Write response to rp_client_response.json
   ├─ Create done flag (rp_client_done.flag)
   ├─ Clear ready flag
   └─ Display confirmation

9. Continue Loop (Lines 346-348)
   └─ Wait for next message
```

### Timing

- **Step 3 (Automation)**: ~5-10 seconds
- **Step 5 (Claude call)**: 5-30 seconds (depends on model)
- **Step 7 (Background tasks)**: Starts parallel, doesn't block
- **Total turnaround**: ~10-40 seconds for user

---

## SDK Mode Details

### ClaudeSDKClient (`src/clients/claude_sdk.py`)

**What It Does**:
- Manages persistent Node.js SDK bridge process
- Handles JSON communication over pipes
- Streams responses character by character
- Manages session state

**Key Methods**:
- `__init__(cwd)` - Start Node.js bridge with working directory
- `query(prompt, cached_context)` - Send query, get streaming response
- `get_last_response()` - Get complete response after streaming
- `get_cache_stats()` - Get token/cache statistics
- `clear_session()` - Reset conversation

**Node.js Bridge** (`src/clients/claude_sdk_bridge.mjs`):
- Runs separately as Node.js process
- Uses @anthropic-ai/sdk
- Communicates with Python via JSON stdin/stdout
- Handles streaming and caching

**Streaming**:
- Receives response token-by-token
- Each chunk printed to bridge terminal
- TUI reads complete response from file

**Cache Stats**:
- Shows in bridge terminal
- Token counts for input/output
- Cache creation/read statistics
- Percent savings calculation

### SDK Mode Flow

```
TUI Message
    ↓
Bridge reads from rp_client_input.json
    ↓
Run automation (generate prompt)
    ↓
ClaudeSDKClient.query(prompt)
    ↓
Python sends JSON to Node.js process (stdin)
    ↓
Node.js SDK calls Claude API
    ↓
Node.js receives streaming response
    ↓
Node.js sends each chunk back to Python (stdout)
    ↓
Python receives chunks, accumulates response
    ↓
Bridge prints to terminal in real-time
    ↓
Bridge writes complete response to rp_client_response.json
    ↓
TUI reads response and displays
```

---

## API Mode Details

### ClaudeAPIClient (`src/clients/claude_api.py`)

**What It Does**:
- Direct HTTP client to Anthropic Claude API
- Uses requests library for HTTP
- Manages conversation history
- Handles prompt caching directly

**Key Methods**:
- `send_message(user_message, cached_context, conversation_history, thinking_mode, thinking_budget)` - Send message and get response
- `format_cache_stats(usage)` - Format usage/cache statistics
- `load_api_key()` - Load key from environment or config

**Prompt Caching**:
- Sends TIER_1 files as cached context
- Explicit `cache_control` directives in API calls
- Claude API handles cache creation/retrieval
- Results in significant token savings (54-61% typical)

**Extended Thinking**:
- `thinking_mode` parameter controls budget
- Options: disabled, think, think_hard, megathink, think_harder, ultrathink
- Custom `thinking_budget` overrides mode

### API Mode Flow

```
TUI Message
    ↓
Bridge reads from rp_client_input.json
    ↓
Run automation (generate prompt)
    ↓
Get conversation history from ConversationManager
    ↓
ClaudeAPIClient.send_message()
    ↓
Build HTTP request with:
  - User message
  - Cached context (TIER_1)
  - Conversation history
  - System prompt (if proxy mode)
  - Thinking parameters
    ↓
POST to https://api.anthropic.com/v1/messages
    ↓
Wait for response (no streaming in current implementation)
    ↓
Receive complete response + usage stats
    ↓
Print cache stats to bridge terminal
    ↓
ConversationManager records user + assistant messages
    ↓
Bridge writes complete response to rp_client_response.json
    ↓
TUI reads response and displays
```

---

## Prompt Caching

### How It Works

**Automation generates two parts of prompt**:

1. **Cached Context** (TIER_1 files)
   - AUTHOR'S_NOTES.md
   - STORY_GENOME.md
   - NAMING_CONVENTIONS.md
   - SCENE_NOTES.md
   - Current state, story arc
   - Player character sheet
   - First chapter excerpt
   - ~4-10KB typical

2. **Dynamic Prompt** (User message + TIER_2/3)
   - User's message
   - Current situation (TIER_2/3)
   - Relevant entities (TIER_3)
   - ~1-5KB typical

### SDK Mode Caching

- SDK bridge sends cached_context to Claude API
- Claude API handles cache creation/retrieval
- Cache persists across SDK calls
- Cache stats shown in bridge terminal

### API Mode Caching

- Explicit `cache_control: {"type": "ephemeral"}` on cached context
- API explicitly creates/reads cache
- Token savings calculated and displayed
- Conversation history NOT cached (changes each turn)

### Cache Statistics (API Mode)

```
📊 Token Usage:
  Input: 1,234 tokens
  Output: 567 tokens
  💾 Cache Read: 8,901 tokens (saved!)
  💰 Savings: 87.8% (CACHE_HIT)
```

**Cache Hit**: Claude used cached context (87% token savings)
**Cache Write**: First use of context (25% overhead, saves on future uses)
**No Cache**: Context below 1024 tokens or too variable

---

## Extended Thinking

### Thinking Modes

| Mode | Budget | Use Case |
|------|--------|----------|
| **disabled** | 0 | No thinking - fastest |
| **think** | ~5k | Quick planning |
| **think_hard** | ~10k | Feature design |
| **megathink** | ~10k | Standard (default) |
| **think_harder** | ~25k | Complex decisions |
| **ultrathink** | ~32k | System design |

### Configuration

**In config.json**:
```json
{
  "thinking_mode": "megathink",    // Change default
  "thinking_budget": 15000         // Override budget
}
```

**Or in F8 Settings (TUI)**:
- Select thinking mode
- Optionally set custom budget
- Saved to config.json

### How It's Used

**SDK Mode**:
- Passes thinking parameters to Node.js bridge
- Bridge includes in SDK call

**API Mode**:
- `thinking_mode` parameter to API
- `thinking_budget` for custom override
- Claude API handles thinking internally

---

## Background Automation

### What Runs in Background

**Lines 290-325 in tui_bridge.py**:

After response received from Claude, queue these tasks:

1. **Response Analyzer** - Analyze response quality
2. **Entity Extraction** - Find characters/locations mentioned
3. **Memory Creation** - Extract memorable moments
4. **Fact Extraction** - Extract world facts
5. **Plot Thread Detection** - Find story threads
6. **Relationship Analysis** - Analyze character dynamics
7. **Contradiction Detection** - Find inconsistencies
8. **Knowledge Extraction** - Extract world knowledge

### Non-Blocking Execution

- Tasks added to queue immediately after response
- User can type next message while tasks run
- Results cached in `state/agent_analysis.md`
- Next response includes agent insights

### Task Configuration

In `state/automation_config.json`:

```json
{
  "auto_entity_cards": true,          // Create entity cards
  "entity_mention_threshold": 2,      // After 2 mentions
  "auto_story_arc": true,             // Generate story arcs
  "arc_frequency": 50,                // Every 50 responses
  "auto_memory_update": true,         // Create memories
  "memory_frequency": 15              // Every 15 responses
}
```

---

## IPC Communication

### File-Based Inter-Process Communication

**Why Files Instead of Pipes**:
- TUI and Bridge are completely separate processes
- Can run on different computers theoretically
- Survives process crashes (data in files)
- Easy to debug (can inspect files)
- No complex IPC setup needed

### Input Flow

```
TUI (rp_client_tui.py)
  ├─ User types message
  ├─ User presses Ctrl+Enter
  ├─ Write message to: state/rp_client_input.json
  │  {
  │    "message": "user's message text"
  │  }
  ├─ Create flag: state/rp_client_ready.flag
  └─ Poll for: state/rp_client_done.flag

Bridge (tui_bridge.py)
  ├─ Poll for: state/rp_client_ready.flag
  ├─ When flag exists, read: state/rp_client_input.json
  ├─ Process message
  ├─ Delete flag: state/rp_client_ready.flag
  └─ Continue...
```

### Output Flow

```
Bridge (tui_bridge.py)
  ├─ Process complete
  ├─ Write response to: state/rp_client_response.json
  │  {
  │    "response": "claude's response text"
  │  }
  ├─ Create flag: state/rp_client_done.flag
  └─ Continue...

TUI (rp_client_tui.py)
  ├─ Poll for: state/rp_client_done.flag
  ├─ When flag exists, read: state/rp_client_response.json
  ├─ Display response in chat
  ├─ Delete flag: state/rp_client_done.flag
  └─ Ready for next message
```

### Synchronization Files

| File | Set By | Checked By | Purpose |
|------|--------|-----------|---------|
| `rp_client_ready.flag` | TUI | Bridge | "Input is ready" |
| `rp_client_done.flag` | Bridge | TUI | "Response is ready" |
| `tui_active.flag` | TUI | Bridge | "TUI is running" |
| `claude_session_active.flag` | Bridge | Bridge | Session tracking |

### Race Condition Prevention

- Flag creation signals readiness
- File read only after flag exists
- Flag deletion after read confirms processing
- Polling interval: 0.5 seconds

---

## Session Management

### What Is a Session

A session is a continuous conversation. It includes:
- Conversation history (user + assistant messages)
- Context from TIER_1 files
- Cache state (if using caching)
- Entity knowledge accumulated so far

### Session Types

**Continuous Session** (Default):
- Remembers all previous messages
- Claude has context from entire RP
- Prompt caching accumulates benefits
- Session persists until `/new` command

**Fresh Session** (`/new` command):
- Clears conversation history
- Clears session flags
- Clears agent cache
- Next message starts fresh conversation

### Session Implementation

**SDK Mode** (Lines 214-216):
- `sdk_client.clear_session()` - Resets Node.js bridge
- Session history managed in bridge

**API Mode** (Lines 211-213):
- `conversation_manager.clear_history()` - Clears Python history
- Next message will have no prior messages

### ConversationManager (`src/clients/claude_api.py`)

Manages conversation history for API mode:

```python
# Add messages to history
conversation_manager.add_user_message(message)
conversation_manager.add_assistant_message(response)

# Get history for API call
history = conversation_manager.get_history()

# Clear for fresh start
conversation_manager.clear_history()
```

**History Stored In**: `state/conversation_history.json`

---

## Error Handling

### Error Scenarios

**Lines 157-175 in tui_bridge.py**:

1. **SDK Initialization Error**
   - Print error message
   - Show troubleshooting steps
   - Mention Node.js requirement
   - Exit with error code 1

2. **API Mode Without Key**
   - Print warning
   - Fall back to SDK mode
   - Continue normally

3. **Config Load Error**
   - Caught exception
   - Fall back to defaults
   - Continue with SDK mode

4. **Message Processing Error** (Lines 199-202)
   - Log error
   - Skip ready flag
   - Try again next cycle

### Error Recovery

- Most errors don't crash bridge
- Bridge continues running
- Notifies about problem
- Falls back to working mode
- User can continue

### Debugging

**Check Bridge Terminal**:
- Print all important events
- Error messages are descriptive
- Shows mode selection
- Shows automation progress

**Check Log File**:
- `state/hook.log` - Full execution log
- Captures all agent activity
- Timestamps for debugging

---

## Configuration

### Global Configuration

**File**: `config/config.json` (created by TUI F8 settings)

```json
{
  "use_api_mode": false,
  "thinking_mode": "megathink",
  "thinking_budget": null,
  "use_proxy": false,
  "check_for_updates": true,
  "update_check_interval": 86400
}
```

### Per-RP Configuration

**File**: `{RP}/state/config.json`

- Overrides global for this RP only
- Same format as global
- Optional (uses global if not present)

### Environment Variables

**API Mode Only**:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Bridge will use this if set.

---

## Summary

The TUI Bridge is a sophisticated backend that:

✅ **Supports Two Modes**: SDK (default, no key needed) and API (direct, key required)
✅ **Processes Messages**: With full automation pipeline
✅ **Manages Caching**: For 50-90% token savings
✅ **Handles Sessions**: Continuous or fresh
✅ **Runs Background Tasks**: Non-blocking analysis
✅ **Communicates via Files**: Robust IPC
✅ **Handles Errors Gracefully**: Falls back or continues
✅ **Configurable**: Per-instance or per-RP settings

Both modes support:
- Prompt caching
- Extended thinking
- Conversation history
- Background automation
- Proxy mode for custom prompts

---

**Related Documentation**:
- [LAUNCHER_DOCUMENTATION.md](LAUNCHER_DOCUMENTATION.md) - Launcher system
- [RP_DIRECTORY_MAP.md](RP_DIRECTORY_MAP.md) - File structure
- [AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md) - Automation agents
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Overall design

---

**Last Updated**: 2025-10-16
**Version**: 1.0.0
**Status**: Complete and current
