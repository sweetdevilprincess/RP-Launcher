# Slash Commands Documentation

Complete guide to all available slash commands for the RP system.

---

## Quick Reference

| Command | Purpose | Cost |
|---------|---------|------|
| `/status` | System status report | Free |
| `/continue` | Start new session | Free |
| `/endSession` | End session protocol | Mixed* |
| `/arc` | Generate story arc | Free |
| `/gencard [type], [name]` | Create entity card | ~$0.001 |
| `/note [text]` | Add quick note | Free |
| `/memory` | Update memory | ~$0.0005 |
| `/updateGenome` | Regenerate story genome | Free |

\*Mixed = Claude analysis (expensive) + DeepSeek updates (cheap)

---

## `/status` - System Status Report

**Purpose**: Displays comprehensive RP system status and progress

**Usage**:
```
/status
```

**What it shows**:
1. **Current State**: Chapter, timestamp, location, plot threads
2. **Progress**: Total responses, countdown to next arc generation
3. **Entity Tracking**: Tracked entities, mention counts, card status
4. **Automation**: Current configuration (on/off, thresholds)
5. **Recent Activity**: Last events from hook log
6. **Available Files**: Count of characters, entities, chapters
7. **Memory Status**: Whether memory tracking is active

**Example Output**:
```
# 🎭 RP System Status

**Generated**: Nov 11, 2024 10:30 AM

---

## 📍 Current State

**Chapter**: 23
**Timestamp**: Sunday, November 6th, 2024 - 11:30 PM
**Location**: Silas's Apartment

**Active Plot Threads**:
- Lilith moved in with Silas
- Gabriel terrified, refusing to eat
- Marcus planning intervention

---

## 📊 Progress

**Total Responses**: 217
**Next Arc Generation**: 33 responses away

---

## 🎭 Entities

**Tracked**: 8 entities
**Cards Created**: 5 cards

**Entities with 2+ mentions**:
- Silas: 45 mentions ✅ Card Created
- Gabriel: 12 mentions ✅ Card Created
- Marcus: 8 mentions ✅ Card Created
- Apartment: 3 mentions ✅ Card Created
- Camera: 2 mentions ⏳ Pending

---

## ⚙️ Automation

✅ **Entity Card Generation**: ON (Threshold: 2 mentions)
✅ **Story Arc Generation**: ON (Every 50 responses)

---

## 🔍 Recent Activity

- Auto-generated entity card: Camera
- Trigger match: Loading Silas.md
- Time tracking: conversation (15 min)
- Entity mentioned: Gabriel (12 mentions)

---

## 📁 Available Files

**Characters**: 3 files
- Lilith
- Silas
- Marcus

**Entity Cards**: 5 files
**Chapter Summaries**: 22 files

**Memory**: ✅ Active (Last updated: Nov 10, 2024)

---

**Tip**: Keep `CURRENT_STATUS.md` open in a second pane for live updates!
```

**When to use**:
- Check system state at any time
- Verify automation is working
- See entity tracking progress
- Troubleshoot issues
- Understand current configuration

**Cost**: Free (just reads and displays files)

**Note**: For lighter status info, keep `CURRENT_STATUS.md` open in a second pane - it auto-updates every response!

---

## `/continue` - Start Session

**Purpose**: Loads context and last RP response to continue story seamlessly

**Usage**:
```
/continue
```

**What it does**:
1. Loads "Follow config/CLAUDE.md for this session"
2. Displays current context:
   - Current chapter
   - Current timestamp
   - Current location
   - Active plot threads
   - Relevant entities (from last session)
3. **Displays full last RP response** (the story response you ended on)
4. Ready for you to respond and continue

**Example Output**:
```
Follow config/CLAUDE.md for this session.

## Session Context:

**Current Chapter**: 23
**Current Timestamp**: Sunday, November 6th, 2024 - 11:30 PM
**Current Location**: Silas's Apartment

**Active Plot Threads**: [from story_arc.md]
- Lilith moved in with Silas
- Gabriel terrified, refusing to eat
- Marcus planning intervention

**Relevant Entities This Session**: [from session_triggers.txt]
- Silas (Triggers: Silas,boyfriend,him')
- Gabriel (Triggers: Gabriel,cat,the cat')
- Apartment (Triggers: apartment,his place,Silas's apartment')

---

## Last Response (Continue from here):

[FULL last RP story response displayed here]

---

**Continue the story from where the last response ended.**
```

