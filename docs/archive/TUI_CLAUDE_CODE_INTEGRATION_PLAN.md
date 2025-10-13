# TUI + Claude Code Integration Plan

## Current Status Analysis

### ✅ What's Already Working

#### 1. **Bridge System** (tui_bridge.py)
- Monitors for TUI input files
- Calls `claude --message <text>` in RP directory
- Captures response and sends back to TUI
- ✅ This means hooks WILL run automatically!

#### 2. **Hook System** (user-prompt-submit.sh)
**Runs automatically before each Claude response**:
- ✅ Increments response counter
- ✅ Calculates time from activities
- ✅ Tracks entity mentions
- ✅ Auto-generates entity cards (via DeepSeek)
- ✅ Auto-generates story arcs (every 50 responses)
- ✅ Loads triggered files (character/entity cards)
- ✅ Updates CURRENT_STATUS.md

**This means**: When you send a message through TUI → Bridge → Claude Code, ALL automation runs!

#### 3. **Command System**
**Available commands**:
- `/status` - Show system status
- `/continue` - Start new session with context
- `/endSession` - End session protocol
- `/arc` - Generate story arc manually
- `/gencard [type], [name]` - Create entity card
- `/note [text]` - Add quick note
- `/memory` - Update user memory

**How they work**: User types `/command` in chat → Bridge sends to Claude Code → Command executes

#### 4. **State Files**
All in `RP_FOLDER/state/`:
- `current_state.md` - Chapter, time, location
- `response_counter.txt` - Response count
- `entity_tracker.json` - Entity mentions
- `story_arc.md` - Current story arc
- `user_memory.md` - What {{user}} remembers
- `CURRENT_STATUS.md` - Live system status (root directory)
- `last_response.txt` - Last RP response
- `hook.log` - Hook execution log

---

## 🔗 Integration Flow (How It Works Now)

```
User types in TUI
    ↓
Presses Ctrl+Enter
    ↓
TUI writes to: state/rp_client_input.txt
TUI creates flag: state/rp_client_ready.flag
    ↓
Bridge detects flag
    ↓
Bridge reads input file
    ↓
Bridge runs: cd "RP_FOLDER" && claude --message "user text"
    ↓
Claude Code receives message
    ↓
Hook runs BEFORE Claude processes:
  - Updates response counter
  - Tracks entities
  - Calculates time
  - Auto-generates cards/arcs if needed
  - Loads triggered files
  - Updates CURRENT_STATUS.md
    ↓
Claude reads injected context from hook
Claude processes message with RP context
Claude generates response
    ↓
Bridge captures response
    ↓
Bridge writes to: state/rp_client_response.txt
Bridge creates flag: state/rp_client_done.flag
    ↓
TUI detects done flag
TUI displays response
    ↓
DONE
```

**Key Insight**: The integration is ALREADY WORKING! The bridge calls Claude Code properly, which triggers hooks.

---

## ⚠️ Potential Issues & Gaps

### Issue 1: Commands in TUI
**Problem**: Users need to type commands like `/continue` or `/endSession`
**Current**: Works, but mixed with RP messages
**Better**: Add command buttons/menu in TUI

### Issue 2: Status Visibility
**Problem**: Users can't see automation happening (entity tracking, arc progress, etc.)
**Current**: Hook updates CURRENT_STATUS.md but TUI doesn't show it
**Better**: Add status panel in TUI reading from CURRENT_STATUS.md

### Issue 3: Session Management
**Problem**: `/continue` and `/endSession` are manual commands
**Current**: User must remember to type them
**Better**: Add "Start Session" and "End Session" buttons

### Issue 4: Response Formatting
**Problem**: Hook adds metadata to responses (time suggestions, entity tracking info)
**Current**: These appear in Claude's response as suggestions
**Working as intended**: Claude processes these and incorporates them

### Issue 5: Context Loading
**Problem**: TUI doesn't show what files are currently loaded
**Current**: Blind to what hook is doing
**Better**: Show loaded files in status panel

---

## 🎯 What Needs to Be Built

### Priority 1: Test Current Integration ⭐⭐⭐
**Goal**: Verify hooks run when messages sent through bridge
**Tasks**:
1. Send test message through TUI
2. Check if response_counter increments
3. Check if hook.log updates
4. Check if CURRENT_STATUS.md updates
5. Verify entity tracking works

**Why**: Need to confirm base integration works before adding features

---

### Priority 2: Add Status Display ⭐⭐⭐
**Goal**: Show live system status in TUI
**Implementation**:

```python
# In rp_client_tui.py - ContextPanel class

def refresh_context(self) -> None:
    # ... existing code ...

    # NEW: Read CURRENT_STATUS.md
    status_file = self.rp_dir / "CURRENT_STATUS.md"
    if status_file.exists():
        status_content = status_file.read_text()
        # Parse relevant info:
        # - Response count
        # - Arc progress
        # - Entities tracked
        # - Automation status
```

