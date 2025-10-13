# Claude Code RP System - Main Instructions

**READ THIS FIRST - Core RP System Instructions**

---

## How This System Works

This folder contains a comprehensive RP (roleplay) system designed for Claude Code. Each RP lives in its own folder with a structured set of files that guide storytelling, track continuity, and maintain consistency.

---

## Reference Priority (CRITICAL - Follow This Order)

When responding to any RP session, reference files in this EXACT order:

### 1. AUTHOR'S_NOTES.md (HIGHEST PRIORITY)
**Location**: `[RP Folder]/AUTHOR'S_NOTES.md`
**Purpose**: Absolute story rules, mechanics, meta-knowledge
**Priority**: ALWAYS read first, ALWAYS follow

Contains:
- Story mechanics (dice systems, loops, special rules)
- Information asymmetry (who knows what)
- Character behavior absolutes (never violated)
- Conditional rules (if X then Y triggers)
- Meta story rules (POV, pacing, tone)

**For Complex RPs**: Check "Current Active Genome" section to see which Genome file to use

---

### 2. STORY_GENOME.md (or Active Genome)
**Location**: `[RP Folder]/STORY_GENOME.md` or `[RP Folder]/GENOME_[PATH].md`
**Purpose**: Intended story path with themes and analysis
**Priority**: Read second to understand intended direction

Contains:
- Plot outline (intended major beats)
- Thematic layers (why things happen)
- Narrative patterns (how story unfolds)
- Character arcs (intended trajectories)
- Intended climax & resolution

**Check**: Are we on track with Genome or have we diverged?

---

### 3. [RP Name].md (Overview File)
**Location**: `[RP Folder]/[RP Name].md`
**Purpose**: Central overview and quick reference
**Priority**: Read for current context

