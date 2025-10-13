# TUI + Claude Code Integration Status Report

**Date**: December 2024
**Project**: RP System for Claude Code with TUI Interface
**Status**: 🟡 Partial Integration - Bridge Works, Hooks Don't Run

---

## 📊 Executive Summary

**Good News**: ✅ TUI successfully connects to Claude Code through bridge
**Bad News**: ❌ Automation (hooks) don't run in non-interactive mode
**Solution**: Migrate automation from bash hooks to Python bridge

---

## ✅ What's Working

### 1. TUI Application (rp_client_tui.py)
- ✅ Launches without errors
- ✅ Multi-line text input works
- ✅ Enter adds new lines
- ✅ Ctrl+Enter sends messages (mapped to Ctrl+J internally)
- ✅ Footer shows functional buttons
- ✅ Overlays work when clicked (Memory, Arc, Characters, etc.)
- ✅ F1 help overlay works
- ✅ Context panel displays properly
- ✅ Chat history displays messages

### 2. Bridge Script (tui_bridge.py)
- ✅ Monitors state files correctly
- ✅ Detects ready flag
- ✅ Reads user input from file
- ✅ Calls Claude Code with correct path: `C:\Users\green\.local\bin\claude.exe`
- ✅ Uses correct CLI flag: `-p` (print mode)
- ✅ Changes to RP directory before calling Claude
- ✅ Captures Claude's response
- ✅ Writes response back to TUI
- ✅ Creates done flag
- ✅ TUI receives and displays response

### 3. Communication Flow
```
User types in TUI
    ↓
Presses Ctrl+Enter
    ↓
TUI writes: state/rp_client_input.txt
TUI creates: state/rp_client_ready.flag
    ↓
Bridge detects flag (0.5s polling)
    ↓
Bridge calls: claude.exe -p "message" (in RP dir)
    ↓
Claude responds (SUCCESSFULLY!)
    ↓
Bridge writes: state/rp_client_response.txt
Bridge creates: state/rp_client_done.flag
    ↓
TUI detects done flag (0.5s polling)
    ↓
TUI displays response
    ↓
✅ MESSAGE FLOW WORKS!
```

### 4. File Structure
- ✅ All folders present (state/, characters/, entities/, etc.)
- ✅ Templates exist
- ✅ Bash hooks exist (just not running)
- ✅ Commands defined
- ✅ State directory writable

### 5. Fixed Issues
1. **claude command not found** → Fixed with full path
2. **--message flag error** → Fixed using `-p` flag
3. **Ctrl+Enter keybinding** → Fixed using Ctrl+J
4. **Alt key bindings** → Removed, using footer buttons instead

---

## ❌ What's NOT Working

### 1. Hooks Don't Execute
**File**: `.claude/hooks/user-prompt-submit.sh`
**Expected**: Runs before each Claude response
**Reality**: Does NOT run when using `-p` print mode

**Evidence**:
- `state/response_counter.txt` = 0 (never incremented)
- `state/hook.log` = doesn't exist (never created)
- `CURRENT_STATUS.md` = doesn't exist (never generated)
- `state/entity_tracker.json` = not being updated

**Why**: Claude Code's `-p/--print` flag is for non-interactive output and **intentionally skips hooks** for performance/simplicity

### 2. No Automation Running
Because hooks don't run, these features are non-functional:

- ❌ **Response Counter**: Not incrementing
- ❌ **Time Tracking**: Not calculating elapsed time
- ❌ **Entity Tracking**: Not tracking mentions
- ❌ **Auto Entity Cards**: Not generating
- ❌ **Auto Story Arcs**: Not generating
- ❌ **Conditional File Loading**: Not loading triggered files
- ❌ **Status Updates**: CURRENT_STATUS.md not being created/updated

### 3. No Context Injection
Hook would inject:
- Time suggestions
- Entity information
- Triggered character/entity cards
- Story arc references

Without hooks:
- Claude doesn't get automatic context
- User must manually provide all context
- No automation benefits

---

## 🔍 Root Cause Analysis

### The Core Problem

Claude Code has two modes:

