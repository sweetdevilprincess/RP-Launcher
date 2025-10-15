# RP Claude Code System - Complete Overview

**Last Updated:** October 12, 2025

This document provides a complete technical overview of the RP Claude Code TUI system.

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Components](#components)
3. [Data Flow](#data-flow)
4. [File Structure](#file-structure)
5. [How to Use](#how-to-use)
6. [Related Documentation](#related-documentation)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAUNCHES                             │
│                      launch_rp_tui.py                            │
└──────────────┬──────────────────────────────┬────────────────────┘
               │                              │
               ▼                              ▼
    ┌──────────────────┐          ┌─────────────────────┐
    │   TUI WINDOW     │          │  BRIDGE WINDOW      │
    │ (rp_client_tui)  │◄────────►│  (tui_bridge.py)    │
    │                  │  Files   │                     │
    │ - User types     │          │ - Runs automation   │
    │ - Shows overlays │          │ - Calls Claude Code │
    │ - Displays chat  │          │ - Returns response  │
    └──────────────────┘          └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │    CLAUDE CODE CLI   │
                                  │  (claude.exe)        │
                                  └──────────────────────┘
```

---

## Components

### 1. **Launcher** (`launch_rp_tui.py`)

**What it does:**
- Detects and selects RP folder
- Starts the bridge in a separate terminal window
- Starts the TUI in current window
- Manages cleanup when TUI closes

**Who runs it:** User (double-click or command line)

**Commands:**
```bash
# Normal launch (bridge visible for debugging)
python launch_rp_tui.py

# Future: Background mode (bridge hidden)
python launch_rp_tui.py --background
```

**Process:**
1. Fixes Python path if needed (conda pkgs cache issue)
2. Scans for RP folders with `state/` subdirectory
3. Prompts user to select folder (if multiple)
4. Starts bridge in new terminal (`CREATE_NEW_CONSOLE` on Windows)
5. Starts TUI in current terminal
6. Waits for TUI to close
7. Stops bridge and cleans up

---

### 2. **TUI** (`rp_client_tui.py`)

**What it does:**
- Provides terminal interface for typing messages
- Shows quick-access overlays (Memory, Arc, Characters, etc.)
- Displays conversation history
- Shows real-time context (chapter, time, location, progress)

**Who runs it:** Automatically started by launcher

**Key Features:**

#### **Text Input:**
- Multi-line text area (Enter for new lines)
- Ctrl+Enter to send message
- No glitches, unlimited length

#### **Quick Access Overlays:**
| Key | Overlay | Shows |
|-----|---------|-------|
| F1 | Help | Keyboard shortcuts |
| F2 | Memory | User memory (state/user_memory.md) |
| F3 | Arc | Story arc (state/story_arc.md) |
| F4 | Characters | Active and all characters |
| F5 | Scene Notes | SCENE_NOTES.md |
| F6 | Entities | Tracked entities (entity_tracker.json) |
| F7 | Genome | Story Genome (STORY_GENOME.md) |
| F8 | Status | System status and automation config |

#### **Context Panel:**
Real-time display showing:
- Current chapter
- Timestamp
- Location
- Active characters
- Response count (X/250)
- Arc progress bar
- Next arc generation countdown

**How it communicates:**
Uses file-based communication with bridge:

**Sending a message:**
1. User types and presses Ctrl+Enter
2. TUI writes message to `state/rp_client_input.txt`
3. TUI creates `state/rp_client_ready.flag` (signal to bridge)
4. TUI shows "⏳ Waiting for Claude..."

**Receiving a response:**
1. TUI polls for `state/rp_client_done.flag` (every 0.5 seconds)
2. When flag exists, reads `state/rp_client_response.txt`
3. Displays response in chat
4. Cleans up flag files
5. Shows "✅ Response received"

---

### 3. **Bridge** (`tui_bridge.py`)

**What it does:**
- Monitors for TUI input
- Runs ALL automation (entity tracking, time calculation, file loading)
- Builds enhanced prompt with context
- Calls Claude Code CLI
- Returns response to TUI

**Who runs it:** Automatically started by launcher (visible in separate window)

**Main Loop:**
```python
while True:
    if ready_flag exists and input_file exists:
        1. Read user message from input file
        2. Run automation (see AUTOMATION_GUIDE.md)
        3. Build enhanced prompt with TIER files
        4. Call Claude Code CLI
        5. Write response to response file
        6. Create done flag
        7. Clean up ready flag

    sleep(0.5 seconds)
```

**Bridge Terminal Output:**
```
🌉 TUI Bridge started
📁 Monitoring: Example RP
⏳ Waiting for TUI input...

📨 Received input from TUI
📝 Message: Hello
⚙️ Running automation (Phases 1-3: Full System)...
📚 TIER_3 entities loaded: Sarah, Marcus
✅ Automation complete
🤖 Sending to Claude Code...
✓ Response received
📤 Response sent to TUI

⏳ Waiting for next input...
```

**What automation does:** (See [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) for full details)
- Increments response counter
- Tracks entities (capitalized words)
- Calculates time from activities
- Loads files based on TIER system
- Triggers conditional file loading
- Auto-generates entity cards (at mention threshold)
- Auto-generates story arcs (every 50 responses)
- Updates status files
- Logs everything to hook.log

---

### 4. **Client Modules** (`work_in_progress/clients/`)

#### **`claude.py`**
Wraps Claude Code CLI for easy calling.

**What it does:**
- Finds `claude.exe` in common locations
- Calls Claude Code with message via stdin (avoids command-line length limits)
- Returns stdout, stderr, return code

**Key function:**
```python
run_claude(message, cwd=rp_dir, timeout=300)
```

**Claude.exe locations checked:**
1. System PATH
2. `%USERPROFILE%\.local\bin\claude.exe` ✓ (Your location)
3. `%LOCALAPPDATA%\Programs\claude\claude.exe`
4. `%PROGRAMFILES%\Claude\claude.exe`

#### **`deepseek.py`**
Wraps DeepSeek API (via OpenRouter) for auto-generation.

**What it does:**
- Loads API key from env vars or secrets.json
- Calls DeepSeek API for entity cards, summaries, arcs
- Returns generated text

**API key sources (checked in order):**
1. `DEEPSEEK_API_KEY` environment variable
2. `OPENROUTER_API_KEY` environment variable
3. `{rp_dir}/state/secrets.json`
4. `./state/secrets.json`

**Used by:**
- Auto entity card generation
- Auto story arc generation
- Auto chapter summaries (not yet implemented)

---

### 5. **Utilities** (`work_in_progress/utils/`)

#### **`python_fix.py`**
Fixes conda Python path issues.

**The Problem:**
Windows file associations sometimes point to conda's package cache Python (`C:\Users\green\miniconda3\pkgs\python-3.13.5-...\python.exe`) instead of the environment Python (`C:\Users\green\miniconda3\python.exe`).

The pkgs cache Python doesn't have your installed packages (textual, rich, etc.), causing import errors.

**The Solution:**
1. Detects if running from pkgs cache Python
2. Finds correct environment Python
3. Relaunches script with correct Python
4. **PyInstaller-aware:** Skips fix if running from .exe (bundled Python)

**Used by:**
- `launch_rp_tui.py`
- `tui_bridge.py`

---

## Data Flow

### Complete Message Flow

```
USER TYPES MESSAGE
      ↓
TUI: Write to state/rp_client_input.txt
TUI: Create state/rp_client_ready.flag
TUI: Show "Waiting..."
      ↓
BRIDGE: Detect ready flag
BRIDGE: Read input file
BRIDGE: Run automation
  ├─ Increment counter (1 → 2)
  ├─ Track entities (Sarah: 1 mention → 2 mentions)
  ├─ Calculate time (eating: 10 minutes)
  ├─ Load TIER_1 files (always)
  ├─ Load TIER_2 files (if response count % 4 == 0)
  ├─ Load TIER_3 files (if triggers match: "Sarah" → load Sarah.md)
  ├─ Check for auto-generation
  │   ├─ Entity cards? (if mentions >= threshold)
  │   └─ Story arc? (if count % 50 == 0)
  └─ Build enhanced prompt
      ↓
BRIDGE: Call claude.exe with enhanced prompt (via stdin)
      ↓
CLAUDE CODE: Process message
CLAUDE CODE: Generate response
      ↓
BRIDGE: Receive response
BRIDGE: Write to state/rp_client_response.txt
BRIDGE: Create state/rp_client_done.flag
      ↓
TUI: Detect done flag
TUI: Read response file
TUI: Display response
TUI: Clean up flags
TUI: Show "Response received"
```

---

## File Structure

```
RP Claude Code/
├── launch_rp_tui.py          # Main launcher (START HERE)
├── rp_client_tui.py           # TUI interface
├── tui_bridge.py              # Bridge + automation
├── requirements.txt           # Python dependencies
├── config/
│   └── CLAUDE.md              # Project instructions for Claude
│
├── work_in_progress/          # Refactored modules
│   ├── clients/
│   │   ├── claude.py          # Claude Code CLI wrapper
│   │   └── deepseek.py        # DeepSeek API wrapper
│   └── utils/
│       └── python_fix.py      # Python path fix
│
├── Guidelines/                # RP guidelines (TIER_2)
│   ├── Timing.txt             # Activity time costs
│   └── Session_End_Protocol.md
│
├── templates/                 # Templates for new RPs
│   ├── TEMPLATE_automation_config.json
│   ├── TEMPLATE_ENTITY_CHARACTER.md
│   └── ...
│
├── scripts/                   # Helper scripts
│   └── deepseek_call.sh       # Legacy bash script
│
├── readmes/                   # Documentation
│   ├── SYSTEM_OVERVIEW.md     # This file
│   ├── AUTOMATION_GUIDE.md    # Automation details
│   └── FILE_LOADING_TIERS.md  # TIER system
│
├── Writing_Style_Guide.md     # Style guidelines (TIER_2)
├── NPC_Interaction_Rules.md   # NPC rules (TIER_2)
├── POV_and_Writing_Checklist.md  # POV checklist (TIER_2)
├── Time_Tracking_Guide.md     # Time tracking (TIER_2)
├── Story Guidelines.md        # Story guidelines (TIER_2)
│
└── Example RP/                # Example RP folder
    ├── Example RP.md          # RP overview
    ├── AUTHOR'S_NOTES.md      # Author notes (TIER_1)
    ├── STORY_GENOME.md        # Story outline (TIER_1)
    ├── SCENE_NOTES.md         # Scene notes (TIER_1)
    ├── CURRENT_STATUS.md      # Auto-generated status
    ├── characters/
    │   ├── {{user}}.md        # User character (TIER_1)
    │   └── Alex.md            # Main character (TIER_1)
    ├── entities/
    │   └── [CHAR] Sarah.md    # Conditional (TIER_3)
    ├── chapters/
    │   └── Chapter 2.txt      # Chapter summaries
    └── state/
        ├── current_state.md   # Current state (TIER_1)
        ├── story_arc.md       # Story arc (TIER_1)
        ├── user_memory.md     # User memory
        ├── response_counter.txt     # Response count
        ├── entity_tracker.json      # Entity tracking
        ├── automation_config.json   # Automation settings
        ├── trigger_history.json     # TIER_3 trigger tracking
        ├── hook.log                 # Automation log
        ├── rp_client_input.txt      # TUI → Bridge
        ├── rp_client_response.txt   # Bridge → TUI
        ├── rp_client_ready.flag     # Signal: input ready
        └── rp_client_done.flag      # Signal: response ready
```

---

## How to Use

### First Time Setup

1. **Install Dependencies:**
   ```bash
   cd "C:\Users\green\Desktop\RP Claude Code"
   pip install -r requirements.txt
   ```

2. **Create RP Folder:**
   - Copy `Example RP/` folder
   - Rename to your RP name
   - Edit files (characters, story genome, etc.)
   - Must have `state/` subdirectory

3. **(Optional) Configure Automation:**
   - Edit `{your RP}/state/automation_config.json`
   - Set thresholds, enable/disable features

### Daily Usage

**Launch:**
```bash
# Just double-click:
launch_rp_tui.py

# Or from terminal:
python launch_rp_tui.py
```

**What happens:**
1. Two windows open:
   - **Bridge window** (debug output)
   - **TUI window** (your interface)

2. Type your RP message in TUI
3. Press **Ctrl+Enter** to send
4. Watch bridge window for automation activity
5. Response appears in TUI

**Close:**
- Press **Ctrl+Q** in TUI
- Both windows close automatically

### Keyboard Shortcuts

**In TUI:**
- `Ctrl+Enter` - Send message
- `Enter` - New line
- `Ctrl+Q` - Quit
- `F1` - Help
- `F2-F8` - Quick access overlays (Memory, Arc, etc.)
- `ESC` - Close overlay

---

## Related Documentation

- **[AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)** - Detailed automation features
  - Entity tracking
  - Time calculation
  - Auto-generation (cards, arcs)
  - Trigger system

- **[FILE_LOADING_TIERS.md](FILE_LOADING_TIERS.md)** - TIER system explained
  - TIER_1: Always loaded
  - TIER_2: Periodic loading
  - TIER_3: Conditional/triggered
  - TIER_3 escalation rules

---

## Troubleshooting

### Bridge not connecting to Claude
**Symptom:** "Claude Code CLI not found" error

**Solutions:**
1. Make sure Claude Code is installed
2. Check that `claude.exe` exists at `C:\Users\green\.local\bin\claude.exe`
3. Or add Claude to system PATH

### Import errors (textual, rich, etc.)
**Symptom:** "No module named 'textual'"

**Solution:**
Python path issue. The launcher should auto-fix this. If not:
```bash
# Explicitly use conda Python:
C:\Users\green\miniconda3\python.exe launch_rp_tui.py
```

### TUI closes immediately
**Symptom:** Window flashes and closes

**Solution:**
1. Launch from terminal to see error
2. Check that RP folder has `state/` subdirectory
3. Check requirements are installed

---

## Future Enhancements

- **Background mode** - Hide bridge window (`--background` flag)
- **PyInstaller packaging** - Single .exe file
- **Additional automation** - Chapter summaries, memory updates
- **Enhanced TUI** - Better chat display, message history

---

*For questions or issues, check the bridge terminal for detailed logs.*
