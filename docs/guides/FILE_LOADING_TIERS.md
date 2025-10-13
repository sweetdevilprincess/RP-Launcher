# File Loading TIER System - Complete Guide

**Last Updated:** October 12, 2025

This document explains the **three-tier file loading system** that determines which files get loaded into Claude's context with each message.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [TIER_1: Core Files (Always)](#tier_1-core-files-always)
3. [TIER_2: Guidelines (Periodic)](#tier_2-guidelines-periodic)
4. [TIER_3: Conditional (Triggered)](#tier_3-conditional-triggered)
5. [TIER_3 Escalation](#tier_3-escalation)
6. [Complete Loading Flow](#complete-loading-flow)
7. [Optimization Tips](#optimization-tips)

---

## Overview

### Why Three Tiers?

**Problem:** Claude Code has a context limit. We can't load every file every time.

**Solution:** Three-tier system prioritizes files by importance and relevance:
- **TIER_1** - Essential files (always loaded)
- **TIER_2** - Important guidelines (loaded periodically)
- **TIER_3** - Conditional files (loaded when relevant)

### Loading Frequency

| Tier | Frequency | File Count | Purpose |
|------|-----------|------------|---------|
| TIER_1 | **Every response** | ~7 files | Core RP context |
| TIER_2 | **Every 4th response** | ~6 files | Writing guidelines |
| TIER_3 | **When triggered** | Variable | Conditional entities |

### Example Loading Pattern

```
Response 1:  TIER_1 ✓  TIER_2 ✗  TIER_3 (Sarah) ✓
Response 2:  TIER_1 ✓  TIER_2 ✗  TIER_3 (none)  ✗
Response 3:  TIER_1 ✓  TIER_2 ✗  TIER_3 (Marcus) ✓
Response 4:  TIER_1 ✓  TIER_2 ✓  TIER_3 (Sarah, Marcus) ✓  ← Guidelines loaded
Response 5:  TIER_1 ✓  TIER_2 ✗  TIER_3 (Sarah) ✓
```

### Code Location

**Bridge:** `tui_bridge.py`
- `load_tier1_files()` - Line 751
- `load_tier2_files()` - Line 791
- `identify_triggers()` - Line 277 (TIER_3)
- `track_tier3_triggers()` - Line 833 (escalation)
- `run_automation()` - Line 880 (orchestrates all)

---

## TIER_1: Core Files (Always)

### What It Does

Loads **essential RP files** that Claude needs for every response.

**Frequency:** Every single response (100%)

**Purpose:** Provide core context (story, characters, current state)

### Files Loaded

```
1. AUTHOR'S_NOTES.md          - Author's guidance
2. STORY_GENOME.md             - Story outline/beats
3. SCENE_NOTES.md              - Current scene notes
4. state/current_state.md      - Current timestamp, location, POV
5. state/story_arc.md          - Story arc (next 11 beats)
6. characters/{{user}}.md      - User character
7. characters/{main}.md        - Main character (first non-{{user}})
```

### Example TIER_1 Files

**RP Folder:** `Example RP/`

```
TIER_1 files loaded:
✓ AUTHOR'S_NOTES.md
✓ STORY_GENOME.md
✓ SCENE_NOTES.md
✓ state/current_state.md
✓ state/story_arc.md
✓ characters/{{user}}.md
✓ characters/Alex.md          ← First main character
```

**Not loaded:**
- `characters/Sarah.md` (not main character, would be TIER_3)
- `entities/[CHAR] Marcus.md` (TIER_3 only)

### Code

```python
def load_tier1_files(rp_dir, log_file):
    tier1_files = {}

    files_to_load = [
        rp_dir / "AUTHOR'S_NOTES.md",
        rp_dir / "STORY_GENOME.md",
        rp_dir / "SCENE_NOTES.md",
        rp_dir / "state" / "current_state.md",
        rp_dir / "state" / "story_arc.md",
        rp_dir / "characters" / "{{user}}.md",
    ]

    # Find main character
    for char_file in (rp_dir / "characters").glob("*.md"):
        if char_file.name != "{{user}}.md":
            files_to_load.append(char_file)
            break  # Only first one

    # Load all files
    for file_path in files_to_load:
        if file_path.exists():
            tier1_files[file_path.name] = file_path.read_text()

    return tier1_files
```

### Log Output

```
[timestamp] --- TIER_1 Loading (Core Files) ---
[timestamp] TIER_1: Loaded AUTHOR'S_NOTES.md
[timestamp] TIER_1: Loaded STORY_GENOME.md
[timestamp] TIER_1: Loaded SCENE_NOTES.md
[timestamp] TIER_1: Loaded current_state.md
[timestamp] TIER_1: Loaded story_arc.md
[timestamp] TIER_1: Loaded {{user}}.md
[timestamp] TIER_1: Loaded Alex.md
```

### When Files Are Missing

**If file doesn't exist:**
```
[timestamp] TIER_1: File not found: SCENE_NOTES.md
```

**If file can't be read:**
```
[timestamp] WARNING: Could not load TIER_1 file AUTHOR'S_NOTES.md: [error]
```

**Result:** Continues loading other files (graceful degradation)

---

## TIER_2: Guidelines (Periodic)

### What It Does

Loads **writing and style guidelines** periodically to reinforce rules without overwhelming context.

**Frequency:** Every 4th response (25%)

**Purpose:** Remind Claude of writing style, POV rules, NPC handling, etc.

### Files Loaded

```
1. Guidelines/Timing.txt              - Activity time costs
2. Writing_Style_Guide.md             - Writing style rules
3. NPC_Interaction_Rules.md           - How to handle NPCs
4. POV_and_Writing_Checklist.md       - POV guidelines
5. Time_Tracking_Guide.md             - Time advancement rules
6. Story Guidelines.md                - General story guidelines
7. {RP Name}.md                       - RP overview (if exists)
```

**Note:** These files are in the **root folder** or **Guidelines/** folder, not inside the RP folder.

### When It Loads

```python
if response_count % 4 == 0:
    # Load TIER_2 files
```

**Loading pattern:**
```
Response 1: ✗
Response 2: ✗
Response 3: ✗
Response 4: ✓  ← TIER_2 loaded
Response 5: ✗
Response 6: ✗
Response 7: ✗
Response 8: ✓  ← TIER_2 loaded
```

### Code

```python
def load_tier2_files(rp_dir, response_count, log_file):
    tier2_files = {}

    # Only load every 4th response
    if response_count % 4 != 0:
        return tier2_files

    log("[timestamp] TIER_2: Loading (response {response_count} is divisible by 4)")

    files_to_load = [
        rp_dir.parent / "guidelines" / "Timing.txt",
        rp_dir.parent / "Writing_Style_Guide.md",
        rp_dir.parent / "NPC_Interaction_Rules.md",
        rp_dir.parent / "POV_and_Writing_Checklist.md",
        rp_dir.parent / "Time_Tracking_Guide.md",
        rp_dir.parent / "Story Guidelines.md",
    ]

    # Also load RP overview if exists
    rp_name = rp_dir.name
    overview_file = rp_dir / f"{rp_name}.md"
    if overview_file.exists():
        files_to_load.append(overview_file)

    # Load all files
    for file_path in files_to_load:
        if file_path.exists():
            tier2_files[file_path.name] = file_path.read_text()

    return tier2_files
```

### Log Output

**Response 4 (loads):**
```
[timestamp] --- TIER_2 Loading (Guidelines) ---
[timestamp] TIER_2: Loading (response 4 is divisible by 4)
[timestamp] TIER_2: Loaded Timing.txt
[timestamp] TIER_2: Loaded Writing_Style_Guide.md
[timestamp] TIER_2: Loaded NPC_Interaction_Rules.md
[timestamp] TIER_2: Loaded POV_and_Writing_Checklist.md
[timestamp] TIER_2: Loaded Time_Tracking_Guide.md
[timestamp] TIER_2: Loaded Story Guidelines.md
[timestamp] TIER_2: Loaded Example RP.md
```

**Response 5 (skips):**
```
[timestamp] --- TIER_2 Loading (Guidelines) ---
(no files loaded - not divisible by 4)
```

### Customizing Frequency

To load more/less often, modify `tui_bridge.py`:

```python
# Load every 2nd response
if response_count % 2 == 0:

# Load every 8th response
if response_count % 8 == 0:

# Always load (not recommended - bloats context)
if True:
```

---

## TIER_3: Conditional (Triggered)

### What It Does

Loads **character and entity files** only when **trigger words** appear in your message.

**Frequency:** When relevant (0-100% depending on message)

**Purpose:** Provide detailed info only when character/entity is mentioned

### How It Works

**1. Define triggers in files**

**Example:** `entities/[CHAR] Sarah.md`
```markdown
[Triggers:Sarah,her,girlfriend']

# Sarah Mitchell
- Age: 24
- Role: Alex's girlfriend
```

**2. User mentions trigger word**

```
Message: "Sarah called me this morning"
         ↑
    Trigger word found!
```

**3. File gets loaded into context**

```
TIER_3 files loaded this response:
✓ entities/[CHAR] Sarah.md
```

### Trigger Formats

**Format 1:** AI Dungeon style
```markdown
[Triggers:word1,word2,word3']
```

**Format 2:** Markdown bold
```markdown
**Triggers**: word1, word2, word3
```

**Both work!**

### Directories Scanned

```
characters/        - Character files
entities/          - Entity files
```

**File patterns:**
```
characters/Sarah.md
characters/Marcus.md
entities/[CHAR] Sarah.md
entities/[ITEM] Red Car.md
entities/[LOC] Coffee Shop.md
entities/[EVENT] First Date.md
```

### Trigger Matching

**Case-sensitive substring match:**

```markdown
[Triggers:Sarah,her,girlfriend']
```

**Matches:**
- "Sarah smiled" ✓
- "Sarah" ✓
- "her eyes" ✓
- "his girlfriend" ✓

**Doesn't match:**
- "sarah" ✗ (wrong case)
- "Sar ah" ✗ (not substring)

### Code

```python
def identify_triggers(message, rp_dir, log_file):
    files_to_load = []
    entity_names = []

    # Check characters directory
    for char_file in (rp_dir / "characters").glob("*.md"):
        content = char_file.read_text()

        # Extract triggers (both formats)
        triggers = []
        for line in content.split('\n'):
            if line.startswith('**Triggers**:'):
                triggers = line.split(':', 1)[1].strip().split(',')
            elif line.startswith('[Triggers:'):
                triggers = line[10:].rstrip("']").split(',')

        # Check if any trigger in message
        for trigger in triggers:
            if trigger and trigger in message:
                files_to_load.append(char_file)
                entity_names.append(char_file.stem)
                break

    # Same for entities directory
    # ...

    return files_to_load, entity_names
```

### Log Output

```
[timestamp] --- TIER_3 Loading (Conditional) ---
[timestamp] Trigger match: Loading [CHAR] Sarah.md (matched: Sarah)
[timestamp] Trigger match: Loading [CHAR] Marcus.md (matched: Marcus)
[timestamp] Conditional files loaded: 2
```

**Bridge terminal shows:**
```
📚 TIER_3 entities loaded: Sarah, Marcus
```

### Example Scenarios

**Scenario 1:** Mention Sarah
```
Message: "Sarah and I went to the cafe"

TIER_3 loaded:
✓ entities/[CHAR] Sarah.md  (trigger: "Sarah")
```

**Scenario 2:** Mention car
```
Message: "I got in my car and drove home"

TIER_3 loaded:
✓ entities/[ITEM] Red Car.md  (trigger: "car")
```

**Scenario 3:** Multiple triggers
```
Message: "Sarah drove us in my car to Marcus's house"

TIER_3 loaded:
✓ entities/[CHAR] Sarah.md   (trigger: "Sarah")
✓ entities/[ITEM] Red Car.md (trigger: "car")
✓ entities/[CHAR] Marcus.md  (trigger: "Marcus")
```

**Scenario 4:** No triggers
```
Message: "I went for a walk"

TIER_3 loaded:
(none)
```

---

## TIER_3 Escalation

### What It Does

Files that are triggered **frequently** (3+ times in last 10 responses) get **escalated** to TIER_2-like treatment.

**Purpose:** If a character is constantly appearing, load their file more often without needing triggers.

**Threshold:** 3+ triggers in last 10 responses

### How It Works

**1. Track trigger history**

**File:** `state/trigger_history.json`
```json
{
  "trigger_history": [
    ["entities/[CHAR] Sarah.md"],           // Response 1
    [],                                      // Response 2
    ["entities/[CHAR] Sarah.md"],           // Response 3
    ["entities/[CHAR] Sarah.md", "..."],   // Response 4
    // ... keeps last 10
  ]
}
```

**2. Count triggers per file (last 10 responses)**

```
Sarah.md: 5 triggers in last 10 responses
Marcus.md: 1 trigger in last 10 responses
```

**3. Escalate if >= 3 triggers**

```
Sarah.md: 5 >= 3 ✓ ESCALATE
Marcus.md: 1 < 3 ✗ Don't escalate
```

**4. Load escalated files (even without trigger)**

```
TIER_3 ESCALATED files:
✓ entities/[CHAR] Sarah.md  (triggered 5/10 times)
```

### Code

```python
def track_tier3_triggers(triggered_files, tracker_file, log_file):
    # Load history
    history = json.loads(tracker_file.read_text())

    # Add current triggers
    history["trigger_history"].append([str(f) for f in triggered_files])

    # Keep only last 10
    history["trigger_history"] = history["trigger_history"][-10:]

    # Count triggers per file
    trigger_counts = {}
    for response_triggers in history["trigger_history"]:
        for file_path in response_triggers:
            trigger_counts[file_path] += 1

    # Escalate if >= 3
    escalated = []
    for file_path, count in trigger_counts.items():
        if count >= 3:
            escalated.append(file_path)
            log(f"TIER_3 ESCALATION: {file_path} triggered {count}/10 times")

    return escalated
```

### Log Output

```
[timestamp] TIER_3 ESCALATION: [CHAR] Sarah.md triggered 5/10 times
```

### Example Escalation

**Responses 1-10:**
```
R1:  Sarah mentioned → Trigger
R2:  (no Sarah)
R3:  Sarah mentioned → Trigger
R4:  Sarah mentioned → Trigger
R5:  Sarah mentioned → Trigger
R6:  (no Sarah)
R7:  Sarah mentioned → Trigger
R8:  (no Sarah)
R9:  (no Sarah)
R10: (no Sarah)

Sarah.md triggered: 5/10 times → ESCALATE
```

**Response 11 onward:**
```
R11: "I went for a walk" (no Sarah mentioned)

TIER_3 loaded:
✓ entities/[CHAR] Sarah.md  (ESCALATED - loaded anyway)
```

### Deescalation

If triggers drop below 3 in last 10 responses, file is no longer escalated.

**Example:**
```
R11-R20: Sarah not mentioned much (only 2/10)
R21: Sarah.md no longer escalated
```

---

## Complete Loading Flow

### Full Process (Every Message)

```
USER SENDS MESSAGE: "Sarah and I went to the cafe"

BRIDGE AUTOMATION:
├─ 1. Increment counter (42 → 43)
├─ 2. Track entities (Sarah: 2 → 3 mentions)
├─ 3. Calculate time (no activities)
├─ 4. TIER_1: Load core files (always)
│     ├─ AUTHOR'S_NOTES.md
│     ├─ STORY_GENOME.md
│     ├─ SCENE_NOTES.md
│     ├─ current_state.md
│     ├─ story_arc.md
│     ├─ {{user}}.md
│     └─ Alex.md
├─ 5. TIER_2: Check if response 43 % 4 == 0?
│     └─ No → Skip TIER_2
├─ 6. TIER_3: Identify triggers in message
│     └─ "Sarah" found → Load [CHAR] Sarah.md
├─ 7. TIER_3 Escalation: Check trigger history
│     └─ Sarah.md: 5/10 triggers → Already being loaded
├─ 8. Build enhanced prompt
│     ├─ TIER_1 files (7 files)
│     ├─ TIER_2 files (0 files - not 4th response)
│     ├─ TIER_3 files (1 file - Sarah.md)
│     ├─ TIER_3 ESCALATED (0 - Sarah already in TIER_3)
│     └─ User message
└─ 9. Send to Claude Code
```

### Prompt Structure

**What Claude receives:**
```
<!-- ========== TIER_1: CORE RP FILES (ALWAYS LOADED) ========== -->

<!-- FILE: AUTHOR'S_NOTES.md -->
[content]

<!-- FILE: STORY_GENOME.md -->
[content]

<!-- FILE: SCENE_NOTES.md -->
[content]

<!-- FILE: current_state.md -->
[content]

<!-- FILE: story_arc.md -->
[content]

<!-- FILE: {{user}}.md -->
[content]

<!-- FILE: Alex.md -->
[content]


<!-- ========== TIER_2: GUIDELINES (PERIODIC) ========== -->
(skipped this response - not 4th)


<!-- ========== TIER_3: TRIGGERED FILES (CONDITIONAL) ========== -->

<!-- FILE: [CHAR] Sarah.md -->
[content]


<!-- ========== USER MESSAGE ========== -->
Sarah and I went to the cafe
```

### Response Statistics

**Logged at end:**
```
[timestamp] Prompt built: TIER_1=7 files, TIER_2=0 files, TIER_3=1 files, Escalated=0 files
[timestamp] Phase 3: Arc generation=NO, Entity cards auto-generated (see above)
[timestamp] ========== Automation Complete ==========
```

---

## Optimization Tips

### Reducing Context Size

**Problem:** Too many files, hitting context limits

**Solutions:**

1. **Reduce TIER_2 frequency**
   ```python
   # Load every 8th instead of 4th
   if response_count % 8 == 0:
   ```

2. **Stricter trigger words**
   ```markdown
   # Instead of generic:
   [Triggers:her,she']

   # Use specific:
   [Triggers:Sarah,Sarah's']
   ```

3. **Shorter TIER_1 files**
   - Keep AUTHOR'S_NOTES.md concise
   - Summarize STORY_GENOME.md

4. **Limit escalation threshold**
   ```python
   # Escalate at 5 instead of 3
   if count >= 5:
   ```

### Increasing Context

**Problem:** Not enough guidance, Claude forgets rules

**Solutions:**

1. **Increase TIER_2 frequency**
   ```python
   # Load every 2nd instead of 4th
   if response_count % 2 == 0:
   ```

2. **Move important files to TIER_1**
   - Edit `load_tier1_files()` in `tui_bridge.py`
   - Add your critical files

3. **Lower escalation threshold**
   ```python
   # Escalate at 2 instead of 3
   if count >= 2:
   ```

### Debugging File Loading

**Check what's being loaded:**

1. **Bridge terminal** - Shows TIER_3 entities
2. **hook.log** - Complete loading log
3. **CURRENT_STATUS.md** - Shows loaded entities

**Example debug session:**
```bash
# Watch log live
tail -f "{RP folder}/state/hook.log"

# Filter for TIER loading
grep "TIER" "{RP folder}/state/hook.log"

# Count files per tier
grep "TIER_1: Loaded" hook.log | wc -l
grep "TIER_2: Loaded" hook.log | wc -l
grep "TIER_3: " hook.log | grep "Loading" | wc -l
```

---

## Summary

**File Loading Tiers:**

| Tier | Frequency | Files | When | Purpose |
|------|-----------|-------|------|---------|
| **TIER_1** | Every response | 7 | Always | Core context |
| **TIER_2** | Every 4th | 6-7 | Periodic | Guidelines |
| **TIER_3** | When triggered | 0-N | Conditional | Entities |
| **Escalated** | When frequent | 0-N | Auto-promoted | Hot entities |

**Key Points:**
- ✅ TIER_1 provides essential story context
- ✅ TIER_2 reinforces writing rules periodically
- ✅ TIER_3 loads details only when relevant
- ✅ Escalation auto-promotes frequently used files
- ✅ All configurable via code or trigger thresholds

**Best Practices:**
- Keep TIER_1 files concise
- Use specific trigger words
- Monitor hook.log for loading patterns
- Adjust frequencies if hitting context limits

---

*For automation details (entity tracking, time calculation, auto-generation), see [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)*