**When to use**: At the start of every new session

**Cost**: Free (just loads and displays files)

---

## `/endSession` - End Session Protocol

**Purpose**: Comprehensive session end - updates everything, creates summary

**Usage**:
```
/endSession
```

**What it does** (follows Session_End_Protocol.md):

### Phase 1: Save & Analyze (Claude)
1. **Find & save last RP response** → state/last_response.txt
2. **Analyze ALL character changes** → state/character_updates_session_[X].txt
   - Living situations, physical states, emotional states
   - Goals, behavioral patterns, knowledge boundaries
   - Relationships, arc progress, possessions
   - Everything that changed (with strikethrough format)

### Phase 2: Apply Updates (DeepSeek - Cheap)
3. **Update character sheets** using DeepSeek
   - Reads character_updates summary
   - Applies changes with ~~strikethrough~~ format
   - Updates all relevant sections

4. **Update memory** (if exists) using DeepSeek
   - Moves immediate → recent
   - Adds new immediate memories
   - Compresses past memories

### Phase 3: State & Summary (Claude)
5. **Update state files**:
   - current_state.md (chapter, timestamp, location, plot threads)
   - story_arc.md (recent developments)
   - session_triggers.txt (relevant entities for next session)

6. **Create chapter summary** (~3,000 words)
   - Summary of Events
   - Relationship Tracking
   - Quote Preservation
   - Timeline Documentation
   - Theme Tracking
   - World Details

7. **Update master references** (if exist)
   - Locations_Master.md
   - Themes_Master.md

### Final Output:
```
✅ Last RP response saved to state/last_response.txt
✅ Character changes analyzed and saved
✅ Character sheets updated (DeepSeek): Lilith, Silas, Marcus, Gabriel
✅ Chapter 23 summary created
✅ State files updated
✅ Memory updated (DeepSeek)
✅ Master references updated

Session ended at: Sunday, November 6th, 2024 - 11:30 PM, Silas's Apartment

Next session:
- Use /continue to load context and last response
- Relevant entities: Silas, Gabriel, apartment

Suggested starting point: Morning after moving in
```

**When to use**: At the end of every session

**Cost**:
- Claude analysis & summary: ~5,000-10,000 tokens (moderate cost)
- DeepSeek updates: ~3,000-5,000 tokens (~$0.0007 total - very cheap)
- **Total per session**: ~$0.02-0.05 (depending on session length)

---

## `/arc` - Generate Story Arc

**Purpose**: Create updated story arc outline (11 future beats + full arc summary)

**Automation**: ✅ **Auto-runs every 50 responses** (configurable in `state/automation_config.json`)

**Manual Usage**:
```
/arc
```
Use this to manually generate arc on-demand (anytime, not just at 50-response intervals)

**What it does**:
1. Reads STORY_GENOME.md (intended path)
2. Reads last 2-3 chapter summaries
3. Reads current_state.md and story_arc.md
4. Compares actual events to Genome
5. **Generates 11 future story beats** (AI Dungeon format - under 7 words each)
6. Creates full arc summary with:
   - Where we are in Genome (on track vs diverged)
   - Future beats list
   - Recent key events
   - Active plot threads
   - Character developments
   - Relationship dynamics
   - Themes
   - Next direction
7. Saves to state/story_arc.md

**Example Output**:
```
**Current Story Arc**

**Arc Title**: The Trap Tightens
**Current Phase**: Rising Action

**Where We Are in Genome**:
- Genome Beat: "Point of No Return - Living Together"
- Status: On track
- Notes: Following intended dark romance escalation

**Future Story Arc (Next 11 Major Beats)**:
1. Gabriel refuses apartment, worries Lilith
2. Silas controls her belongings arrangement
3. Marcus confronts Lilith about concerns
4. Lilith discovers surveillance evidence
5. Silas gaslights, minimizes discovery
6. Physical intimacy increases, boundaries erode
7. Camera footage reveal (to reader)
8. Friends attempt intervention
9. Lilith trapped, lease ended
10. Breaking point confrontation
11. [Climax - resolution depends on choices]

[Full arc summary continues...]
```

