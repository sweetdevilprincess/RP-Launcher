# Prompt Templates Guide

Complete reference for the genre-specific narrative templates system used to customize Claude's writing style for different story types.

---

## QUICK OVERVIEW

**What**: Genre-specific writing guidance templates (JSON files)
**Where**: `config/templates/prompts/`
**Who Uses**: `src/automation/prompt_templates.py` (PromptTemplateManager)
**How**: Injected into Claude's prompt as formatting guidance
**When**: Every response generation cycle

---

## AVAILABLE GENRES

The system includes **11 pre-built genre templates**:

1. **action.json** - High-energy action with clear stakes
2. **comedy.json** - Humor-focused narrative
3. **dark_romance.json** - Emotional depth with darker themes
4. **dark_romance_thriller.json** - Combination of dark romance + thriller
5. **grimdark.json** - Dark, gritty tone with moral ambiguity
6. **grimdark_horror.json** - Grimdark + horror elements
7. **horror.json** - Fear and tension
8. **mystery.json** - Investigation and intrigue
9. **slice_of_life.json** - Everyday moments with emotional authenticity
10. **slice_of_life_comedy.json** - Slice of life + comedic elements
11. **thriller.json** - Suspense and pacing

---

## TEMPLATE STRUCTURE

Each template is a **JSON file** with this structure:

```json
{
  "genre": "action",                    // Unique identifier (lowercase_underscore)
  "display_name": "Action",             // Human-readable name
  "sections": {                         // Named sections of guidance
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "High energy and kinetic momentum",
        "Clear stakes and immediate danger",
        "Adrenaline and intensity drive the narrative"
        // ... more bullet points
      ]
    },
    "pacing": {
      "title": "Pacing",
      "content": [
        "Fast-paced action sequences with clarity",
        // ...
      ]
    },
    "dialogue_style": {
      "title": "Dialogue Style",
      "content": [
        "Quick, efficient dialogue during action",
        // ...
      ]
    },
    "scene_construction": {
      "title": "Scene Construction",
      "content": [
        "Establish geography and stakes before action",
        // ...
      ]
    },
    "descriptive_focus": {
      "title": "Descriptive Focus",
      "content": [
        "Kinetic descriptions of movement and impact",
        // ...
      ]
    },
    "common_pitfalls": {
      "title": "Common Pitfalls to Avoid",
      "content": [
        "Don't sacrifice clarity for style in action scenes",
        // ...
      ]
    }
  },
  "highlights": [                       // Key takeaways
    "High energy with clear choreography",
    "Competence on display",
    "Physical consequences matter",
    "Escalating stakes and momentum"
  ]
}
```

### Section Purposes

- **tone_and_atmosphere** - Overall mood and feeling
- **pacing** - Story rhythm and timing
- **dialogue_style** - How characters speak
- **scene_construction** - How to structure scenes
- **descriptive_focus** - What to emphasize in descriptions
- **common_pitfalls** - What to avoid
- **highlights** - Quick summary points (used in layered mode)

---

## HOW IT WORKS

### The Flow

```
1. User's RP has a ROLEPLAY_OVERVIEW.md file
   ↓
2. PromptTemplateManager reads it during automation
   ↓
3. Extracts **Genre**: field (e.g., "Action / Thriller")
   ↓
4. Selects appropriate template(s) based on mode
   ↓
5. Converts JSON to markdown formatting
   ↓
6. Injects into Claude's prompt as guidance
   ↓
7. Claude follows the guidance while writing response
```

### Template Injection

The template is injected as a comment block in the prompt:

```markdown
<!-- ========== NARRATIVE TEMPLATE ========== -->
**Genre**: Action

**Tone & Atmosphere**:
- High energy and kinetic momentum
- Clear stakes and immediate danger
- Adrenaline and intensity drive the narrative

**Pacing**:
- Fast-paced action sequences with clarity
- Short, punchy sentences during intense moments

[... more sections ...]
```

Claude sees this and applies the guidance to its writing.

