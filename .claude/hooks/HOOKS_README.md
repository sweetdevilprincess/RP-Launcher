# Hooks Documentation

## What Are Hooks?

Hooks are scripts that run automatically at specific points in your Claude Code workflow. They enable automation without requiring manual commands.

---

## Available Hooks

### `user-prompt-submit.sh`

**When it runs**: Before every user message is processed by Claude

**What it does**:
1. ✅ **Increments response counter** → Tracks total responses for arc generation trigger
2. ✅ **Calculates time from activities** → Reads user message, matches with Timing.txt, suggests time elapsed
3. ✅ **Tracks entity mentions** → Logs mentions in JSON, auto-generates cards at threshold
4. ✅ **Identifies conditional triggers** → Searches for character/entity keywords, injects matching files
5. ✅ **AUTO: Generates entity cards** → When entity hits 2+ mentions (configurable)
6. ✅ **AUTO: Generates story arcs** → Every 50 responses (configurable)

**Output**:
- Updates `state/response_counter.txt`
- Updates `state/current_state.md` with time suggestions
- Updates `state/entity_tracker.json` with mention counts
- Injects character/entity files when triggered
- **NEW**: Auto-creates entity cards in `entities/` folder
- **NEW**: Auto-generates story arc in `state/story_arc.md`

