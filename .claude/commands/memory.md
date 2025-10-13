Update {{user}}'s memory system - what the character would realistically remember.

## Usage

`/memory` or `/memory update` - Update memory based on recent events

## Purpose

Track what {{user}} character would realistically remember:
- Recent events fade in detail over time
- Important moments stay vivid (Significant Memories)
- Older events become vague or forgotten
- Prevents {{user}} from knowing things player knows but character doesn't

## Step 1: Check if Memory System Exists

**If state/user_memory.md doesn't exist**:
```
Memory system not set up for this RP.

Would you like to create it? This will:
- Create state/user_memory.md for {{user}} character
- Track what {{user}} realistically remembers
- Auto-update with /endSession (using DeepSeek)
- Prevent character from knowing player meta-knowledge

Create memory system? (yes/no)
```

If yes → Create from template (see Memory Template below)

## Step 2: Extract Recent Events (Compact Format)

Read:
1. Last chapter summary (chapters/Chapter [X].txt)
2. state/current_state.md (current session events)
3. Existing state/user_memory.md

**Extract events to compact JSON**:
```json
[
  {"ts": "Nov 5, 7:20 PM", "event": "brief event summary", "sig": "high/medium/low", "emotion": "emotion"},
  {"ts": "Nov 5, 8:00 PM", "event": "brief event summary", "sig": "high/medium/low", "emotion": "emotion"}
]
```

**Summarize current memory structure**:
- Immediate: [list current items]
- Recent: [list current items]
- Significant: [list current items]
- Past: [list current items]

## Step 3: Update Memory with DeepSeek (Optimized)

**Use DeepSeek to minimize cost**

**OpenRouter API**:
- Model: deepseek/deepseek-chat-v3.1
- API Key: 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

**Implementation Method**:
Use: `python -m work_in_progress.clients.deepseek "[prompt]"`

**Optimized Prompt**:
```
Update character memory for {{user}} using structured event data.

**Current Memory** (brief structure):
Immediate: [list]
Recent: [list]
Significant: [list]
Past: [list]

**New Events** (JSON):
[paste event JSON array]

**Instructions**:
1. Expand new events into "Immediate Memory" (2-3 sentences each, vivid detail)
2. Move old immediate → "Recent Memory" (compress to 1 sentence each)
3. Promote high-sig events to "Significant Memories" if warranted:
   - Major revelations or discoveries
   - Traumatic events
   - Life-changing moments
   - Important emotional beats
4. Update "Forgotten / Fuzzy" if character wouldn't remember clearly:
   - Minor details from weeks ago
   - Things character was distracted during
5. Compress "Past Memory" (older events - key points only)

**Character Perspective**: Only what {{user}} would realistically remember
- No player meta-knowledge
- Consider mental state, stress, distractions
- Natural memory fading

**Output**: Complete updated state/user_memory.md in markdown format.
```

## Step 4: Save Updated Memory

Save DeepSeek's output to `state/user_memory.md`

## Step 5: Confirm Update

```
✅ Memory updated for {{user}}

Updated sections:
- Immediate Memory: [Count] new events added
- Recent Memory: [Count] events moved from immediate
- Significant Memories: [Count] new significant events (if any)
- Forgotten/Fuzzy: [Count] items added (if any)
- Past Memory: Compressed older events

Last Updated: [Date, Chapter X]

Memory will be automatically referenced during RP to maintain realistic character knowledge.
```

---

## Memory Template (For Initial Creation)

```markdown
# {{user}} Memory - [Character Name]

**Character**: [{{user}} name]
**Last Updated**: [Date, Chapter X]

---

## Immediate Memory (Last Session/Chapter)

**These are fresh, detailed memories from the most recent events:**

- [Recent event 1 - vivid detail]
- [Recent event 2 - vivid detail]
- [Recent event 3 - vivid detail]

---

## Recent Memory (Last 2-3 Chapters)

**These memories are clear but less detailed than immediate:**

- [Event from 1-2 chapters ago - summarized]
- [Event from 1-2 chapters ago - summarized]

---

## Past Memory (Older Chapters)

**These are faded memories - key points only:**

- [Older event - general awareness, few details]
- [Older event - general awareness, few details]

---

## Significant Memories (Never Fade)

**Major moments that stay vivid regardless of time:**

### [Event Name] - Chapter [X]
- [What happened - vivid detail]
- [Why it's significant]
- [Emotional impact]

### [Event Name] - Chapter [Y]
- [What happened - vivid detail]
- [Why it's significant]
- [Emotional impact]

---

## Forgotten / Fuzzy

**Things character doesn't remember clearly or at all:**

- [Minor detail from long ago - forgotten]
- [Thing character was distracted during - fuzzy]
- [Information overload moment - partial memory only]

---

## Memory Notes

**Factors affecting {{user}}'s memory:**
- [Any relevant info: stress levels, mental state, trauma, etc.]
- [Memory quirks specific to this character]

**Meta-Knowledge {{user}} Doesn't Have:**
- [Player knows X, but character doesn't]
- [Reader knows Y, but character doesn't]
```

---

## Integration with /endSession

When `/endSession` is called:
- Automatically runs `/memory update` if memory system exists
- Uses DeepSeek to update memory (cost-effective)
- Saves updated memory for next session

No manual memory updates needed between sessions (unless desired).

---

## Manual Memory Management

### View Current Memory
```
/memory
→ Displays current state/user_memory.md
```

### Force Update
```
/memory update
→ Runs update process immediately
```

### Add Significant Memory Manually
```
/note @memory: [Event] - [Why significant]
→ Adds to Significant Memories section
```

---

## Cost Optimization

**DeepSeek for memory updates**: ~$0.14 per million tokens
- Typical memory update: ~2,000 tokens input + 1,500 tokens output
- Cost per update: ~$0.0005 (less than a penny)
- Even with auto-updates every session: Very cheap

**Memory prevents costly mistakes**:
- Character acting on information they don't have
- Breaking immersion with meta-knowledge
- Continuity errors from forgetting past events

---

## Example Memory Progression

**Session 1** (Chapter 1):
```markdown
## Immediate Memory
- Met Silas at bar, approached him
- Makeout session in parking lot
- Felt instant connection
```

**Session 5** (Chapter 5):
```markdown
## Immediate Memory
- Moved in with Silas
- Gabriel terrified, won't eat
- Marcus warned about moving in

## Recent Memory
- Started dating Silas (few weeks ago)
- Friends expressed concerns (vague memory)

## Past Memory
- Met at bar (general memory, few details)
```

**Session 10** (Chapter 10):
```markdown
## Immediate Memory
- Discovered camera in bedroom
- Silas confessed to stalking
- Confrontation about trust

## Recent Memory
- Living with Silas (last few chapters)
- Gabriel's fear escalating
- Marcus's intervention attempt

## Significant Memories
### Meeting Silas - Chapter 1
- Approached him at bar, felt instant connection
- First kiss in parking lot
- Why significant: Started the relationship

### Camera Discovery - Chapter 10
- Found hidden camera, realized extent of surveillance
- Silas's confession
- Why significant: Trust shattered, revelation of truth

## Forgotten / Fuzzy
- Exact conversations with Marcus (remembers warnings, not exact words)
- What she wore on third date (minor detail, forgotten)
```

---

**The memory system maintains character authenticity and prevents meta-knowledge bleeding into RP.**