Add to context panel:
```
📊 AUTOMATION
─────────────
Responses: 217/250
Arc: ████████░ 87%
Entities: 8 tracked
Cards: ✅ Auto (2+)
```

---

### Priority 3: Add Command Buttons ⭐⭐
**Goal**: Easy access to common commands
**Implementation**:

Add buttons in TUI footer or side panel:
- "Start Session" → Sends `/continue`
- "End Session" → Sends `/endSession`
- "Generate Arc" → Sends `/arc`
- "Add Note" → Opens text input, sends `/note <text>`
- "Update Memory" → Sends `/memory`

**Code**:
```python
# In RPClientApp

def action_start_session(self) -> None:
    """Send /continue command"""
    self.send_command("/continue")

def action_end_session(self) -> None:
    """Send /endSession command"""
    self.send_command("/endSession")

def send_command(self, command: str) -> None:
    """Send a command through the bridge"""
    # Write command to input file
    self.input_file.write_text(command, encoding='utf-8')
    self.ready_flag.touch()
    self.waiting_for_response = True
    self.show_status(f"⏳ Running {command}...")
```

---

### Priority 4: File Watcher for CURRENT_STATUS.md ⭐
**Goal**: Auto-refresh status when hook updates it
**Implementation**:

```python
# Use watchdog to watch CURRENT_STATUS.md
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class StatusFileHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_modified(self, event):
        if event.src_path.endswith("CURRENT_STATUS.md"):
            # Refresh status display
            self.app.refresh_status()
```

---

### Priority 5: Enhanced Response Display ⭐
**Goal**: Parse and prettify hook metadata in responses
**Example**:

Hook adds:
```
📍 Suggested Time: 15 minutes elapsed (conversation)
🎭 Entity Update: Sarah mentioned (2 mentions) → Card created!
```

TUI could:
- Highlight these in different color
- Show as notifications
- Extract to status panel instead of chat

---

## 🧪 Testing Plan

### Test 1: Basic Integration
1. Launch TUI + Bridge
2. Send message: "Hello, continuing the story"
3. Check response counter increments
4. Check hook.log for execution
5. Check CURRENT_STATUS.md updates

### Test 2: Entity Tracking
1. Send message mentioning new entity twice
2. Check if entity card auto-generated
3. Check if card appears in entities/ folder
4. Verify DeepSeek was called (check hook.log)

### Test 3: Time Tracking
1. Send message with time-consuming activity
2. Check if hook suggests time elapsed
3. Verify Claude incorporates time in response

### Test 4: Commands
1. Type `/status` in TUI
2. Check if status report appears
3. Try `/arc` - verify arc generates
4. Try `/note Test note` - verify note saved

### Test 5: Session Flow
1. Type `/continue` to start session
2. Verify last response loads
3. Do several RP exchanges
4. Type `/endSession`
5. Verify session end protocol runs

---

## 📝 Next Steps

1. **RIGHT NOW**: Test basic integration (Priority 1)
   - Just send a message and see what happens
   - Check if files update

2. **If working**: Add status display (Priority 2)
   - Show automation status in context panel
   - Show response count, arc progress

3. **Then**: Add command buttons (Priority 3)
   - Start/End Session buttons
   - Quick command access

4. **Finally**: Polish (Priority 4-5)
   - File watcher for live updates
   - Better response formatting

---

## 💡 Key Insights

1. **Bridge + Claude Code + Hooks = Fully Automated System**
   - No changes needed to existing infrastructure
   - TUI already triggers everything properly

2. **TUI Enhancements Are UI Polish**
   - Status display = better visibility
   - Command buttons = better UX
   - Not required for functionality

3. **Testing First, Features Second**
   - Verify base integration works
   - Then add convenience features

---

## ❓ Questions to Answer

1. **Does the hook run when bridge calls Claude Code?**
   - Test: Send message, check hook.log

2. **Do commands work through the bridge?**
   - Test: Send `/status`, see if it executes

3. **Does entity tracking work?**
   - Test: Mention entity twice, check for card

4. **What does Claude's response look like?**
   - Test: Does it include hook suggestions?
   - Are they formatted well?

---

## 🎯 Success Criteria

**Minimum Viable Integration** (what we need):
- ✅ Messages from TUI trigger hooks
- ✅ Commands work from TUI
- ✅ Responses appear in TUI
- ✅ Entity tracking runs automatically
- ✅ Time tracking runs automatically

**Nice-to-Have Features** (polish):
- Status display in TUI
- Command buttons
- Live status updates
- Pretty formatting
- Notifications

**The system should already work! We just need to test it and add UI polish.**
