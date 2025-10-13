# Bash Automation Backup

**Created**: December 2024
**Purpose**: Backup of working bash-based automation before migrating to Python

---

## Why This Backup Exists

When integrating the TUI with Claude Code, we discovered that the `-p/--print` flag (needed for non-interactive output capture) **does not run hooks**.

To solve this, we're migrating all automation from bash hooks → Python bridge script.

**This backup preserves the original working bash implementation for reference.**

---

## What's Backed Up

### 1. `hooks/user-prompt-submit.sh` (634 lines)

**Original Location**: `.claude/hooks/user-prompt-submit.sh`

**Functions**:
- `load_config()` - Load automation settings from JSON
- `increment_counter()` - Increment response counter, trigger arc generation
- `calculate_time()` - Parse Timing.txt and detect activity durations
- `track_entities()` - Track entity mentions in JSON, trigger card generation
- `identify_triggers()` - Scan for trigger words, load conditional files
- `update_status_file()` - Generate CURRENT_STATUS.md
- `auto_generate_entity_card()` - Call DeepSeek API to create entity cards
- `auto_generate_arc()` - Inject instructions for Claude to generate story arc
- `log_to_file()` - Write to hook.log with timestamps

**When It Ran**: Before each Claude response (via hook system)

**Why It Worked**: Interactive mode runs hooks automatically

**Why We Can't Use It With TUI**: Print mode (`-p`) skips hooks for performance

---

### 2. `scripts/deepseek_call.sh`

**Original Location**: `scripts/deepseek_call.sh`

**Purpose**: Reusable script to call DeepSeek API via OpenRouter

**Used For**:
- Auto-generating entity cards (~$0.001 each)
- Memory updates during /endSession
- Character sheet updates during /endSession

**API Details**:
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Model: `deepseek/deepseek-chat-v3.1`
- Cost: ~$0.14 per million tokens (very cheap)

---

## Python Migration Status

### Phase 1: Core Automation (In Progress)
Migrating to `tui_bridge.py`:
- ✅ Response counter increment
- ✅ Entity tracking (JSON updates)
- ✅ Time calculation from Timing.txt
- ✅ Conditional file loading (triggers)
- ✅ Status file generation
- ✅ Logging system

### Phase 2: Context Loading (Future)
- Load triggered files
- Inject context into Claude prompt
- Time suggestions in prompt

### Phase 3: Auto-Generation (Future)
- Auto entity card generation (DeepSeek API)
- Auto story arc generation (Claude context)

---

## Key Differences: Bash vs Python

| Feature | Bash Hook (Original) | Python Bridge (New) |
|---------|---------------------|---------------------|
| **Runs** | Before Claude response | Before calling Claude |
| **Mode** | Interactive mode only | Works with `-p` print mode |
| **When** | Automatic (hook system) | Explicit in bridge script |
| **Language** | Bash (634 lines) | Python (cleaner, more maintainable) |
| **Dependencies** | jq, grep, sed | Pure Python + stdlib |
| **Context Injection** | Via stderr redirect | Via enhanced prompt |
| **Cost** | FREE (local) | FREE (local) |

---

## How to Use This Backup

### If Something Goes Wrong:
1. Stop the TUI bridge
2. Review this bash implementation
3. Compare with Python version
4. Fix logic differences

### If You Need to Restore Bash Hooks:
```bash
# Copy hook back to original location
cp bash_automation_backup/hooks/user-prompt-submit.sh ../.claude/hooks/

# Copy DeepSeek script back
cp bash_automation_backup/scripts/deepseek_call.sh ../scripts/

# Make executable
chmod +x ../.claude/hooks/user-prompt-submit.sh
chmod +x ../scripts/deepseek_call.sh
```

### If You Want to Compare Implementations:
- Bash version: `bash_automation_backup/hooks/user-prompt-submit.sh`
- Python version: `../tui_bridge.py` (automation module)

---

## Testing Notes (From Original System)

### Verified Working Features:
- ✅ Response counter increments properly
- ✅ Entity tracking works (JSON updates via jq)
- ✅ Time calculation accurate (100+ activities in Timing.txt)
- ✅ Conditional file loading (trigger matching)
- ✅ Status file generation (with progress bar)
- ✅ Auto entity card generation (DeepSeek API)
- ✅ Auto story arc generation (Claude context)
- ✅ Logging to hook.log with timestamps

### Known Issues:
- ❌ Doesn't work with Claude Code's `-p` print mode
- ❌ Windows bash compatibility issues (Git Bash/WSL differences)
- ⚠️ jq dependency required for JSON manipulation

---

## Cost Analysis (From Original System)

**Per Session (30 responses, 3 new entities)**:
- Entity cards: 3 × $0.001 = $0.003
- Story arc: Not reached = $0.00
- Everything else: FREE (local bash)
- **Total**: ~$0.003

**At 50 Responses (5 new entities)**:
- Entity cards: 5 × $0.001 = $0.005
- Story arc: 1 × FREE = $0.00
- **Total**: ~$0.005

**Very affordable!** (Python version has same costs)

---

## Related Documentation

- `INTEGRATION_STATUS_REPORT.md` - Why we migrated to Python
- `TUI_CLAUDE_CODE_INTEGRATION_PLAN.md` - Original integration analysis
- `PROJECT_STATUS_AND_ROADMAP.md` - Full project overview

---

**This backup ensures we never lose the working bash implementation!**

*If the Python version has issues, we can always reference this for correct logic.*
