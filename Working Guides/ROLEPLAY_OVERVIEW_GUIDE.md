# ROLEPLAY_OVERVIEW.md Guide

Complete reference for the ROLEPLAY_OVERVIEW.md file - what it is, what reads from it, and how to format it.

---

## QUICK ANSWER

**Format Required**: Markdown file with `**Genre**: Field`

**What Reads From It**: Primarily `PromptTemplateManager` (for auto-detecting narrative templates)

**Currently Used**: The `**Genre**:` field (other sections are reference/context)

---

## OVERVIEW

### What is ROLEPLAY_OVERVIEW.md?

A **comprehensive quick-reference file** for your RP that contains:
- Story overview and metadata
- Character progressions
- Current state snapshot
- Active plot threads
- Key relationships
- Session preparation checklist
- Important reminders

### File Location

**In Each RP**: Project root directory
```
RPs/YourRP/ROLEPLAY_OVERVIEW.md
```

### Purpose

- Quick reference before each session
- Central hub for story context
- Auto-detection of narrative templates
- Session preparation checklist
- Information asymmetry tracking

---

## WHAT READS FROM ROLEPLAY_OVERVIEW.md

### Currently Active

#### 1. PromptTemplateManager
**What It Reads**: `**Genre**:` field only

**How It Works**:
1. Searches for line: `**Genre**: [value]`
2. Extracts the genre(s)
3. Auto-detects narrative template
4. Injects template into Claude's prompt

**Required Format**:
```markdown
**Genre**: Primary / Secondary
```

**Examples**:
- `**Genre**: Dark Romance / Thriller`
- `**Genre**: Action`
- `**Genre**: Slice of Life / Comedy`
- `**Genre**: Grimdark / Horror`

**Case Handling**:
- "Dark Romance" → `dark_romance` (lowercase, spaces to underscores)
- "Slice of Life" → `slice_of_life`
- Any casing works (auto-normalized)

### Future/Potential Uses

The template includes other sections that could be read by:
- Status display systems
- Character tracking
- Plot thread management systems
- Session preparation automation

But currently, **only the Genre field is actively used**.

---

## REQUIRED FORMAT

### Minimal Working Format

```markdown
# Your RP Name

**Genre**: Primary Genre
```

That's all that's technically required for the template system to work.

### Full Recommended Format

```markdown
# Your RP Name

**READ THIS FILE EVERY RESPONSE - Core Overview & Quick Reference**

---

## Story Overview

**Genre**: Primary Genre / Secondary Genre
**Setting**: Time period, location, world type
**Tone**: Overall tone/atmosphere

**Premise**:
[1-2 sentence story premise]

**Themes**:
- [Core theme]
- [Secondary theme]

---

## Character Progressions (Quick Reference)

### [Character Name]
**Started as**: [Initial state]
**Arc**: [Key events] → [Current state]
**Current status**: [Where they are now]
**Key traits**: [Defining characteristics]

---

## Current State Snapshot

**Current Chapter**: [Number]
**Current Timestamp**: [Day, Date, Time, Location]
**Active Characters**: [Who's present]

**Recent Major Events** (Last 3):
1. [Event]
2. [Event]
3. [Event]

**Immediate Context**:
[What's happening right now]

---

## Active Plot Threads

1. **[Thread]**: [Status and next development]
2. **[Thread]**: [Status and next development]

---

## Session Preparation Checklist

- [ ] Read AUTHOR'S_NOTES.md
- [ ] Read STORY_GENOME.md
- [ ] Read state/story_arc.md
- [ ] Read SCENE_NOTES.md
- [ ] Check state/current_state.md
```

---

## GENRE FIELD - DETAILED

### The Critical Field

```markdown
**Genre**: Primary / Secondary
```

This is the **only field currently used** by the automation system.

### Supported Genres

All 11 built-in templates:
- `action`
- `comedy`
- `dark_romance`
- `grimdark`
- `horror`
- `mystery`
- `slice_of_life`
- `thriller`

### Combination Genres

Pre-made combinations:
- `dark_romance_thriller` → auto-loads `dark_romance_thriller.json`
- `grimdark_horror` → auto-loads `grimdark_horror.json`
- `slice_of_life_comedy` → auto-loads `slice_of_life_comedy.json`

### Format Variations

All of these work:

```markdown
**Genre**: Dark Romance
**Genre**: Dark Romance / Thriller
**Genre**: Thriller / Dark Romance
**Genre**: DARK ROMANCE
**Genre**: dark romance / thriller
**Genre**: Dark-Romance / Thriller
```

All normalize to the same genre names.

### How Auto-Detection Works

1. **System reads**: `**Genre**: Dark Romance / Thriller`

2. **Normalizes**:
   - Lowercase: `dark romance / thriller`
   - Replace spaces: `dark_romance / thriller`
   - Split on `/`: `["dark_romance", "thriller"]`

3. **Tries in order**:
   - Look for `dark_romance_thriller.json` ✓ (found!)
   - Load that template

