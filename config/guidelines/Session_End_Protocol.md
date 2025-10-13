# Session End Protocol - Enhanced for New System

## When to Use This

At the end of a roleplay session, the user will trigger this protocol by typing `/endSession` or saying "End session".

This will trigger the following tasks automatically.

---

## Task 1: Save Last RP Response

### Purpose:
Save the final roleplay story response for `/continue` command to reference next session.

### Action:
Look backwards through conversation history and find the last assistant message that contains a timestamp in this format:
```
[Day, Month Date, Year - HH:MM AM/PM, Location]
```

Example timestamp: `[Saturday, November 5th, 2024 - 7:20 PM, Bruno's Italian Restaurant]`

Save that entire message (the full RP response) to `state/last_response.txt`.

**Important**: This should be the RP story response, NOT the session end summary response.

---

## Task 2: Analyze Character Changes (Claude)

### Purpose:
Create a comprehensive summary of ALL character changes during this session for DeepSeek to apply.

### Action:
Analyze the entire session and create a detailed "Character Changes Summary" covering:

**For Each Character:**
1. **Living Situation/Physical Location**: Where they live, where possessions are
2. **Physical State/Condition**: Injuries, health, fatigue, appearance changes
3. **Emotional State**: Current emotions, mental state, stress levels
4. **Goals/Motivations**: What they want, what drives them (if shifted)
5. **Behavioral Patterns**: New patterns, changed behaviors, habits
6. **Knowledge Boundaries**:
   - New "Knows" (confirmed information gained)
   - New "Suspects" (things they're questioning)
   - Moved from "Suspects" to "Knows" (confirmed suspicions)
7. **Relationship Dynamics**: Changes with each other character
8. **Character Arc Progress**: Where they are in their development
9. **Possessions/Resources**: New items, lost items, gained/lost resources
10. **Any Other Changes**: Anything else that changed about the character

### Format:
Save to `state/character_updates_session_[X].txt`:

```markdown
# Character Updates - Session [X]
# Generated: [Date]

## [Character Name] ({{user}}/{{char}}/NPC)

### Living Situation
~~[Old situation]~~ → [New situation]
(Or: No change)

### Physical State/Condition
~~[Old state]~~ → [New state]
(Or: No change)

### Emotional State
~~[Old state]~~ → [New state]
(Or: No change)

### Goals/Motivations
~~[Old goal]~~ → [New goal]
(Or: No change)

### Behavioral Patterns
~~[Old pattern]~~ → [New pattern]
(Or: No change / New pattern: [description])

### Knowledge Boundaries - New Knows
- [New confirmed information]
- [New confirmed information]

### Knowledge Boundaries - New Suspects
- [New suspicion]
- [New suspicion]

### Knowledge Boundaries - Suspects → Knows
- ~~Suspected: [thing]~~ → Knows: [thing]

### Relationship Dynamics
**With [Character]**:
- ~~[Old dynamic]~~ → [New dynamic]
- Recent interaction: [summary]
- Trust/intimacy shift: [description]

### Character Arc Progress
- Current stage: [where in arc]
- Recent development: [what progressed]

### Possessions/Resources
- Gained: [items/resources]
- Lost: [items/resources]
- Moved: [items] from [location] to [location]

### Other Changes
- [Any other relevant changes]

---

[Repeat for each character that had changes]
```

**Example:**
```markdown
## Lilith ({{user}})

### Living Situation
~~Lives at her apartment (428 Oak Street)~~ → Lives with Silas at his apartment

### Physical State/Condition
No change (healthy, well-rested)

### Emotional State
~~Hopeful and excited about relationship~~ → Anxious but rationalizing, cognitive dissonance increasing, trying to convince herself everything is fine

### Goals/Motivations
No change (wants connection, wants to be loved, wants to believe in relationship)

### Behavioral Patterns
New pattern: Actively dismissing red flags to maintain relationship
New pattern: Rationalizing Silas's suspicious knowledge of her routine

### Knowledge Boundaries - New Knows
- Silas knows her routine in detail (noticed he knew when she'd be home)
- Gabriel is terrified of Silas and won't eat at his apartment
- Marcus is planning some kind of intervention

### Knowledge Boundaries - New Suspects
- Suspects Silas might have been watching her more than he admitted
- Suspects Marcus and Jenna coordinated their warnings

### Knowledge Boundaries - Suspects → Knows
- ~~Suspected: Silas following her occasionally~~ → Knows: Silas has been following her (he admitted it but minimized)

### Relationship Dynamics
**With Silas**:
- ~~Boyfriend, dating, separate living~~ → Boyfriend, living together, increased physical intimacy
- Recent interaction: Moved in together, he was possessive about arrangement of her things
- Trust shift: Slightly shaken by his knowledge of routine but dismissed it

**With Gabriel**:
- Recent interaction: Cat is terrified in new environment, won't eat
- Emotional impact: Worried about Gabriel but rationalizing it as "adjusting"

**With Marcus**:
- Recent interaction: He texted warning about moving in, she dismissed it
- Trust shift: Pulling away from his warnings, getting defensive

### Character Arc Progress
- Current stage: Deepening entanglement (point of no return crossed)
- Recent development: Moved in with Silas, harder to leave now

### Possessions/Resources
- Moved: All belongings from apartment to Silas's apartment
- Moved: Gabriel (cat) to Silas's apartment
- Lost: Independence/escape route (lease ended, can't easily leave)

### Other Changes
- Now sleeping in Silas's bed (shared bedroom)
- Has key to his apartment
```

---

## Task 3: Update Character Sheets (DeepSeek)

### Purpose:
Apply all character changes to the actual character sheet files using DeepSeek (cost-effective).

### Action:
For each character that had changes:

1. **Read** `state/character_updates_session_[X].txt` (the changes summary)
2. **Read** `characters/[CharacterName].md` (existing character sheet)
3. **Apply updates** with strikethrough formatting where things changed:
   - Use `~~old info~~` for replaced information
   - Add new information below
   - Preserve all other sections unchanged

4. **Update "Last Updated"** timestamp to current session/chapter

### Example Update:
```markdown
# Lilith

**Last Updated**: Chapter 23, November 6th, 2024

## Living Situation
~~Lives at apartment (428 Oak Street, Apt 3B)~~
**Currently**: Lives with Silas at his apartment (Downtown, 15th floor)

## Physical State
- Healthy, well-rested
- No injuries or conditions

## Emotional State
~~Hopeful and excited about relationship~~
**Currently**: Anxious but rationalizing, cognitive dissonance increasing, actively trying to convince herself everything is fine

[Continue through all sections...]

## Knowledge Boundaries

### Knows
- Silas has been following her (he admitted but minimized)
- Silas knows her routine in suspicious detail
- Gabriel is terrified of Silas
- Marcus is planning intervention
- [Previous knowledge...]

### Suspects
- Silas might have been watching her more than admitted
- Marcus and Jenna coordinated warnings
- [Previous suspects...]

### Doesn't Know
- Hidden camera in bedroom
- Full extent of surveillance (6 months)
- [Previous doesn't know...]
```

### DeepSeek Implementation:

**API Configuration**:
- Model: deepseek/deepseek-chat-v3.1
- API Key: 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
- Endpoint: https://openrouter.ai/api/v1/chat/completions

**Implementation Method**:
Use the reusable DeepSeek API script: `python -m work_in_progress.clients.deepseek`

```bash
# Build prompt with character updates and existing sheet
PROMPT="You are updating character sheets...
[Full prompt with character_updates and sheet content]"

# Call DeepSeek API and save updated sheet
UPDATED_SHEET=$(python -m work_in_progress.clients.deepseek "$PROMPT")
echo "$UPDATED_SHEET" > "characters/CharacterName.md"
```

**DeepSeek Prompt**:
```
You are updating character sheets based on session changes.

Read the character updates summary and the existing character sheet.

Apply ALL changes with this formatting:
- Use ~~strikethrough~~ for old information that changed
- Add new information below the strikethrough
- If something is completely new (not replacing), just add it
- If "No change" is noted, leave that section unchanged
- Update "Last Updated" timestamp

Preserve the exact structure and all unchanged sections.

Character Updates: [paste character_updates_session_X.txt]
Existing Sheet: [paste characters/CharacterName.md]

Output the fully updated character sheet.
```

---

## Task 4: Update State Files

### state/current_state.md
**Update:**

```markdown
**Last Updated**: [Current date and time]
**Current Chapter**: [Increment chapter number]
**Current Timestamp**: [Final timestamp from last RP response]
**Current Location**: [Final location from last RP response]

## Active NPCs Present
[List NPCs currently in scene or relevant]

## Active Plot Threads
[Copy from story_arc.md or list current threads]
```

### state/story_arc.md
**Update if significant developments:**

- Add recent key events to "Key Recent Events"
- Update "Active Plot Threads" with new developments
- Update "Character Developments" section
- Update "Relationship Dynamics" with shifts
- Update "Next Direction" based on where session ended

---

## Task 5: Generate Entity Trigger List

### Purpose:
Create a list of entities/characters relevant for next session.

### Action:
Create or update `state/session_triggers.txt`:

**Format:**
```
# Relevant Entities for Next Session
# Generated: [Date]

Characters:
- [Character name] (Triggers: [Triggers:trigger1,trigger2,trigger3'])
- [Character name] (Triggers: [Triggers:trigger1,trigger2'])

Locations:
- [Location name] (Triggers: [Triggers:trigger1,trigger2'])

Items:
- [Item name] (Triggers: [Triggers:trigger1'])

Context:
[Brief note about next session]
```

**Use AI Dungeon trigger format**: `[Triggers:word1,word2,word3']`

---

## Task 6: Update Memory System (If Using)

### If state/user_memory.md exists:

**Update {{user}}'s memory using DeepSeek:**

**API Configuration**:
- Model: deepseek/deepseek-chat-v3.1
- API Key: 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
- Endpoint: https://openrouter.ai/api/v1/chat/completions

**Implementation Method**:
Use the reusable DeepSeek API script: `python -m work_in_progress.clients.deepseek`

```bash
# Build prompt with current memory and recent events
PROMPT="Update character memory for {{user}}...
[Full prompt with memory state and session events]"

# Call DeepSeek API and save updated memory
UPDATED_MEMORY=$(python -m work_in_progress.clients.deepseek "$PROMPT")
echo "$UPDATED_MEMORY" > "state/user_memory.md"
```

**DeepSeek Prompt**:
```
Update character memory for {{user}} in this roleplay.

Current Memory State:
[paste state/user_memory.md]

Recent Events (from this session):
[paste session summary/recent events]

Instructions:
1. Move "Immediate Memory" content to "Recent Memory" (summarize, reduce detail)
2. Update "Immediate Memory" with new session events (detailed, vivid)
3. Check if any events qualify as "Significant Memories":
   - Major revelations or discoveries
   - Traumatic events
   - Life-changing moments
   - Important emotional beats
4. Update "Forgotten / Fuzzy" if character wouldn't remember something clearly:
   - Minor details from weeks/months ago
   - Things character was distracted during
   - Information overload moments
5. Compress "Past Memory" (older events)

IMPORTANT: Maintain character perspective - only what {{user}} would realistically remember.

Output the complete updated memory file in markdown format.
```

---

## Task 7: Create Chapter Summary

### File Naming:
`chapters/Chapter [X].txt`

### Summary Prompt:

```
Create a comprehensive chapter summary (~3,000 words) covering this session.

FOCUS ON:
- Dramatic moments and emotional beats
- Power dynamics and relationship shifts
- Information asymmetry
- Boundary violations or escalations
- Character decisions and motivations
- Environmental details and atmosphere
- Quotes that reveal character or advance plot
- Turning points and critical moments

WRITE IN:
- Past tense, third person
- Genre-appropriate tone
- Vivid, specific details
- Natural quote integration
- Dramatic irony where relevant

AVOID:
- Generic summaries
- Skipping important decisions
- Breaking information boundaries
- Vague time references
- Missing red flags or significant moments

Include:
1. Summary of Events (~3,000 words)
2. Relationship Tracking
3. Quote Preservation (8-12 quotes, verbatim)
4. Timeline Documentation (with timestamps)
5. Theme Tracking
6. World Details
```

### Structure:

```markdown
## Summary of Events: Chapter [X]

[~3,000 word narrative with integrated quotes]

### Relationship Tracking

**[Character]:**
- **[Character]**: [Status, developments]

[For all major characters]

## Quote Preservation

- [Character] (to [Character]): "[Quote]"

[8-12 significant quotes]

## Timeline Documentation

[Day, Month Date, Year]:
- [HH:MM AM/PM]: [Event with location]

[Chronological list]

## Theme Tracking

**Recurring Themes:**
- [Theme]: [How it appeared]

## World Details

**Locations:** [New locations]
**Objects/Technology:** [New items]
**Setting Details:** [Environmental details]
```

---

## Task 8: Update Master References (If Exist)

- **Locations_Master.md**: Add new locations
- **Themes_Master.md**: Add theme occurrences

---

## Output Format

### 1. Find and Save Last RP Response
Search for last message with timestamp → save to `state/last_response.txt`

### 2. Confirmation
```
Creating chapter summary and updating all tracking documents...
```

### 3. Execute Updates:
1. **Character Changes Summary (Claude)** → `state/character_updates_session_[X].txt`
2. **Character Sheets (DeepSeek)** → Apply changes to all `characters/*.md`
3. **State files** → current_state.md, story_arc.md, session_triggers.txt
4. **Memory (DeepSeek if exists)** → user_memory.md
5. **Chapter Summary** → chapters/Chapter [X].txt
6. **Master references** → if exist

### 4. Final Confirmation
```
✅ Last RP response saved to state/last_response.txt
✅ Character changes analyzed and saved to state/character_updates_session_[X].txt
✅ Character sheets updated (DeepSeek): [list characters]
✅ Chapter [X] summary created
✅ State files updated: current_state.md, story_arc.md, session_triggers.txt
✅ Memory updated (DeepSeek): user_memory.md (if exists)
✅ Master references updated (if exist)

Session ended at: [final timestamp and location]

Next session:
- Use /continue to load context and last response
- Relevant entities: [from session_triggers.txt]

Suggested starting point: [brief suggestion]
```

---

## Cost Optimization

**Claude (expensive - full context access)**:
- Analyze session
- Create character changes summary
- Create chapter summary
- Manage overall protocol

**DeepSeek (cheap - targeted tasks)**:
- Apply character sheet updates (reads summary + sheet)
- Update memory (reads summary + memory file)

**Result**: Comprehensive updates at minimal cost

---

## Integration

Works with:
- `/continue` - Loads last_response.txt, session_triggers.txt
- `/memory` - Uses updated memory
- Hook system - Uses entity_tracker.json
- Story Arc - Updated with developments
- Character sheets - Fully comprehensive updates

Everything ready for next session!

