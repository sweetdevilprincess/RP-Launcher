Add a note to the RP system.

## Usage

**Quick Scene Note** (default):
- `/note [text]` - Adds to SCENE_NOTES.md "Temporary Reminders" section

**Formatted Document Notes** (with prefix):
- `/note @character [Name]: [note]` - Adds to character sheet
- `/note @plot: [note]` - Adds to story_arc.md active threads
- `/note @genome: [note]` - Adds to STORY_GENOME.md divergence log
- `/note @scene: [note]` - Adds to SCENE_NOTES.md (explicit)

## Examples

```
/note Remember: Marcus is out of town this week
→ Adds to SCENE_NOTES.md

/note @character Marcus: Now knows about the camera
→ Adds to Marcus.md knowledge section

/note @plot: Camera discovery imminent, building tension
→ Adds to story_arc.md active threads

/note @genome: Story diverged - Lilith refused to move in
→ Adds to STORY_GENOME.md divergence log
```

## Processing Logic

### 1. Parse Input

Check for prefix:
- `@character` - Character sheet update
- `@plot` - Plot/arc update
- `@genome` - Genome update
- `@scene` - Scene notes (explicit)
- No prefix - Scene notes (default)

### 2. Route to Appropriate Handler

#### A) Quick Scene Note (no prefix or @scene)

**Action**: Append to SCENE_NOTES.md

**Location**: Under "## Temporary Reminders" section

**Format**:
```markdown
## Temporary Reminders
- [Existing reminders]
- [NEW] [Note text] (Added: [date])
```

#### B) Character Note (@character [Name]: [note])

**Action**: Add to character sheet's notes or knowledge section

**Steps**:
1. Extract character name from input
2. Find `characters/[Name].md`
3. Determine where to add:
   - If note is about knowledge → Add to Knowledge Boundaries
   - If note is about behavior → Add to Behavioral Patterns
   - Otherwise → Add to Notes section
4. Append note with timestamp

**Format in character sheet**:
```markdown
## Notes
- [Existing notes]
- [Note text] (Added: [date])
```

#### C) Plot Note (@plot: [note])

**Action**: Add to story_arc.md

**Location**: Under "## Active Plot Threads" or create "## Notes" section

**Format**:
```markdown
## Active Plot Threads
- [Existing threads]
- [NEW] [Note text] (Added: [date])
```

#### D) Genome Note (@genome: [note])

**Action**: Add to STORY_GENOME.md divergence log

**Location**: Under "## Divergence Log" section (create if doesn't exist)

**Format**:
```markdown
## Divergence Log

### [Date] - [Brief Title from Note]
**Note**: [Note text]
**Impact**: [To be filled by user or leave blank]
```

### 3. Confirm Addition

**Output**:
```
✅ Note added to [target file]

Target: [filename]
Section: [section name]
Note: "[note text]"

The note has been saved and will be referenced in future sessions.
```

## Special Cases

### If Character Not Found (@character [Unknown]: [note])

```
❌ Character sheet not found: characters/[Name].md

Available character sheets:
- [List .md files in characters/]

Please check the character name or create the character sheet first.
```

### If File Doesn't Exist (target file missing)

**For SCENE_NOTES.md**:
- Create it with basic template
- Add note
- Confirm creation + note addition

**For other files**:
- Error message
- Suggest creating the file first

### If Note Is Too Long

- No limit, but suggest keeping under 200 words for quick notes
- For longer notes, suggest creating dedicated document

## Advanced: Multi-Note Format

**Allow multiple notes in one command**:
```
/note @scene: Build tension; @plot: Camera reveal coming; Marcus intervention planned
```

**Processing**:
- Split by semicolon
- Process each note separately
- Confirm all additions

## Output Examples

### Example 1: Quick Scene Note
```
Input: /note Gabriel still won't eat, Lilith is worried

✅ Note added to SCENE_NOTES.md

Section: Temporary Reminders
Note: "Gabriel still won't eat, Lilith is worried (Added: Nov 10, 2024)"
```

### Example 2: Character Note
```
Input: /note @character Silas: Starting to show more overt control, less hiding it

✅ Note added to characters/Silas.md

Section: Behavioral Patterns
Note: "Starting to show more overt control, less hiding it (Added: Nov 10, 2024)"
```

### Example 3: Plot Note
```
Input: /note @plot: Next chapter - Marcus confronts Lilith about moving in

✅ Note added to state/story_arc.md

Section: Active Plot Threads
Note: "Next chapter - Marcus confronts Lilith about moving in (Added: Nov 10, 2024)"
```

### Example 4: Genome Note
```
Input: /note @genome: Story diverged - Lilith discovered camera early, confrontation happening now instead of chapter 30

✅ Note added to STORY_GENOME.md

Section: Divergence Log
Entry: "Nov 10, 2024 - Camera Discovered Early"
Note: "Story diverged - Lilith discovered camera early, confrontation happening now instead of chapter 30"
```

---

**Note**: This command is for quick additions during or between sessions. For major updates, use `/endSession` for comprehensive updates.
