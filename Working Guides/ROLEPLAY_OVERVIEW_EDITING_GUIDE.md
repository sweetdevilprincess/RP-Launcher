# Who Can Edit ROLEPLAY_OVERVIEW.md Guide

Complete reference for what systems, processes, and people can edit ROLEPLAY_OVERVIEW.md and when.

---

## QUICK ANSWER

**Who can edit ROLEPLAY_OVERVIEW.md:**
1. ✅ **You (User)** - Manually, anytime
2. ✅ **End Session Protocol** - Automatically updates certain sections
3. ✅ **Claude (Me)** - When instructed via `/endSession` command

**What gets automatically updated**: Character Progressions, Current State Snapshot, Plot Threads

**What doesn't auto-update**: Genre, Story Overview (you must update manually)

---

## MANUAL EDITING (User)

### When You Should Edit

**Anytime During Development**:
- Story direction changes
- Genre changes
- Character progression updates
- Plot thread updates
- Current state changes

### What You Can Edit

**All sections are editable**:
- ✅ Genre field
- ✅ Story Overview
- ✅ Character Progressions
- ✅ Current State Snapshot
- ✅ Plot Threads
- ✅ Relationships
- ✅ All other sections

### How to Edit

1. Open `RPs/YourRP/ROLEPLAY_OVERVIEW.md`
2. Edit any section
3. Save file
4. Next automation cycle uses updated values

**Example**: Changing genre

```markdown
Before:
**Genre**: Dark Romance

After:
**Genre**: Dark Romance / Thriller
```

Result: Next response will auto-detect and use `dark_romance_thriller.json` template.

---

## AUTOMATIC EDITING (End Session Protocol)

### When It Happens

When you type `/endSession` or say "End session", the **Session End Protocol** automatically executes.

### What It Updates Automatically

The End Session Protocol (see SESSION_INSTRUCTIONS.md and Session_End_Protocol.md) performs **8 tasks**:

#### Task 1: Save Last RP Response
- Saves last response to: `state/last_response.txt`
- ROLEPLAY_OVERVIEW: **Not updated**

#### Task 2: Analyze Character Changes
- Analyzes session for character changes
- Saves to: `state/character_updates_session_[X].txt`
- ROLEPLAY_OVERVIEW: **Not directly updated** (info for Task 3)

#### Task 3: Update Character Sheets
- Updates: `characters/[Name].md` files
- ROLEPLAY_OVERVIEW: **Not updated**

#### Task 4: Update State Files
**This is where ROLEPLAY_OVERVIEW sections could be affected**

Updates to **state/current_state.md**:
```markdown
**Last Updated**: [Current date and time]
**Current Chapter**: [Increment chapter number]
**Current Timestamp**: [Final timestamp from last RP response]
**Current Location**: [Final location from last RP response]
**Active NPCs Present**: [List of NPCs]
**Active Plot Threads**: [Current threads]
```

Updates to **state/story_arc.md**:
- Key Recent Events
- Active Plot Threads
- Character Developments
- Relationship Dynamics
- Next Direction

**IMPORTANT**: These are separate from ROLEPLAY_OVERVIEW.md, but contain similar info.

#### Task 5: Generate Entity Trigger List
- Creates/updates: `state/session_triggers.txt`
- ROLEPLAY_OVERVIEW: **Not updated**

#### Task 6: Update Memory (If Using)
- Updates: `state/user_memory.md`
- ROLEPLAY_OVERVIEW: **Not updated**

#### Task 7: Create Chapter Summary
- Creates: `chapters/Chapter [X].txt`
- ROLEPLAY_OVERVIEW: **Not updated**

#### Task 8: Update Master References
- Updates: `Locations_Master.md`, `Themes_Master.md`
- ROLEPLAY_OVERVIEW: **Not updated**

### So What Actually Updates ROLEPLAY_OVERVIEW?

**Currently: Nothing automatically updates ROLEPLAY_OVERVIEW.md during End Session Protocol.**