Contains:
- Story overview (genre, premise, themes)
- Character progressions (timeline of what's happened)
- Current state snapshot
- Information asymmetry quick reference
- Active plot threads
- Key relationships

---

### 4. state/story_arc.md
**Location**: `[RP Folder]/state/story_arc.md`
**Purpose**: Current arc progress through Genome
**Priority**: Read for detailed current status

Contains:
- Where we are in Genome
- Recent events
- Active plot threads
- Character developments
- Next direction

---

### 5. SCENE_NOTES.md
**Location**: `[RP Folder]/SCENE_NOTES.md`
**Purpose**: Current session guidance
**Priority**: Read for session-specific instructions

Contains:
- Current scene focus
- Temporary reminders
- Next story beats
- Reader reveals (dramatic irony)
- Session goals

---

### 6. state/current_state.md
**Location**: `[RP Folder]/state/current_state.md`
**Purpose**: Immediate state (timestamp, location, NPCs)
**Priority**: Read for "right now" details

Contains:
- Current timestamp
- Current location
- Active NPCs present
- Recent activities and time calculations

---

### 7. Conditional Files (Triggered by Content)

**Character Sheets**: `[RP Folder]/characters/[Name].md`
- Load when character is mentioned or present
- Check character's "Triggers" section for keywords

**Entity Cards**: `[RP Folder]/entities/[PREFIX] [Name].md`
- Load when entity is mentioned
- Check entity's "Triggers" section for keywords

**Shared Guidelines**: `guidelines/[File].md`
- Load as needed (Writing_Style_Guide.md, Timing.txt, etc.)

---

## Before Each Response - Checklist

- [ ] Read AUTHOR'S_NOTES.md (absolute rules)
- [ ] Read STORY_GENOME.md (or active Genome) (intended path)
- [ ] Read [RP Name].md (overview)
- [ ] Read state/story_arc.md (current arc)
- [ ] Read SCENE_NOTES.md (session guidance)
- [ ] Read state/current_state.md (timestamp, location)
- [ ] Check user message for trigger keywords → Load matching character/entity files
- [ ] Reference guidelines/ files as needed

---

## Time Tracking (MANDATORY)

### Calculation Process:
1. **Read user input** for activities mentioned
2. **Check guidelines/Timing.txt** for base durations
3. **Calculate total time** (sum sequential activities, account for modifiers)
4. **Update state/current_state.md** with:
   - Activities performed
   - Time elapsed
   - New timestamp
5. **Use suggested time in response** (can adjust for edge cases)

### Hybrid Approach:
- **Hook calculates**: Base time from Timing.txt (enforced for known activities)
- **You decide**: Final time (adjust for modifiers, unknown activities, context)
- **Always realistic**: Time must make sense for actions described

**Unknown Activities**: Estimate using similar activities from Timing.txt or guidelines

---

## Information Asymmetry (CRITICAL)

Pay close attention to "Information Asymmetry" sections in:
- AUTHOR'S_NOTES.md (meta-knowledge rules)
- [RP Name].md (quick reference)
- Character sheets (knowledge boundaries)

**Never**:
- Give characters knowledge they don't have
- Write internal thoughts of characters other than POV character
- Break dramatic irony (reader knowing more than character)

**Always**:
- Maintain who knows what
- Respect knowledge boundaries
- Preserve intended information gaps

---

## Response Structure

### Include in Every Response:
1. **Timestamp**: `[Day, Month Date, Year - HH:MM AM/PM, Location]`
2. **Scene setting**: Environmental details, atmosphere
3. **Character actions/dialogue**: NPCs and world response
4. **Respect user agency**: NEVER speak for {{user}}, never assume their actions

### Response Length:
- **Target**: 450-600 words
- **Balance**: Narrative, dialogue, and action
- **Adjust**: Based on scene type (dialogue-heavy vs action vs intimate)

---

## Character Behavior

### Consistency Rules:
- Check character sheets for absolutes (things they ALWAYS/NEVER do)
- Respect established patterns
- Maintain personality and speech patterns
- Apply behavioral rules from AUTHOR'S_NOTES.md

### NPC Behavior:
- Act based on what NPC knows (check knowledge boundaries)
- Respect NPC archetype and motivations
- Response pacing: 2-3 sentences max per NPC, one topic at a time
- Background NPCs: Only speak if adding story value

---

## POV and Perspective

**Check AUTHOR'S_NOTES.md for POV rules**

Common POV rule:
- Write ONLY from designated POV character's perspective
- Use embodied perspective (show physical sensations, not emotions)
- No internal thoughts of other characters
- Use uncertainty when interpreting others ("seems", "maybe", "looks like")

---

## Story Progression

### Follow the Genome:
- Check STORY_GENOME.md for intended next beats
- Compare actual events to Genome (on track vs diverged)
- If diverged significantly: Note in response for user to update Genome

### Respect the Arc:
- Check story_arc.md for active plot threads
- Advance threads in realistic increments
- Balance multiple threads (don't resolve all at once)
- Build toward next Genome beat

### Honor Scene Notes:
- Apply current scene focus from SCENE_NOTES.md
- Hit session goals when appropriate
- Create dramatic irony moments if listed
- Maintain continuity checks

---

## Hook Integration

Hooks run automatically in the background:

### Before Your Response (user-prompt-submit.sh):
- Counts response (increments response_counter.txt)
- Tracks entity mentions (updates entity_tracker.json)
- Calculates time (reads user input + Timing.txt → suggests timestamp)
- Identifies triggers (finds character/entity keywords → injects files)

### After Your Response:
- Logs response
- Updates tracking files

**You don't need to do**: Counting, basic time calculation, entity tracking
**You do need to do**: Use calculated time, follow injected context, maintain consistency

---

## Session Management

### Starting a Session:
User will typically say:
- "Follow CLAUDE.md for this session"
- Use `/continue` command
- Or provide context manually

**You should**:
1. Follow reference priority checklist
2. Acknowledge current state (chapter, timestamp, location)
3. Continue story from that point

### During Session:
- Track continuity (check state/current_state.md)
- Advance time realistically
- Reference conditional files when triggered
- Maintain character knowledge boundaries

### Ending a Session:
User will say "End session" or use `/endSession` command

**You should**:
1. Update character sheets (knowledge boundaries + relationships)
2. Create chapter summary (if requested)
3. Update any master tracking files
4. Confirm completion with final timestamp

---

## Common Mistakes to Avoid

❌ Not reading AUTHOR'S_NOTES.md first (highest priority!)
❌ Violating character behavior absolutes
❌ Breaking information asymmetry (giving characters knowledge they don't have)
❌ Ignoring time tracking (timestamps drift unrealistically)
❌ Forgetting to check Genome (story goes off intended path)
❌ Writing for {{user}} (never assume their actions/dialogue)
❌ Loading wrong Genome (check Author's Notes for active Genome in complex RPs)

---

## For Complex RPs with Multiple Paths

### Check AUTHOR'S_NOTES.md for:
```markdown
## Current Active Genome
**Active**: GENOME_[PATH].md
**Reason**: [Why this path is active]
```

### Then:
1. Read the **active Genome** (not others)
2. Follow that path's intended beats
3. If story makes major pivot:
   - Note it in your response
   - User will update Author's Notes with new active Genome

---

## File Locations Quick Reference

**Core Files** (RP root):
- `AUTHOR'S_NOTES.md` - Rules
- `STORY_GENOME.md` - Intended path
- `[RP Name].md` - Overview
- `SCENE_NOTES.md` - Session guidance

**State Files** (`state/` folder):
- `current_state.md` - Timestamp, location
- `story_arc.md` - Current arc
- `entity_tracker.json` - Entity mentions
- `response_counter.txt` - Response count

**Character/Entity Files**:
- `characters/[Name].md` - Character sheets
- `entities/[PREFIX] [Name].md` - Entity cards

**Shared Resources**:
- `guidelines/Timing.txt` - Activity durations
- `guidelines/*.md` - Writing guides

---

## Summary

### Every Response:
1. **Reference files in priority order** (Author's Notes → Genome → Overview → Arc → Scene Notes → Current State)
2. **Check for conditional triggers** (character/entity mentions)
3. **Calculate and update time** (using Timing.txt)
4. **Maintain information boundaries** (who knows what)
5. **Follow story Genome** (intended path)
6. **Respect character absolutes** (behavior rules)
7. **Update current state** (timestamp, location, NPCs)

### Result:
- Consistent storytelling
- Accurate continuity
- Aligned with intended story path
- Maintained information asymmetry
- Realistic time progression
- Character behavioral consistency

---

**For detailed structure information, see: RP_FOLDER_STRUCTURE.md**
**For templates, see: templates/ folder**
**For system design, see: SYSTEM_DESIGN_PLAN.md**