---

## CONFIGURATION MODES

### Mode 1: Auto (Default)

**How it works**:
1. Reads `ROLEPLAY_OVERVIEW.md`
2. Extracts `**Genre**: Primary / Secondary` field
3. Automatically selects template

**Configuration in automation_config.json**:
```json
{
  "narrative_template": {
    "mode": "auto"
  }
}
```

**Examples**:
- Genre: "Action" → Uses `action.json`
- Genre: "Dark Romance / Thriller" → Tries `dark_romance_thriller.json`, falls back to layered
- Genre: "Slice of Life / Comedy" → Tries `slice_of_life_comedy.json`, falls back to layered

### Mode 2: Composite

**How it works**:
- Directly specify which template to load
- For pre-made combinations

**Configuration**:
```json
{
  "narrative_template": {
    "mode": "composite",
    "template": "dark_romance_thriller"
  }
}
```

**Use when**:
- You want to lock a specific template
- Testing a genre combination
- Your genre doesn't auto-detect

### Mode 3: Modular

**How it works**:
- Mix sections from different genres
- Create custom blend of writing guidance

**Configuration**:
```json
{
  "narrative_template": {
    "mode": "modular",
    "sections": {
      "tone_and_atmosphere": "action",
      "dialogue_style": "comedy",
      "pacing": "thriller",
      "scene_construction": "action",
      "descriptive_focus": "dark_romance",
      "common_pitfalls": "action"
    }
  }
}
```

**Use when**:
- You want fine-grained control
- Combining elements from 3+ genres
- Creating a unique custom blend

### Mode 4: Layered

**How it works**:
- Primary template + secondary highlights
- Emphasizes key points from secondary genre

**Configuration**:
```json
{
  "narrative_template": {
    "mode": "layered",
    "primary": "dark_romance",
    "secondary": "thriller"
  }
}
```

**Results in**:
- Full dark_romance template as base
- Plus highlighted points from thriller

**Auto mode uses this as fallback** when secondary genre doesn't have dedicated template.

---

## WHERE THINGS GO

### File Locations

```
config/
└── templates/
    └── prompts/
        ├── action.json
        ├── comedy.json
        ├── dark_romance.json
        ├── dark_romance_thriller.json    ← Pre-made combination
        ├── grimdark.json
        ├── grimdark_horror.json          ← Pre-made combination
        ├── horror.json
        ├── mystery.json
        ├── slice_of_life.json
        ├── slice_of_life_comedy.json     ← Pre-made combination
        └── thriller.json
```

### Configuration Location

In each RP's `state/automation_config.json`:

```json
{
  "narrative_template": {
    "mode": "auto"    // or "composite", "modular", "layered"
    // ... other mode-specific config
  }
}
```

### How ROLEPLAY_OVERVIEW.md Is Read

**File**: `RPs/YourRP/ROLEPLAY_OVERVIEW.md`

The PromptTemplateManager searches for:
```markdown
**Genre**: Primary / Secondary
```

Examples:
- `**Genre**: Action` - Single genre
- `**Genre**: Dark Romance / Thriller` - Primary / Secondary
- `**Genre**: Slice of Life / Comedy` - Primary / Secondary

The system:
1. Extracts the genre field
2. Normalizes it (lowercase, spaces to underscores)
3. Looks for matching template files
4. Applies appropriate mode (auto tries composite, then layered)

---

## HOW TO USE

### For Your Current RP

1. **Create/Edit** `ROLEPLAY_OVERVIEW.md` in your RP folder
2. **Add** a `**Genre**:` line with your genre(s)
3. **Save** the file
4. **Next response** will use the template

### Example ROLEPLAY_OVERVIEW.md

```markdown
# My Story Overview

**Genre**: Dark Romance / Thriller

**Story Premise**:
A dark romance with suspenseful elements...

**Main Characters**:
- Character A: ...
- Character B: ...

**Setting**:
...
```

### To Change Templates