The protocol updates *related* files like:
- `state/current_state.md`
- `state/story_arc.md`
- `state/character_updates_session_[X].txt`
- `characters/*.md` (character sheets)
- `chapters/Chapter [X].txt` (chapter summaries)

But the ROLEPLAY_OVERVIEW itself is **manually maintained**.

---

## MANUAL VS AUTOMATIC - WHICH FILES

### ROLEPLAY_OVERVIEW.md (Manual)
**You edit directly**:
- Genre (if changing)
- Story Overview (narrative, premise, themes)
- Character Progressions (you add significant developments)
- Current State Snapshot (you update as story progresses)
- Plot Threads (you add/update)
- Relationships (you update key shifts)

**Updated automatically**: None (currently)

**Where**: `RPs/YourRP/ROLEPLAY_OVERVIEW.md`

### State Files (Automatic)
**System updates automatically after /endSession**:
- `state/current_state.md` - Timestamp, location, active characters
- `state/story_arc.md` - Recent events, developments, next direction
- `state/character_updates_session_[X].txt` - Change summary
- `characters/*.md` - Full character sheets with all changes
- `chapters/Chapter [X].txt` - Comprehensive session summary

**Where**: `state/` directory

### Character Sheets (Automatic)
**DeepSeek updates automatically after /endSession**:
- `characters/[Name].md` - All character info with changes applied

**Where**: `characters/` directory

---

## WORKFLOW EXAMPLE

### Session Flow

**1. Start Session**
```
You: "Follow config/CLAUDE.md for this session"
Me: [Reads ROLEPLAY_OVERVIEW.md for genre and context]
Me: [Reads character sheets]
Me: [Generates first response]
```

**2. During Session**
```
You: [Lilith's actions and dialogue]
Me: [Response as world/NPCs]
[Back and forth multiple times]
```

**3. End Session**
```
You: "End session"
System: [Executes Session End Protocol - Tasks 1-8]
System: [Updates state files, character sheets, etc.]
Me: [Confirms all updates]
```

**4. After Session**

**What's Updated**:
- ✅ state/current_state.md (auto)
- ✅ state/story_arc.md (auto)
- ✅ characters/Lilith.md (auto, DeepSeek)
- ✅ characters/Silas.md (auto, DeepSeek)
- ✅ chapters/Chapter_23.txt (auto)

**What's NOT Updated**:
- ❌ ROLEPLAY_OVERVIEW.md (you do this manually if needed)

### Between Sessions

**Before Next Session, You Might**:
1. Update ROLEPLAY_OVERVIEW.md Character Progressions with latest developments
2. Update ROLEPLAY_OVERVIEW.md Current State Snapshot with new chapter number
3. Update ROLEPLAY_OVERVIEW.md Active Plot Threads if major changes
4. Update Genre if story direction shifted

**Then Say**: "Follow config/CLAUDE.md for this session"

---

## WHEN TO UPDATE ROLEPLAY_OVERVIEW

### Update After End Session
When you want to prepare ROLEPLAY_OVERVIEW for next session:

- [ ] Character Progressions: Add latest Arc entries
- [ ] Current State Snapshot: Update chapter number, timestamp, location
- [ ] Active Plot Threads: Add newly discovered threads
- [ ] Recent Major Events: Update last 3 events

**Example Update**:

```markdown
## Current State Snapshot

**Current Chapter**: ~~22~~ 23
**Current Timestamp**: Sunday, November 6th, 2024 - 11:30 PM, Silas's Apartment
**Active Characters**: Lilith, Silas

**Recent Major Events** (Last 3):
1. ~~Lilith discovered Silas following her~~ Lilith moved in with Silas
2. ~~Silas reframed stalking~~ Gabriel shows extreme terror of Silas
3. ~~Decision made: moving in~~ Marcus plans intervention, Jenna has safety system
```

### Update When Genre Changes

```markdown
**Genre**: ~~Dark Romance~~ Dark Romance / Thriller
```

### Update During Development (Not After Session)

- Adding new character progressions mid-story
- Discovering new plot threads
- Major relationship shifts

---

## HOW STATE FILES DIFFER

### state/current_state.md (Automatically Updated)

