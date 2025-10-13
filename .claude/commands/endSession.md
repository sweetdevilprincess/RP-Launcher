**AUTOMATED SESSION END PROTOCOL**

Execute all tasks automatically using Claude analysis + DeepSeek automation.

---

## Task 1: Extract Session Data (Compact Format)
**Purpose**: Extract RP exchanges in compact structured format for DeepSeek processing

**Process**:
1. Review conversation history for all RP exchanges this session
2. Extract in compact JSON-like format:
   ```json
   {
     "chapter": X,
     "date_range": "Nov 5, 2024",
     "locations": ["Restaurant", "Apartment"],
     "exchanges": [
       {
         "ts": "7:20 PM, Restaurant",
         "u": "Agreed to move in, felt nervous but excited",
         "c": "Leaned forward intense, took her hand possessively",
         "key": ["major decision", "possessive behavior"],
         "quote_u": "I want this. I want us.",
         "quote_c": "You won't regret this. I'll take such good care of you."
       },
       {
         "ts": "7:45 PM, Restaurant",
         "u": "Phone buzzed Marcus, hesitated then ignored it",
         "c": "Noticed hesitation, squeezed hand tighter, asked if everything okay",
         "key": ["dismissed warning", "increased control"]
       },
       {
         "ts": "8:30 PM, Apartment",
         "u": "Noticed Gabriel terrified cowering corner",
         "c": "Dismissed concern, said cat just needs time adjust",
         "key": ["red flag ignored", "gaslighting"],
         "quote_u": "Gabriel seems really scared...",
         "quote_c": "Cats are like that in new places. He'll be fine."
       }
     ],
     "key_developments": [
       "User agreed to move in (point of no return)",
       "Dismissed Marcus warning",
       "Gabriel showing fear (canary in coal mine)",
       "Silas showing possessive/dismissive patterns"
     ]
   }
   ```

**Note**: Only include `quote_u`/`quote_c` when dialogue is significant - not every exchange needs quotes
3. Focus on: actions, decisions, emotions, key dialogue (not full prose)
4. **IMPORTANT - Quotes**: Include direct quotes VERBATIM for:
   - Significant character-revealing dialogue
   - Emotional moments
   - Decision-making dialogue
   - Red flags or warnings
   - Turning points
   - Use `quote_u` and `quote_c` fields - copy exact words from RP
5. Keep action/dialogue summaries brief (5-10 words per exchange)
6. **Do NOT paraphrase quotes** - copy them exactly as spoken

---

## Task 2: Generate Chapter Summary (DeepSeek)
**Purpose**: Create detailed summary for future reference

**Process**:
1. Use the compact session data from Task 1
2. Read STORY_GENOME.md for context (brief excerpt only)
3. Call DeepSeek using: `python -m work_in_progress.clients.deepseek "[prompt]"`

**DeepSeek Prompt** (Optimized):
```
Generate comprehensive chapter summary (2,500-3,000 words) from structured session data.

**Session Data** (JSON):
[paste compact JSON from Task 1]

**Story Context** (brief):
Genre: [genre]
Themes: [main themes]
Current Arc: [current arc point]

**Task**:
Expand the compact session data into a rich narrative summary following this structure:

# Chapter [X] Summary - [Title]

**Date Range**: [from session_data]
**Locations**: [from session_data]
**Word Count**: ~2,500-3,000 words

## Summary of Events

[Expand exchanges into flowing narrative prose. Each exchange in the data should become 2-3 paragraphs. Include:]
- Expand "u" and "c" summaries into vivid prose
- Integrate provided quotes naturally
- Add atmospheric details and emotional subtext
- Show character thoughts and reactions
- Build tension and pacing

## Character Developments

### {{user}}:
[Deduce from key developments and exchange patterns]
- Emotional trajectory
- Key realizations
- Relationship shifts
- Internal conflicts

### [Character]:
[Deduce from exchange patterns]
- Mask status/tactics
- Escalation points
- Emotional state

## Relationship Tracking

[Analyze dynamic shifts from exchanges]

## Quote Preservation

**IMPORTANT**: Use ALL provided `quote_u` and `quote_c` from the exchange data VERBATIM
- List every quote that was captured in the exchanges array
- Format: `- Character (to Character): "Quote text"`
- Then infer 4-6 additional significant quotes from the exchange summaries
- Preserve exact wording for all quotes

## Timeline Documentation

[Expand from ts data with events]

## Theme Tracking

[Deduce themes from key developments and patterns]

**Output**: Full markdown chapter summary matching Chapter 2 format.
```

4. Save DeepSeek output to `chapters/Chapter_X.txt`
5. Also save raw compact data to `sessions/Chapter_X-data.json` (for reference)

---

## Task 3: Analyze Character Changes (Claude)
**Purpose**: Extract character changes in compact format

**Process**:
1. Review the compact session data from Task 1
2. For EACH character involved, extract changes in JSON format:

```json
{
  "character": "{{user}}",
  "changes": {
    "living": {"old": "428 Oak St apt", "new": "Silas's apartment 15th floor"},
    "physical": null,
    "emotional": {"old": "hopeful excited", "new": "anxious rationalizing cognitive dissonance"},
    "goals": null,
    "knowledge_new": ["Silas knows routine detail", "Gabriel terrified", "Marcus planning intervention"],
    "knowledge_suspects": ["Silas watching more than admitted", "Marcus Jenna coordinated"],
    "knowledge_confirmed": [],
    "relationships": {
      "Silas": {"was": "dating separate living", "now": "living together", "trust": "shaken but dismissed"},
      "Marcus": {"was": "close friend", "now": "pulling away", "dynamic": "defensive against warnings"}
    },
    "arc": {"stage": "Deepening entanglement", "progress": "Point of no return crossed"},
    "possessions_gained": [],
    "possessions_lost": ["Independence escape route"],
    "possessions_moved": ["All belongings", "Gabriel cat"],
    "other": ["Now sleeping in Silas's bed", "Has key to apartment"]
  }
}
```

