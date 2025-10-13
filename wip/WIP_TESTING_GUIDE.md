# 🚧 WIP Testing Guide - Using the Development Environment

**Purpose**: Test new features safely without affecting your production RP sessions.

---

## Overview

You now have TWO separate launchers:

| Launcher | Purpose | Uses | When to Use |
|----------|---------|------|-------------|
| `launch_rp_tui.py` | **PRODUCTION** | `src/tui_bridge.py` | Normal RP sessions |
| `launch_rp_tui_wip.py` | **TESTING** | `wip/tui_bridge.py` | Testing new features |

**Key Benefit**: You can test new features without breaking your active RP!

---

## How It Works

### Production System (Unchanged)
```
launch_rp_tui.py
├── Uses: src/tui_bridge.py (stable)
├── Uses: src/rp_client_tui.py
└── Your active RP sessions - SAFE!
```

### WIP System (Testing)
```
launch_rp_tui_wip.py  🚧
├── Uses: wip/tui_bridge.py (development)
├── Uses: src/rp_client_tui.py (same TUI)
└── Test RP or safe copy - EXPERIMENTAL!
```

**Important**: Both systems use the same RP folders but different automation code.

---

## Quick Start

### 1. Normal RP Session (Production)
```bash
python launch_rp_tui.py
```
Uses stable code, no experiments

### 2. Testing Session (WIP)
```bash
python launch_rp_tui_wip.py
```
Uses development code with new features

---

## Visual Indicators - How to Tell Which Mode You're In

### Production Mode
```
================================
  TUI Bridge started
  Monitoring: Example RP
================================
```
Clean, simple output

### WIP Mode
```
======================================================================
🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧
======================================================================
          🚧 WIP BRIDGE - DEVELOPMENT VERSION 🚧
======================================================================
  Using DEVELOPMENT code with NEW FEATURES:
  • Strikethrough formatting for entity card updates
  • Preserves character history (~~old~~ → new)
======================================================================
🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧
======================================================================

🚧 WIP Bridge started (SDK MODE - High Performance)
💾 TIER_1 files will be cached for maximum efficiency!
⚡ Real-time streaming enabled!
✨ NEW: Strikethrough updates enabled for entity cards!

📁 Monitoring: Example RP
⏳ Waiting for TUI input...
🚧 WIP MODE: Testing strikethrough entity updates
```
VERY OBVIOUS you're in WIP mode!

---

## Testing Strikethrough Updates

### Current WIP Features

**1. Strikethrough Entity Card Updates**
- When entity cards are updated, old information is preserved
- Uses `~~old~~ → new` format
- Shows character evolution over time

### Test Scenario

#### Step 1: Create or Use Test RP
**Option A**: Use Example RP (safe for testing)
```bash
python launch_rp_tui_wip.py
# Select "Example RP"
```

**Option B**: Create a test RP
```bash
# Copy Example RP
cp -r "Example RP" "Test WIP"
python launch_rp_tui_wip.py
# Select "Test WIP"
```

#### Step 2: Trigger Entity Card Creation
1. Start WIP launcher
2. Mention a new character 2+ times
   ```
   Example message: "I met Sarah at the coffee shop"
   Next message: "Sarah and I talked for a while"
   ```
3. Watch bridge window for:
   ```
   [AUTO-GEN] Generating entity card for: Sarah
   [SUCCESS] Auto-generated new entity card: entities/[CHAR] Sarah.md
   ```
4. Check `entities/[CHAR] Sarah.md` - should have standard format

#### Step 3: Test Update with Strikethrough
1. Manually edit the card to add some info:
   ```markdown
   ## Employment
   - Barista at Coffee Corner Cafe

   ## Living Situation
   - Lives alone in downtown apartment
   ```
2. Mention Sarah again with context showing changes:
   ```
   Message: "Sarah told me she quit the cafe and moved in with Marcus"
   ```
3. Wait for auto-update (may need a few more mentions to trigger)
4. Check the card - should now have:
   ```markdown
   ## Employment
   - ~~Barista at Coffee Corner Cafe~~ → Looking for new job

   ## Living Situation
   - ~~Lives alone in downtown apartment~~ → Lives with boyfriend Marcus
   ```

#### Step 4: Verify Strikethrough Works
- ✅ Old information preserved with strikethrough
- ✅ New information added with arrow
- ✅ Change Log section updated
- ✅ Mention count incremented
- ✅ All chapter appearances kept

---

## Safety Guidelines

### What's Safe to Test

✅ **Test RPs**: Create copies for testing
✅ **Example RP**: Generally safe for experimentation
✅ **Entity cards**: Can be regenerated if needed
✅ **Trigger various automations**: All safe

### What to Avoid

❌ **Active RP stories**: Use production launcher instead
❌ **Irreplaceable content**: Make backups first
❌ **Multiple simultaneous launches**: Pick one launcher

---

## Comparing Production vs WIP

### Side-by-Side Comparison

| Feature | Production | WIP |
|---------|-----------|-----|
| Entity card creation | Standard format | Standard format |
| Entity card updates | Overwrites old info | Preserves old with strikethrough |
| Character history | Lost on update | Preserved visually |
| Stability | Proven stable | Experimental |

### Example: Character Job Change

**Production Behavior** (current):
```markdown
## Employment
- Legal Assistant at Morrison Law
```
(Old "Barista" information is lost)