#### Interactive Mode (normal `claude` command)
- Opens interactive chat session
- **Runs hooks before/after each turn**
- Loads .claude/commands
- Full feature set
- ❌ Can't capture output for TUI easily
- ❌ Terminal control issues

#### Print Mode (`claude -p "text"`)
- Non-interactive, single response
- **Skips hooks for performance**
- Returns output to stdout
- ✅ Perfect for scripting/automation
- ✅ Easy to capture output
- ❌ No hooks = no automation

### Why We're Using Print Mode

**Bridge needs**: Non-interactive mode to capture output
**Print mode provides**: Clean stdout we can capture
**Trade-off**: Lose hook execution

### Fundamental Limitation

**There is no Claude Code mode that gives us both:**
- Non-interactive output capture (for TUI)
- Hook execution (for automation)

---

## 💡 Solutions Explored

### Attempt 1: Fix Command Path
**Goal**: Make `claude` command findable
**Result**: ✅ SUCCESS - Found at `C:\Users\green\.local\bin\claude.exe`
**Impact**: Bridge can now call Claude

### Attempt 2: Fix CLI Flags
**Goal**: Use correct Claude CLI syntax
**Result**: ✅ SUCCESS - Changed from `--message` to `-p`
**Impact**: Claude executes without errors

### Attempt 3: Test Hook Execution
**Goal**: Verify hooks run with print mode
**Result**: ❌ FAIL - Hooks do not run in `-p` mode
**Impact**: Discovered fundamental limitation

---

## 🎯 Recommended Solution: Option 1 (Python Automation in Bridge)

### The Plan

**Migrate all automation from bash hooks to Python bridge script**

Instead of:
```
User → Bridge → Claude (with hooks) → Response
```

Do this:
```
User → Bridge (runs automation) → Claude (-p mode) → Response
          ↓
    - Increment counter
    - Track entities
    - Calculate time
    - Generate cards
    - Update status
```

### What to Migrate

From `.claude/hooks/user-prompt-submit.sh` to `tui_bridge.py`:

#### 1. **Response Counter**
```python
def increment_response_counter(rp_dir):
    counter_file = rp_dir / "state" / "response_counter.txt"
    count = int(counter_file.read_text() or "0")
    count += 1
    counter_file.write_text(str(count))
    return count
```

#### 2. **Entity Tracking**
```python
def track_entities(message, rp_dir):
    tracker_file = rp_dir / "state" / "entity_tracker.json"
    tracker = json.loads(tracker_file.read_text())

    # Extract entity mentions from message
    # Update mention counts
    # Check for threshold (2+ mentions)
    # Return entities to load
```

#### 3. **Time Calculation**
```python
def calculate_time(message, timing_file):
    # Read Timing.txt
    # Detect activities in message
    # Sum up durations
    # Return time suggestion
```

#### 4. **Status File Updates**
```python
def update_status_file(rp_dir, count, entities, time_calc):
    # Create/update CURRENT_STATUS.md
    # Include response count, arc progress, entities
```

#### 5. **Entity Card Generation** (via DeepSeek)
```python
def auto_generate_entity_card(entity_name, rp_dir):
    # Call DeepSeek API
    # Generate entity card
    # Save to entities/ folder
```

#### 6. **Story Arc Triggers**
```python
def check_arc_generation(count, arc_frequency=50):
    if count % arc_frequency == 0:
        # Trigger arc generation
        # Could inject instruction to Claude's prompt
```

### Integration Point in Bridge

```python
# In tui_bridge.py main loop, BEFORE calling Claude:

if ready_flag.exists():
    message = input_file.read_text()

    # ===== NEW AUTOMATION BLOCK =====
    count = increment_response_counter(rp_dir)
    entities_found = track_entities(message, rp_dir)
    time_suggestion = calculate_time(message, timing_file)
    update_status_file(rp_dir, count, entities_found, time_suggestion)

    # Check for auto-generation triggers
    if entities_need_cards(entities_found):
        auto_generate_cards(entities_found, rp_dir)

    if should_generate_arc(count):
        arc_instruction = get_arc_generation_prompt()
        message = f"{message}\n\n{arc_instruction}"

    # Build enhanced prompt with context
    context = load_triggered_files(entities_found, rp_dir)
    enhanced_prompt = f"{context}\n\n{message}\n\nTime: {time_suggestion}"
    # ===== END AUTOMATION BLOCK =====

    # Call Claude with enhanced prompt
    result = subprocess.run([claude_path, '-p', enhanced_prompt], ...)
```

