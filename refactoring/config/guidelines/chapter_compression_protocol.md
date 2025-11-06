# Chapter Compression Protocol

## Purpose

This protocol defines how to compress completed chapters into summaries for long-term story continuity. Chapter compression serves to:
- Reduce context window usage as stories grow longer
- Preserve essential plot points, character development, and relationship dynamics
- Maintain narrative coherence across many chapters
- Enable faster chapter loading without losing critical story details

## When to Compress

Compress chapters when:
- A chapter is marked complete and the story is moving to a new chapter
- The full conversation history exceeds practical context limits
- The user explicitly requests chapter compression
- The system triggers automatic compression (based on configured thresholds)

## Compression Target

**Target Length:** Approximately 3,000 words

This length balances:
- Sufficient detail for continuity and reference
- Manageable context usage when loading multiple chapter summaries
- Preservation of character voice and relationship progression

## Compression Instructions

When compressing a chapter, follow these directives:

### Core Events & Context
- Provide **chronological progression** of key plot points
- Include essential background information introduced in this chapter
- Capture cause-and-effect chains that impact future chapters
- Note setting changes, time progression, and spatial movement
- Preserve worldbuilding details and lore revelations

### Character Dynamics
- Track the **developing relationship** between {{user}} and main characters
- Document shifts in relationship status, intimacy levels, or power dynamics
- Note character revelations, vulnerabilities shared, or trust built/broken
- Capture emotional turning points and how characters respond to each other
- Include relationship tier changes if applicable

### Intimate Moments
- Provide **detailed coverage** of intimate scenes (physical, emotional, or both)
- Include sensory details that characterize how these characters interact
- Preserve emotional beats and vulnerability
- Note progression patterns (hesitation → comfort, distance → closeness, etc.)
- Characters spend significant time together; intimate moments are major interaction sources

### Memorable Quotes
Include **8-12 direct quotes** that:
- **Reveal character personality/voice** for consistency when continuing the story
- **Mark pivotal moments** in plot or character development
- **Advance key relationships or conflicts** through dialogue
- Demonstrate character-specific speech patterns, humor, or emotional expression
- Serve as touchstones for maintaining character consistency in future chapters

**Quote Format:**
```
"[Exact dialogue]" — [Character Name], [brief context]
```

Example:
```
"You making me want it means you want me wanting it." — Silas, during negotiation of boundaries
```

### Format Requirements

**Scene Breaks:**
- Use clear scene breaks (`---` or section headers) to separate distinct sequences
- Group related events into cohesive scene blocks
- Maintain chronological flow

**Tone Preservation:**
- Match the chapter's actual tone (dark, light, tense, comfortable, etc.)
- Don't sanitize or soften events
- Preserve emotional weight and consequences

**No Conclusions:**
- **This RP is ongoing** — more chapters will follow
- Don't write chapter-ending reflections or wrap-ups
- Don't include "lessons learned" or thematic statements
- End with the chapter's final event, not analysis

## Output Format

```markdown
# Chapter [X] Summary

**Chapter Title:** [Title if applicable]
**Time Span:** [Duration covered]
**Primary Location(s):** [Key settings]
**Characters Present:** [Main participants]

## Events

[Chronological narrative of events with scene breaks]

---

## Key Character Moments

[Significant character development, dynamics, intimate scenes]

---

## Memorable Quotes

1. "[Quote]" — [Character], [context]
2. "[Quote]" — [Character], [context]
[...8-12 total quotes...]

---

## Continuity Notes

[Any unresolved threads, promises made, items carried forward, relationship status changes]
```

## Usage in Automation

When chapter compression is triggered:
1. **Agent reads this protocol** to understand compression requirements
2. **Agent receives full chapter text** from conversation history
3. **Agent applies protocol** to generate summary
4. **Summary is saved** to `state/chapters/chapter_[X]_summary.md`
5. **Future sessions load summary** instead of full conversation history for that chapter

## Quality Checks

A good chapter summary:
- ✅ Can be read by someone unfamiliar with the chapter and understood
- ✅ Preserves character voices through quotes
- ✅ Maintains emotional continuity (joy, tension, grief, intimacy)
- ✅ Includes enough sensory/behavioral detail to recreate character interaction patterns
- ✅ Avoids vague summaries like "they talked" → specify what was discussed and why it matters
- ✅ Captures relationship progression clearly (strangers → acquaintances → friends, etc.)
- ✅ Notes any physical/emotional/situational changes that affect future chapters

## Bad Summary Examples (Avoid These)

❌ **Too vague:** "They spent time together and grew closer."
✅ **Specific:** "After Lilith opened up about her past trauma with the Crimson Circle, Silas shared his own history with loss, marking the first time either character revealed genuine vulnerability. Their relationship shifted from wary allies to tentative friends."

❌ **Missing quotes:** [No dialogue included]
✅ **Includes voice:** Multiple quotes demonstrating each character's distinct speech patterns and emotional states

❌ **Sanitized tone:** "They had a disagreement but worked it out."
✅ **Authentic tone:** "Their argument escalated into shouting, with Lilith storming out and slamming the door. She didn't return for three hours. When she did, neither apologized, but Silas had made coffee — his version of a peace offering."

---

*This protocol ensures chapter summaries serve as effective narrative continuity tools while preserving the essence of character interactions and story progression.*