1. Edit `state/automation_config.json` in your RP
2. Change the `narrative_template` section
3. Restart the next session

---

## CREATING A NEW TEMPLATE

### Step 1: Understand the Structure

Review an existing template (e.g., `action.json`):
- All have same sections (tone, pacing, dialogue, scene, descriptive, pitfalls)
- Each section is a title + array of bullet points
- Highlights is a summary array

### Step 2: Create Your Template File

**File**: `config/templates/prompts/your_genre_name.json`

```json
{
  "genre": "your_genre_name",
  "display_name": "Your Genre Display Name",
  "sections": {
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "First guidance point",
        "Second guidance point",
        "Third guidance point"
      ]
    },
    "pacing": {
      "title": "Pacing",
      "content": [
        "Pacing guidance point 1",
        "Pacing guidance point 2"
      ]
    },
    "dialogue_style": {
      "title": "Dialogue Style",
      "content": [
        "Dialogue guidance"
      ]
    },
    "scene_construction": {
      "title": "Scene Construction",
      "content": [
        "Scene construction guidance"
      ]
    },
    "descriptive_focus": {
      "title": "Descriptive Focus",
      "content": [
        "Descriptive guidance"
      ]
    },
    "common_pitfalls": {
      "title": "Common Pitfalls to Avoid",
      "content": [
        "Pitfall 1",
        "Pitfall 2"
      ]
    }
  },
  "highlights": [
    "Key highlight 1",
    "Key highlight 2",
    "Key highlight 3"
  ]
}
```

### Step 3: Test It

1. Save the file
2. Edit a RP's `automation_config.json`:
```json
{
  "narrative_template": {
    "mode": "composite",
    "template": "your_genre_name"
  }
}
```
3. Generate a response
4. Check `state/hook.log` for load success/errors

### Step 4: Add to Documentation

- Add to list in this guide
- Document the genre purpose
- Add example usage

---

## CREATING A COMBINATION TEMPLATE

### For Pre-Made Genre Combinations

Some combinations are so common they get their own template:
- `dark_romance_thriller.json` (Dark Romance + Thriller)
- `grimdark_horror.json` (Grimdark + Horror)
- `slice_of_life_comedy.json` (Slice of Life + Comedy)

### When to Create One

- Used frequently in multiple RPs
- Needs custom balance of sections
- Two genres clash without specific tuning
- You want auto-mode to find it instantly

### How to Create

1. Copy one genre template as base
2. Blend sections from both genres
3. Balance the guidance for both tones
4. Name it `genre1_genre2.json` (or `genre2_genre1.json`)
5. Test with auto mode (it will find it)

**Example**: `dark_romance_thriller.json`
- Tone/Atmosphere: Balance darkness + romance
- Pacing: Thriller pacing with emotional beats
- Dialogue: Emotional but tense
- Scenes: Mix romance scenes + suspenseful scenes
- Descriptive: Dark + intimate details
- Pitfalls: Avoid melodrama, maintain tension

---

## DEBUGGING

### Template Not Loading

**Check log**: `state/hook.log`

```
[PromptTemplateManager] Error loading dark_romance: [error message]
```

**Common causes**:
1. JSON syntax error - Use JSON validator
2. File not found - Check spelling and location
3. Wrong path - Should be in `config/templates/prompts/`
4. Genre name mismatch - Name in file must match filename

### Auto-Mode Not Working

**Check**:
1. Does ROLEPLAY_OVERVIEW.md exist?
2. Does it have `**Genre**:` line?
3. Is genre name spelled correctly?
4. Check log for parsing messages

**Example genre line**:
```markdown
**Genre**: Dark Romance / Thriller
```

### Template Not Affecting Output

**Check**:
1. Is template being loaded? (Check log)
2. Is mode correct? (Check automation_config.json)
3. Is template valid JSON?
4. Does template have all 6 sections?

### Mode-Specific Issues