---

## 📋 Migration Checklist

### Phase 1: Core Features (Essential)
- [ ] Response counter increment
- [ ] Status file creation/update
- [ ] Entity mention tracking (JSON)
- [ ] Basic logging (hook.log equivalent)

### Phase 2: Context Loading (Important)
- [ ] Read Timing.txt and calculate time
- [ ] Load triggered character/entity files
- [ ] Inject context into Claude prompt
- [ ] Time suggestions in prompt

### Phase 3: Auto-Generation (Nice-to-Have)
- [ ] Auto entity card generation (DeepSeek API)
- [ ] Arc generation triggers (every 50 responses)
- [ ] Threshold detection

### Phase 4: Polish
- [ ] Better status formatting
- [ ] Error handling
- [ ] Performance optimization
- [ ] Logging improvements

---

## 🔄 Alternative Solutions (NOT Recommended)

### Option 2: Interactive Mode with Piping

**Idea**: Use interactive mode but pipe input/output

```python
process = subprocess.Popen(
    [claude_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    cwd=rp_dir
)
```

**Pros**:
- ✅ Hooks would run
- ✅ Keep existing bash automation

**Cons**:
- ❌ Complex terminal control
- ❌ Hard to detect when response is complete
- ❌ Session state management issues
- ❌ May break TUI display

### Option 3: Hybrid Approach

**Idea**: Python for essentials, bash for complex features

**Pros**:
- ✅ Quick to implement basics
- ✅ Can gradually migrate

**Cons**:
- ❌ Inconsistent experience
- ❌ Bash still problematic on Windows
- ❌ Two systems to maintain

---

## 📁 File Structure Reference

```
RP Claude Code/
├── tui_bridge.py              ← NEEDS UPDATES (add automation)
├── rp_client_tui.py           ← Working ✅
├── .claude/
│   ├── hooks/
│   │   └── user-prompt-submit.sh  ← Reference for migration
│   └── commands/
│       ├── continue.md        ← Working ✅
│       ├── status.md          ← Working ✅
│       └── endSession.md      ← Working ✅
├── Example RP/
│   ├── state/
│   │   ├── response_counter.txt   ← Currently 0, needs updating
│   │   ├── entity_tracker.json    ← Exists but not updating
│   │   ├── current_state.md       ← Exists ✅
│   │   ├── rp_client_input.txt    ← Bridge communication ✅
│   │   ├── rp_client_response.txt ← Bridge communication ✅
│   │   ├── rp_client_ready.flag   ← Bridge communication ✅
│   │   └── rp_client_done.flag    ← Bridge communication ✅
│   ├── CURRENT_STATUS.md      ← NOT being created ❌
│   └── characters/, entities/, chapters/ ← All present ✅
└── integration_status/
    └── INTEGRATION_STATUS_REPORT.md ← This document
```

---

## 🧪 Testing Strategy

### Test 1: Counter Increment
1. Add counter increment to bridge
2. Send message through TUI
3. Check if response_counter.txt increases
4. ✅ PASS if counter = 1

### Test 2: Status File
1. Add status file generation
2. Send message
3. Check if CURRENT_STATUS.md created
4. ✅ PASS if file exists with correct format

### Test 3: Entity Tracking
1. Add entity tracking logic
2. Send message: "I met Sarah. Sarah was nice."
3. Check entity_tracker.json
4. ✅ PASS if Sarah: mentions=2

### Test 4: Time Calculation
1. Add time calculation
2. Send message: "We had a long conversation"
3. Check if time suggestion appears
4. ✅ PASS if "15 minutes" or similar suggested

### Test 5: Full Integration
1. Complete all automation
2. Run 3-4 RP exchanges
3. Check all features work together
4. ✅ PASS if counter increments, entities track, status updates

---

