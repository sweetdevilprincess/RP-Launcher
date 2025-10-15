# RP Folder Structure - Complete Guide

**How to organize your roleplay folders for the Claude Code RP system**

---

## Complete Structure Overview

```
RP Claude Code/                          # Main project folder
│
├── .claude/                             # Claude Code configuration (SHARED)
│   ├── commands/                        # Slash commands (SHARED across all RPs)
│   │   ├── continue.md
│   │   ├── endSession.md
│   │   ├── arc.md
│   │   └── track.md
│   └── hooks/                           # Automation hooks (SHARED)
│       ├── user-prompt-submit.sh        # Pre-response hook
│       └── time-tracker.sh              # Time calculation hook
│
├── guidelines/                          # SHARED writing guidelines
│   ├── Writing_Style_Guide.md           # Prose guidelines (shared)
│   ├── Timing.txt                       # Activity durations (shared)
│   └── Common_Tropes.md                 # Reference materials (shared)
│
├── templates/                           # Template files (for reference)
│   ├── TEMPLATE_AUTHORS_NOTES.md
│   ├── TEMPLATE_SCENE_NOTES.md
│   ├── TEMPLATE_STORY_GENOME.md
│   └── TEMPLATE_ROLEPLAY_OVERVIEW.md
│
├── Roleplay 1/                          # Individual RP folder
│   ├── Roleplay 1.md                    # Overview & quick reference
│   ├── AUTHOR'S_NOTES.md                # Absolute story rules
│   ├── STORY_GENOME.md                  # Intended story path
│   ├── SCENE_NOTES.md                   # Current session guidance
│   │
│   ├── characters/                      # Character sheets
│   │   ├── {{user}}.md                  # Player character
│   │   ├── {{char}}.md                  # Main NPC
│   │   └── [NPCName].md                 # Supporting characters
│   │
│   ├── entities/                        # Auto-generated entity cards
│   │   ├── [CHAR] Name.md               # Character entities
│   │   ├── [LOC] Name.md                # Location entities
│   │   ├── [ITEM] Name.md               # Item entities
│   │   └── [EVENT] Name.md              # Event entities
│   │
│   ├── chapters/                        # Story chapters
│   │   ├── Chapter 01.txt
│   │   ├── Chapter 02.txt
│   │   └── ...
│   │
│   ├── sessions/                        # Session logs/chatlogs
│   │   ├── Session 01.txt
│   │   ├── Session 02.txt
│   │   └── ...
│   │
│   └── state/                           # Tracking & state files
│       ├── current_state.md             # Current timestamp, location, NPCs
│       ├── story_arc.md                 # Current story arc
│       ├── entity_tracker.json          # Entity mention tracking
│       └── response_counter.txt         # Response count for arc generation
│
├── Roleplay 2/                          # Another RP (same structure)
│   └── [Same structure as Roleplay 1]
│
├── config/
│   └── CLAUDE.md                        # Main Claude Code instructions
│
└── [Documentation files]                # Planning docs, design docs, etc.
```

---

## Folder Breakdown

### Root Level (`RP Claude Code/`)

**Purpose**: Contains all RPs, shared resources, and system configuration

**Contents**:
- `.claude/` - Configuration and automation (shared)
- `config/` - Configuration files including CLAUDE.md
- `guidelines/` - Writing guides (shared across all RPs)
- `templates/` - Template files for new RPs
- Individual RP folders
- Documentation files

---

### `.claude/` - Shared Configuration

**Purpose**: Claude Code system configuration (applies to all RPs)

#### `.claude/commands/` - Slash Commands
Custom commands available in any RP:
- `/continue` - Smart session start
- `/endSession` - Session end protocol
- `/arc` - Generate/view story arc
- `/track [entity]` - Create entity card

#### `.claude/hooks/` - Automation Hooks
Scripts that run automatically:
- `user-prompt-submit.sh` - Runs before each response
  - Time calculation
  - Conditional file injection
  - Entity mention tracking
  - Response counting

---

### `guidelines/` - Shared Resources

**Purpose**: Writing guides and references used across multiple RPs

**Common Files**:
- `Writing_Style_Guide.md` - General prose guidelines
- `Timing.txt` - Activity duration reference
- `POV_Guide.md` - POV best practices
- `Dialogue_Guide.md` - Dialogue writing tips
- `Genre_Guides/` - Genre-specific guidelines
  - `Dark_Romance.md`
  - `Fantasy.md`
  - `Sci_Fi.md`

