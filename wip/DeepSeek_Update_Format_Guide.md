# DeepSeek Entity Update Formatting Guide

**Purpose:** This guide ensures entity cards track character evolution over time by preserving old information with strikethrough formatting when updates occur.

---

## Core Principle: NEVER Delete, Always Strike Through

When updating entity information that has changed, you must:
1. ✅ Keep the old information with strikethrough formatting
2. ✅ Add the new information immediately after
3. ❌ NEVER remove old information completely

This creates a living history that shows character progression.

---

## Strikethrough Format

Use double tildes `~~` for strikethrough in markdown:

```markdown
~~Old information~~ -> New information
```

**IMPORTANT**: Use ASCII arrow `->` (dash + greater-than) not Unicode arrow for compatibility with all display systems.

---

## Update Examples

### Example 1: Living Situation Changed

**Before:**
```markdown
## Living Situation
- Lives alone in downtown apartment
- Apartment is small, one bedroom
```

**After (CORRECT):**
```markdown
## Living Situation
- ~~Lives alone in downtown apartment~~ -> Lives with boyfriend Marcus in his house
- ~~Apartment is small, one bedroom~~ -> House has 3 bedrooms, suburban area
```

**After (INCORRECT - Don't do this!):**
```markdown
## Living Situation
- Lives with boyfriend Marcus in his house
- House has 3 bedrooms, suburban area
```

### Example 2: Job Changed

**Before:**
```markdown
## Employment
- **Current Job**: Barista at Coffee Corner Cafe
- **Position**: Part-time barista
- **Schedule**: Morning shifts, 5 days/week
```

**After (CORRECT):**
```markdown
## Employment
- **~~Current~~ Previous Job**: ~~Barista at Coffee Corner Cafe~~ (Chapter 1-3)
- **Current Job**: Legal Assistant at Morrison & Associates Law Firm (Chapter 4+)
- **Position**: ~~Part-time barista~~ -> Full-time legal assistant
- **Schedule**: ~~Morning shifts, 5 days/week~~ -> Standard office hours, Monday-Friday
```

### Example 3: Relationship Status Changed

**Before:**
```markdown
## Relationships
- **Marcus**: Close friend, known for 2 years
- **Alex**: Roommate
```

**After (CORRECT):**
```markdown
## Relationships
- **Marcus**: ~~Close friend~~ -> Boyfriend (started dating Chapter 3), known for 2 years
- **Alex**: ~~Roommate~~ -> Former roommate (moved out Chapter 3), still friends
```

### Example 4: Personality/Traits Evolved

**Before:**
```markdown
## Personality
- Shy and introverted
- Avoids social situations
- Nervous around strangers
```

**After (CORRECT):**
```markdown
## Personality
- ~~Shy and introverted~~ -> More confident and outgoing (growth in Chapter 4-5)
- ~~Avoids social situations~~ -> Now comfortable in small group settings
- ~~Nervous around strangers~~ -> Still cautious but more approachable
```

### Example 5: Physical Appearance Changed

**Before:**
```markdown
## Appearance
- Long brown hair
- Wears casual jeans and t-shirts
- No piercings or tattoos
```

**After (CORRECT):**
```markdown
## Appearance
- ~~Long brown hair~~ -> Short pixie cut (changed Chapter 5)
- Wears ~~casual jeans and t-shirts~~ -> More professional attire for work, casual on weekends
- ~~No piercings or tattoos~~ -> Got small wrist tattoo (Chapter 6)
```

---

## Special Cases

### Adding Completely New Information
If information is NEW (not replacing something), just add it normally:

```markdown
## Hobbies
- Loves reading mystery novels
- Plays guitar (learned in Chapter 4) ← NEW, no strikethrough needed
```

### Temporary Changes
For temporary situations, note the timeline:

```markdown
## Current Status
- ~~Living at apartment~~ -> Staying at Marcus's house temporarily (Chapter 3-4)
- Returned to apartment (Chapter 5+)
```

### Multiple Changes Over Time
Track each change chronologically:

```markdown
## Job History
- ~~Coffee Corner Cafe (Ch. 1-3)~~ -> ~~Temp agency (Ch. 4-5)~~ -> Morrison Law Firm (Ch. 6+)
```

---

## Section-Specific Guidelines

### Description Section
Keep original description, add evolution notes:

```markdown
## Description
Sarah is a ~~24~~ 25-year-old woman with ~~long brown hair~~ short pixie-cut hair and green eyes.
She is ~~shy and reserved~~ now more confident and outgoing, standing at 5'6".
Originally worked as a ~~barista~~ legal assistant.
```

### Appearances Section
ALWAYS keep all appearance entries, never delete chapters:

```markdown
## Appearances

### Chapter 1
- First mentioned at the coffee shop
- Served {{user}} a latte

### Chapter 3
- Started dating Marcus
- ~~Working at cafe~~ -> Mentioned job interview at law firm

### Chapter 5
- Now working at Morrison & Associates
- Cut hair short
```

### Notes Section
Add chronological updates:

```markdown
## Notes
- Character has undergone significant development
- Major life changes: ~~Single, living alone, barista~~ -> Dating Marcus, living together, legal assistant
- Personal growth: Became more confident and assertive over time (Ch. 1-6)
- **Last Major Update**: Chapter 6 - Got promoted to senior legal assistant
```

---

## Update Checklist

When updating an entity card, ensure you:

- [ ] Read the existing card completely
- [ ] Identify what information has CHANGED (not just added)
- [ ] Apply strikethrough to ALL changed information
- [ ] Add the new information with arrow notation (->) or inline
- [ ] Keep all Appearances entries (never delete chapters)
- [ ] Update the "Last Updated" date at bottom
- [ ] Increment the Mention Count
- [ ] Add a note in the Notes section about what changed

---

## Template for Updates

When you update an entity card, add a change log entry at the top:

```markdown
# [CHAR] Character Name

[Triggers:name,variations']

## Change Log
- **[Current Date]**: Updated living situation (moved in with partner), job (barista -> legal assistant)
- **[Previous Date]**: Initial card creation

## [Rest of card with strikethrough updates...]
```

---

## Examples of Good vs Bad Updates

### ❌ BAD - Information Lost
```markdown
## Job
- Legal Assistant at Morrison & Associates
```

### ✅ GOOD - History Preserved
```markdown
## Job
- ~~Barista at Coffee Corner Cafe (Ch. 1-3)~~ -> Legal Assistant at Morrison & Associates (Ch. 4+)
```

---

### ❌ BAD - No Context
```markdown
## Relationship
- Dating Marcus
```

### ✅ GOOD - Evolution Shown
```markdown
## Relationship
- **Marcus**: ~~Friends (Ch. 1-2)~~ -> ~~Dating (Ch. 3-4)~~ -> Living together (Ch. 5+)
```

---

## Key Reminders

1. **Preserve History**: Every change tells a story
2. **Use Strikethrough**: `~~old~~` -> new
3. **Add Timestamps**: Note which chapter changes occurred
4. **Never Delete**: Deletion removes valuable context
5. **Be Specific**: "Changed job" is vague, "Barista -> Legal Assistant" is clear

---

## For New Entity Cards

If creating a card for the first time (no existing card), use the standard format WITHOUT strikethrough:

```markdown
# [CHAR] Character Name

[Triggers:name,variations']
**Type**: Character
**First Mentioned**: Chapter X
**Mention Count**: X

## Description
[Current information, no strikethrough needed]

## Role in Story
[Current role]

[etc.]
```

Only use strikethrough when UPDATING an existing card.

---

**Remember**: The goal is to create a living document that shows character growth and change over time, not a static snapshot that loses history.