## 💰 Cost Implications

### Current (Bash Hook) System
- Entity cards: ~$0.001 each (DeepSeek API)
- Arc generation: FREE (uses Claude's context)
- Everything else: FREE (local processing)

### Python Bridge System
- **Same costs!**
- Entity cards: ~$0.001 each (same DeepSeek API call)
- Arc generation: FREE (same approach)
- Everything else: FREE (local Python processing)

**No cost difference!**

---

## ⏱️ Implementation Time Estimate

### Phase 1: Core (Essential) - ~2-3 hours
- Response counter: 15 min
- Status file: 30 min
- Entity tracking (basic): 1 hour
- Testing: 30 min

### Phase 2: Context (Important) - ~2-3 hours
- Time calculation: 1 hour
- File loading: 45 min
- Prompt enhancement: 45 min
- Testing: 30 min

### Phase 3: Auto-gen (Nice-to-Have) - ~3-4 hours
- DeepSeek API integration: 1.5 hours
- Entity card generation: 1 hour
- Arc triggers: 45 min
- Testing: 45 min

**Total: ~7-10 hours for full migration**

**MVP (Phase 1+2): ~4-6 hours**

---

## 🎯 Success Criteria

### Minimum Viable Product (MVP)
- ✅ Response counter increments
- ✅ Entity mentions tracked
- ✅ CURRENT_STATUS.md updates
- ✅ Basic time tracking works
- ✅ Messages flow through TUI successfully

### Full Feature Parity
- ✅ Everything in MVP
- ✅ Auto entity card generation
- ✅ Auto arc generation triggers
- ✅ Conditional file loading
- ✅ Time suggestions accurate
- ✅ All original hook features work

---

## 📝 Current Todo List

**Status as of session end:**

1. ✅ **COMPLETED**: Analyze existing integration between TUI, bridge, hooks, and commands
2. ✅ **COMPLETED**: Test that hooks run properly when messages sent through bridge
   - Result: Hooks don't run in `-p` print mode
3. ✅ **COMPLETED**: Create comprehensive status document
4. ⏳ **PENDING**: Implement Python automation in bridge (Phase 1: Core)
   - Response counter
   - Entity tracking
   - Status file generation
5. ⏳ **PENDING**: Implement Python automation in bridge (Phase 2: Context)
   - Time calculation
   - File loading
   - Prompt enhancement
6. ⏳ **PENDING**: Add status display in TUI from CURRENT_STATUS.md
   - Read status file
   - Display in context panel
   - Auto-refresh

## 📝 Next Steps (Immediate)

1. **Document User Approval** ✅ (Got Option 1 approval)

2. **Start Phase 1 Implementation**
   - Create automation module in bridge
   - Implement response counter
   - Implement status file generation
   - Test basic functionality

3. **Iterate Through Phases**
   - Phase 1 → Test → Phase 2 → Test → Phase 3 → Test

4. **Update Documentation**
   - Document new Python automation
   - Update README_TUI.md
   - Update integration guides

---

## 📚 Related Documents

- `TUI_CLAUDE_CODE_INTEGRATION_PLAN.md` - Original integration analysis
- `CTRL_ENTER_TROUBLESHOOTING_LOG.md` - Keybinding debugging journey
- `TUI_INTEGRATION_TEST_CHECKLIST.md` - Testing checklist
- `.claude/hooks/user-prompt-submit.sh` - Original bash automation (reference)
- `tui_bridge.py` - Bridge script (needs updates)
- `rp_client_tui.py` - TUI application (working)

---

## 🏆 Achievements So Far

1. ✅ Built functional TUI interface
2. ✅ Created bridge communication system
3. ✅ Fixed keybinding issues (Ctrl+J discovery)
4. ✅ Resolved Alt key problems (switched to F-keys/buttons)
5. ✅ Got Claude CLI working with correct flags
6. ✅ Established file-based communication protocol
7. ✅ Documented everything thoroughly
8. ✅ **Messages successfully flow: TUI → Bridge → Claude → TUI**

**The foundation is solid. Now we add the automation layer!**

---

**End of Report**

*This document will be updated as implementation progresses.*