4. **If no combo found**:
   - Load primary: `dark_romance.json`
   - Add secondary highlights: `thriller` points
   - Use "layered" mode (primary + secondary)

### What Happens If Genre Missing

If no `**Genre**:` line found:
```
[PromptTemplateManager] No **Genre**: field found in ROLEPLAY_OVERVIEW.md
[PromptTemplateManager] Auto mode: No genre found in ROLEPLAY_OVERVIEW.md
```

Result: No template injected (Claude writes without genre guidance)

### What Happens If Genre Unknown

If you use an unsupported genre:
```
**Genre**: Cyberpunk Noir
```

Results:
- Normalizes to: `cyberpunk_noir`
- Searches for: `cyberpunk_noir.json` (not found)
- Falls back to: No template
- Claude writes without guidance

---

## SECTION BREAKDOWN

### Story Overview

```markdown
**Genre**: [Primary / Secondary or just Primary]
**Setting**: [Time period, location, world type]
**Tone**: [Overall tone/atmosphere]

**Premise**:
[1-2 sentence story premise]

**Themes**:
- [Core theme]
- [Secondary theme]
- [Tertiary theme]
```

**Purpose**: Context for Claude when reading this file manually or for reference

**Currently Read By**: Human reference only (not automated)

### Character Progressions

```markdown
### [Character Name]
**Started as**: [Initial state/situation]
**Arc**: [Key events in order] → [Current state]
**Current status**: [Where they are now]
**Key traits**: [Defining characteristics]
```

**Purpose**: Quick reference of character development

**Currently Read By**: Human reference only

**Example**:
```markdown
### Lilith
**Started as**: Barista, unknowingly stalked for 6 months
**Arc**: Approached Silas → became girlfriend → discovered stalking → rationalized → moving in together
**Current status**: Moving in with Silas in 2 weeks, increasing cognitive dissonance
**Key traits**: Rationalizes red flags, dismisses warnings, craves connection
```

### Current State Snapshot

```markdown
**Current Chapter**: [Number]
**Current Timestamp**: [Day, Date, Time, Location]
**Active Characters**: [Who's present in current scene]

**Recent Major Events** (Last 3):
1. [Recent event]
2. [Recent event]
3. [Recent event]

**Immediate Context**:
[What's happening right now / what just happened]
```

**Purpose**: Quick reference of where story currently is

**Currently Read By**: Human reference only

### Information Asymmetry (Optional but Important)

```markdown
**What [Character A] Knows** (that [Character B] doesn't):
- [Key knowledge item]

**What [Character B] Knows** (that [Character A] doesn't):
- [Key knowledge item]

**What Reader Knows** (that no character knows):
- [Dramatic irony item]
```

**Purpose**: Tracking what each character knows (important for roleplay)

**Currently Read By**: Human reference only

### Active Plot Threads

```markdown
1. **[Thread name]**: [Current status and next likely development]
2. **[Thread name]**: [Current status and next likely development]
3. **[Thread name]**: [Current status and next likely development]
```

**Purpose**: Track what plot threads are active

**Currently Read By**: Human reference only (though background agents track in `state/plot_threads_master.md`)

### Key Relationships

```markdown
### [Character A] ←→ [Character B]
**Dynamic**: [Current relationship state]
**Tension**: [Active conflict or friction]
**Recent shift**: [How it's changing]
```

**Purpose**: Track relationship dynamics and changes

**Currently Read By**: Human reference only

### Session Preparation Checklist

```markdown
- [ ] Read AUTHOR'S_NOTES.md
- [ ] Read STORY_GENOME.md
- [ ] Read state/story_arc.md
- [ ] Read SCENE_NOTES.md
```

**Purpose**: Pre-session preparation checklist

**Currently Read By**: Human reference only

### Important File Locations

```markdown
**Character Sheets**: `/characters/[Name].md`
**Entity Cards**: `/entities/[PREFIX] [Name].md`
**Chapters**: `/chapters/Chapter [X].txt`
**State Tracking**: `/state/`
```

**Purpose**: Quick reference of where files are

**Currently Read By**: Human reference only

### Notes & Reminders

```markdown
### Story-Specific Reminders
- [Unique reminder]
- [Unique reminder]

### Common Pitfalls to Avoid
- [Mistake to watch for]
- [Mistake to watch for]
```

**Purpose**: Important notes and pitfalls to remember

**Currently Read By**: Human reference only

---

## HOW TO USE

### Creating a New RP

1. **Copy the template**:
   ```
   config/templates/TEMPLATE_ROLEPLAY_OVERVIEW.md
   ```

2. **To your RP root**:
   ```
   RPs/YourRP/ROLEPLAY_OVERVIEW.md
   ```

3. **Fill in the Genre field**:
   ```markdown
   **Genre**: Your Genre
   ```

4. **Fill in other sections** as you develop the story

### Updating During Development

**Genre changes**:
```markdown
**Genre**: Dark Romance → **Genre**: Dark Romance / Thriller
```
Next response will auto-detect the new template.

**Character updates**:
Update the Character Progressions section with latest developments.

