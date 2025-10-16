# RP Launcher Documentation

Complete reference guide for the RP Launcher system (`launch_rp_tui.py`) - the entry point and main interface for running roleplay sessions.

**Version**: Current (2025-10-16)
**Status**: Complete system documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Detailed Usage](#detailed-usage)
5. [F-Key Commands](#f-key-commands)
6. [Features](#features)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

---

## Overview

The RP Launcher is a three-component system that manages roleplaying sessions:

1. **Launcher** (`launch_rp_tui.py`) - Entry point, manages processes
2. **Bridge** (`tui_bridge.py`) - Backend process, handles Claude API and automation
3. **TUI** (`rp_client_tui.py`) - Frontend interface, displays chat and overlays

**Location**: `launch_rp_tui.py` (project root)

**Purpose**:
- Manage Python interpreter (detect conda issues)
- Select which RP to load
- Start the bridge process
- Launch the TUI interface
- Handle lifecycle and cleanup

---

## Architecture

### Three-Process System

```
┌─────────────────────────────────────────────────────────┐
│                  launch_rp_tui.py                       │
│              (Launcher / Process Manager)               │
│  - Handles Python interpreter issues                    │
│  - Detects conda pkgs cache conflicts                   │
│  - Selects RP folder                                    │
│  - Starts bridge and TUI                                │
│  - Manages cleanup                                      │
└──────┬──────────────────────────────┬───────────────────┘
       │                              │
       │ Spawns                       │ Spawns
       ▼                              ▼
┌──────────────────┐      ┌──────────────────────────┐
│  tui_bridge.py   │      │   rp_client_tui.py       │
│  (Backend)       │      │  (Frontend TUI)          │
│                  │      │                          │
│ • Calls Claude   │◄────►│ • Displays chat          │
│ • Runs agents    │ IPC  │ • Gets user input        │
│ • Updates state  │files │ • Shows overlays         │
│ • Manages files  │      │ • Keyboard shortcuts     │
└─────────┬────────┘      └──────────────────────────┘
          │
          ▼
    Claude API / DeepSeek API
```

### Communication Method

**Inter-Process Communication (IPC)** via JSON files:

| File | Direction | Purpose |
|------|-----------|---------|
| `state/rp_client_input.json` | TUI → Bridge | User message |
| `state/rp_client_response.json` | Bridge → TUI | Claude response |
| `state/rp_client_ready.flag` | TUI → Bridge | Input is ready |
| `state/rp_client_done.flag` | Bridge → TUI | Response is ready |
| `state/tui_active.flag` | TUI ↔ Launcher | TUI is running |

---

## Quick Start

### Basic Launch

```bash
# Auto-detect single RP or show menu for multiple RPs
python launch_rp_tui.py

# Launch specific RP by name
python launch_rp_tui.py "My RP Name"

# Skip update check
python launch_rp_tui.py --skip-update-check

# Run bridge in background (hidden)
python launch_rp_tui.py --background
```

### First Time Setup

1. Create an RP with: `python setup/quick_setup.py "My RP Name"`
2. Launch with: `python launch_rp_tui.py "My RP Name"`
3. TUI opens - start typing!

---

## Detailed Usage

### Launcher Process (launch_rp_tui.py)

#### What Happens on Launch

1. **Python Check** (Lines 15-90)
   - Detects if using conda pkgs cache Python
   - Relaunches with correct interpreter if needed
   - Checks for pythonw.exe and relaunches with python.exe

2. **Update Check** (Lines 259-306)
   - Checks for available updates
   - Shows notification if new version exists
   - Can be disabled with `--skip-update-check`

3. **RP Folder Selection** (Lines 309-376)
   - Scans `RPs/` directory for valid folders
   - Valid = contains `state/` subdirectory
   - Auto-selects if only one RP exists
   - Shows menu if multiple RPs exist
   - Can specify on command line: `launch_rp_tui.py "RP Name"`

4. **Bridge Start** (Lines 101-156)
   - Starts `tui_bridge.py` in separate process
   - Default: hidden background process
   - Debug mode: visible terminal window
   - Waits 0.1s for bridge to initialize

5. **TUI Launch** (Lines 387-391)
   - Creates `RPClientApp` instance
   - Runs TUI interface
   - Monitors bridge process

6. **Cleanup** (Lines 205-229)
   - On exit: terminates bridge process
   - Removes `tui_active.flag`
   - Graceful shutdown with 5-second timeout

#### Command-Line Options

```bash
# Specify RP name
python launch_rp_tui.py "Example RP"

# Skip update checking (faster startup)
python launch_rp_tui.py --skip-update-check

# Run bridge in background (future use)
python launch_rp_tui.py --background

# Combine options
python launch_rp_tui.py "My RP" --skip-update-check
```

### Bridge Process (tui_bridge.py)

**Location**: `src/tui_bridge.py`

**Purpose**: Backend worker that:
- Monitors for user input (IPC)
- Calls Claude API
- Runs automation agents
- Manages state files
- Sends responses back to TUI

**Features**:
- Uses modular automation system
- Caches agent results
- Debounces file writes
- Handles errors gracefully

**Startup**:
```bash
python src/tui_bridge.py "RP Name"
```

**Communication**:
- Reads: `state/rp_client_input.json`
- Writes: `state/rp_client_response.json`
- Monitors: `state/rp_client_ready.flag` (input signal)
- Creates: `state/rp_client_done.flag` (response signal)

### TUI Interface (rp_client_tui.py)

**Location**: `src/rp_client_tui.py`

**Purpose**: Frontend interface providing:
- Chat display
- Text input area
- Context information (chapter, time, location)
- Progress tracking
- Overlay menus
- Status messages

**Components**:
- **Header**: Shows time/clock
- **Context Panel**: Chapter, timestamp, location, active characters
- **Chat Display**: Conversation history
- **Input Area**: Multi-line text entry
- **Footer**: Available keyboard shortcuts
- **Overlays**: F-key accessible panels

---

## F-Key Commands

### Complete F-Key Reference

**Current Mapping** (from Line 1262-1275 of rp_client_tui.py):

| Key | Command | Overlay | Purpose |
|-----|---------|---------|---------|
| **F1** | Show Help | Help | Display keyboard shortcuts |
| **F2** | Show Character Sheet | Character | View {{user}} character sheet + memory |
| **F3** | Show Story Overview | Story | View story arc + STORY_GENOME combined |
| **F4** | Show Entities | Entities | View entity cards (characters, locations, orgs) |
| **F5** | Show Notes | Notes | View SCENE_NOTES.md (current session guidance) |
| **F6** | Show Modules | Modules | Toggle automation modules on/off |
| **F7** | Show Status | Status | View current RP status and progress |
| **F8** | Show Settings | Settings | Configure launcher settings |
| **F10** | Restart Bridge | — | Restart the bridge process |

### Other Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+J** / **Ctrl+Enter** | Send message |
| **Enter** | New line in input (not send) |
| **Escape** | Close any overlay |
| **Ctrl+Q** | Quit launcher |

### F-Key Details

#### F1 - Help
**Shows**: All keyboard shortcuts and available commands
**Content**: Dynamic help overlay listing all F-key functions
**Close**: Press Escape

#### F2 - Character Sheet
**Shows**: Combined view of:
- {{user}} character sheet (from `characters/{{user}}.md`)
- Character memory (if available)
- Quick reference for your character

**Content**:
```
# {{user}} Character Sheet

## 📖 Memory
[Character memory content from user_memory.md]

## Character Details
[Character sheet from characters/{{user}}.md]
```

**Close**: Press Escape

#### F3 - Story Overview
**Shows**: Combined story information:
- Current story arc (from `state/story_arc.md`)
- STORY_GENOME (from `STORY_GENOME.md`)

**Purpose**: Quick reference for where story is heading and what's planned

**Close**: Press Escape

#### F4 - Entities
**Shows**: All entity cards grouped by type:
- **Characters**: [CHAR] entities
- **Locations**: [LOC] entities
- **Organizations**: [ORG] entities

**Format**: Searchable list of all known entities with names and basic info

**Close**: Press Escape

#### F5 - Notes
**Shows**: Current session notes (from `SCENE_NOTES.md`)

**Purpose**: Session-specific guidance about current scene, goals, and focus

**Close**: Press Escape

#### F6 - Modules
**Shows**: Automation module toggles

**Available Modules**:
- Auto Entity Cards (enable/disable)
- Auto Story Arc (enable/disable)
- Auto Memory (enable/disable)
- Background agents (enable/disable)

**Purpose**: Enable/disable automation features on the fly

**Close**: Press Escape

#### F7 - Status
**Shows**: Current RP status:
- Response count
- Arc progress
- Active characters
- Current location
- Automation status

**Format**:
```
Response Count: 47 / 50
Arc Progress: 94% (3 responses until next arc)
Active Characters: Sarah, Alex
Current Location: Apartment - Living Room
Automation: ✅ ON
```

**Close**: Press Escape

#### F8 - Settings
**Shows**: Configuration options:
- API Key (OpenRouter or Anthropic)
- Model Selection
- Thinking Mode
- API Mode
- Advanced settings

**Purpose**: Configure how the launcher works

**Close**: Press Escape

#### F10 - Restart Bridge
**Action**: Restarts the bridge process
**Use When**: Bridge becomes unresponsive, errors, or after changing settings
**Result**: Bridge restarts, connection reestablished within ~2 seconds

---

## Features

### 1. Python Interpreter Management

**Problem Solved**: Conda environments can use wrong Python from pkgs cache

**Solution** (Lines 20-56):
- Detects if running from conda pkgs cache
- Automatically relaunches with correct Python
- Prevents Unicode/emoji errors

**Automatic**: Happens transparently on startup

---

### 2. Console Window Handling

**Problem Solved**: pythonw.exe doesn't show console window

**Solution** (Lines 70-90):
- Detects pythonw.exe usage
- Relaunches with python.exe
- Ensures visible console window

**Automatic**: Happens transparently on startup

---

### 3. Process Cleanup

**Orphaned Process Prevention** (Lines 35-49):
- Detects existing bridge processes
- Terminates them before launching new bridge
- Prevents multiple bridge instances

**Features**:
- Uses psutil if available
- Graceful termination
- 5-second timeout before forced kill

---

### 4. Update Checking

**Automatic Checks** (Lines 259-306):
- Checks GitHub for new versions on startup
- Shows notification if update available
- Caches results for 24 hours (configurable)
- 3-second timeout (doesn't block startup)
- Can skip with `--skip-update-check`

**Configuration**:
```json
{
  "check_for_updates": true,
  "update_check_interval": 86400
}
```

---

### 5. RP Folder Auto-Selection

**Smart Detection** (Lines 231-376):
- Scans RPs/ directory
- Validates folders (must have `state/` subdirectory)
- Auto-selects if only one valid RP
- Shows interactive menu if multiple exist

**Command-Line Override**:
```bash
python launch_rp_tui.py "Specific RP Name"
```

---

### 6. Bridge Management

**Starting Bridge** (Lines 101-156):
```python
process = start_bridge(rp_dir, background=False)
```

**Features**:
- Runs as separate process
- Background mode (hidden) or debug mode (visible)
- 0.1s initialization delay
- Process handle returned for cleanup

**Restarting Bridge** (Lines 177-202):
- Called when user presses F10
- Graceful stop and restart
- Auto-detects RP directory from flag files

---

### 7. Lifecycle Management

**Startup Sequence**:
1. Python check & relaunch if needed
2. Console check & relaunch if needed
3. Update check & display notification
4. RP folder selection
5. Bridge start
6. TUI launch

**Shutdown Sequence**:
1. TUI exits
2. TUI active flag removed
3. Bridge terminated (graceful with 5s timeout)
4. Processes cleaned up
5. Return to command line

---

## Configuration

### config.json (Project Root)

Located at project root (`config.json`)

**Update Check Settings**:
```json
{
  "check_for_updates": true,
  "update_check_interval": 86400
}
```

- `check_for_updates`: Enable/disable update checking
- `update_check_interval`: Seconds between checks (default: 24 hours = 86400)

### RP-Specific Configuration

Located at `{RP Name}/state/automation_config.json`

**Automation Settings**:
```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 50,
  "auto_memory_update": true,
  "memory_frequency": 15
}
```

**Settings**:
- `auto_entity_cards`: Enable automatic entity card generation
- `entity_mention_threshold`: How many mentions before creating card (2-3 typical)
- `auto_story_arc`: Enable automatic story arc generation
- `arc_frequency`: Generate arc every N responses (50 typical)
- `auto_memory_update`: Enable automatic memory creation
- `memory_frequency`: Create memory every N responses

---

## Troubleshooting

### Issue: "RP folder not found"

**Cause**: RP folder doesn't exist or isn't in `RPs/` directory

**Solution**:
1. Verify folder is in `RPs/` directory: `C:\....\RP Claude Code\RPs\{Name}`
2. Check folder name exactly matches what you specified
3. Verify folder contains `state/` subdirectory

**Example**:
```bash
# Wrong - folder not found
python launch_rp_tui.py "My RP"

# Right - if folder is RPs/My RP
python launch_rp_tui.py "My RP"

# Create new RP if missing
python setup/quick_setup.py "My RP"
```

---

### Issue: "Not a valid RP folder (no state/ directory)"

**Cause**: Folder doesn't have `state/` subdirectory

**Solution**:
1. Check folder contents: `RPs/{Name}/state/` should exist
2. If not: Run quick_setup to recreate structure
3. Or manually create `state/` directory and add required files

---

### Issue: Unicode/Emoji errors on startup

**Cause**: Running wrong Python interpreter (conda pkgs cache)

**Solution**:
- Launcher auto-detects and relaunches with correct Python
- If still occurs:
  1. Ensure conda environment is activated
  2. Verify `python --version` returns non-conda version
  3. Manually activate correct Python environment

---

### Issue: Bridge won't start or keeps crashing

**Cause**: Existing bridge process, port conflict, or configuration error

**Solution**:
1. **Restart bridge**: Press F10 in TUI
2. **Restart launcher**: Close TUI and relaunch
3. **Check bridge process**:
   ```bash
   # Kill any existing bridge processes
   taskkill /IM python.exe /F  # Windows (careful!)
   # Or more targeted:
   # Find python process running tui_bridge.py and kill it
   ```
4. **Check logs**: Look at `state/hook.log` for errors

---

### Issue: "pythonw.exe" error

**Cause**: Launcher started with pythonw.exe (no console window)

**Solution**:
- Launcher auto-detects and relaunches with python.exe
- If persistent: Use python.exe directly in shortcuts/batch files

---

### Issue: Responses not appearing or TUI frozen

**Cause**: Bridge not responding, API timeout, or communication issue

**Solution**:
1. Press F10 to restart bridge (wait 2 seconds)
2. Check API key in F8 settings
3. Check internet connection
4. Look at bridge terminal window for errors
5. Restart launcher completely

---

### Issue: Update notification keeps appearing

**Cause**: Update check not finding cached results

**Solution**:
1. Update the project: `git pull`
2. Or skip update check: `python launch_rp_tui.py --skip-update-check`
3. Or disable in config.json: `"check_for_updates": false`

---

## Advanced Usage

### Debug Mode (Visible Bridge)

See bridge terminal output for debugging:

```python
# Modify start_bridge() call (line 384)
_bridge_process = start_bridge(rp_dir, background=False)
```

This opens a visible terminal window showing bridge output.

### Skip Update Check

For faster startup (especially on slow connections):

```bash
python launch_rp_tui.py --skip-update-check
```

### Background Bridge Mode

Run bridge without visible window:

```bash
python launch_rp_tui.py --background
```

### Direct Bridge Launch

For development/debugging, launch bridge separately:

```bash
cd src
python tui_bridge.py "RP Name"
```

Then launch TUI in another terminal.

---

### Multiple RPs

**To switch between RPs**:
1. Close TUI (Ctrl+Q)
2. Launcher returns to RP selection menu
3. Choose different RP
4. Or specify on command line: `python launch_rp_tui.py "Other RP"`

---

### Customizing F-Keys

**To modify F-key bindings**:

Edit `src/rp_client_tui.py` lines 1262-1275:

```python
BINDINGS = [
    Binding("f1", "action_name", "Label"),
    # Add/modify your bindings here
]
```

Then implement corresponding `action_name()` method.

---

## Architecture Deep Dive

### Process Communication

**Message Flow**:

```
User types in TUI
    ↓
Ctrl+J pressed
    ↓
TUI writes state/rp_client_input.json
    ↓
TUI creates state/rp_client_ready.flag
    ↓
Bridge detects flag, reads input.json
    ↓
Bridge processes with Claude API
    ↓
Bridge writes state/rp_client_response.json
    ↓
Bridge creates state/rp_client_done.flag
    ↓
TUI detects done flag, reads response
    ↓
TUI displays response in chat
    ↓
Ready for next message
```

**Files Involved**:
- `state/rp_client_input.json` - User message JSON
- `state/rp_client_response.json` - Claude response JSON
- `state/rp_client_ready.flag` - Synchronization signal
- `state/rp_client_done.flag` - Completion signal
- `state/tui_active.flag` - TUI running indicator

### Error Handling

**Bridge Errors**:
- Logged to `state/hook.log`
- Shown in bridge terminal (if visible)
- TUI may show "No response" message
- User can restart with F10

**TUI Errors**:
- Logged to console
- May show as status message
- Can close and relaunch

**Launcher Errors**:
- Shown on console
- Cleanup automatically triggered
- Safe exit on all error paths

---

## Performance Considerations

### Process Overhead
- TUI: ~50-100MB RAM
- Bridge: ~100-150MB RAM (higher during API calls)
- Total: ~200-300MB typical

### Response Time
- TUI input → Bridge: <50ms (file-based IPC)
- Bridge → Claude API: 5-30 seconds (depends on model)
- Response → TUI display: <100ms
- Total turnaround: 5-30 seconds typical

### File I/O
- Uses debounced write queue (500ms default)
- Prevents disk thrashing
- State files written efficiently

---

## Security Notes

### API Keys
- Stored in launcher settings (F8)
- Passed to bridge via environment variables
- Not logged or displayed
- Store securely, don't commit to git

### Input Files
- User input sanitized before API call
- API responses validated
- File operations use safe error handling

### Process Security
- Bridge runs as separate user process
- TUI runs as separate process
- Limited inter-process communication
- Clean process cleanup on exit

---

## Related Documentation

- [RP_DIRECTORY_MAP.md](RP_DIRECTORY_MAP.md) - File structure and interactions
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Overall system design
- [AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md) - Background automation
- [CLAUDE.md](../CLAUDE.md) - Project guidelines

---

## Summary

The RP Launcher is a robust, user-friendly system for managing roleplay sessions. It handles:

✅ Process lifecycle management
✅ Python interpreter issues
✅ RP folder detection and selection
✅ Bridge process startup and shutdown
✅ TUI interface display
✅ Update checking
✅ Graceful error handling
✅ Process cleanup on exit

Users interact through:
- Simple command-line launch
- Interactive TUI interface
- F-key shortcuts for features
- Settings menu for configuration

Behind the scenes:
- Bridge handles API calls and automation
- State files enable IPC
- Write queue optimizes disk I/O
- Process management ensures stability

---

**Last Updated**: 2025-10-16
**Version**: 1.0.0
**Status**: Complete and current