**Why Shared**: These don't change between RPs, so share them to avoid duplication.

---

### `templates/` - Template Files

**Purpose**: Reference templates for starting new RPs

**Contents**: All template files we created:
- `TEMPLATE_AUTHORS_NOTES.md`
- `TEMPLATE_SCENE_NOTES.md`
- `TEMPLATE_STORY_GENOME.md`
- `TEMPLATE_ROLEPLAY_OVERVIEW.md`

**How to Use**: Copy to new RP folder and fill in with your story details.

---

### Individual RP Folder (`Roleplay 1/`)

**Purpose**: Contains everything for one specific roleplay

---

## Core Files (RP Root)

### `[RP Name].md` - Overview File
**Purpose**: Central overview and quick reference
**Referenced**: Every response

**Contains**:
- ⚠️ Critical files reference list
- Story overview (genre, setting, premise)
- Character progressions (timeline style)
- Current state snapshot
- Information asymmetry quick reference
- Active plot threads
- Key relationships
- Session prep checklist

**Example**: `Lilith and Silas.md`

---

### `AUTHOR'S_NOTES.md` - Absolute Rules
**Purpose**: Story mechanics, rules, and meta-knowledge
**Referenced**: FIRST (highest priority)

**Contains**:
- Story mechanics & systems
- Information asymmetry (who knows what)
- Character behavior rules (absolutes)
- Absolute constraints
- Conditional rules (if X then Y)
- Meta story rules (POV, pacing)

**For Complex RPs**: May include pointer to active Genome:
```markdown
## Current Active Genome
**Active**: GENOME_DEMON_LORD_PATH.md
**Since**: Chapter 15
**Reason**: Healer chose demon lord over church
```

---