**Plot updates**:
Update Active Plot Threads section as threads develop.

### For Template Detection

```markdown
**Genre**: Dark Romance / Thriller
```

Next automation cycle:
- PromptTemplateManager reads this
- Auto-selects `dark_romance_thriller.json` template
- Injects into Claude's prompt
- Claude follows the genre guidance

---

## INTEGRATION EXAMPLES

### Example 1: Simple Genre

```markdown
# My Action Adventure

**Genre**: Action

## Story Overview
**Setting**: Modern day, urban city
**Tone**: High-energy with clear stakes
**Premise**: Undercover agent on a dangerous mission

[... rest of sections ...]
```

**Result**: Injects `action.json` template into prompt

### Example 2: Combination Genre

```markdown
# Dark Psychological Story

**Genre**: Dark Romance / Thriller

## Story Overview
**Setting**: Contemporary, isolated location
**Tone**: Suspenseful with psychological elements
**Premise**: Two characters caught in a dangerous game

[... rest of sections ...]
```

**Result**: Injects `dark_romance_thriller.json` template (if exists), or layered fallback

### Example 3: Slice of Life Comedy

```markdown
# Everyday Stories

**Genre**: Slice of Life / Comedy

## Story Overview
**Setting**: Modern day neighborhood
**Tone**: Humorous with heartfelt moments
**Premise**: Friends navigating daily life mishaps

[... rest of sections ...]
```

**Result**: Injects `slice_of_life_comedy.json` template (if exists), or layered fallback

---

## TROUBLESHOOTING

### Template Not Loading

**Check**:
1. Does Genre field exist? `**Genre**: ...`
2. Is spelling correct?
3. Check log: `state/hook.log`

**Log messages**:
```
[PromptTemplateManager] Auto-selected: action
[PromptTemplateManager] Loaded composite template: dark_romance_thriller
[PromptTemplateManager] No genre found in ROLEPLAY_OVERVIEW.md
[PromptTemplateManager] Could not load template for unknown_genre
```

### Genre Not Recognized

```markdown
**Genre**: SCI-FI WESTERN
```

Result: `sci_fi_western` template not found → no template

**Fix**: Use supported genres or create custom template (see PROMPT_TEMPLATES_GUIDE.md)

### File Not Found

No `ROLEPLAY_OVERVIEW.md` in RP root

Result: Warning in log, no template

**Fix**: Create file in RP root with at least:
```markdown
# RP Name
**Genre**: Some Genre
```

---

## CURRENT USAGE SUMMARY

**Location**: `RPs/[YourRP]/ROLEPLAY_OVERVIEW.md`

**Critical Field**: `**Genre**: Primary / Secondary`

**What Reads It**:
- ✅ PromptTemplateManager (reads **Genre** field only)
- ⚠️ Human reference (all other sections)

**Auto-Detection**: Yes, via PromptTemplateManager
- Normalizes genre names
- Looks for matching template file
- Uses layered fallback if combo not found
- No template if genre not found

**Manual Configuration**: Via `state/automation_config.json`
- Can override auto mode
- Can specify composite/modular/layered modes

---

## BEST PRACTICES

### 1. Always Include Genre Field

Even if minimal:
```markdown
**Genre**: Your Genre
```

### 2. Use Supported Genres

For auto-detection to work:
- Use one of 11 built-in genres
- Or combinations (primary / secondary)
- Or create custom template

### 3. Keep It Updated

Update as story evolves:
- Genre changes → Update field
- Characters develop → Update progressions
- Plot advances → Update threads

### 4. Use as Quick Reference

ROLEPLAY_OVERVIEW is your quick reference before each session:
1. What's the genre? (Genre field)
2. Where is the story? (Current State Snapshot)
3. What characters are active? (Active Characters)
4. What's coming next? (Active Plot Threads)

### 5. Combine With Other Files

ROLEPLAY_OVERVIEW works with:
- AUTHOR'S_NOTES.md - Absolute rules
- STORY_GENOME.md - Story blueprint
- state/story_arc.md - Current arc
- state/current_state.md - Detailed state
- SCENE_NOTES.md - Session notes

---

## SUMMARY

**What**: Markdown file with RP overview and quick reference

**Format**: Any markdown structure, but `**Genre**:` field is critical

**Critical Field**: `**Genre**: Primary / Secondary` (or just Primary)

**What Reads It**:
- PromptTemplateManager reads **Genre** field for auto-template detection
- Everything else is human reference

**How It Works**:
1. You add `**Genre**: Dark Romance / Thriller`
2. Next automation cycle, PromptTemplateManager reads it
3. Auto-detects matching template from config/templates/prompts/
4. Injects template into Claude's prompt as guidance
5. Claude follows the genre guidance

**Minimal Setup**:
```markdown
# Your RP
**Genre**: Your Genre
```

**Full Setup**: See TEMPLATE_ROLEPLAY_OVERVIEW.md in config/templates/

---

**Last Updated**: 2025-10-16
**Part of**: Documentation Suite v1.0.1
