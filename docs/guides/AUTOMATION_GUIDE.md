# Automation Guide - Complete Reference

**Last Updated:** October 12, 2025

This document explains all automation features in the RP Claude Code system. All automation runs in the **bridge** (`tui_bridge.py`) automatically with each message.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Configuration](#configuration)
3. [Response Counter](#response-counter)
4. [Entity Tracking](#entity-tracking)
5. [Time Calculation](#time-calculation)
6. [Trigger System](#trigger-system)
7. [Auto-Generation](#auto-generation)
8. [Status Updates](#status-updates)
9. [Logging](#logging)

---

## Overview

Every time you send a message through the TUI, the bridge runs a **full automation pipeline** before sending to Claude Code:

```
USER MESSAGE
    ↓
1. Increment response counter
2. Track entities in message
3. Calculate time from activities
4. Load TIER files (see FILE_LOADING_TIERS.md)
5. Identify trigger-based files
6. Check for auto-generation thresholds
7. Update status files
8. Log everything
9. Build enhanced prompt
    ↓
SEND TO CLAUDE CODE
```

**Location:** All automation code is in `tui_bridge.py` (lines 40-992)

**Configuration:** `{RP folder}/state/automation_config.json`

---

## Configuration

### Automation Config File

**Location:** `{RP folder}/state/automation_config.json`

**Example:**
```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 50
}
```

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `auto_entity_cards` | `true` | Auto-generate entity cards when mention threshold reached |
| `entity_mention_threshold` | `2` | Number of mentions before auto-generating card |
| `auto_story_arc` | `true` | Auto-generate story arc at frequency interval |
| `arc_frequency` | `50` | Generate arc every N responses |

### Creating Config

If the file doesn't exist, defaults are used. To create:

```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 3,
  "auto_story_arc": true,
  "arc_frequency": 50
}
```

Save to: `{RP folder}/state/automation_config.json`

---

## Response Counter

### What It Does

Tracks the total number of Claude responses in this RP.

**File:** `{RP folder}/state/response_counter.txt`

**Content:** Single number (e.g., `42`)

**Increments:** Every time bridge sends a message to Claude Code

### Used For

1. **Arc generation** - Trigger at specific intervals (every 50 responses)
2. **TIER_2 loading** - Load guidelines every 4th response
3. **Chapter estimation** - Rough chapter calculation (10 responses ≈ 1 chapter)
4. **Progress tracking** - Show in TUI context panel (e.g., "42/250 responses")

### How It Works

**Code:** `tui_bridge.py` - `increment_counter()`

```python
# Read current count
count = int(response_counter.txt)  # e.g., 41

# Increment
count += 1  # 42

# Save
response_counter.txt = "42"

# Log
hook.log: "[timestamp] Response counter: 42"

# Check arc threshold
if count % 50 == 0:  # 42 % 50 = 42 (not yet)
    # Will trigger at 50, 100, 150, etc.
```

### Manual Reset

To restart counter:
```bash
echo "0" > "{RP folder}/state/response_counter.txt"
```

---

## Entity Tracking

### What It Does

Automatically tracks **capitalized words** (potential entity names) in your messages, counts mentions, and can auto-generate character cards.

**File:** `{RP folder}/state/entity_tracker.json`

**Example:**
```json
{
  "entities": {
    "Sarah": {
      "mentions": 3,
      "first_chapter": 1,
      "last_chapter": 2,
      "card_created": true
    },
    "Marcus": {
      "mentions": 1,
      "first_chapter": 2,
      "last_chapter": 2,
      "card_created": false
    }
  }
}
```

### How It Works

**Code:** `tui_bridge.py` - `track_entities()`

**Every message:**
1. **Extract capitalized words** from message
   ```
   Message: "Sarah and Marcus went to the cafe"
   Found: ["Sarah", "Marcus"]
   ```

2. **Filter common words**
   - Skips: The, A, I, You, He, She, It, They, We, etc.
   - Keeps: Sarah, Marcus (proper nouns)

3. **Track mentions**
   - Sarah: 2 mentions → 3 mentions
   - Marcus: 0 mentions → 1 mention

4. **Update chapter info**
   - Rough estimate: `current_chapter = (response_count // 10) + 1`
   - Response 25 → Chapter 3

5. **Check auto-generation threshold**
   - If `mentions >= entity_mention_threshold` AND `card_created == false`
   - Trigger auto-generation (see [Auto-Generation](#auto-generation))

**Log output:**
```
[timestamp] Entity mentioned: Sarah
[timestamp] Entity 'Sarah': 3 mentions
[timestamp] TRIGGERING AUTO-GENERATION: Sarah reached 2 mentions
```

### Skipped Words

The following words are ignored (not tracked as entities):

```python
skip_words = {
    'The', 'A', 'An', 'I', 'You', 'He', 'She', 'It', 'They', 'We',
    'Is', 'Was', 'Are', 'Were', 'Be', 'Been', 'Have', 'Has', 'Had',
    'Do', 'Does', 'Did', 'Will', 'Would', 'Could', 'Should', 'May',
    'Might', 'Must', 'Can', 'My', 'Your', 'His', 'Her', 'Their', 'Our'
}
```

### Viewing Tracked Entities

**In TUI:**
- Press `F6` to open Entities overlay
- Shows all tracked entities, mention counts, card status

**In file:**
```bash
cat "{RP folder}/state/entity_tracker.json"
```

---

## Time Calculation

### What It Does

Automatically calculates elapsed time based on **activities** mentioned in your message, using predefined time costs.

**Time costs file:** `Guidelines/Timing.txt`

**Example Timing.txt:**
```
# Activity time costs (in minutes)
eat: 10, drink: 3, walk: 5, drive: 15, sleep: 480, shower: 10
```

**Example:**
```
Message: "Alex finished eating and went for a walk"

Activities detected:
- eating (matched "eat") → 10 minutes
- walk → 5 minutes

Total time: 15 minutes
```

### How It Works

**Code:** `tui_bridge.py` - `calculate_time()`

**Process:**
1. **Load timing file** (`Guidelines/Timing.txt`)
2. **Parse activities** (format: `activity: minutes, activity: minutes`)
3. **Search message** for activity keywords (with word boundaries)
4. **Sum up time** for all matched activities
5. **Update current_state.md** with suggestion

**Example flow:**
```python
# Timing.txt contains:
# eat: 10, drink: 3, walk: 5

Message: "Sarah ate lunch and drank coffee"

# Search for activities in message:
"ate" matches "eat" → 10 minutes
"drank" matches "drink" → 3 minutes

Total: 13 minutes

# Add to current_state.md:
## Time Calculation Suggestion (Latest)
**Activities detected**: eat (10 min), drink (3 min)
**Suggested time elapsed**: 13 minutes
**Note**: Review and adjust for modifiers (fast/slow) or unknown activities
```

### Log Output

```
[timestamp] Time tracking: eat (10 min), drink (3 min) = 13 minutes
```

### Adding Custom Activities

Edit `Guidelines/Timing.txt`:
```
# Add your activities:
eat: 10, drink: 3, walk: 5, drive: 15
read: 30, cook: 45, workout: 60
```

Format: `activity: minutes` separated by commas

### Limitations

- Only detects activities in Timing.txt
- Exact word match (with word boundaries)
- No context awareness (can't distinguish "fast walk" vs "slow walk")
- Suggestion only - Claude decides actual time advancement

---

## Trigger System

### What It Does

Automatically loads character/entity files when **trigger words** appear in your message.

**This is TIER_3 conditional loading** - see [FILE_LOADING_TIERS.md](FILE_LOADING_TIERS.md) for full details.

### Trigger Formats

Entity/character files can define triggers in two formats:

**Format 1:** Markdown bold
```markdown
**Triggers**: Sarah, her, she
```

**Format 2:** AI Dungeon style
```markdown
[Triggers:Sarah,her,she']
```

### How It Works

**Code:** `tui_bridge.py` - `identify_triggers()`

**Every message:**
1. **Scan character files** (`{RP folder}/characters/*.md`)
2. **Scan entity files** (`{RP folder}/entities/*.md`)
3. **Extract triggers** from each file
4. **Check if any trigger appears in message**
5. **Load matching files** into enhanced prompt

**Example:**

**File:** `entities/[CHAR] Sarah.md`
```markdown
[Triggers:Sarah,her,girlfriend']

# Sarah Mitchell
- Age: 24
- Role: Alex's girlfriend
```

**Message:** "Sarah called me this morning"

**Result:**
- "Sarah" found in message
- Load `[CHAR] Sarah.md` into prompt (TIER_3)

**Log:**
```
[timestamp] Trigger match: Loading [CHAR] Sarah.md (matched: Sarah)
[timestamp] Conditional files loaded: 1
```

### Creating Triggered Files

**For characters:**
```markdown
# characters/Marcus.md

[Triggers:Marcus,him,friend']

**Name**: Marcus Thompson
**Role**: Best friend
```

**For entities:**
```markdown
# entities/[ITEM] Red Car.md

**Triggers**: car, vehicle, dodge, charger

**Type**: Item
**Description**: Alex's red Dodge Charger
```

### Trigger Escalation

Files that trigger **3+ times in the last 10 responses** get **escalated to TIER_2** treatment (loaded more frequently).

See [FILE_LOADING_TIERS.md](FILE_LOADING_TIERS.md) for details.

---

## Auto-Generation

### What It Does

Automatically generates content using **DeepSeek API** when certain thresholds are reached.

**API:** DeepSeek via OpenRouter

**Required:** API key in environment or `state/secrets.json`

### 1. Auto Entity Cards

**Trigger:** Entity mentioned >= `entity_mention_threshold` times

**Default threshold:** 2 mentions

**What it generates:**
- Character card for the entity
- Based on context from recent chapters
- Saved to `entities/[CHAR] {name}.md`

**Example:**

```
Response 5: "Sarah walked in"    → Sarah: 1 mention
Response 7: "Sarah smiled"       → Sarah: 2 mentions → AUTO-GENERATE

DeepSeek generates:

# [CHAR] Sarah Mitchell

[Triggers:Sarah']
**Type**: Character
**First Mentioned**: Chapter 1
**Mention Count**: 2

## Description
Based on story context, Sarah appears to be...

## Role in Story
...

Saved to: entities/[CHAR] Sarah.md
```

**Code:** `tui_bridge.py` - `auto_generate_entity_card()`

**Process:**
1. **Search recent chapters** for lines mentioning entity
2. **Build context** from matching lines
3. **Create prompt** for DeepSeek
4. **Call DeepSeek API**
5. **Save card** to `entities/[CHAR] {name}.md`
6. **Mark as created** in entity_tracker.json
7. **Log success**

**Log:**
```
[timestamp] [AUTO-GEN] Generating entity card for: Sarah
[timestamp] [SUCCESS] Auto-generated entity card: entities/[CHAR] Sarah.md
```

**Configuration:**
```json
{
  "auto_entity_cards": true,        # Enable/disable
  "entity_mention_threshold": 2     # Mentions needed
}
```

### 2. Auto Story Arc

**Trigger:** Response count reaches `arc_frequency` interval

**Default frequency:** Every 50 responses

**What it generates:**
- Instructions injected into Claude's prompt
- Claude reads Story Genome, recent chapters, current state
- Claude generates 11-beat future arc
- Claude saves to `state/story_arc.md`

**Example:**

```
Response 49: Normal response
Response 50: ARC GENERATION TRIGGERED

Bridge injects special instructions into prompt:

<!-- ========================================
AUTOMATIC STORY ARC GENERATION TRIGGERED
======================================== -->

Read: STORY_GENOME.md (intended plot beats)
Read: Last 2-3 chapter summaries
Read: state/current_state.md
Read: state/story_arc.md (existing arc)

GENERATE UPDATED STORY ARC:
... detailed instructions ...

Claude generates arc and saves to state/story_arc.md
```

**Code:** `tui_bridge.py` - `auto_generate_story_arc()`

**Process:**
1. **Check response count** (`count % 50 == 0`)
2. **Build arc generation prompt** (comprehensive instructions)
3. **Inject into enhanced prompt** (before user message)
4. **Claude processes** and generates arc
5. **Claude saves** to `state/story_arc.md`

**Log:**
```
[timestamp] Arc generation threshold reached at response 50
[timestamp] Phase 3: Arc generation=YES (injected)
```

**Configuration:**
```json
{
  "auto_story_arc": true,    # Enable/disable
  "arc_frequency": 50        # Every N responses
}
```

### 3. Future Auto-Generation

**Not yet implemented:**
- Auto chapter summaries (when chapter changes)
- Auto memory updates (periodic or on request)
- Auto character sheet updates (from session activity)

### API Key Setup

**Option 1: Environment variable**
```bash
set OPENROUTER_API_KEY=sk-or-v1-...
# or
set DEEPSEEK_API_KEY=sk-or-v1-...
```

**Option 2: secrets.json**
```json
// {RP folder}/state/secrets.json
{
  "OPENROUTER_API_KEY": "sk-or-v1-..."
}
```

**Code checks in order:**
1. `DEEPSEEK_API_KEY` env var
2. `OPENROUTER_API_KEY` env var
3. `{rp_dir}/state/secrets.json`
4. `./state/secrets.json`

---

## Status Updates

### What It Does

Auto-generates `CURRENT_STATUS.md` with real-time system status.

**File:** `{RP folder}/CURRENT_STATUS.md`

**Updates:** Every message

**Example output:**
```markdown
# Current RP Status

**Last Updated**: 2025-10-12 19:30:15

---

## 📍 Current State

- **Timestamp**: Morning, Day 3
- **Location**: Alex's apartment
- **Chapter**: Chapter 2
- **Response Count**: 42

---

## 📊 Progress

**Story Arc**: 42 / 50 responses
- Next arc generation in: **8 responses**
- Progress: ████████░░

---

## 🎭 Entities

**Tracked**: 5 entities in entity_tracker.json
**Loaded This Response**: Sarah, Marcus

---

## ⚙️ Automation

**Entity Cards**: ✅ ON (Threshold: 2 mentions)
**Story Arcs**: ✅ ON (Every 50 responses)

---

## 📝 Quick Commands

- `/status` - Detailed status report
- `/continue` - Load session context
- `/endSession` - End session protocol
```

**Code:** `tui_bridge.py` - `update_status_file()`

**Includes:**
- Current timestamp, location, chapter
- Response count
- Arc progress bar
- Entities loaded this response
- Automation settings
- Recent activity from hook.log (last 10 lines)

### Viewing Status

**In TUI:** Press `F8` for Status overlay

**In file:** Open `{RP folder}/CURRENT_STATUS.md`

**Keep open:** Recommended to keep this file open in a second pane for live updates

---

## Logging

### What It Does

Logs all automation activity to `hook.log` with timestamps.

**File:** `{RP folder}/state/hook.log`

**Format:** `[YYYY-MM-DD HH:MM:SS] Message`

**Example:**
```
[2025-10-12 19:30:15] ========== RP Automation Starting (Phases 1-3: Full System) ==========
[2025-10-12 19:30:15] Response counter: 42
[2025-10-12 19:30:15] Time tracking: eat (10 min) = 10 minutes
[2025-10-12 19:30:15] Entity mentioned: Sarah
[2025-10-12 19:30:15] Entity 'Sarah': 3 mentions
[2025-10-12 19:30:15] --- TIER_1 Loading (Core Files) ---
[2025-10-12 19:30:15] TIER_1: Loaded AUTHOR'S_NOTES.md
[2025-10-12 19:30:15] TIER_1: Loaded STORY_GENOME.md
[2025-10-12 19:30:15] --- TIER_2 Loading (Guidelines) ---
[2025-10-12 19:30:15] --- TIER_3 Loading (Conditional) ---
[2025-10-12 19:30:15] Trigger match: Loading [CHAR] Sarah.md (matched: Sarah)
[2025-10-12 19:30:15] Conditional files loaded: 1
[2025-10-12 19:30:15] Prompt built: TIER_1=7 files, TIER_2=0 files, TIER_3=1 files, Escalated=0 files
[2025-10-12 19:30:15] Phase 3: Arc generation=NO, Entity cards auto-generated (see above)
[2025-10-12 19:30:15] ========== Automation Complete ==========
```

### Viewing Logs

**In TUI:** Press `F8` for Status overlay (shows last 10 lines)

**Full log:**
```bash
cat "{RP folder}/state/hook.log"
# or
tail -f "{RP folder}/state/hook.log"  # Live view
```

**In bridge terminal:** All log messages also print to bridge console

### Log Levels

**INFO:** Normal operations
```
[timestamp] Response counter: 42
[timestamp] TIER_1: Loaded AUTHOR'S_NOTES.md
```

**WARNING:** Non-fatal issues
```
[timestamp] WARNING: Could not read Timing.txt
[timestamp] WARNING: Could not load TIER_1 file SCENE_NOTES.md
```

**ERROR:** Failures
```
[timestamp] ERROR: Could not save entity tracker: [error]
[timestamp] ERROR: DeepSeek API error: [error]
```

**SUCCESS:** Auto-generation completions
```
[timestamp] [SUCCESS] Auto-generated entity card: entities/[CHAR] Sarah.md
```

### Clearing Logs

To start fresh:
```bash
rm "{RP folder}/state/hook.log"
# Or
echo "" > "{RP folder}/state/hook.log"
```

---

## Summary

**Every message triggers:**
1. ✅ Response counter +1
2. ✅ Entity tracking (capitalized words)
3. ✅ Time calculation (from activities)
4. ✅ TIER file loading (1/2/3)
5. ✅ Trigger-based loading (conditional)
6. ✅ Auto-generation checks (cards, arcs)
7. ✅ Status file update
8. ✅ Complete logging

**Configurable via:**
- `state/automation_config.json` - Thresholds, enable/disable
- `Guidelines/Timing.txt` - Activity time costs
- Trigger words in entity/character files

**Monitored via:**
- `state/hook.log` - Complete activity log
- `CURRENT_STATUS.md` - Live status dashboard
- Bridge terminal - Real-time console output
- TUI Status overlay (F8) - Quick view

---

*For file loading details (TIER system), see [FILE_LOADING_TIERS.md](FILE_LOADING_TIERS.md)*
