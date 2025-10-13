Generate an entity card using OpenRouter + DeepSeek.

## Usage

`/gencard [type], [title]` or `/gencard [type], [title], [extra info]`

**Examples**:
- `/gencard character, Marcus`
- `/gencard location, Cathedral, gothic architecture`
- `/gencard item, Hidden Camera`
- `/gencard event, First Kiss`

## Step 1: Parse Input

Extract:
- **Type**: character, location, item, or event
- **Title**: Name of entity
- **Extra Info**: Optional additional context

## Step 2: Search and Extract Entity Data (Compact)

Search recent chapters (last 2-3) and current session for mentions of [title]:
- Extract key info in compact format
- Note first appearance (chapter/timestamp)
- Count mentions (or check state/entity_tracker.json)
- Gather related entities, significance

**Extract to JSON**:
```json
{
  "entity": "[name]",
  "type": "[character/location/item/event]",
  "first_ch": X,
  "mentions": X,
  "appearances": [
    {"ch": X, "context": "brief summary"},
    {"ch": Y, "context": "brief summary"}
  ],
  "relationships": ["entity: relationship"],
  "traits": ["trait1", "trait2"] // if character
}
```

## Step 3: Generate Card with DeepSeek (Optimized)

**OpenRouter API Configuration**:
- **Endpoint**: https://openrouter.ai/api/v1/chat/completions
- **API Key**: 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
- **Model**: deepseek/deepseek-chat-v3.1

**Optimized Prompt Template**:

```
Generate entity card from structured data.

**Entity Data** (JSON):
[paste JSON from Step 2]

**Extra Info**: [if provided by user]

Task: Generate detailed entity card in markdown following this structure:

# [PREFIX] [Title]

[Triggers:[trigger1,trigger2,trigger3']]
**Type**: [from entity_data.type]
**First Mentioned**: Chapter [from entity_data.first_ch]
[Type-specific fields - see below]

## Description
[Expand from appearances.context and traits if character]

## Significance
[Deduce from appearances and relationships]

[Type-specific sections based on type]

## Appearances / Related Events
[Expand from appearances array - each entry becomes a bullet]

## Notes
[Infer additional information from data]

---

**Instructions for Type-Specific Content**:

IF CHARACTER:
- **Role**: [infer from appearances]
- **Personality**: [expand from traits array]
- **Relationships**: [expand from relationships array]

IF LOCATION:
- **Atmosphere**: [infer from appearances]
- **Frequent Visitors**: [infer from appearances]
- **Access**: [infer if possible]

IF ITEM:
- **Current Location/Owner**: [infer from latest appearance]
- **Related Events**: [from appearances]

IF EVENT:
- **When**: [from first appearance]
- **Participants**: [infer from appearances]
- **Consequences**: [infer from context]

**Triggers**: Generate 3-5 keywords in [Triggers:word1,word2,word3'] format
- Include entity name + variations
- Use exact punctuation with apostrophe at end

**Output**: ONLY the completed entity card in markdown format.
```

## Step 4: Determine Prefix

Based on type:
- `character` → `[CHAR]`
- `location` → `[LOC]`
- `item` → `[ITEM]`
- `event` → `[EVENT]`

## Step 5: Save Card

Save generated card to: `entities/[PREFIX] [Title].md`

Example: `entities/[CHAR] Marcus.md`

## Step 6: Confirm

Output:
```
✅ Entity card created: entities/[PREFIX] [Title].md

Card Details:
- Type: [type]
- Name: [title]
- Triggers: [list triggers from card]
- First Mentioned: Chapter [X]

The card will be automatically loaded when triggers are mentioned in future responses.
```

## Error Handling

**If entity not found in story**:
- Ask user for basic details
- Generate card from user-provided info instead of story context

**If type is invalid**:
- Ask user to clarify type (character/location/item/event)

**If DeepSeek API fails**:
- Fall back to template-based card
- Fill in basic info, leave detailed sections for manual completion
- Notify user of fallback

## OpenRouter Implementation Notes

**IMPORTANT - Implementation Method**:
Use the reusable DeepSeek API script located at `scripts/deepseek_call.sh`

**Usage**:
```bash
# Call the script with your prompt
RESULT=$(scripts/deepseek_call.sh "Your prompt here with all the entity context and template instructions...")

# The script handles:
# - Creating temporary JSON request
# - Calling OpenRouter API with DeepSeek
# - Parsing response
# - Cleaning up temp files
# - Returning just the generated content

# Save the result to entity file
echo "$RESULT" > "entities/[PREFIX] [Title].md"
```

**Simple Example**:
```bash
CARD=$(scripts/deepseek_call.sh "Create entity card for character named Marcus...")
echo "$CARD" > "entities/[CHAR] Marcus.md"
```

**Request JSON Structure**:
```json
{
  "model": "deepseek/deepseek-chat-v3.1",
  "messages": [
    {
      "role": "user",
      "content": "[Full prompt with entity info and template structure]"
    }
  ],
  "temperature": 0.3
}
```

**Response Structure**:
```json
{
  "choices": [
    {
      "message": {
        "content": "[Generated entity card in markdown]"
      }
    }
  ],
  "usage": {
    "total_tokens": 949
  }
}
```

Extract `choices[0].message.content` as the generated card.

---

**Cost**: ~$0.14 per million tokens with DeepSeek (very cheap for card generation)