3. Create one JSON object per character with changes
4. Save to `state/character_updates_session_[X].json` (compact format)
5. Use null for "No change" to save tokens

---

## Task 4: Update Character Sheets (DeepSeek)
**Purpose**: Apply all character changes to actual sheets

**Process**:
For each character with changes:

1. Read `state/character_updates_session_[X].json` (compact format)
2. Read `characters/[Character].md`
3. Call DeepSeek with optimized prompt:

**DeepSeek Prompt** (Optimized):
```
Apply character changes to sheet using structured data.

**Changes** (JSON):
[paste JSON from character_updates file]

**Current Sheet**:
[paste characters/CharacterName.md - full sheet needed]

**Task**:
Apply all changes from JSON to the character sheet:
- For changes with "old"/"new": Use ~~old~~ → new format
- For null values: No change needed, skip
- For arrays (knowledge_new, etc.): Add items to appropriate sections
- For relationships: Update relationship entries with "was"/"now" notes
- Update "Last Updated" timestamp to current session/chapter
- Preserve ALL unchanged sections exactly
- Maintain exact markdown structure

**Output**: Complete updated character sheet in markdown.
```

4. Save DeepSeek output back to `characters/[Character].md`

---

## Task 5: Final Memory Update (DeepSeek)
**Purpose**: Consolidate and organize all session memories

**Process**:
1. Read current `state/user_memory.md`
2. Extract key events from compact session data (Task 1)
3. Call DeepSeek with optimized prompt:

**DeepSeek Prompt** (Optimized):
```
Consolidate memory for {{user}} using structured event data.

**Current Memory** (brief structure):
Immediate: [list current immediate memories]
Recent: [list current recent memories]
Significant: [list current significant memories]
Past: [list current past memories]

**New Events** (JSON):
[
  {"ts": "Nov 5, 7:20 PM", "event": "Agreed to move in with Silas", "sig": "high", "emotion": "nervous but excited"},
  {"ts": "Nov 5, 7:45 PM", "event": "Dismissed Marcus warning text", "sig": "high", "emotion": "defensive"},
  {"ts": "Nov 5, 8:30 PM", "event": "Gabriel terrified won't eat", "sig": "medium", "emotion": "worried rationalizing"},
  {"ts": "Nov 5, 9:00 PM", "event": "Noticed Silas possessive hints", "sig": "medium", "emotion": "uneasy but dismissed"}
]

**Task**:
Generate updated memory file in markdown format:

1. **Immediate Memory**: Expand new events with vivid detail (2-3 sentences each)
2. **Recent Memory**: Move old immediate → recent (compress to 1 sentence each)
3. **Significant Memories**: Promote high-sig events if warranted (major revelations/turning points)
4. **Past Memory**: Compress older recent memories
5. **Forgotten/Fuzzy**: Add minor details from weeks ago
6. **Character perspective**: Only what {{user}} would realistically remember

**Output**: Complete updated state/user_memory.md in markdown format.
```

4. Save to `state/user_memory.md`

---

## Task 6: Save Last RP Response
**Purpose**: For /continue command next session

**Process**:
1. Find last RP story response in this conversation (with timestamp bracket)
2. Save entire response to `state/last_response.txt`

---

## Task 7: Update State Files
**Purpose**: Update tracking files for next session

**Update `state/current_state.md`**:
- Current timestamp (from last response)
- Current location (from last response)
- Current chapter (increment if needed)

**Update `state/story_arc.md`** (if major events):
- Add to "Key Recent Events"
- Update "Active Plot Threads"
- Update "Character Developments"
- Update "Next Direction"

**Create `state/session_triggers.txt`**:
```
# Relevant Entities for Next Session
Generated: [Date]

Characters:
- [Name] (Triggers: [Triggers:word1,word2'])

Locations:
- [Name] (Triggers: [Triggers:word1'])

Context: [Brief note about where story left off]
```

---

## Task 8: Increment Chapter Counter
**Purpose**: Track chapter progression

**Process**:
1. Calculate current chapter: (response_count / 25) + 1
2. Note in current_state.md

---

## FINAL OUTPUT

After completing all tasks, display:

```
✅ Session End Complete

**Generated Files**:
- sessions/Chapter_X-[Name].txt (session chatlog)
- chapters/Chapter_X.txt (chapter summary)
- state/character_updates_session_X.txt (change analysis)

**Updated Files**:
- characters/[Character].md (X characters updated)
- state/user_memory.md (memory consolidated)
- state/current_state.md (timestamp, location, chapter)
- state/last_response.txt (saved for /continue)
- state/session_triggers.txt (entities for next session)

**Session Stats**:
- Final timestamp: [timestamp]
- Final location: [location]
- Responses this session: [count]
- Chapter: [number]

**Next Session**:
Use /continue to load context and last response.
Active entities: [from session_triggers.txt]

Suggested starting point: [brief suggestion based on where session ended]
```

---

**Notes**:
- All DeepSeek calls use: `python -m work_in_progress.clients.deepseek "[prompt]"`
- Use Write tool to save all generated/updated files
- Maintain exact markdown formatting
- Focus on automation - minimize manual work