**WIP Behavior** (new):
```markdown
## Employment
- ~~Barista at Coffee Corner (Ch. 1-3)~~ → Legal Assistant at Morrison Law (Ch. 4+)
```
(Full history visible!)

---

## Troubleshooting

### Issue: Both launchers running at once
**Symptom**: Weird behavior, conflicts

**Solution**: Close one launcher, keep only one running
```bash
# Check which is running by looking at bridge window title:
Production: "TUI Bridge"
WIP: "🚧 WIP BRIDGE" (has construction emoji)
```

### Issue: WIP bridge shows errors
**Symptom**: Bridge crashes or shows Python errors

**Solution**:
1. Check the error message
2. WIP code is experimental - may have bugs
3. Report the issue
4. Use production launcher for actual RP

### Issue: Can't find wip/tui_bridge.py
**Symptom**: "WIP bridge not found" error

**Solution**: Make sure `wip/tui_bridge.py` exists
```bash
ls wip/tui_bridge.py  # Should exist
```

### Issue: Changes not appearing
**Symptom**: Testing strikethrough but not seeing changes

**Solution**:
1. Increase entity mentions (need more than threshold)
2. Check `state/entity_tracker.json` for mention count
3. Watch bridge window for auto-generation logs
4. Remember: Updates only trigger when mention count increases

---

## Development Workflow

### For Developers/Advanced Users

**1. Edit WIP Code**
```bash
# Edit wip/tui_bridge.py
# Make your changes
```

**2. Test Changes**
```bash
python launch_rp_tui_wip.py
# Use test RP
# Verify feature works
```

**3. Iterate**
```bash
# Close WIP launcher
# Edit code again
# Relaunch to test
```

**4. Deploy to Production** (when ready)
```bash
# Backup current production
cp src/tui_bridge.py src/tui_bridge.py.backup

# Deploy from WIP
cp wip/tui_bridge.py src/tui_bridge.py

# Test with production launcher
python launch_rp_tui.py
```

**5. Rollback if Needed**
```bash
# Restore backup
cp src/tui_bridge.py.backup src/tui_bridge.py
```

---

## File Locations

```
RP Claude Code/
├── launch_rp_tui.py          # ✅ PRODUCTION launcher
├── launch_rp_tui_wip.py      # 🚧 WIP launcher
│
├── src/                       # ✅ PRODUCTION code
│   ├── tui_bridge.py         # Stable automation
│   ├── rp_client_tui.py      # TUI (used by both)
│   └── clients/              # Stable clients
│
├── wip/                       # 🚧 DEVELOPMENT code
│   ├── tui_bridge.py         # Experimental automation
│   ├── TEMPLATE_ENTITY_CHARACTER.md  # Updated template
│   ├── DeepSeek_Update_Format_Guide.md  # Guide
│   ├── STRIKETHROUGH_UPDATE_IMPLEMENTATION.md  # Docs
│   └── WIP_TESTING_GUIDE.md  # This file!
│
└── [Your RP folders]/         # Shared by both launchers
    └── Example RP/
```

---

## What's Currently in WIP

### ✨ Strikethrough Entity Updates
**Status**: Ready for testing
**What it does**: Preserves entity card history with `~~old~~ → new`
**File**: `wip/tui_bridge.py` - `auto_generate_entity_card()` function
**Docs**: `wip/STRIKETHROUGH_UPDATE_IMPLEMENTATION.md`

### Future WIP Features
Add new features here as they're developed:
- [ ] Story arc strikethrough updates
- [ ] Enhanced chapter summaries
- [ ] [Your feature here]

---

## FAQ

### Q: Will WIP launcher affect my production RPs?
**A**: No! WIP launcher uses different code (`wip/tui_bridge.py`). Your production launcher (`launch_rp_tui.py`) uses stable code (`src/tui_bridge.py`).

### Q: Can I use both launchers at the same time?
**A**: Technically yes, but not recommended. Use one at a time to avoid confusion.

### Q: What if WIP breaks something?
**A**: Just close the WIP launcher and use production launcher. WIP only affects entity cards, which can be regenerated or manually fixed.

### Q: When should I use WIP vs production?
**A**:
- **Production**: All normal RP sessions, anything important
- **WIP**: Testing new features, experimenting, providing feedback

### Q: How do I know if a feature is ready for production?
**A**: Check the WIP docs. Features marked "Ready for testing" are stable in WIP. Features marked "Ready for deployment" can be moved to production.

### Q: Can I test WIP with my active RP?
**A**: You can, but it's safer to use a test RP copy first. Entity card updates are generally safe but it's best to verify with test data first.

---

## Feedback

When testing WIP features, note:
- ✅ What worked well
- ❌ What didn't work
- 💡 Suggestions for improvement
- 🐛 Bugs encountered

Document in `wip/TEST_RESULTS.md` or similar.

---

## Summary

**Two launchers, two environments**:
- `launch_rp_tui.py` = Production (safe, stable)
- `launch_rp_tui_wip.py` = Development (testing, experimental)

**Clear visual indicators**: 🚧 emojis everywhere in WIP mode

**Safe testing**: Your production RP system is unaffected

**Easy deployment**: Copy from `wip/` to `src/` when ready

---

Happy testing! 🚧✨