**Auto mode**: Check ROLEPLAY_OVERVIEW.md format
**Composite mode**: Check "template" field in config
**Modular mode**: Check all genres exist, all sections listed
**Layered mode**: Check "primary" and optional "secondary" fields

---

## BEST PRACTICES

### 1. Use Auto Mode by Default

- Simplest configuration
- Auto-detects from ROLEPLAY_OVERVIEW.md
- Auto tries smart fallbacks

### 2. Name Genres Consistently

Your RP's ROLEPLAY_OVERVIEW.md:
```markdown
**Genre**: Dark Romance / Thriller
```

Will automatically find:
- `dark_romance_thriller.json` (if exists)
- Falls back to layered: dark_romance + thriller highlights

### 3. Keep Guidance Concise

Each bullet point should be:
- One clear idea
- Action-oriented ("Use X", "Avoid Y")
- Specific to the genre
- 5-10 words typically

### 4. Balance Sections

All templates should have:
- ✅ 6 main sections
- ✅ 2-6 bullet points per section
- ✅ 3-4 highlights
- ✅ Clear, actionable guidance

### 5. Test New Templates

1. Create JSON file
2. Set to composite mode in config
3. Generate responses
4. Verify Claude is following guidance
5. Check log for load messages

---

## INTEGRATION WITH OTHER SYSTEMS

### Used By

**PromptTemplateManager** (`src/automation/prompt_templates.py`):
- Loads templates during automation
- Converts JSON to markdown
- Injects into prompt

**PromptBuilder** (`src/automation/helpers/prompt_builder.py`):
- Receives formatted template from manager
- Injects into prompt for Claude
- Passed through for every response

### Data Flow

```
ROLEPLAY_OVERVIEW.md
        ↓
PromptTemplateManager (reads genre)
        ↓
Selects template(s) based on mode
        ↓
Loads JSON from config/templates/prompts/
        ↓
Formats to markdown
        ↓
PromptBuilder receives it
        ↓
Injects into prompt sent to Claude
        ↓
Claude sees guidance comment block
        ↓
Claude applies to writing
```

---

## REFERENCE

### All 11 Built-In Templates

| Template | File | Primary Focus |
|----------|------|---|
| Action | action.json | High-energy with clear choreography |
| Comedy | comedy.json | Humor emerges from character/situation |
| Dark Romance | dark_romance.json | Emotional depth with darker themes |
| Dark Romance + Thriller | dark_romance_thriller.json | Blend of darkness, emotion, suspense |
| Grimdark | grimdark.json | Dark, gritty, morally ambiguous |
| Grimdark + Horror | grimdark_horror.json | Dark grit + fear and tension |
| Horror | horror.json | Fear, tension, unsettling atmosphere |
| Mystery | mystery.json | Investigation, intrigue, puzzle-solving |
| Slice of Life | slice_of_life.json | Everyday moments, authentic emotion |
| Slice of Life + Comedy | slice_of_life_comedy.json | Mundane life with humor |
| Thriller | thriller.json | Suspense, pacing, high stakes |

### Configuration Modes at a Glance

| Mode | Config | Use Case |
|------|--------|----------|
| auto | `{"mode": "auto"}` | Default, reads genre from ROLEPLAY_OVERVIEW.md |
| composite | `{"mode": "composite", "template": "name"}` | Lock specific template |
| modular | `{"mode": "modular", "sections": {...}}` | Mix sections from multiple genres |
| layered | `{"mode": "layered", "primary": "X", "secondary": "Y"}` | Primary + secondary highlights |

---

## SUMMARY

**What**: JSON files with genre-specific writing guidance
**Where**: `config/templates/prompts/`
**How**: PromptTemplateManager loads and injects into prompts
**Why**: Consistent genre-specific writing style for Claude
**Configure**: Via automation_config.json `narrative_template` section
**Auto-detect**: From `**Genre**:` line in ROLEPLAY_OVERVIEW.md
**Extend**: Create new JSON files following the template structure

---

**Last Updated**: 2025-10-16
**Part of**: Documentation Suite v1.0.1