### `STORY_GENOME.md` - Intended Path
**Purpose**: Intended story trajectory with themes and analysis
**Referenced**: Second (after Author's Notes)

**Contains**:
- Plot outline (intended major beats)
- Thematic layers (why things happen)
- Narrative patterns (how story unfolds)
- Character arcs (intended trajectories)
- Relationship dynamics evolution
- Intended climax & resolution
- Divergence log (when story changes path)

**For Complex RPs**: Multiple Genome files:
- `GENOME_CHURCH_PATH.md`
- `GENOME_DEMON_LORD_PATH.md`
- `GENOME_NEUTRAL_PATH.md`

---

### `SCENE_NOTES.md` - Session Guidance
**Purpose**: Temporary session-specific instructions
**Referenced**: After Arc, before character sheets

**Contains**:
- Current scene focus
- Temporary reminders
- Next story beats
- Reader reveals (dramatic irony)
- Character development focus
- Continuity checks
- Session goals

**Updated**: Each session or as needed

---

## Subfolders

### `characters/` - Character Sheets

**Purpose**: Detailed character information

**File Naming**: `[CharacterName].md`

**Standard Files**:
- `{{user}}.md` - Player character (you)
- `{{char}}.md` - Main NPC
- `Marcus.md`, `Jenna.md`, etc. - Supporting characters

**Contains** (typical character sheet):
- Basic info
- Physical description
- Personality traits
- Knowledge boundaries (knows/suspects/doesn't know)
- Relationship dynamics
- Behavioral patterns
- **Triggers**: Keywords for conditional loading

**Example Triggers Section**:
```markdown
**Triggers**: Marcus, Marc, protective friend, coworker
```

---

### `entities/` - Auto-Generated Cards

**Purpose**: Cards for recurring entities (generated manually or by hook)

**File Naming**: `[PREFIX] EntityName.md`

**Prefixes**:
- `[CHAR]` - Characters (minor NPCs, background)
- `[LOC]` - Locations
- `[ITEM]` - Important items
- `[EVENT]` - Significant events

**Examples**:
- `[CHAR] Bartender.md`
- `[LOC] Bruno's Restaurant.md`
- `[ITEM] Hidden Camera.md`
- `[EVENT] First Kiss.md`

**Contains**:
- Type and description
- First mentioned (chapter/timestamp)
- Significance
- Related entities
- Appearances log
- **Triggers**: Keywords for conditional loading

---

### `chapters/` - Story Chapters

**Purpose**: Chapter summaries (from session end protocol)

**File Naming**: `Chapter [XX].txt`

**Contains** (typical chapter summary):
- Summary of events
- Relationship tracking
- Quote preservation
- Timeline documentation
- Theme tracking
- World details

---

### `sessions/` - Session Logs

**Purpose**: Raw chat logs or session transcripts

**File Naming**: `Session [XX].txt` or `Chapter [XX]-chatlog.txt`

**Optional**: Some people prefer to keep raw logs separate from curated chapter summaries.

---

### `state/` - Tracking Files

**Purpose**: System state and tracking data

---

#### `current_state.md`
**Purpose**: Current game state
**Updated**: Every response (by hook or manual)

**Contains**:
```markdown
# Current State

**Last Updated**: [Timestamp]
**Current Chapter**: 22
**Current Timestamp**: Saturday, November 5th, 2024 - 7:20 PM
**Current Location**: Bruno's Italian Restaurant

## Recent Activities (Last Response)
- eat: 10 minutes
- talk: 10 minutes
- Total: 20 minutes
- New timestamp: 7:40 PM

## Active NPCs Present
- Silas ({{char}})
- Restaurant staff (background)

## Active Plot Threads
- [From story arc]
```

---

#### `story_arc.md`
**Purpose**: Current story arc (generated periodically)

**Contains**:
```markdown
# Current Story Arc

**Generated**: [Date]
**Arc Title**: Moving In Together
**Current Phase**: Rising Action

## Where We Are in Genome
- Genome Beat: "Point of No Return - Moving In"
- Status: On track / Diverged / Modified

## Key Recent Events
- [Events]

## Active Plot Threads
- [Threads]

## Character Developments
- [Developments]

## Next Direction
- [Based on Genome + recent events]
```

---

#### `entity_tracker.json`
**Purpose**: Track entity mentions for auto-card generation

**Format**:
```json
{
  "entities": {
    "Marcus": {
      "type": "character",
      "mentions": 15,
      "first_chapter": 2,
      "last_chapter": 20,
      "card_exists": true
    },
    "Cathedral": {
      "type": "location",
      "mentions": 3,
      "first_chapter": 18,
      "last_chapter": 20,
      "card_exists": false
    }
  }
}
```

**Updated**: By hook after each response

---

#### `response_counter.txt`
**Purpose**: Track response count for arc generation trigger

**Format**:
```
47
```

**Updated**: By hook after each response
**Trigger**: When counter reaches 50, suggest arc generation

---

## Reference Priority Order

When Claude responds, files are referenced in this order:

```
1. AUTHOR'S_NOTES.md              (absolute rules - HIGHEST)
2. STORY_GENOME.md                (intended path)
3. [RP Name].md                   (overview & quick ref)
4. state/story_arc.md             (current progress)
5. SCENE_NOTES.md                 (session guidance)
6. state/current_state.md         (timestamp, location)
7. characters/[Name].md           (CONDITIONAL - if triggered)
8. entities/[PREFIX] [Name].md    (CONDITIONAL - if triggered)
9. guidelines/ files              (as needed)
```

**Conditional Loading**:
- Hook reads user message
- Searches for trigger keywords
- Injects matching character/entity files

**Example**:
- User mentions "Marcus" → Hook injects `characters/Marcus.md`
- User mentions "cathedral" → Hook injects `entities/[LOC] Cathedral.md`

---

## Setting Up a New RP

### Step 1: Create RP Folder
```bash
mkdir "Roleplay Name"
cd "Roleplay Name"
```

### Step 2: Copy Templates
Copy from `templates/` folder:
- `TEMPLATE_ROLEPLAY_OVERVIEW.md` → `Roleplay Name.md`
- `TEMPLATE_AUTHORS_NOTES.md` → `AUTHOR'S_NOTES.md`
- `TEMPLATE_STORY_GENOME.md` → `STORY_GENOME.md`
- `TEMPLATE_SCENE_NOTES.md` → `SCENE_NOTES.md`

### Step 3: Create Subfolders
```bash
mkdir characters
mkdir entities
mkdir chapters
mkdir sessions
mkdir state
```

### Step 4: Create State Files
```bash
# In state/ folder:
touch current_state.md
touch story_arc.md
echo "0" > response_counter.txt
echo "{}" > entity_tracker.json
```

### Step 5: Fill in Templates
Edit each copied template with your story details.

### Step 6: Create Character Sheets
Create character files in `characters/`:
- `{{user}}.md` (player character)
- `{{char}}.md` (main NPC)
- Others as needed

---

## For Complex RPs (Multiple Paths)

### Additional Files:
```
Roleplay Name/
├── AUTHOR'S_NOTES.md              (points to active Genome)
├── GENOME_PATH_A.md               (ending A)
├── GENOME_PATH_B.md               (ending B)
├── GENOME_PATH_C.md               (ending C, optional)
└── [rest of structure]
```

### In AUTHOR'S_NOTES.md:
```markdown
## Current Active Genome
**Active**: GENOME_PATH_B.md
**Since**: Chapter 15
**Reason**: Character chose X over Y

## Genome Switching Triggers
- If [condition] → Switch to GENOME_PATH_A.md
- If [condition] → Switch to GENOME_PATH_C.md
```

---

## Quick Reference Checklist

### Before Starting Session:
- [ ] All core files exist (Overview, Author's Notes, Genome, Scene Notes)
- [ ] current_state.md is updated with last timestamp
- [ ] SCENE_NOTES.md reflects current session goals
- [ ] Character sheets have trigger keywords

### After Each Response:
- [ ] Hook updates response_counter.txt (+1)
- [ ] Hook tracks entity mentions in entity_tracker.json
- [ ] Hook calculates time, updates current_state.md
- [ ] Hook injects conditional files based on triggers

### Every 50 Responses:
- [ ] Generate/update story_arc.md
- [ ] Compare to STORY_GENOME.md (on track vs diverged)
- [ ] Update Genome if major divergence occurred

### End of Session:
- [ ] Update character sheets (knowledge boundaries)
- [ ] Create chapter summary (chapters/)
- [ ] Save session log (sessions/)
- [ ] Update SCENE_NOTES.md for next session
- [ ] Update Genome if story path changed

---

## File Size Guidelines

**Keep files manageable**:
- **Core files** (Author's Notes, Genome, Overview): 2000-5000 words
- **Character sheets**: 500-1500 words
- **Entity cards**: 200-500 words
- **Scene Notes**: 500-1000 words (clear between sessions)
- **Chapter summaries**: 1500-3000 words

**Why**: Large files slow context loading. If file gets too big, split or archive.

---

## Migration from Existing RP

### If You Have an Existing RP:

1. **Create new folder** using structure above
2. **Map existing files**:
   - Your CLAUDE.md → Parts go to Author's Notes, parts to Overview
   - Character sheets → `characters/` folder
   - Chapters → `chapters/` folder
   - Guidelines → `guidelines/` folder (shared)
3. **Create new required files**:
   - STORY_GENOME.md (write intended path based on story so far)
   - SCENE_NOTES.md (current session)
   - state/ files (initialize with current state)
4. **Test with a few responses** before committing

---

## Common Mistakes to Avoid

❌ **Putting everything in one file** (Overview gets too long)
✅ **Separate concerns** (Rules, Genome, Overview, Scene Notes)

❌ **No trigger keywords** (conditional loading won't work)
✅ **Add triggers to all character/entity files**

❌ **Not updating current_state.md** (timestamp drifts)
✅ **Let hook update it** or manually update each response

❌ **Genome too vague** (doesn't guide Arc generation)
✅ **Detailed Genome with themes and analysis**

❌ **Forgetting to update Genome when story diverges**
✅ **Use Divergence Log** in Genome, update intended path

---

## Summary

### What Goes Where:

| Content | File | When to Update |
|---------|------|----------------|
| Absolute story rules | AUTHOR'S_NOTES.md | Rarely |
| Intended story path | STORY_GENOME.md | When story diverges |
| What's actually happened | [RP Name].md | After major events |
| Current arc progress | state/story_arc.md | Every 50 responses |
| Session guidance | SCENE_NOTES.md | Each session |
| Right now details | state/current_state.md | Every response |
| Character details | characters/*.md | When knowledge changes |
| Entity details | entities/*.md | When created/updated |

### Reference Priority:
1. Rules (Author's Notes)
2. Plan (Genome)
3. Reality (Overview)
4. Progress (Arc)
5. Focus (Scene Notes)
6. Now (Current State)
7. Details (Characters/Entities - conditional)

---

**This structure supports**:
✅ Simple linear RPs (one Genome, straightforward)
✅ Complex branching RPs (multiple Genomes, path switching)
✅ Long-running RPs (organized chapters, sessions, state)
✅ Multiple simultaneous RPs (each in own folder, shared guidelines)
✅ Automation (hooks track and inject automatically)
✅ Flexibility (add/remove files as needed)