Contains **current snapshot** automatically updated by End Session Protocol:
- Last Updated timestamp
- Current Chapter (incremented)
- Current Timestamp (from last response)
- Current Location (from last response)
- Active NPCs
- Active Plot Threads

**Used by**: Automation system for context

**Updated**: After each /endSession

### state/story_arc.md (Automatically Updated)

Contains **arc context** with:
- Current Arc Name & Status
- Key Recent Events (updated with session events)
- Active Plot Threads (updated with new threads)
- Character Developments (updated with changes)
- Relationship Dynamics (updated with shifts)
- Next Direction (updated with clues from session)

**Used by**: Automation and reference

**Updated**: After each /endSession (if significant developments)

### ROLEPLAY_OVERVIEW.md (Manually Updated)

Contains **quick reference** that you maintain:
- Genre (rarely changes)
- Story Overview (narrative arc)
- Character Progressions (major milestones)
- Current State Snapshot (general info)
- Plot Threads (overview)
- Relationships (overview)

**Used by**:
- You (quick reference)
- PromptTemplateManager (Genre field only)

**Updated**: Manually by you

---

## BEST PRACTICES

### 1. Use state/ Files for Current Info

Don't edit ROLEPLAY_OVERVIEW for every small change.
Use `state/current_state.md` and `state/story_arc.md` for detailed tracking.

### 2. Use ROLEPLAY_OVERVIEW for Big Picture

Update ROLEPLAY_OVERVIEW when:
- Major arc milestones reached
- Character progression fundamentally changes
- Genre shifts
- Before next session (to summarize)

### 3. Genre Field is Auto-Used

The **only field actively used by automation**:
```markdown
**Genre**: Your Genre
```

Keep it accurate - it auto-detects templates.

### 4. Manual Maintenance Schedule

**After Each Session**:
- State files auto-update (do nothing)
- Character sheets auto-update (do nothing)
- Chapter summary auto-created (do nothing)

**Before Next Session** (optional but recommended):
- Update ROLEPLAY_OVERVIEW Character Progressions with latest arcs
- Update Current State Snapshot with new chapter number
- Verify Genre field is correct
- Update Active Plot Threads if needed

### 5. Don't Duplicate Information

ROLEPLAY_OVERVIEW is **overview/reference**, not detailed tracking.

For detailed tracking, use:
- `state/story_arc.md` - Full arc details
- `state/current_state.md` - Current detailed state
- `characters/*.md` - Full character sheets
- `chapters/Chapter_[X].txt` - Complete session summaries

---

## EDITING CHECKLIST

### When You Edit ROLEPLAY_OVERVIEW.md

- [ ] Genre field is correct (if changing)
- [ ] Story Overview reflects current direction
- [ ] Character Progressions include latest milestones
- [ ] Current State Snapshot is up to date
- [ ] Active Plot Threads are current
- [ ] No duplicate info with state/story_arc.md

### Before Saying "Follow config/CLAUDE.md"

- [ ] ROLEPLAY_OVERVIEW.md Genre is set correctly
- [ ] state/story_arc.md has latest context
- [ ] state/current_state.md has correct chapter/timestamp
- [ ] Character sheets are updated

---

## SUMMARY

**ROLEPLAY_OVERVIEW.md**:
- ✅ You edit manually anytime
- ✅ Only Genre field is auto-used
- ❌ NOT auto-updated by End Session Protocol
- 💡 Use for quick reference and overview

**state/ Files**:
- ✅ Auto-updated after /endSession
- ✅ Used for detailed tracking
- ✅ More current than ROLEPLAY_OVERVIEW
- 💡 Source of truth for current state

**Character Sheets** (characters/*.md):
- ✅ Auto-updated after /endSession
- ✅ DeepSeek applies all changes
- ✅ Include knowledge, relationships, everything
- 💡 Most complete character records

---

**Last Updated**: 2025-10-16
**Part of**: Documentation Suite v1.0.1
**Related Files**: SESSION_INSTRUCTIONS.md, Session_End_Protocol.md, ROLEPLAY_OVERVIEW_GUIDE.md