**When to use manually**:
- After major story events (don't want to wait for 50-response threshold)
- When you feel story direction unclear
- To regenerate arc if automatic one needs adjustment
- Any time you want an updated arc, regardless of response count

**Automatic behavior**:
- Runs automatically every 50 responses (or custom frequency)
- Can be disabled in `state/automation_config.json`
- No user action needed when auto-enabled

**Cost**: Free (uses Claude's main context)

---

## `/gencard [type], [name]` - Generate Entity Card

**Purpose**: Auto-generate entity card from story context

**Automation**: ✅ **Auto-creates cards when entities reach 2 mentions** (configurable in `state/automation_config.json`)

**Manual Usage**:
```
/gencard character, Marcus
/gencard location, Cathedral, gothic architecture
/gencard item, Hidden Camera
/gencard event, First Kiss
```
Use this to manually create cards for:
- Entities with only 1 mention (below auto-threshold)
- Specific entity types (location/item/event instead of default character)
- Re-generating cards with additional context

**Parameters**:
- **type**: character, location, item, or event
- **name**: Entity name
- **extra info**: (Optional) Additional context

**What it does**:
1. Searches recent chapters for entity mentions
2. Extracts all context about the entity
3. **Uses DeepSeek** to generate detailed card
4. Includes AI Dungeon-style triggers: `[Triggers:word1,word2,word3']`
5. Saves to `entities/[PREFIX] [Name].md`
   - [CHAR] for characters
   - [LOC] for locations
   - [ITEM] for items
   - [EVENT] for events

**Example Output**:
```
✅ Entity card created: entities/[CHAR] Marcus.md

Card Details:
- Type: character
- Name: Marcus
- Triggers: [Triggers:Marcus,Marc,coworker,protective friend']
- First Mentioned: Chapter 2

The card will be automatically loaded when triggers are mentioned in future responses.
```

**When to use manually**:
- Entity mentioned only once (won't auto-generate yet)
- Need to specify entity type (location/item/event instead of default character)
- Want to add extra context beyond what's in chapters
- Need to regenerate/refine an auto-generated card

**Automatic behavior**:
- Creates cards automatically when entities reach 2 mentions (configurable)
- Auto-generated cards are always type "character" (manual command for other types)
- Can be disabled in `state/automation_config.json`
- Marks entities as "card_created" to avoid duplicates

**Cost**: ~$0.001 per card (DeepSeek generation)

**Configuration**:
- Uses OpenRouter API
- Model: deepseek/deepseek-chat-v3.1
- API Key: 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

---

## `/note [text]` - Add Quick Note

**Purpose**: Add notes to various RP files quickly

**Usage**:

### Quick Scene Note (default):
```
/note Remember: Marcus is out of town this week
→ Adds to SCENE_NOTES.md
```

### Formatted Notes (with prefix):
```
/note @character Marcus: Now knows about the camera
→ Adds to Marcus.md

/note @plot: Camera discovery imminent
→ Adds to story_arc.md

/note @genome: Story diverged - early camera discovery
→ Adds to STORY_GENOME.md divergence log

/note @scene: Build tension this session
→ Explicitly adds to SCENE_NOTES.md
```

**Prefixes**:
- `@character [Name]: [note]` - Character sheet update
- `@plot: [note]` - Plot/arc update
- `@genome: [note]` - Genome divergence note
- `@scene: [note]` - Scene notes (explicit)
- No prefix - Scene notes (default)

**Example Output**:
```
✅ Note added to SCENE_NOTES.md

Section: Temporary Reminders
Note: "Remember: Marcus is out of town this week (Added: Nov 10, 2024)"
```

**When to use**:
- Quick reminders during session
- Document plot ideas
- Note character discoveries
- Track story divergences

**Cost**: Free (just appends text to files)

---

## `/memory` - Update Character Memory

**Purpose**: Track what {{user}} character realistically remembers

**Usage**:
```
/memory
→ Updates memory based on recent events

/memory update
→ Same as above (explicit)
```

**What it does**:
1. Checks if state/user_memory.md exists (creates if not)
2. Gathers recent events (last chapter/session)
3. **Uses DeepSeek** to update memory:
   - Moves immediate → recent memory (summarized)
   - Updates immediate with new events (detailed)
   - Adds to significant memories (if applicable)
   - Updates forgotten/fuzzy section
   - Compresses past memories
4. Saves updated memory

**Memory Structure**:
- **Immediate Memory**: Last session (vivid, detailed)
- **Recent Memory**: Last 2-3 chapters (clear but summarized)
- **Past Memory**: Older chapters (faded, key points only)
- **Significant Memories**: Major events (never fade)
- **Forgotten/Fuzzy**: Things character wouldn't remember clearly

**Example Output**:
```
✅ Memory updated for Lilith

Updated sections:
- Immediate Memory: 5 new events added
- Recent Memory: 3 events moved from immediate
- Significant Memories: 1 new (Camera Discovery)
- Forgotten/Fuzzy: 2 items added (minor details from weeks ago)
- Past Memory: Compressed older events

Last Updated: Nov 10, 2024, Chapter 23
```

**When to use**:
- Automatically called by `/endSession`
- Manually if you want to update memory mid-session
- To check what character remembers

**Cost**: ~$0.0005 per update (DeepSeek - very cheap)

**Purpose**: Prevents character from acting on player meta-knowledge

---

## Command Workflow Examples

### Starting a New Session:
```
1. You: /continue
2. Claude: [Displays context + last RP response]
3. You: [Respond to the story]
4. Claude: [Continues RP]
[Session continues...]
```

### Ending a Session:
```
1. [RP response with timestamp] ← This gets saved
2. You: /endSession
3. Claude: [Executes full protocol, creates summary]
4. You: Session complete!

Next session:
5. You: /continue
6. Claude: [Loads that saved RP response]
```

### Creating Entity Cards Mid-Session:
```
During RP, Marcus mentioned 3 times:
You: /gencard character, Marcus
Claude: ✅ Entity card created

Now when you mention "Marcus" in future:
Hook: Detects trigger → Auto-loads Marcus.md
```

### Adding Quick Notes:
```
You: /note @plot: Next chapter - Marcus confronts Lilith
Claude: ✅ Added to story_arc.md

You: /note Gabriel still won't eat
Claude: ✅ Added to SCENE_NOTES.md
```

### Generating Story Arc:
```
After ~50 responses or major event:
You: /arc
Claude: [Analyzes Genome + recent chapters]
Claude: [Generates 11 future beats + full arc]
Claude: ✅ Saved to story_arc.md
```

---

## Cost Summary

| Feature | Cost | Frequency | Auto/Manual |
|---------|------|-----------|-------------|
| `/continue` | Free | Every session start | Manual |
| `/endSession` | ~$0.02-0.05 | Every session end | Manual |
| `/arc` | Free | Every 50 responses | **AUTO** (or manual) |
| `/gencard` | ~$0.001 each | 2+ mentions | **AUTO** (or manual) |
| `/note` | Free | As needed | Manual |
| `/memory` | ~$0.0005 | Auto with /endSession | AUTO |

**With automation enabled** (typical 30-response session with 3 new entities):
- Entity cards: 3 × $0.001 = **$0.003**
- Story arc: (not reached) = **$0.00**
- `/endSession`: ~**$0.02-0.05**
- **Session total**: **~$0.023-0.053**

**Very affordable for full automation!**

---

## Tips & Best Practices

### Session Management:
- Always start with `/continue`
- Always end with `/endSession`
- This creates clean session boundaries

### Entity Cards:
- **Automatic**: Cards auto-generate at 2+ mentions (if enabled)
- **Manual**: Use `/gencard` for entities below threshold or specific types (location/item/event)
- Good triggers make auto-loading work better
- Use AI Dungeon format: `[Triggers:word1,word2,word3']`
- Check `state/entity_tracker.json` to see mention counts

### Notes:
- Use `/note` for quick ideas during session
- Use prefixes (`@character`, `@plot`) for organized notes
- Clear SCENE_NOTES.md between sessions (or let /endSession handle it)

### Memory:
- Let `/endSession` handle updates automatically
- Check memory if character seems to know too much
- Use memory to prevent meta-knowledge issues

### Story Arc:
- **Automatic**: Arc auto-generates every 50 responses (if enabled)
- **Manual**: Use `/arc` after major events or when you want immediate update
- Compare to Genome (are we on track?)
- Update Genome if story diverged significantly

### Automation Configuration:
- **File**: `state/automation_config.json`
- **Toggle features**: Set `auto_entity_cards` or `auto_story_arc` to `true`/`false`
- **Adjust thresholds**: Change `entity_mention_threshold` (default: 2) or `arc_frequency` (default: 50)
- **No restart needed**: Changes apply on next response
- **See**: `templates/AUTOMATION_CONFIG_README.md` for full documentation

---

## Troubleshooting

### `/continue` shows old response:
- Check state/last_response.txt - is it correct?
- May need to manually update if /endSession didn't save correctly

### `/endSession` taking long time:
- Normal - analyzes full session, creates summary
- DeepSeek updates are fast, Claude analysis takes time

### `/gencard` can't find entity:
- Entity might not have enough mentions in recent chapters
- Provide extra info: `/gencard character, Name, brief description`

### `/note` not finding character:
- Check spelling of character name
- Make sure character sheet exists in characters/

### `/memory` not updating:
- Check if state/user_memory.md exists
- DeepSeek API might have failed - check console

### Auto-generation not working:
- **Entity cards not creating**: Check if `jq` is installed (required for JSON), verify `auto_entity_cards: true` in config, check console for DeepSeek errors
- **Story arc not generating**: Verify you've reached threshold (default: 50 responses), check `auto_story_arc: true` in config
- **Wrong threshold**: Edit `state/automation_config.json` to adjust `entity_mention_threshold` or `arc_frequency`

### Want to disable automation:
- Edit `state/automation_config.json`
- Set `auto_entity_cards: false` and/or `auto_story_arc: false`
- Manual commands still work normally

---

## `/updateGenome` - Regenerate Story Genome

**Purpose**: Create updated STORY_GENOME.md when story has diverged from original plan

**Usage**:
```
/updateGenome
```

**When to use**:
- Story has taken unexpected turns due to character choices
- Major plot divergence from original intended path
- Want to realign future planning with actual story trajectory
- Need to document the new intended direction after organic story evolution

**What it does**:
1. **Backs up original**: Saves current STORY_GENOME.md to `STORY_GENOME_backup_[date].md`
2. **Analyzes actual story**: Reviews last 3-5 chapter summaries, current arc, character sheets
3. **Compares intended vs. actual**: Documents what diverged and why
4. **Generates new genome**: Creates updated genome reflecting actual story direction
5. **Preserves what works**: Keeps relevant original beats, updates the rest
6. **Documents changes**: Notes major divergences for future reference

**Philosophy**:
Stories evolve. Characters make unexpected choices. That's good writing. The genome should reflect reality and guide from there, not force compliance with an outdated plan.

**Example scenario**:
```
Original Plan: Lilith realizes Silas is dangerous → leaves him → rebuilds life
Actual Story: Lilith rationalizes red flags → moves in → gets more entangled

Result: Original genome beats no longer match reality. Need new genome that
        reflects actual trajectory (deepening entanglement) and plans realistic
        future beats from THIS position, not the abandoned position.
```

**Output format**:
- Original genome backed up safely
- New genome reflects actual story state
- Divergence summary explains what changed and why
- Realistic future beats from current position
- Updated story_arc.md aligned with new genome

**Cost**: FREE (uses Claude analysis, no DeepSeek calls)

**Notes**:
- Original genome is NEVER deleted, only backed up
- Can run multiple times as story continues to evolve
- New genome should be realistic, not aspirational
- Honors organic character choices that led to divergence

---

## Command Files Location

All command files are in: `.claude/commands/`

- `continue.md`
- `endSession.md`
- `arc.md`
- `gencard.md`
- `note.md`
- `memory.md`
- `status.md`
- `updateGenome.md`

To modify a command, edit its .md file.

---

## Integration with System

**Commands work with**:
- **Hooks**: Auto-load triggered entities
- **Session_End_Protocol.md**: /endSession follows this
- **config/CLAUDE.md**: /continue loads main instructions
- **State files**: All commands read/write state/
- **DeepSeek**: /gencard, /memory, /endSession use DeepSeek for cost savings

**Result**: Seamless RP experience with automated tracking and minimal cost

---

**For detailed protocol information, see**: `guidelines/Session_End_Protocol.md`
**For hook information, see**: `.claude/hooks/HOOKS_README.md`
**For folder structure, see**: `RP_FOLDER_STRUCTURE.md`