**Cost**:
- Hook execution: $0 (runs locally)
- Entity card generation: ~$0.001 each (DeepSeek)
- Story arc generation: $0 (uses Claude's main context)

---

## How Hooks Work

### Execution Flow

```
User types message
        ↓
Hook runs (user-prompt-submit.sh)
        ↓
    - Counts response
    - Calculates time
    - Tracks entities
    - Finds triggers
        ↓
Claude receives message + hook output
        ↓
Claude responds using hook suggestions
```

### What Claude Sees

Hooks output comments that Claude can read:

```html
<!-- TIME TRACKING SUGGESTION -->
<!-- Activities detected: eat (10 min), talk (10 min) -->
<!-- Total time: 20 minutes -->

<!-- TRIGGER MATCH: Loading characters/Marcus.md (matched: Marcus) -->
<!-- CONDITIONAL FILES TO REFERENCE: -->
Read: /path/to/characters/Marcus.md
```

Claude uses these suggestions to:
- Update timestamps accurately
- Reference the right character/entity files
- Track story progression

---

## Time Tracking Hook Details

### How It Works

1. **Reads user message**: "Lilith eats dinner and talks with Silas"

2. **Searches Timing.txt**:
   - Found: "eat" → 10 minutes
   - Found: "talk" → 10 minutes

3. **Calculates total**: 20 minutes

4. **Updates current_state.md**:
   ```markdown
   ## Time Calculation Suggestion (Latest)
   **Activities detected**: eat (10 min), talk (10 min)
   **Suggested time elapsed**: 20 minutes
   **Note**: Review and adjust for modifiers (fast/slow) or unknown activities
   ```

5. **Claude sees suggestion**: Uses it to update timestamp

### Supported Activities

All activities from `guidelines/Timing.txt`:
- eat, drink, cook, clean, bathe, wash, dress, sleep, nap, groom, brush
- chat, talk, argue, comfort, teach, scold, debate, joke, lecture, confess
- walk, run, jog, hike, ride, sail, row, climb, sneak, swim, fly
- study, work, write, read, paint, sculpt, invent, build, repair, sew
- And many more...

### Limitations

**Current implementation**:
- ✅ Detects single-word activities ("eat", "walk", "kiss")
- ❌ Doesn't understand compound phrases ("making out", "slow passionate kiss")
- ❌ Doesn't auto-apply modifiers (fast/slow)
- ❌ Doesn't handle simultaneous activities

**Claude handles**:
- Compound activities (e.g., "making out" = kiss + cuddle)
- Modifiers (fast = 0.75x, slow = 1.5x)
- Unknown activities (estimates using similar ones)
- Edge cases (interrupted activities, simultaneous actions)

**Result**: Hook provides baseline, Claude refines

---

## Conditional Reference Triggers

### How Triggers Work

1. **Character/Entity files have Triggers section**:
   ```markdown
   **Triggers**: Marcus, Marc, protective friend, coworker
   ```

2. **User mentions trigger word**: "Marcus walks in"

3. **Hook detects match**: Searches for "Marcus" in triggers

4. **Hook injects file**: Adds `characters/Marcus.md` to context

5. **Claude reads file**: Has character info for response

### Setting Up Triggers

**In character sheets** (`characters/[Name].md`):
```markdown
# Marcus

**Triggers**: Marcus, Marc, protective friend, coworker, work friend

[Rest of character sheet...]
```

**In entity cards** (`entities/[PREFIX] [Name].md`):
```markdown
# [LOC] Bruno's Restaurant

**Triggers**: Bruno's, restaurant, Italian restaurant, Bruno

[Rest of entity card...]
```

### Trigger Best Practices

✅ **DO**:
- Include full name and nicknames
- Include titles/roles (if character known by them)
- Include variations ("Michael" + "Mike" + "Mikey")
- Keep triggers lowercase (hook matches case-insensitive)

❌ **DON'T**:
- Use common words ("the", "a", "person")
- Use vague terms that match too often
- Duplicate triggers across files (causes multiple injections)

---

## Automatic Entity Card Generation 🆕

### How It Works

1. **Hook tracks entity mentions** in user messages:
   - Detects capitalized words (likely names)
   - Updates `state/entity_tracker.json` with mention counts

2. **When entity reaches threshold** (default: 2 mentions):
   - Hook searches recent chapters for context about entity
   - Calls `scripts/deepseek_call.sh` to generate card
   - Saves to `entities/[CHAR] EntityName.md`
   - Marks entity as "card_created" in tracker

3. **Card is auto-loaded on future mentions** via triggers

###Example Flow:
```
Response 15: User mentions "Marcus"
  → entity_tracker.json: {"Marcus": {"mentions": 1, ...}}

Response 23: User mentions "Marcus" again
  → entity_tracker.json: {"Marcus": {"mentions": 2, ...}}
  → THRESHOLD REACHED
  → Auto-generates: entities/[CHAR] Marcus.md
  → Card now loads automatically when "Marcus" is mentioned
```

### Configuration

Edit `state/automation_config.json`:
```json
{
  "auto_entity_cards": true,          // Enable/disable
  "entity_mention_threshold": 2,      // How many mentions trigger generation
  ...
}
```

**Cost**: ~$0.001 per entity card (DeepSeek)

---

## Automatic Story Arc Generation 🆕

### How It Works

1. **Hook increments counter** each response:
   - Response 1, 2, 3... 49, 50

2. **When counter hits threshold** (default: every 50):
   - Hook triggers automatic arc generation
   - Claude reads Story Genome + recent chapters + current state
   - Generates 11-beat future arc (AI Dungeon format)
   - Creates full arc summary
   - Saves to `state/story_arc.md`

3. **Arc updates automatically**: Every 50, 100, 150 responses, etc.

### Example Flow:
```
Response 50 reached
  → Hook triggers: "AUTO-GENERATING STORY ARC"
  → Claude reads: STORY_GENOME.md, recent chapters, current_state.md
  → Claude generates: 11-beat arc + full summary
  → Saves to: state/story_arc.md
  → Notification: "✅ Story arc auto-updated at response 50"
```

### Configuration

Edit `state/automation_config.json`:
```json
{
  ...
  "auto_story_arc": true,      // Enable/disable
  "arc_frequency": 50          // How often (in responses)
}
```

**Options**:
- `25`: Frequent updates (fast-paced RPs)
- `50`: Standard (most RPs)
- `100`: Infrequent (slow-burn RPs)

**Cost**: **FREE** (uses Claude's main context)

### Manual Generation Still Available

You can still manually trigger:
- Entity cards: `/gencard [type], [name]`
- Story arcs: `/arc`

Automation doesn't prevent manual use!

---

## Entity Tracking JSON

### Format

`state/entity_tracker.json` tracks all mentioned entities:

```json
{
  "entities": {
    "Marcus": {
      "mentions": 15,
      "first_chapter": 2,
      "last_chapter": 20,
      "card_created": true
    },
    "Cathedral": {
      "mentions": 3,
      "first_chapter": 18,
      "last_chapter": 20,
      "card_created": false
    }
  }
}
```

**Fields**:
- `mentions`: Total times entity mentioned
- `first_chapter`: Chapter first mentioned (estimated)
- `last_chapter`: Most recent chapter mentioned
- `card_created`: Whether auto-generation has run for this entity

**Auto-generation**: When `mentions >= threshold` and `card_created == false`, hook triggers card creation and sets `card_created = true`

---

## Troubleshooting

### Hook Not Running

**Check**:
1. Are you in RP directory? (must have `state/` folder)
2. Is hook executable? `chmod +x .claude/hooks/user-prompt-submit.sh`
3. Is Claude Code configured to run hooks?

### Time Calculation Incorrect

**Common issues**:
- Activity word not in Timing.txt → Add it
- Compound activity (e.g., "making out") → Hook can't detect, Claude handles
- Typo in activity → Fix in Timing.txt or message

**Remember**: Hook suggests, Claude decides final time

### Triggers Not Working

**Check**:
1. Does character/entity file have "Triggers:" section?
2. Is trigger keyword in user message?
3. Is trigger unique enough (not too common)?

**Debug**: Hook outputs comments like:
```
<!-- TRIGGER MATCH: Loading characters/Marcus.md (matched: Marcus) -->
```

### No Files Injected

**Possible reasons**:
- No triggers matched user message
- Character/entity files don't have Triggers section
- Triggers misspelled or don't match message

**Fix**: Add Triggers to files, ensure they match common usage

---

## Customization

### Modify Time Calculation

**Edit hook**: `.claude/hooks/user-prompt-submit.sh`

**Change detection logic**:
```bash
# Current: Simple word match
if echo "$message" | grep -qi "\b$activity\b"; then
    # Found activity
fi

# Enhanced: Could add phrase detection, modifiers, etc.
```

### Modify Trigger Detection

**Edit hook**: `.claude/hooks/user-prompt-submit.sh`

**Change trigger matching**:
```bash
# Current: Case-insensitive word match
if echo "$message" | grep -qi "\b$trigger\b"; then
    # Trigger matched
fi

# Enhanced: Could add fuzzy matching, context awareness, etc.
```

### Add New Hook Functions

**Add to existing hook** or **create new hook file**:

```bash
# New function in user-prompt-submit.sh
custom_function() {
    # Your logic here
}

# Call in main execution
custom_function "$USER_MESSAGE"
```

---

## Performance Impact

### Execution Time

**Typical hook run**: < 100ms
- Response counter: ~1ms
- Time calculation: ~10-50ms (depends on Timing.txt size)
- Entity tracking: ~10-20ms
- Trigger detection: ~20-50ms (depends on # of character/entity files)

**Impact on user**: Negligible (runs before Claude sees message)

### Cost Analysis

**FREE operations**:
- ✅ File reading/writing (local)
- ✅ Text parsing (local)
- ✅ Simple calculations (local)
- ✅ JSON updates (local)
- ✅ Story arc generation (uses Claude's main context)

**PAID operations** (automatic if enabled):
- Entity card generation: ~$0.001 per card (DeepSeek via OpenRouter)

**Typical session costs** (30 responses, 3 new entities):
- Entity cards: 3 × $0.001 = **$0.003**
- Story arc: Not reached yet = **$0.00**
- **Total**: **~$0.003 per session**

**At 50 responses** (5 new entities):
- Entity cards: 5 × $0.001 = **$0.005**
- Story arc: 1 × FREE = **$0.00**
- **Total**: **~$0.005 total**

**Very affordable for full automation!**

---

## Future Enhancements

### Potential Features

1. **Better compound activity detection**
   - "making out" → kiss + cuddle
   - "passionate encounter" → estimate based on context

2. **Modifier detection**
   - "quick shower" → bathe × 0.75
   - "slow dinner" → eat × 1.5

3. **Smarter entity tracking**
   - Distinguish between mentions and active presence
   - Track entity relationships
   - Detect entity type automatically (character vs location vs item)

4. **Event-based arc triggers**
   - Not just every 50, but also when major events occur
   - Detect divergence from Genome, suggest update

5. **Multi-path Genome support**
   - Detect when story might be switching paths
   - Suggest Genome update in Author's Notes

6. **Entity card refinement**
   - Auto-update cards when new info appears
   - Better context extraction from chapters
   - Support for manual type specification

---

## Summary

### What Hooks Do (Automatically)

✅ **Count responses** → Track progress, trigger arc at threshold
✅ **Calculate time** → Match activities to Timing.txt
✅ **Track entities** → Log mentions in JSON, auto-generate cards at threshold
✅ **Inject files** → Load character/entity files when triggered
✅ **Generate entity cards** 🆕 → Auto-create at 2+ mentions (configurable)
✅ **Generate story arcs** 🆕 → Auto-create every 50 responses (configurable)

### What Hooks DON'T Do

❌ Update Genome (manual edit required)
❌ Update character sheets (use `/endSession` or manual edit)
❌ Create chapter summaries (use `/endSession`)
❌ Modify automation config (manual edit of JSON file)

### Result

**Mostly automated system** that:
- Maintains accurate time tracking (free)
- Ensures relevant files are referenced (free)
- Auto-generates entity cards (~$0.001 each)
- Auto-generates story arcs (free)
- Minimizes manual work while keeping costs very low

**Typical Cost**: ~$0.003-0.005 per session
**Performance**: Negligible (~100-200ms per response)
**User control**: Can disable automation via config file
**Flexibility**: Manual commands still work alongside automation
